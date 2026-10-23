# 外研社新版小学英语单词表（2022 课标）

这是一份**可以用 SQL 查询的小学英语单词表**。教材是外研社《英语》新版（三年级起点），依据《义务教育英语课程标准（2022 年版）》编写，按 Unit 编排。

每个词都能查到：属于哪一册、哪个单元（含单元标题），英式音标、中文释义，是不是短语，以及数据来自哪里。

> 只收新教材。旧版《新标准英语》（2012/2013 年版，按 Module 编排）的词表一律不用。

## 现在有什么

| 册 | 单元 | 词条数 | 数据来源 |
|---|---|---|---|
| 三年级上册 3A | Welcome to school + Unit 1–6 | 209 | 两个教辅网站交叉核对 |
| 三年级下册 3B | Unit 1–6 | 198 | 两个教辅网站交叉核对 |
| 四年级上册 4A | Unit 1–6 | 164 | 一个教辅网站 |
| 四年级下册 4B | Unit 1–6 | 110 | 一个教辅网站 |
| 五年级上册 5A | Unit 1–6 | 113 | 一个教辅网站 |
| 五年级下册 5B | Unit 1–6 | 107 | 一个教辅网站 |
| 六年级上册 6A | Unit 1–6 + 课本剧词汇 | 83 | **课本附录**，逐条对照课本图片录入 |
| 六年级下册 6B | — | — | **暂缺**，网上只有旧版词表 |

一共 984 条。

几点要知道的：

- **六上最可靠**，因为它直接取自课本。课本把课标要求掌握的二级词汇加粗了，数据库里对应 `is_core = 1`，六上共 11 个。
- **三上到五下来自教辅网站**，不是出版社官方词表。四、五年级只有一个来源，可能漏了少量短语。
- 所有音标都是重新标注的英式音标，网上来源和课本词表都不带音标。
- 来源之间的分歧、已修正的错误、疑点，都记在 `issues` 表和[《单词表整理说明与问题报告》](单词表整理说明与问题报告.md)里。用之前建议先看一下这份报告。

## 怎么用

数据库就是一个文件：`外研社新版小学英语单词表_2022课标.db`。不需要装任何服务，可以用下面任意一种方式打开。

