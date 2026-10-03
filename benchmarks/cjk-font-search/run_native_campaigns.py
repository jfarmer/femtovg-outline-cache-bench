#!/usr/bin/env python3
"""Run frozen exploratory native campaigns serially; analyze only afterward."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys

ROOT = Path(__file__).resolve().parent
OLD = Path('/private/tmp/femtovg-font-stress-search-20261002')
def font(family, filename, label=None):
    return (label or Path(filename).stem.replace('[wght]', '-VF'), ROOT/'fonts'/family/filename)
nanum = [font('nanumgothic','NanumGothic-Regular.ttf'),font('nanumgothic','NanumGothic-ExtraBold.ttf'),
    font('nanummyeongjo','NanumMyeongjo-Regular.ttf'),font('nanummyeongjo','NanumMyeongjo-Bold.ttf'),
    font('nanummyeongjo','NanumMyeongjo-ExtraBold.ttf'),font('nanumgothiccoding','NanumGothicCoding-Regular.ttf'),
    font('d2coding','D2Coding-Regular.ttf')]
chinese = [font('babelstone','release/BabelStoneHan.ttf','BabelStoneHan'),
    font('notosanssc','NotoSansSC[wght].ttf'),font('notoserifsc','NotoSerifSC[wght].ttf'),
    font('wqy-microhei','wqy-microhei.ttc','WenQuanYiMicroHei-face0')]
droid = [font('droid','DroidSansFallback.ttf'),font('droid','DroidSansFallbackFull.ttf')]
controls=[('Rye-Regular',OLD/'fonts/rye/Rye-Regular.ttf'),('Vollkorn-Medium',OLD/'fonts/controls/Vollkorn-Medium.ttf')]
campaigns = [('english',OLD/'screen.py',OLD/'build/build.json',controls+nanum+chinese),
    ('ko',ROOT/'prepared-ko-isolated/screen/screen.py',ROOT/'build-ko-isolated/build.json',nanum),
    ('zh',ROOT/'prepared-zh-isolated/screen/screen.py',ROOT/'build-zh-isolated/build.json',chinese),
    ('zh-pure-ui',ROOT/'prepared-zh-pure-ui-isolated/screen/screen.py',ROOT/'build-zh-pure-ui-isolated/build.json',droid+chinese)]
plan=ROOT/'native-campaign-plan.json'
if plan.exists(): raise ValueError('Fresh plan required')
proof={'complete':False,'exploratory':True,'created_utc':datetime.now(timezone.utc).isoformat(),
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'scope':'All fonts retained; four balanced kernel orders, 20 cases, 20 repeats; per-glyph screen does not estimate application/cache gain. No analysis/build/download during timing.',
    'campaigns':[]}
for tag,driver,build,fonts in campaigns:
    command=[sys.executable,'-B',str(driver),'run','--build',str(build),'--mode','timing','--trials','4','--repeats','20','--rounds','1','--output',str(ROOT/('native-'+tag))]
    for label,path in fonts: command += ['--font',label,str(path)]
    proof['campaigns'].append({'tag':tag,'command':command,'complete':False})
plan.write_text(json.dumps(proof,indent=2)+'\n')
for item in proof['campaigns']:
    print('START',item['tag'],flush=True)
    completed=subprocess.run(item['command'])
    item['exit_code']=completed.returncode
    item['complete']=completed.returncode==0
    plan.write_text(json.dumps(proof,indent=2)+'\n')
    if completed.returncode: raise SystemExit(completed.returncode)
proof['complete']=True
proof['finished_utc']=datetime.now(timezone.utc).isoformat()
plan.write_text(json.dumps(proof,indent=2)+'\n')
print('All native exploratory campaigns complete',flush=True)
