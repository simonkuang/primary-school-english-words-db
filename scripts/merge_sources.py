"""合并两个来源：S=yy.suyang123.com（3A–5B 按单元分页），J=yyld.51jiaoxi.com（仅 3A/3B 整册）。
输入 data/source_s.json、data/source_j.json，输出 data/merged.json。用法：python3 scripts/merge_sources.py"""
import json, re
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / 'data'
S = json.load(open(DATA / 'source_s.json', encoding='utf-8'))
J = json.load(open(DATA / 'source_j.json', encoding='utf-8'))
TITLES = {}
for r in S:
    TITLES[(r['book'], r['unit_no'])] = r['unit_title']

def key(w):
    return re.sub(r'\s+', '', w.lower().replace('…', '').replace('...', ''))

def junit(u):
    return 0 if u.lower() == 'welcome' else int(re.search(r'\d+', u).group())

out = []
for book in ['3A', '3B', '4A', '4B', '5A', '5B']:
    units = sorted({r['unit_no'] for r in S if r['book'] == book})
    for u in units:
        s_items = [r for r in S if r['book'] == book and r['unit_no'] == u]
        j_items = [r for r in J if r['book'] == book and junit(r['unit']) == u]
        merged, seen = [], set()
        if j_items:
            s_keys = {key(r['word']): r for r in s_items}
            # 以 J 的顺序为主，S 独有的词按其在 S 中的位置插入
            jk = [key(r['word']) for r in j_items]
            for r in j_items:
                k = key(r['word'])
                if k in seen:
                    continue           # J 中的重复条目
                seen.add(k)
                s = s_keys.get(k)
                merged.append({'word': (s or r)['word'] if s and ' / ' not in s['word'] else r['word'],
                               'meaning_s': s['meaning'] if s else None, 'meaning_j': r['meaning'],
                               'source': 'S+J' if s else 'J', 'url': (s or r).get('source_url') or r['source_url']})
            for i, r in enumerate(s_items):
                k = key(r['word'])
                if k in seen:
                    continue
                seen.add(k)
                # 插到 S 中前一个词之后
                prev = [key(x['word']) for x in s_items[:i]]
                pos = len(merged)
                for p in reversed(prev):
                    idx = next((n for n, m in enumerate(merged) if key(m['word']) == p), None)
                    if idx is not None:
                        pos = idx + 1; break
                merged.insert(pos, {'word': r['word'], 'meaning_s': r['meaning'], 'meaning_j': None, 'source': 'S', 'url': r['source_url']})
        else:
            for r in s_items:
                k = key(r['word'])
                if k in seen:
                    continue
                seen.add(k)
                merged.append({'word': r['word'], 'meaning_s': r['meaning'], 'meaning_j': None, 'source': 'S', 'url': r['source_url']})
        for n, m in enumerate(merged, 1):
            m.update(book=book, unit_no=u, unit_title=TITLES[(book, u)], seq=n)
            out.append(m)
json.dump(out, open(DATA / 'merged.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
from collections import Counter
print(Counter(m['book'] for m in out), Counter(m['source'] for m in out))
