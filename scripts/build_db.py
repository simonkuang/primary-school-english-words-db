"""2022 版课标外研社《英语（三年级起点）》新版教材单词表 → SQLite。
输入 data/merged.json（merge_sources.py 的结果，3A–5B）和 data/textbook_6a.json（据课本录入的六上），音标用 phonetics.py 标注。
用法：python3 scripts/build_db.py <输出.db>"""
import json
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE.parent / 'data'
sys.path.insert(0, str(HERE))
import phonetics  # noqa: E402

DB = Path(sys.argv[1])

BOOKS = {  # 年级, 册, 首次使用学期（三上 2024 秋起逐年换版推算；2026 秋全国义务教育各年级已全部换用新教材）
    '3A': (3, '三年级', '上册', '2024年秋季'),
    '3B': (3, '三年级', '下册', '2025年春季'),
    '4A': (4, '四年级', '上册', '2025年秋季'),
    '4B': (4, '四年级', '下册', '2026年春季'),
    '5A': (5, '五年级', '上册', '2026年秋季'),
    '5B': (5, '五年级', '下册', '2027年春季（尚未开始使用）'),
    '6A': (6, '六年级', '上册', '2026年秋季'),
}
SRC = {'S': '英语朗读宝 yy.suyang123.com（按单元分页）', 'J': '英语朗读宝 yyld.51jiaoxi.com（整册词表，仅三年级）',
       'T': '课本附录 Words and expressions（据教材图片逐条录入）'}
# 据课本录入的册：data/textbook_<册>.json，格式见 data/textbook_6a.json

