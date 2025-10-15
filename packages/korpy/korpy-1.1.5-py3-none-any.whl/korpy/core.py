from typing import Literal, Union, Annotated
import urllib.request
from deep_translator import GoogleTranslator
from datetime import datetime
from functools import lru_cache

PERCENTAGE: Annotated[str, "a formatting text for percentage (round to the nearest 1%)"] = "%.f%%"
PERCENTAGE_UNTIL_1: Annotated[str, "a formatting text for percentage (round to the nearest 0.1%)"] = "%.1f%%"
PERCENTAGE_UNTIL_2: Annotated[str, "a formatting text for percentage (round to the nearest 0.01%)"] = "%.2f%%"

vowels: Annotated[list[str], "korean vowels"] = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
consonants: Annotated[list[str], "korean consonants (initals)"] = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
finals: Annotated[list[str], "korean finals (supports)"] = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

def is_korean(char: str) -> bool:
    cp = ord(char)
    return (
        0x1100 <= cp < 0x1200 or 
        0x3130 <= cp < 0x3190 or 
        0xA960 <= cp < 0xA980 or 
        0xD7B0 <= cp < 0xD800 or 
        0xAC00 <= cp <= 0xD7A3
    )

def group(group_name: Literal['Hangul Jamo', 'Hangul Compatibility Jamo', 'Hangul Jamo Extended-A', 'Hangul Jamo Extended-B', 'Hangul Syllables']) -> range:
    match group_name:
        case 'Hangul Jamo':
            return range(0x1100, 0x1200)
        case 'Hangul Compatibility Jamo':
            return range(0x3130, 0x3190)
        case 'Hangul Jamo Extended-A':
            return range(0xA960, 0xA980)
        case 'Hangul Jamo Extended-B':
            return range(0xD7B0, 0xD800)
        case 'Hangul Syllables':
            return range(0xAC00, 0xD7A4)

def _esc(s: str):
    return "".join(
        "\\u{:04X}".format(ord(c)) if ord(c) <= 0xFFFF else "\\U{:08X}".format(ord(c))
        for c in s
    )

def _no_finals():
    return [0xAC00 + (L * 21 * 28) + (V * 28) for L in range(19) for V in range(21)]

def _with_finals():
    return [0xAC00 + (L * 21 * 28) + (V * 28) + T for L in range(19) for V in range(21) for T in range(1, 28)]

def _find(obj, sized):
    try:
        return sized.index(obj)
    except ValueError:
        return None

def combine(s: Union[str, bytes], *, ensure_korean: bool = True, only_syl: bool = False) -> Union[str, bytes]:
    savetype = type(s)
    if isinstance(s, bytes):
        s = s.decode("utf-8")
    generated_string = []
    nofinals = _no_finals()
    for char in s:
        if generated_string and generated_string[-1] in consonants and char in vowels:
            idx_c = _find(generated_string[-1], consonants) or 0
            idx_v = _find(char, vowels) or 0
            new_unicode = 0xAC00 + idx_c * 21 * 28 + idx_v * 28
            generated_string[-1] = chr(new_unicode)
            continue
        if generated_string and ord(generated_string[-1]) in nofinals and char in finals:
            old_unicode = ord(generated_string[-1])
            idx_t = _find(char, finals) or 0
            new_unicode = old_unicode + idx_t
            generated_string[-1] = chr(new_unicode)
            continue
        if ensure_korean and not is_korean(char):
            generated_string.append(_esc(char))
        else:
            generated_string.append(char)
    if only_syl and len(generated_string) > 1:
        raise ValueError("found multi-syllable string")
    result = "".join(generated_string)
    if savetype is bytes:
        result = result.encode("utf-8")
    return result

def extend(s: Union[str, bytes], *, ensure_korean: bool = True, only_syl: bool = False) -> Union[str, bytes]:
    savetype = type(s)
    if isinstance(s, bytes):
        s = s.decode("utf-8")
    if only_syl and len(s) > 1:
        raise ValueError("found multi-syllable string")
    generated_string = []
    for char in s:
        if not is_korean(char):
            if ensure_korean:
                generated_string.append(_esc(char))
            else:
                generated_string.append(char)
            continue
        old_unicode = ord(char) - 0xAC00
        idx_c = old_unicode // (21 * 28)
        idx_v = (old_unicode % (21 * 28)) // 28
        idx_t = (old_unicode % (21 * 28)) % 28
        generated_string.append(consonants[idx_c])
        generated_string.append(vowels[idx_v])
        generated_string.append(finals[idx_t])
    result = "".join(generated_string)
    if savetype is bytes:
        result = result.encode("utf-8")
    return result

