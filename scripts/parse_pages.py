"""解析 pages/ 下的网页，输出 data/source_s.json 和 data/source_j.json。
用法：python3 scripts/parse_pages.py"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRADES = {'sannianji': 3, 'sinianji': 4, 'wunianji': 5}
TERMS = {'shangce': 'A', 'xiace': 'B'}
S_URL = 'https://yy.suyang123.com/xiaoxue/{}/wybsq_{}_words{}.html'
J_BOOKS = {'sanshang': '3A', 'sanxia': '3B'}
J_URL = 'https://yyld.51jiaoxi.com/{}/wybsq_danci.html'

S_ITEM = re.compile(r'<p class="word-text"[^>]*>([^<]*)</p>.*?<p class="phonetic-text"[^>]*>([^<]*)</p>.*?<p class="cn"[^>]*>([^<]*)</p>', re.S)
# J 页面：单元标题“英语××单词表音频、中文翻译表”之后跟若干词条
J_TOKEN = re.compile(r'英语([^<]{1,20}?)单词表音频、中文翻译表|<p class="en"[^>]*>([^<]*)</p>\s*<div class="phonetic"[^>]*>'
                     r'(?:<p class="text"[^>]*>([^<]*)</p>)?.*?</div>\s*<p class="cn"[^>]*>([^<]*)</p>', re.S)


def parse_s():
    out = []
    for f in sorted((ROOT / 'pages' / 's').glob('*.html')):
        g, t, i = f.stem.split('_')
        text = f.read_text(encoding='utf-8')
        title = html.unescape(re.search(r'<title>([^<]*)', text).group(1))
        unit_full = re.search(r'册英语(.+?)单词音频', title).group(1).strip()
        um = re.match(r'(Unit\s*\d+)\s*(.*)', unit_full)
        unit_no = int(re.search(r'\d+', um.group(1)).group()) if um else 0      # Welcome to school 记为 0
        unit_title = um.group(2) if um else unit_full
        for seq, (w, p, c) in enumerate(S_ITEM.findall(text), 1):
            out.append({'book': f'{GRADES[g]}{TERMS[t]}', 'page_no': int(i), 'unit_no': unit_no, 'unit_title': unit_title,
                        'seq': seq, 'word': html.unescape(w).strip(), 'phonetic': html.unescape(p).strip(),
                        'meaning': html.unescape(c).replace('翻译：', '').strip(), 'source_url': S_URL.format(g, t, i)})
    return out


def parse_j():
    out = []
    for g, book in J_BOOKS.items():
        text = (ROOT / 'pages' / 'j' / f'{g}.html').read_text(encoding='utf-8')
        unit, seq = None, 0
        for m in J_TOKEN.finditer(text):
            if m.group(1):
                unit = m.group(1)
                continue
            if unit:
                seq += 1
                out.append({'book': book, 'unit': unit, 'seq': seq, 'word': html.unescape(m.group(2)).strip(),
                            'meaning': html.unescape(m.group(4)).replace('翻译：', '').strip(), 'source_url': J_URL.format(g)})
    return out


def main():
    s, j = parse_s(), parse_j()
    for name, rows in (('source_s.json', s), ('source_j.json', j)):
        (ROOT / 'data' / name).write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding='utf-8')
    print('S', len(s), 'J', len(j))


if __name__ == '__main__':
    main()