# 新词的音标补充（词典查不到 / 多音词 / 短语）
phonetics.MANUAL.update({
    # 六上（据课本录入）
    'saving': 'ˈseɪvɪŋ', 'surprised': 'səˈpraɪzd', 'cultural': 'ˈkʌltʃərəl', 'drawing': 'ˈdrɔːɪŋ', 'Alan': 'ˈælən',
    'desert': 'ˈdezət', 'natural': 'ˈnætʃrəl', 'fairy tale': 'ˈfeəri teɪl', 'golden touch': 'ˌɡəʊldən ˈtʌtʃ',
    'square kilometre': 'ˌskweə ˈkɪləmiːtə', 'bird feeder': 'ˈbɜːd fiːdə', 'couch potato': 'ˈkaʊtʃ pəˌteɪtəʊ',
    'material': 'məˈtɪəriəl', 'instrument': 'ˈɪnstrəmənt', 'shopkeeper': 'ˈʃɒpkiːpə', 'pocket money': 'ˈpɒkɪt mʌni',
    'everybody': 'ˈevribɒdi', 'pencil case': 'ˈpensl keɪs', 'lost and found': 'ˌlɒst ən ˈfaʊnd',
    'Chinese knot': 'ˌtʃaɪniːz ˈnɒt', 'cheep': 'tʃiːp', 'miaow': 'miˈaʊ', 'urgh': 'ɜːɡ', 'phew': 'fjuː',
    'whoosh': 'wʊʃ', 'chug': 'tʃʌɡ', 'beep': 'biːp', 'whoa': 'wəʊ', 'aha': 'ɑːˈhɑː', 'er': 'ɜː',
    'tick-tock': 'ˌtɪk ˈtɒk', "o'clock": 'əˈklɒk', 'forty-five': 'ˌfɔːti ˈfaɪv', 'tai chi': 'ˌtaɪ ˈtʃiː',
    'to-do list': 'təˈduː lɪst', 'afterschool': 'ˈɑːftəskuːl', 'high-speed': 'ˌhaɪ ˈspiːd',
    'ping-pong': 'ˈpɪŋpɒŋ', 'anymore': 'ˌeniˈmɔː', 'ukulele': 'ˌjuːkəˈleɪli', 'icebox': 'ˈaɪsbɒks',
    'teahouse': 'ˈtiːhaʊs', 'zookeeper': 'ˈzuːkiːpə', 'dressmaker': 'ˈdresmeɪkə', 'hometown': 'ˈhəʊmtaʊn',
    'raindrop': 'ˈreɪndrɒp', 'lunchtime': 'ˈlʌntʃtaɪm', 'horseback': 'ˈhɔːsbæk', 'snowstorm': 'ˈsnəʊstɔːm',
    'cupcake': 'ˈkʌpkeɪk', 'bookmark': 'ˈbʊkmɑːk', 'healthily': 'ˈhelθɪli', 'openly': 'ˈəʊpənli',
    'skier': 'ˈskiːə', 'ID': 'ˌaɪ ˈdiː', 'Yours': 'jɔːz', 'oats': 'əʊts', 'fries': 'fraɪz', 'chips': 'tʃɪps',
    'mooncake': 'ˈmuːnkeɪk', 'police officer': 'pəˈliːs ˌɒfɪsə', 'night owl': 'ˈnaɪt aʊl',
    'police station': 'pəˈliːs ˌsteɪʃn', 'care home': 'ˈkeə həʊm', 'science fiction': 'ˌsaɪəns ˈfɪkʃn',
    'summer camp': 'ˈsʌmə kæmp', 'food group': 'ˈfuːd ɡruːp', 'living room': 'ˈlɪvɪŋ ruːm',
    'dining room': 'ˈdaɪnɪŋ ruːm', 'afternoon tea': 'ˌɑːftənuːn ˈtiː', 'ice cream': 'ˌaɪs ˈkriːm',
    'hot dog': 'ˌhɒt ˈdɒɡ', 'all year round': 'ˌɔːl jɪə ˈraʊnd', 'all around': 'ˌɔːl əˈraʊnd',
    'try your best': 'ˌtraɪ jɔː ˈbest', 'Good job!': 'ˌɡʊd ˈdʒɒb', 'be careful': 'bi ˈkeəfl',
    'on one\'s own': 'ɒn wʌnz ˈəʊn', 'be late for school': 'bi ˈleɪt fə ˈskuːl', "that's enough": 'ˌðæts ɪˈnʌf',
    'Merry Christmas!': 'ˌmeri ˈkrɪsməs', 'here you are': 'ˈhɪə juː ɑː', 'what about…': 'ˈwɒt əˈbaʊt',
    'half past one/two...': 'hɑːf pɑːst ˈwʌn / ˈtuː', 'take care of sb/sth': 'teɪk ˈkeər əv',
    'look at sb/sth': 'ˈlʊk æt', 'because of sb/sth': 'bɪˈkɒz əv', 'a few': 'ə ˈfjuː', 'a lot': 'ə ˈlɒt',
    'come on': 'kʌm ˈɒn', 'come true': 'kʌm ˈtruː', 'give up': 'ɡɪv ˈʌp', 'grow up': 'ɡrəʊ ˈʌp',
    'warm up': 'wɔːm ˈʌp', 'turn on': 'tɜːn ˈɒn', 'turn into': 'tɜːn ˈɪntuː', 'take off': 'teɪk ˈɒf',
    'stand up': 'stænd ˈʌp', 'sit down': 'sɪt ˈdaʊn', 'come back': 'kʌm ˈbæk',
    'live': 'lɪv', 'close': 'kləʊz', 'wind': 'wɪnd', 'read': 'riːd', 'use': 'juːz', 'tear': 'teə',
    'record': 'ˈrekɔːd', 'present': 'ˈpreznt', 'minute': 'ˈmɪnɪt', 'row': 'rəʊ', 'lead': 'liːd',
    'August': 'ˈɔːɡəst', 'March': 'mɑːtʃ', 'may': 'meɪ', 'could': 'kʊd', 'would': 'wʊd', 'must': 'mʌst',
    'should': 'ʃʊd', 'will': 'wɪl', 'feet': 'fiːt', 'children': 'ˈtʃɪldrən', 'noodles': 'ˈnuːdlz',
    'trousers': 'ˈtraʊzəz', 'shorts': 'ʃɔːts', 'clothes': 'kləʊðz', 'these': 'ðiːz', 'their': 'ðeə',
    'us': 'ʌs', 'her': 'hɜː', 'him': 'hɪm', 'them': 'ðem', 'its': 'ɪts', 'our': 'ˈaʊə', 'your': 'jɔː',
    'my': 'maɪ', 'his': 'hɪz', 'scared': 'skeəd', 'worried': 'ˈwʌrid', 'excited': 'ɪkˈsaɪtɪd',
    'tired': 'ˈtaɪəd', 'helpful': 'ˈhelpfl', 'careful': 'ˈkeəfl', 'colourful': 'ˈkʌləfl', 'playful': 'ˈpleɪfl',
    'wonderful': 'ˈwʌndəfl', 'useful': 'ˈjuːsfl', 'beautiful': 'ˈbjuːtɪfl', 'magical': 'ˈmædʒɪkl',
    'musical': 'ˈmjuːzɪkl', 'Mr': 'ˈmɪstə', 'Ms': 'mɪz', 'TV': 'ˌtiːˈviː', 'OK': 'əʊˈkeɪ', 'be': 'biː',
    'a': 'ə', 'the': 'ðə', 'cooking': 'ˈkʊkɪŋ', 'feeling': 'ˈfiːlɪŋ', 'painting': 'ˈpeɪntɪŋ',
    'training': 'ˈtreɪnɪŋ', 'building': 'ˈbɪldɪŋ', 'beginning': 'bɪˈɡɪnɪŋ', 'fireman': 'ˈfaɪəmən',
    'postman': 'ˈpəʊstmən', 'sunflower': 'ˈsʌnflaʊə', 'sunshine': 'ˈsʌnʃaɪn', 'underground': 'ˌʌndəˈɡraʊnd',
    'everywhere': 'ˈevriweə', 'someone': 'ˈsʌmwʌn', 'something': 'ˈsʌmθɪŋ', 'snowman': 'ˈsnəʊmæn',
    'snowy': 'ˈsnəʊi', 'rainy': 'ˈreɪni', 'windy': 'ˈwɪndi', 'sunny': 'ˈsʌni', 'cloudy': 'ˈklaʊdi',
    'sleepy': 'ˈsliːpi', 'yummy': 'ˈjʌmi', 'shiny': 'ˈʃaɪni', 'daddy': 'ˈdædi', 'mummy': 'ˈmʌmi',
    'unhappy': 'ʌnˈhæpi', 'slowly': 'ˈsləʊli', 'quickly': 'ˈkwɪkli', 'carefully': 'ˈkeəfəli',
    'friendly': 'ˈfrendli', 'really': 'ˈrɪəli', 'yesterday': 'ˈjestədeɪ', 'tomorrow': 'təˈmɒrəʊ',
    'grandpa': 'ˈɡrænpɑː', 'grandma': 'ˈɡrænmɑː', 'dad': 'dæd', 'mum': 'mʌm', 'hooray': 'huˈreɪ',
    'woof': 'wʊf', 'hey': 'heɪ', 'oh': 'əʊ', 'hi': 'haɪ', 'bye': 'baɪ', 'no': 'nəʊ', 'one': 'wʌn',
    'sushi': 'ˈsuːʃi', 'evening': 'ˈiːvnɪŋ', 'feed': 'fiːd', 'outside': 'ˌaʊtˈsaɪd', 'bake': 'beɪk',
    'act': 'ækt', 'change': 'tʃeɪndʒ', 'nut': 'nʌt', 'danger': 'ˈdeɪndʒə', 'pie': 'paɪ', 'shape': 'ʃeɪp',
    'side': 'saɪd', 'most': 'məʊst',
    'job': 'dʒɒb', 'police': 'pəˈliːs', 'worried': 'ˈwʌrɪd', 'jewel': 'ˈdʒuːəl', 'ancient': 'ˈeɪnʃənt',
    'central': 'ˈsentrəl', 'difficulty': 'ˈdɪfɪkəlti',
})


