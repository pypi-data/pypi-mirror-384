from .core import is_korean, combine, normalize, extend

QWERTY = {
    'q': 'ㅂ', 'w': 'ㅈ', 'e': 'ㄷ', 'r': 'ㄱ', 't': 'ㅅ',
    'y': 'ㅛ', 'u': 'ㅕ', 'i': 'ㅑ', 'o': 'ㅐ', 'p': 'ㅔ',
    'a': 'ㅁ', 's': 'ㄴ', 'd': 'ㅇ', 'f': 'ㄹ', 'g': 'ㅎ',
    'h': 'ㅗ', 'j': 'ㅓ', 'k': 'ㅏ', 'l': 'ㅣ',
    'z': 'ㅋ', 'x': 'ㅌ', 'c': 'ㅊ', 'v': 'ㅍ', 'b': 'ㅠ',
    'n': 'ㅜ', 'm': 'ㅡ'
}

def typofix_keyboard(text: str, *, keyboard_map: dict[str, str] = None) -> str:
    """Fix text typed with the wrong keyboard layout.
    """
    if keyboard_map is None:
        keyboard_map = QWERTY
    if False in list(map(is_korean, keyboard_map.values())):
        raise ValueError("keyboard_map values must be Korean characters.")
    text = text.lower()
    new_keyboard = {}
    for key, value in keyboard_map.items():
        new_key = key.lower()
        new_value = value.lower()
        new_keyboard[new_key] = new_value
    keyboard_map = new_keyboard
    for bef, aft in keyboard_map.items():
        text = text.replace(bef, aft)
    for char in text:
        if char not in keyboard_map.values():
            raise ValueError(f"Result contains non-Korean character: {char}")
    return text

def spacing(text: str) -> str:
    """Add spacing between Korean and non-Korean characters"""
    spaced = ""
    for i in range(len(text)-1):
        spaced += text[i]
        if is_korean(text[i]) != is_korean(text[i+1]):
            spaced += " "
    return spaced + text[-1]