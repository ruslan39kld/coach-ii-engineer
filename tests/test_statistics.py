import sys
import time
from pathlib import Path
from statistics import mean

# Ensure src is importable
sys.path.append(str(Path(__file__).parent / 'src'))

from hybrid_search import HybridSearch

try:
    from colorama import init as colorama_init, Fore, Style
except ImportError:
    print("colorama не установлена. Установите: pip install colorama")
    sys.exit(1)


def color_for_score(s: float) -> str:
    if s > 0.9:
        return Fore.GREEN
    if s >= 0.7:
        return Fore.YELLOW
    return Fore.RED


def print_divider():
    print("\n" + "-" * 80)


def safe_text(s: str) -> str:
    """Return string safe for current console encoding (strip unencodable chars)."""
    enc = (getattr(sys.stdout, 'encoding', None) or 'utf-8')
    try:
        return (s or '').encode(enc, errors='ignore').decode(enc, errors='ignore')
    except Exception:
        return (s or '').encode('cp1251', errors='ignore').decode('cp1251', errors='ignore')


def main():
    # Improve ANSI handling on Windows terminals
    colorama_init(autoreset=True, strip=False, convert=True)
    # Try to ensure stdout can handle UTF-8; still guard with safe_text
    try:
        sys.stdout.reconfigure(encoding=sys.stdout.encoding or 'utf-8', errors='ignore')
    except Exception:
        pass

    hs = HybridSearch()

    questions = [
        # Простые (прямые совпадения)
        "Как создать запрос на снятие признака МВК?",
        "Что делать после выбора основания запроса?",
        "Как опубликовать план-график закупок?",
        "Где изменить КТРУ позицию?",
        # Средние (перефразированные)
        "Нужно ли согласование, если не подпадает под МВК?",
        "Какие действия после выбора основания для обращения?",
        "Порядок отмены закупки в ЕАСУЗ",
        "Как оформить запрос по признаку МВК?",
        # Сложные (контекст)
        "Когда требуется МВК и что делать при отсутствии признака?",
        "Как скорректировать лоты в плане-графике перед публикацией?",
        "Алгоритм формирования запроса в ЕАСУЗ при ошибке выбора основания",
        "Изменение позиции с учетом КТРУ и требований закупки",
        "Нужно ли дополнительно согласовывать, если МВК неприменим?",
        "Шаги по снятию признака МВК и последующие действия",
        "Как закрыть закупку и отменить публикацию в системе?",
    ]

    top1_scores = []
    times_ms = []

    for q in questions:
        print_divider()
        print(f"Вопрос: {Style.BRIGHT}{safe_text(q)}{Style.RESET_ALL}")

        t0 = time.time()
        results = hs.search(q, top_k=3, vector_weight=0.7)
        dt_ms = (time.time() - t0) * 1000.0
        times_ms.append(dt_ms)

        if results:
            top1_scores.append(float(results[0].get('score', 0.0)))
        else:
            top1_scores.append(0.0)

        for i, r in enumerate(results[:3], 1):
            score = float(r.get('score', 0.0))
            clr = color_for_score(score)
            src = safe_text(r.get('source_file', '') or '-')
            ans = safe_text(r.get('answer', '') or '')
            ans_snip = ans[:100].replace('\n', ' ')
            print(f"  {i}. {clr}score={score:.3f}{Style.RESET_ALL} | source={src}")
            print(f"     Q: {safe_text(r.get('question',''))[:120]}")
            print(f"     A: {ans_snip}")

        print(f"Время поиска: {dt_ms:.1f} ms")

    print_divider()
    print("ИТОГОВАЯ СТАТИСТИКА")
    print_divider()

    avg_score = mean(top1_scores) if top1_scores else 0.0
    min_score = min(top1_scores) if top1_scores else 0.0
    max_score = max(top1_scores) if top1_scores else 0.0
    avg_time = mean(times_ms) if times_ms else 0.0

    pct_08 = 100.0 * sum(1 for s in top1_scores if s > 0.8) / len(top1_scores) if top1_scores else 0.0
    pct_09 = 100.0 * sum(1 for s in top1_scores if s > 0.9) / len(top1_scores) if top1_scores else 0.0

    def colorize_val(val: float) -> str:
        return color_for_score(val) + f"{val:.3f}" + Style.RESET_ALL

    print(f"Средний score (top1): {colorize_val(avg_score)}")
    print(f"Минимальный score (top1): {colorize_val(min_score)}")
    print(f"Максимальный score (top1): {colorize_val(max_score)}")
    print(f"Среднее время поиска: {avg_time:.1f} ms")
    print(f"% вопросов со score > 0.8: {pct_08:.1f}%")
    print(f"% вопросов со score > 0.9: {pct_09:.1f}%")


if __name__ == "__main__":
    main()