def split_forms(w):
    """dad (father) → (dad, father)；let's = let us → (let's, let us)；be(am,is,are) → (be, am, is, are)"""
    w = re.sub(r'\s*/\s*', '/', w) if 'sb' in w else w
    m = re.match(r"^(.+?)\s*=\s*(.+)$", w)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = re.match(r'^([A-Za-z\'\- ]+?)\s*\(([^)]+)\)$', w)
    if m:
        return m.group(1).strip(), re.sub(r'\s*,\s*', ', ', m.group(2).strip())
    return w.strip(), None


def norm_cn(s):
    if not s:
        return s
    s = s.replace('······', '……').replace('......', '……').replace('...', '……')
    s = re.sub(r'([，；：])\s+', r'\1', s)
    return s.strip()


# 处理规则：key = (册, 单元, 原词)；动作 drop / meaning / word
FIX = {
    ('3B', 4, 'lot'): ('drop', '来源 S 写作 lot，是 a lot 的残缺（单独的 lot 不是课本词条）；来源 J 为 a lot，保留 a lot'),
    ('3B', 3, 'noodle'): ('drop', '与 noodles 重复（来源 J 写 noodle，来源 S 写 noodles 并注“一般用复数”），只保留 noodles'),
}
# 两个来源位置不一致：S 把 welcome / to / school 放在 Welcome to school，J 分别放在 Unit 1 / Unit 1 / Unit 2
POSITION_CONFLICT = {('3A', 0, 'welcome'), ('3A', 0, 'to'), ('3A', 0, 'school')}