def get_sound(s: Union[str, bytes], *, only_korean: bool = True) -> Union[str, bytes]:
    generated_string = ""
    consonants_match = {"ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b", "ㅃ": "pp", "ㅅ": "s", "ㅆ": "ss", "ㅇ": "",  "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p", "ㅎ": "h"}
    vowels_match = {"ㅏ": "a","ㅐ": "ae","ㅑ": "ya","ㅒ": "yae","ㅓ": "eo","ㅔ": "e","ㅕ": "yeo","ㅖ": "ye","ㅗ": "o","ㅘ": "wa","ㅙ": "wae","ㅚ": "oe","ㅛ": "yo","ㅜ": "u","ㅝ": "wo","ㅞ": "we","ㅟ": "wi","ㅠ": "yu","ㅡ": "eu","ㅢ": "ui","ㅣ": "i"}
    finals_match = {"": "", "ㄱ": "k","ㄲ": "k","ㄳ": "k","ㄴ": "n","ㄵ": "n","ㄶ": "n","ㄷ": "t","ㄹ": "l","ㄺ": "k","ㄻ": "m","ㄼ": "p","ㄽ": "l","ㄾ": "l","ㄿ": "p","ㅀ": "l","ㅁ": "m","ㅂ": "p","ㅄ": "p","ㅅ": "t","ㅆ": "t","ㅇ": "ng","ㅈ": "t","ㅊ": "t","ㅋ": "k","ㅌ": "t","ㅍ": "p","ㅎ": "t"}
    for char in s:
        if only_korean and not is_korean(char):
            raise ValueError(f"Non-Korean character detected: {char}")
        decomposed = extend(char)
        initial, vowel, final = decomposed[0], decomposed[1], decomposed[2]
        generated_string += consonants_match.get(initial, "")
        generated_string += vowels_match.get(vowel, "")
        generated_string += finals_match.get(final, "")
    return generated_string

def from_sound(s: Union[str, bytes]) -> Union[str, bytes]:
    if isinstance(s, bytes):
        s = s.decode("utf-8")
    consonants_match = {
        "g": "ㄱ", "kk": "ㄲ", "n": "ㄴ", "d": "ㄷ", "tt": "ㄸ",
        "r": "ㄹ", "m": "ㅁ", "b": "ㅂ", "pp": "ㅃ", "s": "ㅅ",
        "ss": "ㅆ", "": "ㅇ", "j": "ㅈ", "jj": "ㅉ", "ch": "ㅊ",
        "k": "ㅋ", "t": "ㅌ", "p": "ㅍ", "h": "ㅎ"
    }
    vowels_match = {
        "a": "ㅏ","ae": "ㅐ","ya": "ㅑ","yae": "ㅒ","eo": "ㅓ","e": "ㅔ",
        "yeo": "ㅕ","ye": "ㅖ","o": "ㅗ","wa": "ㅘ","wae": "ㅙ","oe": "ㅚ",
        "yo": "ㅛ","u": "ㅜ","wo": "ㅝ","we": "ㅞ","wi": "ㅟ","yu": "ㅠ",
        "eu": "ㅡ","ui": "ㅢ","i": "ㅣ"
    }
    result_jamo = []
    i = 0
    while i < len(s):
        matched = False
        for length in (3, 2, 1):
            chunk = s[i:i+length]
            if chunk in consonants_match:
                result_jamo.append(consonants_match[chunk])
                i += length
                matched = True
                break
            if chunk in vowels_match:
                result_jamo.append(vowels_match[chunk])
                i += length
                matched = True
                break
        if not matched:
            result_jamo.append(s[i])
            i += 1
    generated_string = combine("".join(result_jamo))
    return generated_string.encode() if isinstance(s, bytes) else generated_string

