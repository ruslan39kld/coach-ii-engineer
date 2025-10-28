import time
import logging
import sys
from pathlib import Path
import re
import sqlite3

sys.path.append(str(Path(__file__).parent / 'src'))

from database import Database
from hybrid_search import HybridSearch
import config


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def tokenize(text: str):
    return [w for w in re.findall(r"[\w]+", (text or '').lower()) if len(w) > 2]


def relevance_score(query: str, text: str) -> int:
    q_tokens = set(tokenize(query))
    t_tokens = set(tokenize(text))
    return len(q_tokens & t_tokens)


def safe_text(s: str) -> str:
    enc = (getattr(sys.stdout, 'encoding', None) or 'utf-8')
    try:
        return (s or '').encode(enc, errors='ignore').decode(enc, errors='ignore')
    except Exception:
        return (s or '').encode('cp1251', errors='ignore').decode('cp1251', errors='ignore')


def sp(s: str) -> None:
    print(safe_text(s))


def print_results(title: str, results: list, query: str, kind: str):
    print("\n" + "-" * 60)
    print(f"{title} ({kind})")
    print("-" * 60)
    for i, r in enumerate(results, 1):
        if kind == 'LIKE':
            content = r.get('content', '')
            title_txt = r.get('title', '')
            rel = relevance_score(query, content)
            print(f"{i}. {title_txt[:80]} | rel={rel}")
        else:
            q = r.get('question', '')
            a = r.get('answer', '')
            s = float(r.get('score', 0))
            rel = relevance_score(query, q + "\n" + a)
            print(f"{i}. {q[:80]} | score={s:.3f} | rel={rel}")