SUSPECT = {
    ('3B', 1, 'along'): ('释义', '向前（来源 J）', '两个来源释义不同：S 为“一起”，J 为“向前”。along 在 come along / go along 中多为“向前；一起”，请以课本为准'),
    ('3B', 2, 'talk'): ('释义', '讨论，商谈（来源 J）', '两个来源释义不同：S 为“说话”，J 为“讨论，商谈”'),
    ('3B', 2, 'part'): ('释义', '部分（来源 J）', '两个来源释义不同：S 为“器官；部位；组成部分”，J 为“部分”'),
    ('3B', 3, 'much'): ('释义', '大量（来源 J）', '两个来源释义不同：S 为“非常”（very much），J 为“大量”'),
    ('3A', 3, 'magical'): ('释义', '美妙的；有魔力的（来源 J）', '两个来源释义不同：S 为“神奇的；有魔力的”'),
    ('3B', 6, 'afterschool'): ('单词', 'after-school', '常规拼写为 after-school（带连字符），两个来源都写作 afterschool，请以课本为准'),
    ('3A', 4, 'amazing'): ('来源', '仅来源 J 有', '来源 S 的 Unit 4 没有 amazing，而有 us；两者都已收录'),
    ('3A', 4, 'us'): ('来源', '仅来源 S 有', '来源 J 的 Unit 4 没有 us；已收录'),
    ('3A', 1, 'age'): ('来源', '仅来源 S 有', '来源 J 的 Unit 1 没有 age；已收录'),
    ('3A', 1, 'everybody'): ('来源', '仅来源 S 有', '来源 J 在相同位置写的是重复的 everyone，疑为 J 把 everybody 误写成 everyone；已按 S 收录 everybody'),
    ('3B', 6, 'maths'): ('来源', '仅来源 S 有', '来源 J 的 Unit 6 没有 maths；已收录'),
}
# 来源中的明显错误（已采用正确来源的值）
SOURCE_TYPO = [
    ('3A', 1, 'to', '释义', '（用于动词、名词或形容词后，是意思完整）', '（用于动词、名词或形容词后，使意思完整）', '来源 J 错别字“是”→“使”，采用来源 S'),
    ('3A', 3, 'pink', '释义', '粉红色的（的）', '粉红色（的）', '来源 J 多了一个“的”，采用来源 S'),
    ('3B', 5, 'urgh', '释义', '呸，呸', '呃，呸', '来源 J 疑似重复，采用来源 S'),
    ('3A', 1, 'everyone', '单词', 'everyone（第 2 次出现）', 'everybody', '来源 J 的 Unit 1 中 everyone 出现两次，第二处对应来源 S 的 everybody'),
    ('3A', 5, 'daddy', '单词', 'daddy, mummy, where, dog, box（各重复一次）', '去重', '来源 J 的 Unit 5 末尾 5 个词重复出现，已去重'),
    ('3B', 2, 'child', '释义', '（复数children）儿童， 小孩', '（复数children）儿童，小孩', '多余空格'),
    ('3B', 4, 'interesting', '释义', '有趣的， 吸引人的', '有趣的，吸引人的', '多余空格'),
]