def words(*, source: str = None, filter: bool = True) -> list:
    url = "https://raw.githubusercontent.com/acidsound/korean_wordlist/master/wordslistUnique.txt"
    if source != None:
        url = source
    urllib.request.urlretrieve(url, "korean_words.txt")
    with open("korean_words.txt", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    if filter:
        words = [w for w in words if all('가' <= ch <= '힣' for ch in w) and len(w) >= 2]
    return words

def to_korean(text: str, *, start: str = None) -> str:
    if start == None:
        start = "auto"
    translator = GoogleTranslator(source=start, target="ko")
    return translator.translate(text)

def from_korean(text: str, *, destination: str) -> str:
    translator = GoogleTranslator(source="ko", target=destination)
    return translator.translate(text)

def to_int(korean_text: str, *, needs_place_values: bool = True) -> int:
    value_match = {"일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
                   "육": 6, "칠": 7, "팔": 8, "구": 9, "영": 0, "공": 0}
    place_match = {"십":1e+1,"백":1e+2,"천":1e+3,"만":1e+4,"억":1e+8,
                   "조":1e+12,"경":1e+16,"해":1e+20,"자":1e+24,"양":1e+28,
                   "구":1e+32,"간":1e+36,"정":1e+40,"재":1e+44,"극":1e+48,
                   "항하사":1e+52,"아승기":1e+56,"나유타":1e+60,"불가사의":1e+64,
                   "무량대수":1e+68}
    if not needs_place_values:
        digits = [str(value_match[ch]) for ch in korean_text if ch in value_match]
        return int("".join(digits)) if digits else 0
    total = 0
    section = 0
    num = 0
    for ch in korean_text:
        if ch in value_match:
            num = value_match[ch]
        elif ch in place_match:
            unit = place_match[ch]
            if unit >= 1e+4:
                section = (section + (num or 1)) * unit
                total += section
                section = 0
            else:
                section += (num or 1) * unit
            num = 0
        else:
            raise ValueError(f"Unknown character: {ch}")
    return int(total + section + num)

digits = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
units = ["", "십", "백", "천"]
big_units = ["", "만", "억", "조", "경"]

def from_int(num: int, *, include_place_values: bool=True) -> str:
    if num == 0:
        return "영"

    parts = []
    unit_index = 0

    while num > 0:
        chunk = num % 10000
        num //= 10000

        if chunk:
            chunk_str = _convert_chunk(chunk, include_place_values)
            if big_units[unit_index]:
                chunk_str += big_units[unit_index]
            parts.append(chunk_str)

        unit_index += 1

    return ''.join(reversed(parts))

def _convert_chunk(chunk: int, include_place_values=True) -> str:
    result = []
    for i, unit in enumerate(units):
        digit = chunk % 10
        chunk //= 10
        if digit:
            if include_place_values:
                result.append(digits[digit] + unit)
            else:
                result.append(digits[digit])
    return ''.join(reversed(result))

def korean_ratio(text: str, *, style: str = None) -> Union[float, str]:
    pct_count_int = 0
    for char in text:
        pct_count_int += is_korean(char)
    pct_float = pct_count_int / len(text)
    if style == None:
        return pct_float
    else:
        return style % (pct_float * 100)

def fully_korean(text: str) -> bool:
    return korean_ratio(text, style="%.f%%") == "100%"

def from_datetime(dt: datetime, *, place_values: bool = True, has_seperators: bool = True) -> str:
    y = dt.year
    m = dt.month
    d = dt.day
    h = dt.hour
    m2 = dt.minute
    s = dt.second
    ms = dt.microsecond
    if has_seperators:
        return f"{from_int(y, include_place_values=place_values)}년 {from_int(m, include_place_values=place_values)}월 {from_int(d, include_place_values=place_values)}일 {from_int(h, include_place_values=place_values)}시 {from_int(m2, include_place_values=place_values)}분 {from_int(s, include_place_values=place_values)}초 {from_int(ms, include_place_values=place_values)}마이크로초"
    else:
        return f"{from_int(y, include_place_values=place_values)} {from_int(m, include_place_values=place_values)} {from_int(d, include_place_values=place_values)} {from_int(h, include_place_values=place_values)} {from_int(m2, include_place_values=place_values)} {from_int(s, include_place_values=place_values)} {from_int(ms, include_place_values=place_values)}"

def to_datetime(text: str, *, needs_place_values: bool = True, needs_seperators: bool = True) -> datetime:
    text = text[:-4]
    splitted = text.split(" ")
    if needs_seperators:
        for index in range(len(splitted)):
            splitted[index] = splitted[index][:-1]
    all_inputs = []
    for s in splitted:
        all_inputs.append(to_int(s, needs_place_values=needs_place_values))
    return datetime(*all_inputs)

_HANGUL_SYLLABLES = tuple(group('Hangul Syllables'))

def similarity(word1: str, word2: str, *, allow_sentence: bool = False, style: str = None) -> Union[str, float]:
    """
    a function that checks similarity with two korean texts
    """
    if (len(word1.split(" ")) > 1 or len(word2.split(" ")) > 1) and not allow_sentence:
        raise ValueError("sentence found")
    
    length = max(len(word1), len(word2))
    point = 0.0
    for c1, c2 in zip(word1, word2):
        u1, u2 = ord(c1), ord(c2)
        if u1 in _HANGUL_SYLLABLES and u2 in _HANGUL_SYLLABLES:
            point += (1 - abs(u1 - u2) / len(_HANGUL_SYLLABLES)) / length
        else:
            point += 0.0
    
    if style is None:
        return point
    else:
        return style % (point * 100)

def fix_spelling(word: str, words_list: list) -> str:
    """
    a function that fixes spelling
    """
    return max(words_list, key=lambda w: similarity(word, w, allow_sentence=True))

def normalize(char: str) -> str:
    """
    normalizes (breaks down) the compounds, complexes, ancients, parts
    """
    korean_normalization = {
        "ㄲ": "ㄱㄱ",
        "ㄳ": "ㄱㅅ",
        "ㄵ": "ㄴㅈ",
        "ㄶ": "ㄴㅎ",
        "ㄺ": "ㄹㄱ",
        "ㄻ": "ㄹㅁ",
        "ㄼ": "ㄹㅂ",
        "ㄽ": "ㄹㅅ",
        "ㄾ": "ㄹㅌ",
        "ㄿ": "ㄹㅍ",
        "ㅀ": "ㄹㅎ",
        "ㅄ": "ㅂㅅ",
        "ㅆ": "ㅅㅅ",
        "ㅘ": "ㅗㅏ",
        "ㅙ": "ㅗㅐ",
        "ㅚ": "ㅗㅣ",
        "ㅝ": "ㅜㅓ",
        "ㅞ": "ㅜㅔ",
        "ㅟ": "ㅜㅣ",
        "ㅢ": "ㅡㅣ",
        "ㅿ": "ㅅ",
        "ㆁ": "ㅇ",
        "ㆆ": "ㅎ", 
        "ᄛ": "ㅅㅅ", 
        "ᄣ": "ㅅㅎ", 
        "ᄦ": "ㅂㅅㅈ", 
        "ᅇ": "ㅎ",   
        "ᅌ": "ㅇ",   
        "ᅎ": "ㅈㅎ",
        "ㆍ": "ㅏ",
        "ㆎ": "ㅐ",
        "ᆢ": "ㅡㅡ"
    }
    for raw, new in korean_normalization:
        if char == raw:
            return new
    return char

def japanese_sound(japanese_text: str) -> str:
    """
    converts japanese text to korean sound
    """
    kana2hangul = {
        'あ':'아','い':'이','う':'우','え':'에','お':'오',
        'か':'가','き':'기','く':'구','け':'게','こ':'고',
        'さ':'사','し':'시','す':'스','せ':'세','そ':'소',
        'た':'타','ち':'치','つ':'츠','て':'테','と':'토',
        'な':'나','に':'니','ぬ':'누','ね':'네','の':'노',
        'は':'하','ひ':'히','ふ':'후','へ':'헤','ほ':'호',
        'ま':'마','み':'미','む':'무','め':'메','も':'모',
        'や':'야','ゆ':'유','よ':'요',
        'ら':'라','り':'리','る':'루','れ':'레','ろ':'로',
        'わ':'와','を':'오','ん':'응',
        'ア':'아','イ':'이','ウ':'우','エ':'에','オ':'오',
        'カ':'가','キ':'기','ク':'구','ケ':'게','コ':'고',
        'サ':'사','シ':'시','ス':'스','セ':'세','ソ':'소',
        'タ':'타','チ':'치','ツ':'츠','テ':'테','ト':'토',
        'ナ':'나','ニ':'니','ヌ':'누','ネ':'네','ノ':'노',
        'ハ':'하','ヒ':'히','フ':'후','ヘ':'헤','ホ':'호',
        'マ':'마','ミ':'미','ム':'무','メ':'메','モ':'모',
        'ヤ':'야','ユ':'유','ヨ':'요',
        'ラ':'라','リ':'리','ル':'루','レ':'레','ロ':'로',
        'ワ':'와','ヲ':'오','ン':'응',
        'が':'가','ぎ':'기','ぐ':'구','げ':'게','ご':'고',
        'ざ':'자','じ':'지','ず':'즈','ぜ':'제','ぞ':'조',
        'だ':'다','ぢ':'지','づ':'즈','で':'데','ど':'도',
        'ば':'바','び':'비','ぶ':'부','べ':'베','ぼ':'보',
        'ぱ':'파','ぴ':'피','ぷ':'푸','ぺ':'페','ぽ':'포',
        'ガ':'가','ギ':'기','グ':'구','ゲ':'게','ゴ':'고',
        'ザ':'자','ジ':'지','ズ':'즈','ゼ':'제','ゾ':'조',
        'ダ':'다','ヂ':'지','ヅ':'즈','デ':'데','ド':'도',
        'バ':'바','ビ':'비','ブ':'부','ベ':'베','ボ':'보',
        'パ':'파','ピ':'피','プ':'푸','ペ':'페','ポ':'포',
        'きゃ':'갸','きゅ':'규','きょ':'교',
        'しゃ':'샤','しゅ':'슈','しょ':'쇼',
        'ちゃ':'차','ちゅ':'추','ちょ':'초',
        'にゃ':'냐','にゅ':'뉴','にょ':'뇨',
        'ひゃ':'햐','ひゅ':'휴','ひょ':'효',
        'みゃ':'먀','みゅ':'뮤','みょ':'묘',
        'りゃ':'랴','りゅ':'류','りょ':'료',
        'ぎゃ':'갸','ぎゅ':'규','ぎょ':'교',
        'じゃ':'자','じゅ':'주','じょ':'조',
        'びゃ':'뱌','びゅ':'뷰','びょ':'뵤',
        'ぴゃ':'퍄','ぴゅ':'퓨','ぴょ':'표',
        'キャ':'갸','キュ':'규','キョ':'교',
        'シャ':'샤','シュ':'슈','ショ':'쇼',
        'チャ':'차','チュ':'추','チョ':'초',
        'ニャ':'냐','ニュ':'뉴','ニョ':'뇨',
        'ヒャ':'햐','ヒュ':'휴','ヒョ':'효',
        'ミャ':'먀','ミュ':'뮤','ミョ':'묘',
        'リャ':'랴','リュ':'류','リョ':'료',
        'ギャ':'갸','ギュ':'규','ギョ':'교',
        'ジャ':'자','ジュ':'주','ジョ':'조',
        'ビャ':'뱌','ビュ':'뷰','ビョ':'뵤',
        'ピャ':'퍄','ピュ':'퓨','ピョ':'표',
        'ッ':'',
        'ー':''
    }
    result = ''
    for char in japanese_text:
        result += kana2hangul[char]
    return result

def symbol_to_korean(char: str) -> str:
    """
    gets a matching korean text for a symbol
    """
    match char:
        case '℃':
            return "도씨"
        case '℉':
            return "화씨"
        case '°':
            return "도"
        case '©':
            return "저작권"
        case '®':
            return "등록상표"
        case '™':
            return "상표"
        case '±':
            return "플러스마이너스"
        case '×':
            return "곱하기"
        case '÷':
            return "나누기"
        case '√':
            return "루트"
        case '∑':
            return "시그마"
        case '∞':
            return "무한대"
        case '♥':
            return "하트"
        case '♡':
            return "하트"
        case '★':
            return "별"
        case '☆':
            return "별"
    return char

def convert_halfwidth(char: str) -> str:
    """
    converts a fullwidth character to a halfwidth character
    """
    if ord(char) >= 0xFF00 and ord(char) <= 0xFFEF:
        return chr(ord(char)-0xFEFF)
    return char
def convert_fullwidth(char: str) -> str:
    """
    converts a halfwidth character to a fullwidth character
    """
    if ord(char) >= 0x20 and ord(char) <= 0x7E:
        return chr(ord(char)+0xFEFF)
    return char