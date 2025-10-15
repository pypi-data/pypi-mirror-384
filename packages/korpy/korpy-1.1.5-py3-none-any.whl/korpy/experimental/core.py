from ..core import similarity, words
from functools import lru_cache
from typing import Union

@lru_cache(maxsize=1)
def _cached_words(source=None, filter=True):
    return tuple(words(source=source, filter=filter))


def accuracy_per_word(
    word: str,
    *,
    sort: bool = False,
    allow_sentence: bool = False,
    style: str = None,
    source: str = None,
    filter: bool = True
) -> Union[str, float]:
    """
    a function that gives you all accuracy per words
    """
    all_words = _cached_words(source=source, filter=filter)

    scored = [(similarity(word, w, allow_sentence=allow_sentence), w) for w in all_words]

    if sort:
        scored.sort(key=lambda x: x[0], reverse=True)

    if style is not None:
        return style % (scored[0][0] * 100)
    else:
        return scored[0][0]