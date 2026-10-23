"""通过私有 DictionaryServices 接口查 macOS 自带《牛津英汉汉英词典》，取英式音标。需要 pyobjc。"""
import objc, re
from Foundation import NSBundle
_CS = NSBundle.bundleWithIdentifier_('com.apple.CoreServices')
_g = {}
objc.loadBundleFunctions(_CS, _g, [('DCSGetActiveDictionaries', b'@'), ('DCSDictionaryGetName', b'@@'), ('DCSCopyTextDefinition', b'@@@{CFRange=qq}')])
_OX = [d for d in _g['DCSGetActiveDictionaries']() if _g['DCSDictionaryGetName'](d) == '牛津英汉汉英词典'][0]

def lookup(w):
    return _g['DCSCopyTextDefinition'](_OX, w, (0, len(w))) or ''

def bre(w):
    """Return (headword, first BrE IPA) or (None, None)."""
    t = lookup(w)
    m = re.match(r'^(.*?)\s*\|\s*BrE\s+([^|]+?)(?:,\s*AmE[^|]*)?\|', t[:300])
    if not m:
        return (t.split('|')[0].strip() if t else None), None
    head = re.split(r'\s+[A-Z]\.\s', m.group(1).strip())[0]
    head = re.sub(r'\s*\d+$', '', head)
    ipa = m.group(2).split(',')[0].strip()
    return head, ipa

def to_textbook(ipa):
    """Oxford new-style BrE -> 中国教材通用国际音标."""
    s = ipa.replace('ʌɪ', 'aɪ').replace('ɛː', 'eə').replace('ɛ', 'e').replace('əː', 'ɜː')
    s = re.sub(r'a(?![ɪʊː])', 'æ', s)
    s = s.replace('(', '').replace(')', '')
    return s