SCHEMA = """
CREATE TABLE textbooks (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,        -- 3A=三年级上册 … 6A=六年级上册
  publisher TEXT NOT NULL,
  series TEXT NOT NULL,
  curriculum TEXT NOT NULL,         -- 义务教育英语课程标准（2022年版）
  grade INTEGER NOT NULL,
  grade_cn TEXT NOT NULL,
  term TEXT NOT NULL,
  first_use TEXT NOT NULL,          -- 首次使用学期（3A–5B 按逐年换版推算）
  sources TEXT NOT NULL,            -- 词表来源
  note TEXT
);
CREATE TABLE units (
  id INTEGER PRIMARY KEY,
  textbook_id INTEGER NOT NULL REFERENCES textbooks(id),
  unit_no INTEGER NOT NULL,         -- 0 = Welcome to school（三上开篇单元）；六上 7 = 课本剧词汇（Plays）
  unit_name TEXT NOT NULL,          -- Unit 1 / Welcome
  title TEXT NOT NULL,              -- 单元标题，如 Let's be friends!
  UNIQUE (textbook_id, unit_no)
);
CREATE TABLE words (
  id INTEGER PRIMARY KEY,
  textbook_id INTEGER NOT NULL REFERENCES textbooks(id),
  unit_id INTEGER NOT NULL REFERENCES units(id),
  seq INTEGER NOT NULL,             -- 单元内顺序
  global_seq INTEGER NOT NULL,      -- 从三上 Welcome 起的总顺序
  headword TEXT NOT NULL,           -- 单词 / 短语
  forms TEXT,                       -- 完整形式或变体：let's → let us；be → am, is, are；dad → father
  phonetic TEXT,                    -- 英式音标（课本写法，不含方括号）
  phonetic_source TEXT,             -- oxford / oxford_composed / manual
  meaning TEXT NOT NULL,            -- 中文释义
  meaning_alt TEXT,                 -- 另一来源的不同释义（若有）
  is_phrase INTEGER NOT NULL,
  is_core INTEGER,                  -- 1=课本加粗（课标要求掌握的二级词汇） 0=未加粗 NULL=来源未标注（3A–5B）
  source TEXT NOT NULL,             -- S / J / S+J（两个来源都有）/ T（课本）
  source_url TEXT NOT NULL,
  issue_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE issues (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('fixed','suspected','conflict','book')),
                                    -- fixed=已修正 suspected=疑似问题(按原样收录) conflict=来源分歧 book=整册说明
  textbook_id INTEGER REFERENCES textbooks(id),
  unit_no INTEGER,
  word_id INTEGER REFERENCES words(id),
  headword TEXT,
  field TEXT,
  original TEXT,
  suggestion TEXT,
  description TEXT NOT NULL
);
CREATE INDEX idx_words_head ON words(headword COLLATE NOCASE);

CREATE VIEW v_words AS
SELECT w.id, t.code AS book, t.grade, t.grade_cn, t.term, t.grade_cn || t.term AS book_cn,
       u.unit_no, u.unit_name, u.title AS unit_title, w.seq, w.global_seq,
       w.headword, w.forms, w.phonetic, w.meaning, w.meaning_alt, w.is_phrase, w.is_core,
       w.source, w.phonetic_source, w.issue_count, t.series, t.curriculum, t.publisher
FROM words w JOIN textbooks t ON t.id = w.textbook_id JOIN units u ON u.id = w.unit_id;

CREATE VIEW v_issues AS
SELECT i.id, i.kind, t.code AS book, t.grade_cn || t.term AS book_cn, i.unit_no, i.headword,
       i.field, i.original, i.suggestion, i.description
FROM issues i LEFT JOIN textbooks t ON t.id = i.textbook_id;

CREATE VIEW v_word_occurrences AS
SELECT lower(headword) AS word, COUNT(*) AS times,
       group_concat(book || ' ' || unit_name || ' ' || meaning, ' | ') AS where_and_meaning
FROM (SELECT * FROM v_words ORDER BY global_seq)
GROUP BY lower(headword);
"""