- **图形界面**：[DB Browser for SQLite](https://sqlitebrowser.org/)（免费）、TablePlus、DBeaver 等，打开文件后在“执行 SQL”里查询。
- **命令行**：macOS 自带 `sqlite3`。

```bash
sqlite3 -header -column 外研社新版小学英语单词表_2022课标.db
```

- **Python**：用标准库 `sqlite3`。

```python
import sqlite3
db = sqlite3.connect('外研社新版小学英语单词表_2022课标.db')
for row in db.execute("SELECT headword, phonetic, meaning FROM v_words WHERE book='6A' AND unit_no=3"):
    print(row)
```

### 常用查询

大多数时候只需要查视图 `v_words`，它把册、单元、词条拼在了一起。

```sql
-- 某册某单元的词表（按课本顺序）
SELECT headword, phonetic, meaning FROM v_words WHERE book = '4A' AND unit_no = 1 ORDER BY seq;

-- 一个词在哪本书、哪个单元
SELECT book_cn, unit_name, unit_title, headword, phonetic, meaning FROM v_words WHERE headword = 'share';

-- 六上课本加粗的课标二级词（听写重点）
SELECT unit_no, headword, phonetic, meaning FROM v_words WHERE book = '6A' AND is_core = 1 ORDER BY unit_no, seq;

-- 某年级的全部短语
SELECT book, unit_no, headword, meaning FROM v_words WHERE grade = 3 AND is_phrase = 1;

-- 在多个单元重复出现的词（常见于一词多义）
SELECT * FROM v_word_occurrences WHERE times > 1 ORDER BY times DESC;

-- 需要留意的问题清单
SELECT * FROM v_issues WHERE kind IN ('conflict', 'suspected');
```

`book` 的取值是 `3A` `3B` `4A` `4B` `5A` `5B` `6A`，A 是上册，B 是下册。`unit_no = 0` 是三上的 Welcome to school；六上的 `unit_no = 7` 是课本剧词汇（Plays）。

### 表和字段

| 表 / 视图 | 内容 |
|---|---|
| `textbooks` | 每册一行：年级、上下册、课标、首次使用学期、数据来源、整册说明 |
| `units` | 每册的单元编号、单元名和标题 |
| `words` | 词条本身 |
| `issues` | 修正记录（`fixed`）、来源分歧（`conflict`）、疑点（`suspected`）、整册说明（`book`） |
| `v_words` | **最常用**：册 + 单元 + 词条的全部信息 |
| `v_issues` | 问题清单，带册名 |
| `v_word_occurrences` | 同一个词在哪些册、哪些单元出现过，以及各处的释义 |

`words` / `v_words` 的主要字段：

| 字段 | 含义 |
|---|---|
| `headword` | 单词或短语，写法同课本 |
| `forms` | 完整形式或变体，如 let's → let us，be → am, is, are，tooth → teeth |
| `phonetic` | 英式音标，国内课本写法（æ、aɪ、eə、ɜː、əʊ），不带方括号 |
| `phonetic_source` | `oxford` 词典整词，`oxford_composed` 短语逐词拼接，`manual` 手工标注 |
| `meaning` | 中文释义 |
| `meaning_alt` | 另一个来源的不同释义（只有三年级有） |
| `is_phrase` | 1 = 短语 |
| `is_core` | 1 = 课本加粗（课标二级词），0 = 未加粗，空 = 来源没有标注（3A–5B） |
| `seq` / `global_seq` | 单元内顺序 / 从三上开始的总顺序 |
| `source` | `S` / `J` / `S+J` 教辅网站，`T` 课本 |
| `source_url` | 网页地址，或课本页码 |

## 目录结构

```
外研社新版小学英语单词表_2022课标.db   ← 成品数据库
单词表整理说明与问题报告.md            ← 来源、可信度、修正与疑点清单（由脚本生成）
data/
  source_s.json      来源 S（yy.suyang123.com）解析结果，3A–5B
  source_j.json      来源 J（yyld.51jiaoxi.com）解析结果，3A–3B
  merged.json        S、J 合并去重后的结果
  textbook_6a.json   六上：据课本附录人工录入（含加粗标记）
scripts/
  fetch_pages.py     下载网页到 pages/（pages/ 不入库）
  parse_pages.py     解析网页 → data/source_s.json、data/source_j.json
  merge_sources.py   合并两个来源 → data/merged.json
  build_db.py        建库：合并数据 + 课本录入数据 + 音标 + 修正/疑点规则
  make_report.py     生成《单词表整理说明与问题报告》
  phonetics.py       音标标注（手工表 + 词典）
  oxdict.py          调用 macOS 自带《牛津英汉汉英词典》
```

## 重新生成数据库

只用数据库的话不需要这一步。修改了规则、补了新册，或者想从网上重新抓数据时才需要。

环境要求：

- macOS，并在“词典”App 里启用《牛津英汉汉英词典》。音标靠它查。
- Python 3.9 以上，装好 `pyobjc`（`pip install pyobjc`）。

```bash
# 1. （可选）重新下载网页并解析。不做这一步就直接用 data/ 里的快照
python3 scripts/fetch_pages.py
python3 scripts/parse_pages.py
python3 scripts/merge_sources.py

# 2. 建库并生成报告
python3 scripts/build_db.py 外研社新版小学英语单词表_2022课标.db
python3 scripts/make_report.py 外研社新版小学英语单词表_2022课标.db 单词表整理说明与问题报告.md
```

`build_db.py` 最后会打印 `missing phonetic [...]`，列出查不到音标的词。如果列表不为空，就在 `build_db.py` 开头的 `phonetics.MANUAL.update({...})` 里手工补上。

## 补充新的一册（例如六下）

网上的词表质量参差不齐，所以最好照着课本录：

1. 仿照 `data/textbook_6a.json` 新建 `data/textbook_6b.json`。每个单元写 `[单元号, 单元标题, 课本页码, 词条列表]`；每个词条写 `[单词, 释义]`，加粗词写 `[单词, 释义, 1]`，有变形的写 `[单词, 释义, 0, "变形"]`。
2. 在 `scripts/build_db.py` 的 `BOOKS` 里加一行 `'6B': (6, '六年级', '下册', '2027年春季')`。
3. 按上一节重新生成，检查 `missing phonetic`，必要时补手工音标。
4. 有歧义的词（多音词、一词多义）对照课本核对音标，必要时写进 `phonetics.MANUAL_BY_BOOK`。

## 来源

- 英语朗读宝 [yy.suyang123.com](https://yy.suyang123.com/xiaoxue/sannianji/wybsq_shangce_words1.html)：3A–5B，按单元分页
- 英语朗读宝 [yyld.51jiaoxi.com](https://yyld.51jiaoxi.com/sanshang/wybsq_danci.html)：3A、3B 整册词表
- 外研社《英语》六年级上册课本（2024 年审定）附录 Words and expressions，第 96–98、104 页
- 单元标题对照：[中小学课本网](https://kebenwang.cn/book/1090)、[良师宝英语](https://liangshibao.com/english/waiyanshe/xiaoxue/xinbiaozhun/4b/kewen)
