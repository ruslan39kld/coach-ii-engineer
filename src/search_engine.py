# search_engine.py - Поисковая система с embeddings

import faiss
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer

class SearchEngine:
    """Поисковая система для Q&A и инструкций"""
    
    def __init__(self):
        # Пути к индексу
        self.index_path = Path("/data/easuz_index/faiss_index.bin")
        self.metadata_path = Path("/data/easuz_index/index_metadata.pkl")
        
        # Загрузка модели
        print("🤖 Загрузка модели...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Загрузка индекса
        print("📂 Загрузка индекса...")
        self.index = faiss.read_index(str(self.index_path))
        
        # Загрузка метаданных
        with open(self.metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        
        print(f"✅ Загружено: {self.index.ntotal} векторов\n")
    
    def search_qa_only(self, query, top_k=3):
        """Поиск только в Q&A"""
        # Создаем вектор запроса
        query_vector = self.model.encode([query], normalize_embeddings=True)
        
        # Поиск ближайших векторов
        distances, indices = self.index.search(
            query_vector.astype('float32'), 
            20
        )
        
        # Фильтруем только Q&A
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata) and self.metadata[idx]['type'] == 'qa':
                # Для IndexFlatIP distance = cosine similarity (уже от 0 до 1)
                score = float(distance)
                results.append({
                    'score': score,
                    'data': self.metadata[idx]
                })
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_answer(self, query):
        """Получить ответ на вопрос"""
        qa_results = self.search_qa_only(query, top_k=3)
        
        # ДИАГНОСТИКА: Покажем топ-3 результата
        print(f"   🔍 Найдено {len(qa_results)} результатов:")
        for i, r in enumerate(qa_results, 1):
            print(f"      {i}. Score: {r['score']:.3f} | Q: {r['data']['question'][:60]}...")
        
        if qa_results and qa_results[0]['score'] > 0.5:
            result = qa_results[0]
            return {
                'found': True,
                'answer': result['data']['answer'],
                'source': result['data']['source'],
                'confidence': result['score'],
                'question': result['data']['question']
            }
        else:
            return {
                'found': False,
                'answer': None,
                'confidence': qa_results[0]['score'] if qa_results else 0.0
            }


# Тестирование
if __name__ == "__main__":
    print("=" * 80)
    print("🔍 ТЕСТИРОВАНИЕ ВЕКТОРНОГО ПОИСКА")
    print("=" * 80)
    
    engine = SearchEngine()
    
    # Тестовые вопросы
    test_queries = [
        "как зарегистрироваться в системе",
        "заполнить блок кандидатуры",
        "создать закупку"
    ]
    
    for query in test_queries:
        print(f"\n📝 Вопрос: '{query}'")
        print("-" * 80)
        
        result = engine.get_answer(query)
        
        if result['found']:
            print(f"✅ НАЙДЕНО (уверенность: {result['confidence']:.1%})")
            print(f"❓ Похожий вопрос: {result['question']}")
            print(f"💬 Ответ: {result['answer'][:150]}...")
            print(f"📚 Источник: {result['source']}")
        else:
            print("❌ Ответ не найден")
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)