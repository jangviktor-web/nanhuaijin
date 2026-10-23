# 关键词上下文抽取小工具（只读，不改动底本）
import sys, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kw = sys.argv[1]
win = int(sys.argv[2]) if len(sys.argv) > 2 else 120
only = sys.argv[3] if len(sys.argv) > 3 else None
files = sorted(glob.glob(os.path.join(ROOT, 'modules', '*.md')))
if only:
    files = [f for f in files if only in os.path.basename(f)]
for f in files:
    txt = open(f, encoding='utf-8', errors='ignore').read()
    for i, line in enumerate(txt.split('\n'), 1):
        if kw in line:
            for m in re.finditer(re.escape(kw), line):
                s = max(0, m.start()-win); e = min(len(line), m.end()+win)
                print(f'[{os.path.basename(f)}:{i}] ...{line[s:e]}...')
                break
