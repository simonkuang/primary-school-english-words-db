"""生成新版词表的《整理说明与问题报告》。用法：python3 scripts/make_report.py <db> <out.md>"""
import sqlite3
import sys

db = sqlite3.connect(sys.argv[1])
out = []
w = out.append


def esc(s):
    return '' if s is None else str(s).replace('|', '\\|').replace('\n', ' ')


def table(head, rows):
    w('| ' + ' | '.join(head) + ' |')
    w('|' + '---|' * len(head))
    for r in rows:
        w('| ' + ' | '.join(esc(x) for x in r) + ' |')
    w('')


total = db.execute('select count(*) from words').fetchone()[0]
w('# 外研社新版小学英语（三年级起点）单词表：整理说明与问题报告')
w('')
w('教材：外语教学与研究出版社《英语（三年级起点）》新版，依据《义务教育英语课程标准（2022年版）》编写，按 Unit 编排。')
w('')
nbooks = db.execute('select count(*) from textbooks').fetchone()[0]
w(f'数据库：`外研社新版小学英语单词表_2022课标.db`，共 {total} 条，覆盖三年级上册至六年级上册，共 {nbooks} 册。')
w('')
w('## 一、覆盖范围')
w('')
table(['册', '首次使用', '单元', '词条数', '来源', '说明'],
      db.execute('''select t.code || ' ' || t.grade_cn || t.term, t.first_use,
                    (select group_concat(unit_name || ' ' || title, '；') from (select * from units u where u.textbook_id=t.id order by unit_no)),
                    (select count(*) from words x where x.textbook_id=t.id), t.sources, coalesce(t.note,'')
                    from textbooks t order by t.id''').fetchall())
w('- **六年级上册直接取自课本：** 依据新版六上课本（2024 年国家教材委员会专家委员会审核通过，2024 年 10 月出版）附录的 Words and expressions 逐条录入，并与书末 Word list 核对一致。2026 年秋季起全国义务教育各年级已全部换用新教材，新版六上本学期已在使用。')
w('- **六年级下册暂缺：** 手头没有新版六下课本；网上能查到的“外研三起六年级下册”词表仍是旧版（按 Module 编排），所以没有收。拿到课本后可以按六上的方法补充。')
w('- **首次使用学期：** 三上（2024 年秋季）和六上（2026 年秋季）有依据；其余各册是按逐年换版推算的。')
w('- **原 PDF 已全部弃用：** 核对结果是，原 PDF 是 2012/2013 年的旧版教材（其中“五年级下册”实际是一年级起点版），与新版教材不对应，因此这次整套换成了新版词表，没有沿用原 PDF 的任何词条。')
w('')
w('## 二、来源与可信度')
w('')
w('- **来源 S**：英语朗读宝 yy.suyang123.com，按单元分页，三上至五下 6 册都有。')
w('- **来源 J**：英语朗读宝 yyld.51jiaoxi.com，提供整册词表，只有三上和三下的新版。')
w('- **三年级用两个来源交叉核对。** 两个来源都有的词条标记为 `source = S+J`，只在一个来源出现的标记为 S 或 J，全部收录（取并集）。释义优先采用来源 S（错别字更少）；J 的释义如果不同，放在 `meaning_alt` 字段里。')
w('- **四、五年级只有来源 S，可能缺少部分短语。** 拿三年级对照发现，S 漏收了 10 个短语或连字符词：o\'clock、tick-tock、forty-five、half past…、what about…、afternoon tea、hot dog、tai chi、grow up、a lot（S 写成了 lot）。四、五年级也可能有类似遗漏，建议对照课本后面的单词表补齐。')
w('- **来源 T（六上）**：课本附录本身，是唯一直接来自教材的一册。课本在词表中把“义务教育英语课程标准要求掌握的二级词汇”加粗，数据库用 `is_core = 1` 标出（共 11 个）；三上至五下的网上来源不区分加粗，`is_core` 为空。')
w('- 三上至五下来源 S、J 是第三方教辅网站的整理，不是出版社官方发布的词表。单元归属和释义总体可靠，但个别处请以课本为准（见第四节）。')
w('')
w('## 三、已直接修正的问题')
w('')
table(['册', '单元', '条目', '字段', '来源原文', '处理', '说明'],
      db.execute("select book, unit_no, headword, field, original, suggestion, description from v_issues where kind='fixed' order by id").fetchall())
