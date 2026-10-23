"""给单词/短语标注英式音标（国内教材写法）。
优先查手工表（MANUAL_BY_BOOK → PHRASE → MANUAL），再查 macOS 自带《牛津英汉汉英词典》，短语逐词拼接。"""
import re

from oxdict import bre, to_textbook

# 词典查不到、查到的是原形（过去式等）、多音词需按释义取音，或缩写词：手工给出（教材通用英式音标）
MANUAL = {
    'I': 'aɪ', 'a': 'ə', 'the': 'ðə', 'mm': 'm', 'aah': 'ɑː', 'ha': 'hɑː',
    'No.': 'ˈnʌmbə', 'TV': 'ˌtiːˈviː', 'PE': 'ˌpiːˈiː', 'DVD': 'ˌdiːviːˈdiː', 'OK': 'əʊˈkeɪ',
    'Mr': 'ˈmɪstə', 'Mrs': 'ˈmɪsɪz', 'Ms': 'mɪz',
    'met': 'met', 'rang': 'ræŋ', 'won': 'wʌn', 'swam': 'swæm', 'sang': 'sæŋ', 'saw': 'sɔː',
    'went': 'went', 'ate': 'et', 'drank': 'dræŋk', 'took': 'tʊk', 'made': 'meɪd', 'came': 'keɪm',
    'fell': 'fel', 'found': 'faʊnd', 'bought': 'bɔːt', 'carried': 'ˈkærɪd', 'had': 'hæd',
    'did': 'dɪd', 'was': 'wɒz', 'were': 'wɜː', 'told': 'təʊld', 'dropped': 'drɒpt', 'lost': 'lɒst',
    'drove': 'drəʊv', 'sent': 'sent', 'thought': 'θɔːt', 'drew': 'druː', 'brought': 'brɔːt',
    'spent': 'spent', 'flew': 'fluː', 'became': 'bɪˈkeɪm', 'planned': 'plænd', 'got': 'ɡɒt',
    'goes': 'ɡəʊz', 'flies': 'flaɪz', 'does': 'dʌz', 'has': 'hæz', 'men': 'men', 'women': 'ˈwɪmɪn',
    'children': 'ˈtʃɪldrən', 'sweets': 'swiːts', 'noodles': 'ˈnuːdlz', 'trousers': 'ˈtraʊzəz',
    'shorts': 'ʃɔːts', 'scissors': 'ˈsɪzəz', 'chopsticks': 'ˈtʃɒpstɪks', 'stairs': 'steəz',
    'sports': 'spɔːts', 'thanks': 'θæŋks', 'exercises': 'ˈeksəsaɪzɪz', 'pictures': 'ˈpɪktʃəz',
    'lots': 'lɒts', 'clothes': 'kləʊðz', 'is': 'ɪz', 'are': 'ɑː', 'am': 'æm', 'can': 'kæn',
    'present': 'ˈpreznt', 'row': 'rəʊ', 'minute': 'ˈmɪnɪt', 'live': 'lɪv', 'read': 'riːd',
    'her': 'hɜː', 'us': 'ʌs', 'of': 'ɒv', 'from': 'frɒm', 'at': 'æt', 'to': 'tuː', 'and': 'ænd',
    'for': 'fɔː', 'some': 'sʌm', 'as': 'æz', 'or': 'ɔː', 'but': 'bʌt', 'that': 'ðæt', 'you': 'juː',
    'me': 'miː', 'he': 'hiː', 'she': 'ʃiː', 'we': 'wiː', 'them': 'ðem', 'his': 'hɪz', 'him': 'hɪm',
    'your': 'jɔː', 'our': 'ˈaʊə', 'its': 'ɪts', 'there': 'ðeə', 'then': 'ðen', 'do': 'duː',
    'have': 'hæv', 'been': 'biːn', 'be': 'biː', 'an': 'æn', 'not': 'nɒt', 'there\'s': 'ðeəz',
    'win': 'wɪn', 'wind': 'wɪnd', 'paper': 'ˈpeɪpə', 'taikonaut': 'ˈtaɪkənɔːt',
    'presenter': 'prɪˈzentə', 'hide-and-seek': 'ˌhaɪd n ˈsiːk', 'Halloween': 'ˌhæləʊˈiːn',
    'Chinatown': 'ˈtʃaɪnətaʊn', 'woof': 'wʊf', 'tweet': 'twiːt', 'whoops': 'wʊps',
    'ooh': 'uː', 'wow': 'waʊ', 'ouch': 'aʊtʃ', 'hooray': 'huˈreɪ', 'oh': 'əʊ', 'ah': 'ɑː',
    'Thanksgiving': 'ˌθæŋksˈɡɪvɪŋ', 'swimsuit': 'ˈswɪmsuːt', 'kilometer': 'ˈkɪləˌmiːtə',
    'someday': 'ˈsʌmdeɪ', 'goalkeeper': 'ˈɡəʊlkiːpə', 'firefighter': 'ˈfaɪəfaɪtə',
    'grandparent': 'ˈɡrænpeərənt', 'watermelon': 'ˈwɔːtəmelən', 'playground': 'ˈpleɪɡraʊnd',
    'postcard': 'ˈpəʊstkɑːd', 'housework': 'ˈhaʊswɜːk', 'homework': 'ˈhəʊmwɜːk',
    'schoolbag': 'ˈskuːlbæɡ', 'spaceship': 'ˈspeɪsʃɪp', 'toothbrush': 'ˈtuːθbrʌʃ',
    'headache': 'ˈhedeɪk', 'everyone': 'ˈevriwʌn', 'everything': 'ˈevriθɪŋ',
    'beautifully': 'ˈbjuːtɪfli', 'loudly': 'ˈlaʊdli', 'cloudy': 'ˈklaʊdi',
    'name': 'neɪm', 'pen': 'pen', 'in': 'ɪn', "that's": 'ðæts', 'song': 'sɒŋ', 'favourite': 'ˈfeɪvərɪt',
    'man': 'mæn', 'like': 'laɪk', 'swimming': 'ˈswɪmɪŋ', 'shopping': 'ˈʃɒpɪŋ', 'skating': 'ˈskeɪtɪŋ',
    'lake': 'leɪk', 'fishing': 'ˈfɪʃɪŋ', 'left': 'left', 'excuse': 'ɪkˈskjuːz', 'running': 'ˈrʌnɪŋ',
    'interesting': 'ˈɪntrəstɪŋ', 'make': 'meɪk', 'run': 'rʌn', 'come': 'kʌm', 'subject': 'ˈsʌbdʒɪkt',
    'long': 'lɒŋ', 'sun': 'sʌn', 'Miss': 'mɪs', 'miss': 'mɪs', 'ground': 'ɡraʊnd', 'those': 'ðəʊz',
    'hour': 'ˈaʊə', "what's": 'wɒts', 'matter': 'ˈmætə', "That's": 'ðæts', 'fan': 'fæn',
    'bored': 'bɔːd', 'tired': 'ˈtaɪəd', 'broken': 'ˈbrəʊkən', 'amazing': 'əˈmeɪzɪŋ', 'theatre': 'ˈθɪətə',
    'building': 'ˈbɪldɪŋ', 'dancing': 'ˈdɑːnsɪŋ', 'hang': 'hæŋ', 'pleased': 'pliːzd', 'age': 'eɪdʒ',
    'story': 'ˈstɔːri', 'frightened': 'ˈfraɪtnd', 'inside': 'ɪnˈsaɪd', 'stand': 'stænd', 'line': 'laɪn',
    'later': 'ˈleɪtə', 'interested': 'ˈɪntrəstɪd', 'more': 'mɔː', 'mouth': 'maʊθ', 'house': 'haʊs',
    'go': 'ɡəʊ', 'turn': 'tɜːn', 'meet': 'miːt', 'tomorrow': 'təˈmɒrəʊ', 'every': 'ˈevri', 'bed': 'bed',
    'it': 'ɪt', 'cap': 'kæp', 'careful': 'ˈkeəfl', 'who': 'huː', 'sad': 'sæd', 'difficult': 'ˈdɪfɪkəlt', 'beautiful': 'ˈbjuːtɪfl',
}

