# create_vector_index.py - Создание векторного индекса для поиска

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm
import pickle
import os

class VectorIndexCreator:
    """Создание FAISS индекса для быстрого поиска"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.qa_json = self.data_dir / "structured_qa.json"
        self.chunks_json = self.data_dir / "chunks_data.json"
        
        # Выходные файлы - сохраняем в C:\temp (без кириллицы)
        temp_dir = Path("C:/temp/easuz_index")
        temp_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = temp_dir / "faiss_index.bin"
        self.metadata_file = temp_dir / "index_metadata.pkl"
        
        # Модель embeddings (легкая русскоязычная)
        print("🤖 Загрузка модели embeddings...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Модель загружена\n")
    
    def load_data(self):
        """Загрузка данных"""
        print("📂 Загрузка данных...")
        
        # Q&A
        with open(self.qa_json, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
            self.qa_pairs = qa_data['qa_pairs']
        
        # Chunks
        with open(self.chunks_json, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
            self.chunks = chunks_data['chunks']
        
        print(f"✅ Загружено:")
        print(f"   - Q&A: {len(self.qa_pairs)} пар")
        print(f"   - Chunks: {len(self.chunks)} блоков\n")
    
    def create_embeddings(self):
        """Создание embeddings"""
        print("🔄 Создание embeddings...")
        
        # Тексты для векторизации
        texts = []
        metadata = []
        
        # Q&A (векторизуем вопросы)
        print("   Обработка Q&A...")
        for qa in tqdm(self.qa_pairs, desc="Q&A"):
            texts.append(qa['question'])
            metadata.append({
                'type': 'qa',
                'id': qa['id'],
                'question': qa['question'],
                'answer': qa['answer'],
                'source': qa['source']
            })
        
        # Chunks (векторизуем текст)
        print("   Обработка инструкций...")
        for chunk in tqdm(self.chunks, desc="Chunks"):
            texts.append(chunk['text'])
            metadata.append({
                'type': 'chunk',
                'id': chunk['id'],
                'text': chunk['text'],
                'source': chunk['source']
            })
        
        # Создание векторов
        print("\n🧮 Создание векторов (это займет 2-5 минут)...")
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            normalize_embeddings=True
        )
        
        print(f"✅ Создано {len(embeddings)} векторов")
        print(f"   Размерность: {embeddings.shape[1]}")
        
        return embeddings, metadata
    
    def create_faiss_index(self, embeddings, metadata):
        """Создание FAISS индекса"""
        print("\n🔍 Создание FAISS индекса...")
        
        dimension = embeddings.shape[1]
        
        # Используем Inner Product для нормализованных векторов (= Cosine Similarity)
        index = faiss.IndexFlatIP(dimension)
        
        # Добавляем векторы
        index.add(embeddings.astype('float32'))
        
        print(f"✅ Индекс создан:")
        print(f"   - Всего векторов: {index.ntotal}")
        print(f"   - Размерность: {dimension}")
        
        return index
    
    def save_index(self, index, metadata):
        """Сохранение индекса и метаданных"""
        print("\n💾 Сохранение...")
        
        # Сохраняем FAISS индекс (путь уже без кириллицы)
        faiss.write_index(index, str(self.index_file))
        print(f"✅ Индекс: {self.index_file}")
        
        # Сохраняем метаданные
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        print(f"✅ Метаданные: {self.metadata_file}")
    
    def run(self):
        """Полный процесс создания индекса"""
        print("=" * 60)
        print("🚀 СОЗДАНИЕ ВЕКТОРНОГО ИНДЕКСА")
        print("=" * 60)
        
        # Этап 1: Загрузка данных
        self.load_data()
        
        # Этап 2: Создание embeddings
        embeddings, metadata = self.create_embeddings()
        
        # Этап 3: Создание FAISS индекса
        index = self.create_faiss_index(embeddings, metadata)
        
        # Этап 4: Сохранение
        self.save_index(index, metadata)
        
        print("\n" + "=" * 60)
        print("✅ ВЕКТОРНЫЙ ИНДЕКС СОЗДАН")
        print("=" * 60)
        print(f"📊 Статистика:")
        print(f"   - Q&A пар: {len(self.qa_pairs)}")
        print(f"   - Chunks: {len(self.chunks)}")
        print(f"   - Всего векторов: {index.ntotal}")
        print(f"   - Размер индекса: {self.index_file.stat().st_size / 1024 / 1024:.1f} МБ")
        print("=" * 60)
        print(f"\n📍 Файлы сохранены в: C:\\temp\\easuz_index\\")


if __name__ == "__main__":
    creator = VectorIndexCreator()
    creator.run()