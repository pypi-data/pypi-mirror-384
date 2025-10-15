"""
a package for korean texts
"""

from .core import vowels, consonants, extend, combine, group, finals, is_korean, get_sound, from_sound, words, to_korean, from_korean, to_int, from_int, korean_ratio, fully_korean, PERCENTAGE, PERCENTAGE_UNTIL_1, PERCENTAGE_UNTIL_2, from_datetime, to_datetime, similarity, fix_spelling, japanese_sound, symbol_to_korean, convert_halfwidth, convert_fullwidth
from .games import ConcludingRemarksGame, ConcludingRemarksRobot, ConsonantQuiz, ConsonantQuizRobot
from .typofix import typofix_keyboard, QWERTY, spacing
from .holiday import is_korean_holiday

__all__ = ["vowels", "consonants", "extend", "combine", "group", "finals", "is_korean", "get_sound", "from_sound", "words", "to_korean", "from_korean", "to_int", "from_int", "korean_ratio", "fully_korean", "PERCENTAGE", "PERCENTAGE_UNTIL_1", "PERCENTAGE_UNTIL_2", "from_datetime", "to_datetime", "similarity", "fix_spelling", "ConcludingRemarksGame", "ConcludingRemarksRobot", "ConsonantQuiz", "ConsonantQuizRobot", "typofix_keyboard", "QWERTY", "spacing", "japanese_sound", "symbol_to_korean", "symbol_to_korean", "convert_halfwidth", "convert_fullwidth", "is_korean_holiday"]