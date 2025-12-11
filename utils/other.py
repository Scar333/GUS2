# OLD
from difflib import SequenceMatcher
from typing import Tuple


def is_similar(str1: str, str2: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """
    Проверяет схожесть двух строк
    
    Args:
        str1: первая строка
        str2: вторая строка  
        threshold: порог схожести (0.0-1.0)
    
    Returns:
        Tuple[bool, float]: (совпадает ли, коэффициент схожести)
    """
    # Приводим к нижнему регистру для лучшего сравнения
    str1_lower = str1.lower().strip()
    str2_lower = str2.lower().strip()
    
    sim = SequenceMatcher(None, str1_lower, str2_lower).ratio()
    return sim >= threshold, sim


# NEW
# import re
# from difflib import SequenceMatcher
# from typing import Tuple, Optional, Set


# REGEX_NUMBER = re.compile(r'№\s*(\d+)', re.IGNORECASE)

# STOP_WORDS: Set[str] = {
#     'суд', 'судебный', 'участок', 'мировой', 'номер', 'no', '№',
#     'республикa', 'республики', 'республика', 'саха', 'якутия',
#     'улус', 'улуса', 'район', 'района', 'округ', 'городской',
#     'область', 'области', 'край', 'рф', 'и'
# }


# def normalize_text(text: str) -> str:
#     """Нормализация текста"""
#     normalized = text.lower().strip().replace('ё', 'е')
#     normalized = re.sub(r'республик[аи]\s+саха\s*\(якутия\)', ' ', normalized)
#     normalized = re.sub(r'[«»"(),.:;]', ' ', normalized)
#     normalized = re.sub(r'\s+', ' ', normalized).strip()
#     return normalized


# def extract_section_number(text: str) -> Optional[str]:
#     """Извлекает номер участка (строкой) из текста. Если не найден — возвращает None."""
#     match = REGEX_NUMBER.search(text)
#     return match.group(1) if match else None


# def stem_russian_token(token: str) -> str:
#     """Нормализация падежей"""
#     return re.sub(
#         r'(ский|ского|ской|ском|ские|ских|скому|ским|ская|скую|ое|ого|ому|ым|им|ом|ем|ее|ие|ые|ую|ий|ый|ая)$',
#         '',
#         token
#     )


# def build_token_set(text: str, section_number: Optional[str]) -> Set[str]:
#     """
#     Строит множество информативных токенов:
#     - выкидывает служебные слова,
#     - применяет фиксы опечаток и грубый «стемминг»,
#     - добавляет токен с номером участка, если он есть.
#     """
#     words = re.findall(r'\b[а-я\-]+\b', text)
#     tokens: Set[str] = set()

#     for word in words:
#         if word in STOP_WORDS:
#             continue
#         normalized_word = stem_russian_token(word)
#         if normalized_word and normalized_word not in STOP_WORDS:
#             tokens.add(normalized_word)

#     if section_number:
#         tokens.add(f'num_{section_number}')
#     return tokens


# def soft_token_intersection(left_tokens: Set[str], right_tokens: Set[str], similarity_threshold: float = 0.9) -> int:
#     """
#     Возвращает пересечение множеств токенов:
#     - точные совпадения считаются как 1,
#     - близкие по написанию токены (SequenceMatcher ≥ threshold) тоже считаются как 1.
#     Каждый правый токен засчитывается не более одного раза.
#     """
#     intersection_count = 0
#     used_right: Set[str] = set()

#     for left in left_tokens:
#         if left in right_tokens and left not in used_right:
#             intersection_count += 1
#             used_right.add(left)
#             continue

#         best_ratio = 0.0
#         best_right: Optional[str] = None
#         for right in (right_tokens - used_right):
#             ratio = SequenceMatcher(None, left, right).ratio()
#             if ratio > best_ratio:
#                 best_ratio = ratio
#                 best_right = right

#         if best_right and best_ratio >= similarity_threshold:
#             intersection_count += 1
#             used_right.add(best_right)

#     return intersection_count


# def sequence_similarity(a: str, b: str) -> float:
#     """
#     Классическая симметричная похожесть строк (0.0–1.0) по SequenceMatcher.
#     """
#     return SequenceMatcher(None, a, b).ratio()


# def is_similar(left_text: str, right_text: str, threshold: float = 0.7) -> Tuple[bool, float]:
#     """Проверяет, описывают ли две строки один и тот же судебный участок."""
#     left_norm = normalize_text(left_text)
#     right_norm = normalize_text(right_text)

#     left_number = extract_section_number(left_norm)
#     right_number = extract_section_number(right_norm)
#     if left_number and right_number and left_number != right_number:
#         return False, 0.0

#     left_tokens = build_token_set(left_norm, left_number)
#     right_tokens = build_token_set(right_norm, right_number)

#     if not left_tokens or not right_tokens:
#         seq_sim = sequence_similarity(left_norm, right_norm)
#         return (seq_sim >= threshold), seq_sim

#     intersection = soft_token_intersection(left_tokens, right_tokens, similarity_threshold=0.9)
#     union = len(left_tokens | right_tokens)
#     keyword_similarity = intersection / union if union else 0.0

#     seq_sim = sequence_similarity(left_norm, right_norm)
#     combined_similarity = 0.6 * keyword_similarity + 0.4 * seq_sim

#     return (combined_similarity >= threshold), combined_similarity
