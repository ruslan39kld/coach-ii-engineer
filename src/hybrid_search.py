import os
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss
import re


class HybridSearch:
    """
    Гибридный поиск: FAISS (векторный) + BM25 (ключевые слова)
    - Индекс и метаданные берутся из /data/easuz_index/
    - BM25 строится по тем же объектам, что и в векторном индексе (общие IDs)
    Возвращает список словарей: {question, answer, source_file, score}
    """

    def __init__(self,
                 index_dir: str = "/data/easuz_index",
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "faiss_index.bin"
        self.meta_path = self.index_dir / "index_metadata.pkl"

        if not self.index_path.exists() or not self.meta_path.exists():
            raise FileNotFoundError(
                f"Не найдены файлы индекса в '{self.index_dir}'. Ожидаются: faiss_index.bin и index_metadata.pkl"
            )

        logging.info(f"[HybridSearch] Загрузка FAISS индекса из: {self.index_path}")
        self.index = faiss.read_index(str(self.index_path))

        logging.info(f"[HybridSearch] Загрузка метаданных из: {self.meta_path}")
        with open(self.meta_path, 'rb') as f:
            self.metadata = pickle.load(f)
        self.ntotal = len(self.metadata)

        # Модель для векторизации запросов (должна совпадать с индексацией)
        logging.info(f"[HybridSearch] Загрузка модели эмбеддингов: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Подготовка корпуса для BM25 (используем те же элементы, что и в FAISS)
        logging.info("[HybridSearch] Построение BM25 корпуса по метаданным индекса...")
        self.corpus_texts: List[str] = []
        for item in self.metadata:
            if item.get('type') == 'qa':
                text = f"{item.get('question', '')}\n{item.get('answer', '')}"
            else:
                # chunk
                text = item.get('text', '')
            self.corpus_texts.append(text)

        self.corpus_tokens = [self._tokenize_ru(t) for t in self.corpus_texts]
        self.bm25 = BM25Okapi(self.corpus_tokens)
        logging.info(f"[HybridSearch] BM25 готов: документов = {len(self.corpus_tokens)}")

    def _tokenize_ru(self, text: str) -> List[str]:
        # Простая токенизация по словам (кириллица/латиница/цифры)
        return [w for w in re.findall(r"[\w]+", (text or '').lower()) if len(w) > 2]

    def _encode_query(self, query: str) -> np.ndarray:
        q = self.model.encode([query], normalize_embeddings=True)
        return q.astype('float32')

    def _normalize(self, scores: np.ndarray) -> np.ndarray:
        if scores.size == 0:
            return scores
        s_min = float(scores.min())
        s_max = float(scores.max())
        if s_max - s_min < 1e-8:
            return np.zeros_like(scores)
        return (scores - s_min) / (s_max - s_min)

    def search(self, query: str, top_k: int = 5, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Гибридный поиск.
        combined = w * vector_score + (1-w) * bm25_score
        Возвращает [{question, answer, source_file, score}]
        """
        if not query:
            return []

        # 1) Векторный поиск через FAISS
        q_vec = self._encode_query(query)
        faiss_k = min(max(top_k * 5, top_k), self.index.ntotal)
        sims, idxs = self.index.search(q_vec, faiss_k)  # inner product ~ cosine
        vec_scores = sims[0]  # shape: (faiss_k,)
        vec_idxs = idxs[0]

        # Нормализуем векторные оценки в 0..1 (обычно уже 0..1, но на всякий случай)
        vec_scores_norm = self._normalize(vec_scores)

        # 2) Ключевой поиск через BM25
        q_tokens = self._tokenize_ru(query)
        bm25_scores_all = np.array(self.bm25.get_scores(q_tokens), dtype=np.float32)
        # возьмем те же кандидаты из FAISS + топ по BM25, чтобы объединить
        bm25_top_k = min(faiss_k, self.ntotal)
        bm25_top_idxs = np.argsort(-bm25_scores_all)[:bm25_top_k]
        bm25_top_scores = bm25_scores_all[bm25_top_idxs]
        bm25_scores_norm_all = self._normalize(bm25_scores_all)

        # 3) Объединяем кандидатов (множество индексов)
        candidate_set = set(vec_idxs.tolist()) | set(bm25_top_idxs.tolist())

        results: List[Dict[str, Any]] = []
        for i in candidate_set:
            m = self.metadata[i]
            v_score = 0.0
            b_score = 0.0
            # если индекс есть в выборке FAISS — берем норм. балл, иначе 0
            try:
                pos = int(np.where(vec_idxs == i)[0][0])
                v_score = float(vec_scores_norm[pos])
            except Exception:
                v_score = 0.0
            # BM25 норм. балл берём из полного массива
            b_score = float(bm25_scores_norm_all[i])

            combined = vector_weight * v_score + (1.0 - vector_weight) * b_score

            if m.get('type') == 'qa':
                question = m.get('question', '')
                answer = m.get('answer', '')
                source = m.get('source', '')
            else:
                # chunk
                question = (m.get('text', '') or '')[:200]
                answer = ''
                source = m.get('source', '')

            results.append({
                'question': question,
                'answer': answer,
                'source_file': source,
                'score': combined
            })

        # 4) Сортируем по комбинированному скору и отбираем top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        top = results[:top_k]

        logging.info(
            f"[HybridSearch] query='{query[:80]}' | vec_top={len(vec_idxs)} bm25_top={len(bm25_top_idxs)} -> return={len(top)}"
        )
        if top:
            logging.info(f"[HybridSearch] TOP1: {top[0]['question'][:80]} | score={top[0]['score']:.3f}")

        return top
