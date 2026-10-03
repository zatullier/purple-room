"""Validate Blender dependencies and stage only public web files for GitHub Pages."""
from pathlib import Path
import hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
data=json.loads((ROOT/'assets/scene.json').read_text(encoding='utf-8'))
assert sha(ROOT/data['source'])==data['sourceSha256'], 'The .blend changed. Run the Blender export command in README.md before publishing.'
assert sha(ROOT/'scripts/export_scene.py')==data['exporterSha256'], 'The exporter changed. Re-export Blender assets before publishing.'
for name,digest in data['assetSha256'].items():
    assert sha(ROOT/'assets'/name)==digest, f'Render changed independently of Blender: {name}'
animation=data['animation']
assert animation['renderer']=='Blender Cycles'
assert animation['encoder']=='Blender Video Sequencer / H.264'
assert animation['frameCount']==animation['endFrame']-animation['startFrame']+1
assert len(animation['cameraPoses'])==animation['frameCount']
first,last=animation['cameraPoses'][0]['location'],animation['cameraPoses'][-1]['location']
assert sum((a-b)**2 for a,b in zip(first,last))>1, 'Animation must move the actual Blender camera.'
for name in ['fridge-in.mp4','fridge-out.mp4']:
    path=ROOT/'assets'/name
    assert path.stat().st_size>10000 and path.read_bytes()[4:8]==b'ftyp', f'Invalid MP4: {name}'
for x,y in data['fridge']['polygon']:assert 0<=x<=1 and 0<=y<=1
out=ROOT/'_site';out.mkdir(exist_ok=True)
for name in ['index.html','style.css','app.js']:shutil.copy2(ROOT/name,out/name)
(out/'assets').mkdir(exist_ok=True)
for name in ['room.jpg','fridge.jpg','fridge-in.mp4','fridge-out.mp4','scene.json']:shutil.copy2(ROOT/'assets'/name,out/'assets'/name)
(out/'.nojekyll').touch()
print('Verified native Blender camera animation, both clips, stills, and source dependency. Website ready in _site/.')