def run_test():
    db = Database(config.DB_PATH)
    hs = HybridSearch()

    queries = [
        "Что делать после выбора основания запроса?",
        "Как создать запрос на снятие признака МВК?",
        "Нужно ли согласовывать если не попадает под МВК?",
        "Как опубликовать план-график закупок?",
        "Где изменить КТРУ позицию?",
        "Как отменить закупку в ЕАСУЗ?",
    ]

    like_better = 0
    hybrid_better = 0
    details = []  # per-query detail storage
    top1_scores = []
    times_ms = []

    for q in queries:
        print("\n" + "=" * 60)
        print(f"QUERY: {q}")
        print("=" * 60)

        t0 = time.time()
        like = db.search_documents(q, limit=5)
        t_like = (time.time() - t0) * 1000

        t1 = time.time()
        hybrid = hs.search(q, top_k=5, vector_weight=0.7)
        t_hybrid = (time.time() - t1) * 1000
        times_ms.append(t_hybrid)

        # Metrics
        like_rel = max([relevance_score(q, r.get('content','')) for r in like] + [0])
        hybrid_rel = max([relevance_score(q, r.get('question','') + "\n" + r.get('answer','')) for r in hybrid] + [0])

        print_results("LIKE search results", like, q, kind='LIKE')
        print(f"LIKE: found={len(like)} | best_rel={like_rel} | time_ms={t_like:.1f}")

        print_results("Hybrid search results", hybrid, q, kind='HYBRID')
        print(f"HYBRID: found={len(hybrid)} | best_rel={hybrid_rel} | time_ms={t_hybrid:.1f}")
        # Store details for later detailed section
        top_score = float(hybrid[0].get('score', 0.0)) if hybrid else 0.0
        top1_scores.append(top_score)
        details.append({
            'query': q,
            'results': hybrid[:3],
            'time_ms': t_hybrid
        })

        if hybrid_rel > like_rel:
            hybrid_better += 1
        elif like_rel > hybrid_rel:
            like_better += 1

    print("\n" + "#" * 60)
    print("ИТОГИ")
    print("#" * 60)
    print(f"Лучше LIKE: {like_better} запрос(ов)")
    print(f"Лучше HYBRID: {hybrid_better} запрос(ов)")
    if hybrid_better >= like_better:
        sp("✅ Гибридный поиск показывает улучшение или не хуже по релевантности на данных запросах")
    else:
        sp("⚠️ Требуется донастройка параметров вектор_weight/корпуса")

    # ===================== Новая секция: Детальный анализ =====================
    print("\n" + "=" * 60)
    sp("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ЗАПРОСОВ")
    print("=" * 60)

    def fetch_full_answer(question_text: str) -> str:
        try:
            conn = sqlite3.connect(config.DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT answer FROM faq WHERE question = ?", (question_text,))
            row = cur.fetchone()
            conn.close()
            return row[0] if row and row[0] else ""
        except Exception:
            return ""

    def assess(score: float) -> str:
        if score > 0.85:
            return "✅"
        if score >= 0.6:
            return "⚠️"
        return "❌"

    for idx, info in enumerate(details, 1):
        print("\n" + "=" * 60)
        sp(f"🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ЗАПРОСА #{idx}")
        print("=" * 60)
        sp(f"❓ Запрос пользователя: {info['query']}")
        sp("\n📊 ТОП-3 результата HYBRID поиска:")
        for j, r in enumerate(info['results'], 1):
            score = float(r.get('score', 0.0))
            mark = assess(score)
            q_text = r.get('question', '') or ''
            a_text = r.get('answer', '') or ''
            # Если ответа нет, пробуем достать из FAQ по полному вопросу
            if not a_text and q_text:
                full_a = fetch_full_answer(q_text)
                if full_a:
                    a_text = full_a
            a_snip = (a_text[:200] + ("..." if len(a_text) > 200 else "")).replace('\n', ' ')
            if j == 1:
                sp(f"\n1️⃣ Score: {score:.3f} | Time: {info['time_ms']:.0f}ms | Оценка: {mark}")
            else:
                sp(f"\n{j}️⃣ Score: {score:.3f} | Оценка: {mark}")
            sp(f"   📝 Вопрос из базы: {q_text}")
            sp(f"   💬 Ответ (первые 200 символов): {a_snip}")

    # ===================== Итоговая статистика точности =====================
    print("\n" + "#" * 60)
    sp("📊 ИТОГОВАЯ СТАТИСТИКА ТОЧНОСТИ")
    print("#" * 60)

    total = len(details)
    exact = sum(1 for s in top1_scores if s > 0.85)
    partial = sum(1 for s in top1_scores if 0.6 <= s <= 0.85)
    none = sum(1 for s in top1_scores if s < 0.6)

    avg_score = sum(top1_scores) / total if total else 0.0
    min_score = min(top1_scores) if top1_scores else 0.0
    max_score = max(top1_scores) if top1_scores else 0.0
    avg_time = sum(times_ms) / total if total else 0.0

    pct = lambda x: (100.0 * x / total) if total else 0.0
    exact_pct = pct(exact)
    partial_pct = pct(partial)
    none_pct = pct(none)
    overall_success = exact + partial
    overall_success_pct = pct(overall_success)

    print(f"Всего тестовых запросов: {total}")
    print("\nТочность TOP-1 результата:")
    sp(f"  ✅ Точные совпадения (score > 0.85): {exact} запросов ({exact_pct:.1f}%)")
    sp(f"  ⚠️ Частичные совпадения (score 0.6-0.85): {partial} запросов ({partial_pct:.1f}%)")
    sp(f"  ❌ Нерелевантные (score < 0.6): {none} запросов ({none_pct:.1f}%)")

    sp(f"\n📈 Общая успешность: {overall_success_pct:.1f}% (точные + частичные)")
    print("\nПроизводительность:")
    sp(f"  Средний score TOP-1: {avg_score:.3f}")
    sp(f"  ⚡ Среднее время поиска: {avg_time:.1f}ms")
    sp(f"  📊 Лучший score: {max_score:.3f}")
    sp(f"  📉 Худший score: {min_score:.3f}")

    # Сравнение с LIKE — уже посчитано ранее
    total_q = total if total else 1
    print("\nСравнение с LIKE:")
    sp(f"  🎯 HYBRID лучше: {hybrid_better} из {total} запросов ({(100.0*hybrid_better/total_q):.1f}%)")
    sp(f"  📊 LIKE лучше: {like_better} из {total} запросов ({(100.0*like_better/total_q):.1f}%)")

    goal_met = overall_success_pct >= 85.0
    sp("\n🎯 ВЫВОД: Точность " + ("ДОСТИГНУТА ✅" if goal_met else "НЕ ДОСТИГНУТА ❌"))
    sp(f"Целевая точность 85-90%: текущая {overall_success_pct:.1f}%")


if __name__ == "__main__":
    run_test()