def main():
    rows = json.loads((DATA / 'merged.json').read_text(encoding='utf-8'))
    textbooks = {}
    for f in sorted(DATA.glob('textbook_*.json')):
        t = json.loads(f.read_text(encoding='utf-8'))
        textbooks[t['book']] = t
    if DB.exists():
        DB.unlink()
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    tid, uid = {}, {}
    for code, (g, gcn, term, first) in BOOKS.items():
        srcs = 'T' if code in textbooks else 'S + J' if g == 3 else 'S'
        note = textbooks[code].get('note') if code in textbooks else None
        if code == '5B':
            note = '按换版节奏新版五下应在 2027 年春季开始使用，请以正式课本为准'
        if code in textbooks:
            pass
        elif g >= 4:
            note = ((note + '；') if note else '') + '只有一个来源（S），而 S 在三年级对照中漏收了部分短语（如 o\'clock、afternoon tea、hot dog、tai chi、grow up），本册也可能有少量短语缺失'
        tid[code] = db.execute('''INSERT INTO textbooks(code,publisher,series,curriculum,grade,grade_cn,term,first_use,sources,note)
                                  VALUES (?,?,?,?,?,?,?,?,?,?)''',
                               (code, '外语教学与研究出版社（外研社）', '英语（三年级起点）新版',
                                '义务教育英语课程标准（2022年版）', g, gcn, term, first,
                                ' + '.join(SRC[s] for s in srcs.split(' + ')), note)).lastrowid
        if note:
            db.execute('INSERT INTO issues(kind,textbook_id,field,description) VALUES (?,?,?,?)', ('book', tid[code], '整册', note))
    missing, gseq, per_unit = [], 0, {}
    for r in rows:
        book, u = r['book'], r['unit_no']
        key = (book, u, r['word'])
        if key in FIX and FIX[key][0] == 'drop':
            db.execute('INSERT INTO issues(kind,textbook_id,unit_no,headword,field,original,suggestion,description) VALUES (?,?,?,?,?,?,?,?)',
                       ('fixed', tid[book], u, r['word'], '单词', r['word'], '删除', FIX[key][1]))
            continue
        if key in POSITION_CONFLICT:
            db.execute('INSERT INTO issues(kind,textbook_id,unit_no,headword,field,original,suggestion,description) VALUES (?,?,?,?,?,?,?,?)',
                       ('conflict', tid[book], u, r['word'], '所在单元', '来源 S：Welcome to school', '来源 J：' + ('Unit 2' if r['word'] == 'school' else 'Unit 1'),
                        '两个来源单元归属不同。已按来源 J 放在 ' + ('Unit 2' if r['word'] == 'school' else 'Unit 1') + '，没有在 Welcome to school 重复收录；也可能这是 Welcome to school 的标题词，请以课本为准'))
            continue
        if (book, u) not in uid:
            uid[(book, u)] = db.execute('INSERT INTO units(textbook_id,unit_no,unit_name,title) VALUES (?,?,?,?)',
                                        (tid[book], u, 'Welcome' if u == 0 else f'Unit {u}', r['unit_title'])).lastrowid
        head, forms = split_forms(r['word'])
        meaning = norm_cn(r['meaning_s'] or r['meaning_j'])
        alt = norm_cn(r['meaning_j']) if r['meaning_s'] and r['meaning_j'] and norm_cn(r['meaning_j']) != meaning else None
        # 统一短语里 sb/sth 的写法
        head = head.replace('sb / sth', 'sb/sth')
        ph, psrc = phonetics.phonetic_for(book, head)
        if not ph:
            missing.append(f'{book} U{u} {head}')
        gseq += 1
        per_unit[(book, u)] = per_unit.get((book, u), 0) + 1
        is_phrase = 1 if re.search(r"[ ]", head) or head.endswith(('!', '?', '…')) else 0
        wid = db.execute('''INSERT INTO words(textbook_id,unit_id,seq,global_seq,headword,forms,phonetic,phonetic_source,
                            meaning,meaning_alt,is_phrase,source,source_url) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                         (tid[book], uid[(book, u)], per_unit[(book, u)], gseq, head, forms, ph, psrc, meaning, alt,
                          is_phrase, r['source'], r['url'])).lastrowid
        n = 0
        if key in SUSPECT:
            f, sug, desc = SUSPECT[key]
            kind = 'conflict' if f in ('释义', '来源') else 'suspected'
            orig = meaning if f == '释义' else head
            db.execute('INSERT INTO issues(kind,textbook_id,unit_no,word_id,headword,field,original,suggestion,description) VALUES (?,?,?,?,?,?,?,?,?)',
                       (kind, tid[book], u, wid, head, f, orig, sug, desc))
            n += 1
        for b2, u2, w2, f, orig, sug, desc in SOURCE_TYPO:
            if (b2, u2, w2) == (book, u, r['word']):
                db.execute('INSERT INTO issues(kind,textbook_id,unit_no,word_id,headword,field,original,suggestion,description) VALUES (?,?,?,?,?,?,?,?,?)',
                           ('fixed', tid[book], u, wid, head, f, orig, sug, desc))
                n += 1
        if n:
            db.execute('UPDATE words SET issue_count=? WHERE id=?', (n, wid))
    for book, t in textbooks.items():
        for u, title, page, items in t['units']:
            plays = title == 'Words and expressions in plays'
            uid[(book, u)] = db.execute('INSERT INTO units(textbook_id,unit_no,unit_name,title) VALUES (?,?,?,?)',
                                        (tid[book], u, 'Plays' if plays else f'Unit {u}', title)).lastrowid
            for seq, it in enumerate(items, 1):
                head, meaning = it[0], it[1]
                core = it[2] if len(it) > 2 else 0
                forms = it[3] if len(it) > 3 else None
                ph, psrc = phonetics.phonetic_for(book, head)
                if not ph:
                    missing.append(f'{book} U{u} {head}')
                gseq += 1
                db.execute('''INSERT INTO words(textbook_id,unit_id,seq,global_seq,headword,forms,phonetic,phonetic_source,
                              meaning,meaning_alt,is_phrase,is_core,source,source_url) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (tid[book], uid[(book, u)], seq, gseq, head, forms, ph, psrc, meaning, None,
                            1 if ' ' in head else 0, core, 'T', f'课本第 {page} 页'))
    db.execute('''INSERT INTO issues(kind,textbook_id,unit_no,field,original,suggestion,description) VALUES
                  ('suspected', ?, 5, '单元标题', 'School activities', 'School events', '来源 S 的四下 Unit 5 标题为 School activities，良师宝英语的新版四下目录为 School events，请以课本为准')''',
               (tid['4B'],))
    db.commit()
    print('words', gseq, 'missing phonetic', missing)


if __name__ == '__main__':
    main()
