"""下载网上来源的新版词表网页到 pages/（不入库，可随时重新下载）。
来源 S：英语朗读宝 yy.suyang123.com，3A–5B 按单元分页；来源 J：英语朗读宝 yyld.51jiaoxi.com，3A/3B 整册词表。
（两站的六年级都还是旧版 Module 词表，所以不下载。）
用法：python3 scripts/fetch_pages.py"""
import re
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'pages'
S_URL = 'https://yy.suyang123.com/xiaoxue/{g}/wybsq_{t}_words{i}.html'
J_URL = 'https://yyld.51jiaoxi.com/{g}/wybsq_danci.html'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def main():
    (OUT / 's').mkdir(parents=True, exist_ok=True)
    (OUT / 'j').mkdir(parents=True, exist_ok=True)
    for g in ('sannianji', 'sinianji', 'wunianji'):
        for t in ('shangce', 'xiace'):
            for i in range(1, 9):
                try:
                    text = get(S_URL.format(g=g, t=t, i=i))
                except Exception:
                    break
                title = re.search(r'<title>([^<]*)', text)
                if not title or not re.search(r'Unit|Welcome', title.group(1), re.I):
                    break                       # 超出该册单元数
                (OUT / 's' / f'{g}_{t}_{i}.html').write_text(text, encoding='utf-8')
                print('S', g, t, i, title.group(1)[:40])
                time.sleep(0.5)
    for g in ('sanshang', 'sanxia'):
        (OUT / 'j' / f'{g}.html').write_text(get(J_URL.format(g=g)), encoding='utf-8')
        print('J', g)


if __name__ == '__main__':
    main()
