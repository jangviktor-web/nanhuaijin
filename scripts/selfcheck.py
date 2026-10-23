#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""南怀瑾 skill 自检脚本：引文核验 / 编码卫生 / 索引路径校验。

用法：
    python3 scripts/selfcheck.py            # 全部检查
    python3 scripts/selfcheck.py quotes     # 只核引文
    python3 scripts/selfcheck.py index      # 只核索引路径与关键词
    python3 scripts/selfcheck.py enc        # 只查编码

引文核验原理：把 SKILL.md / references / cases 里所有「……」引文抽出，
去掉标点空白后，在 modules/ 全部底本里做子串匹配；核不到的会被列出，
需人工确认是否为「南师大意」改写（改写不该加引号）。
"""
import os, re, sys, glob, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'modules')


def norm(s):
    s = unicodedata.normalize('NFKC', s)
    return re.sub(r'[\s，。、；：！？“”‘’（）《》「」『』·…—－\-\.\,\;\:\!\?\"\'\(\)\[\]]', '', s)


def load_raw():
    corpus = []
    for f in glob.glob(os.path.join(RAW, '*.md')):
        corpus.append(norm(open(f, encoding='utf-8').read()))
    return corpus


def check_quotes():
    """只核「带出处的正式引用块」：`> 「……」——《书名》`。
    分析性引号（研究者自设术语）、含 ×× 的可复用句式模板不参与核验。"""
    corpus = glob.glob(os.path.join(RAW, '*.md'))
    # 平台版未收录的三部书：补查外部全量语料目录（若存在）
    extra = os.path.join(os.path.dirname(ROOT), 'nhj-corpus-staging')
    if os.path.isdir(extra):
        corpus += glob.glob(os.path.join(extra, '*.md'))
    big = '\n'.join(norm(open(f, encoding='utf-8').read()) for f in corpus)
    files = [os.path.join(ROOT, 'SKILL.md')]
    files += glob.glob(os.path.join(ROOT, 'references', '*.md'))
    files += glob.glob(os.path.join(ROOT, 'cases', '*.md'))
    bad, total = [], 0
    for f in files:
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if not line.startswith('>') or '「' not in line:
                continue
            m = re.search(r'「(.+?)」(.*)', line)
            if not m:
                continue
            q, rest = m.group(1), m.group(2)
            if '《' not in rest or '×' in q:
                continue
            total += 1
            segs = [x for x in q.split('……') if len(norm(x)) >= 6]
            if not all(norm(seg) in big for seg in segs):
                bad.append((os.path.relpath(f, ROOT), q[:45]))
    print(f'带出处引用块核验：{total} 条，未命中 {len(bad)} 条')
    for f, q in bad:
        print(f'  ? {f} :: {q}')
    return len(bad)


def check_index():
    sk = open(os.path.join(ROOT, 'SKILL.md'), encoding='utf-8').read()
    paths = set(re.findall(r'`((?:modules|references|cases)/[^`]+?\.md)`', sk))
    miss = [p for p in paths if not os.path.exists(os.path.join(ROOT, p))]
    print(f'索引路径：{len(paths)} 个，缺失 {len(miss)} 个')
    for p in miss:
        print(f'  X {p}')
    rows = re.findall(r'`((?:modules|references|cases)/[^`]+?\.md)`\s*搜"([^"]+)"', sk)
    fail = []
    for p, kws in rows:
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            continue
        t = open(fp, encoding='utf-8').read()
        for kw in [k.strip() for k in kws.replace('、', '|').split('|')]:
            if kw and kw not in t:
                fail.append((p, kw))
    print(f'关键词引用：{len(rows)} 组，失效 {len(fail)} 条')
    for p, kw in fail:
        print(f'  X {p} 搜"{kw}"')
    return len(miss) + len(fail)


def check_enc():
    files = glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True)
    bad = 0
    for f in files:
        b = open(f, 'rb').read()
        try:
            t = b.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f'  X 非法 UTF-8：{os.path.relpath(f, ROOT)} {e}')
            bad += 1
            continue
        n = t.count('\ufffd')
        if n:
            print(f'  X U+FFFD ×{n}：{os.path.relpath(f, ROOT)}')
            bad += n
    print(f'编码卫生：扫描 {len(files)} 个文件，问题 {bad}')
    return bad


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    rc = 0
    if what in ('all', 'quotes'):
        rc += check_quotes()
    if what in ('all', 'index'):
        rc += check_index()
    if what in ('all', 'enc'):
        rc += check_enc()
    print('PASS' if rc == 0 else f'FAIL（{rc} 项待人工确认）')
    sys.exit(0 if rc == 0 else 1)