# 按“册-单词”区分的多音词，如 {('4B', 'close'): 'kləʊs'}
MANUAL_BY_BOOK = {}
# 整条短语直接给出（含括号、连字符等不便逐词拼接的情况）
PHRASE = {
    "haven't (got)": "ˈhævnt (ɡɒt)", "hasn't (got)": "ˈhæznt (ɡɒt)",
    'the Mid-Autumn Festival': 'ðə ˌmɪdˈɔːtəm ˈfestɪvl',
    'T-shirt': 'ˈtiː ʃɜːt', 'ice cream': 'ˌaɪs ˈkriːm', 'hot dog': 'ˌhɒt ˈdɒɡ',
    'table tennis': 'ˈteɪbl tenɪs', 'how much…?': 'haʊ ˈmʌtʃ', 'how about…?': 'haʊ əˈbaʊt',
    'What about…?': 'ˈwɒt əˈbaʊt', 'next to': 'ˈnekst tə', 'of course': 'əv ˈkɔːs',
    'have a look': 'hæv ə ˈlʊk', 'trick or treat': 'ˌtrɪk ɔː ˈtriːt', 'come on': 'kʌm ˈɒn',
    'stomach ache': 'ˈstʌmək eɪk', 'Be careful!': 'biː ˈkeəfl', 'look like': 'ˈlʊk laɪk',
    'more than': 'ˈmɔː ðən', 'lots of': 'ˈlɒts əv', 'there is': 'ðeər ˈɪz', 'there are': 'ðeər ˈɑː',
    "I'd love to.": 'aɪd ˈlʌv tuː', 'long long ago': 'ˌlɒŋ ˌlɒŋ əˈɡəʊ',
    'sports day': 'ˈspɔːts deɪ', 'soya milk': 'ˈsɔɪə mɪlk', 'living room': 'ˈlɪvɪŋ ruːm',
    'moon cake': 'ˈmuːn keɪk', 'pen friend': 'ˈpen frend', 'role model': 'ˈrəʊl mɒdl',
    'member state': 'ˈmembə steɪt', 'skipping rope': 'ˈskɪpɪŋ rəʊp', 'good luck': 'ɡʊd ˈlʌk',
}