w('## 四、来源分歧与疑点（已收录，请对照课本确认）')
w('')
table(['册', '单元', '条目', '字段', '已收录', '另一种说法', '说明'],
      db.execute("select book, unit_no, headword, field, original, suggestion, description from v_issues where kind in ('conflict','suspected') order by kind, id").fetchall())
w('## 五、音标')
w('')
src = dict(db.execute('select phonetic_source, count(*) from words group by phonetic_source').fetchall())
w('网上来源和课本词表都不带音标。数据库中的 `phonetic` 是重新标注的英式音标（外研版课本用英式发音），写法与课本一致（æ、aɪ、eə、ɜː、əʊ 等），不含方括号。')
w('')
w(f'- `oxford`：{src.get("oxford", 0)} 条，取自 macOS 自带《牛津英汉汉英词典》的英式音标，并转写成课本写法；')
w(f'- `oxford_composed`：{src.get("oxford_composed", 0)} 条短语，由各词音标拼接而成；')
w(f'- `manual`：{src.get("manual", 0)} 条，是词典查不到的词、拟声词、复数和缩写，以及需要按释义选读音的词（如 close 作“合上”读 /kləʊz/、live 作“居住”读 /lɪv/、use 作动词读 /juːz/），均为手工标注。')
w('- 短语 take care of sb/sth、look at sb/sth、because of sb/sth 只标到 of / at 为止，sb/sth 部分不标音。')
w('')
w('## 六、数据库结构与常用查询')
w('')
w('| 表/视图 | 内容 |')
w('|---|---|')
w(f'| `textbooks` | {nbooks} 册：年级、上下册、课标、首次使用学期、来源 |')
w('| `units` | 每册的单元（`unit_no = 0` 为三上开篇的 Welcome to school；六上 `unit_no = 7` 为课本剧词汇 Plays），含单元标题 |')
w('| `words` | 词条：单词/短语、完整形式（forms）、音标、释义、另一来源释义、是否短语、是否课标二级词（is_core，仅六上）、来源 |')
w('| `issues` | 修正、分歧、疑点记录 |')
w('| `v_words` | 常用视图：册 + 单元 + 词条全部信息 |')
w('| `v_issues` | 问题清单 |')
w('| `v_word_occurrences` | 同一个词在哪些册、哪些单元出现过，以及各处的释义 |')
w('')
w('```sql')
w("-- 某册某单元的词表")
w("SELECT headword, phonetic, meaning FROM v_words WHERE book = '4A' AND unit_no = 1 ORDER BY seq;")
w("-- 查一个词在哪本书、哪个单元")
w("SELECT book_cn, unit_name, unit_title, headword, phonetic, meaning FROM v_words WHERE headword = 'share';")
w("-- 某年级的全部短语")
w("SELECT book, unit_no, headword, meaning FROM v_words WHERE grade = 3 AND is_phrase = 1;")
w("-- 只在一个来源出现、需要核对的三年级词条")
w("SELECT book, unit_no, headword, source FROM v_words WHERE grade = 3 AND source != 'S+J';")
w("-- 六上课本加粗的课标二级词")
w("SELECT unit_no, headword, phonetic, meaning FROM v_words WHERE book = '6A' AND is_core = 1 ORDER BY unit_no, seq;")
w("-- 多次出现的词")
w("SELECT * FROM v_word_occurrences WHERE times > 1 ORDER BY times DESC;")
w('```')
w('')
w('`scripts/` 目录下是抓取、解析、合并、建库和生成本报告的脚本，`data/` 下是各来源解析后的数据快照，可以重新生成数据库。详见 README.md。音标标注依赖 macOS 自带词典。')
w('')
w('来源网址：')
w('')
w('- https://yy.suyang123.com/xiaoxue/sannianji/wybsq_shangce_words1.html （各册各单元为同一路径格式：sannianji / sinianji / wunianji，shangce / xiace，words1–7）')
w('- https://yyld.51jiaoxi.com/sanshang/wybsq_danci.html 、https://yyld.51jiaoxi.com/sanxia/wybsq_danci.html')
w('- 单元标题对照：https://kebenwang.cn/book/1090 、https://liangshibao.com/english/waiyanshe/xiaoxue/xinbiaozhun/4b/kewen')
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('ok')