def norm_meaning(s):
    s = s.replace('......', '……').replace('...', '……')
    for a, b in ((',', '，'), (';', '；'), ('(', '（'), (')', '）'), ('?', '？'), ('!', '！'), (':', '：')):
        s = s.replace(a, b)
    return s.strip()


def ox_word(tok):
    """单个词查牛津词典，返回 (音标, 来源)；查到的词条必须与原词一致（避免过去式被导向原形）。"""
    head, ipa = bre(tok)
    if ipa and head:
        h = re.sub(r'\s+(British|US)$', '', re.sub(r'\d', '', head).split(',')[0].strip())
        if h == tok:   # 区分大小写，避免 bed 命中 BEd、us 命中 US
            return clean_ox(ipa)
    return None


def clean_ox(ipa):
    s = ipa
    s = re.sub(r'\(ə\)l$', 'l', s)                 # 词尾成音节 l：people [ˈpiːpl]
    s = re.sub(r'(?<=[szdtvf])\(ə\)n$', 'n', s)   # 词尾成音节 n：lesson [ˈlesn]
    s = re.sub(r'\(t\)(?=[sθ])', '', s)            # 牛津的插入音 t：pencil、dance、month 不写
    s = s.replace('(', '').replace(')', '')         # 其余可省略音照常写出：dangerous、French
    return to_textbook(s)


def phonetic_for(book, head):
    """返回 (音标, 来源)。来源：manual = 手工表；oxford = 词典整词；oxford_composed = 短语逐词拼接。"""
    if (book, head) in MANUAL_BY_BOOK:
        return MANUAL_BY_BOOK[(book, head)], 'manual'
    if head in PHRASE:
        return PHRASE[head], 'manual'
    if head in MANUAL:
        return MANUAL[head], 'manual'
    key = head.rstrip('.!?').replace('…', '')
    p = ox_word(key)
    if p:
        return p, 'oxford'
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*\.?", key)
    parts = []
    for t in toks:
        if t in MANUAL:
            parts.append(MANUAL[t]); continue
        if t.lower() in MANUAL:
            parts.append(MANUAL[t.lower()]); continue
        p = ox_word(t) or ox_word(t.lower()) or ox_word(t.capitalize())
        if not p:
            return None, None
        parts.append(p)
    return ' '.join(parts), ('oxford' if len(toks) == 1 else 'oxford_composed')
