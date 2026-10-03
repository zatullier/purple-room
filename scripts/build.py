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
assert data['fridge']['zoom']>1
for x,y in data['fridge']['polygon']:assert 0<=x<=1 and 0<=y<=1
out=ROOT/'_site';out.mkdir(exist_ok=True)
for name in ['index.html','style.css','app.js']:shutil.copy2(ROOT/name,out/name)
(out/'assets').mkdir(exist_ok=True)
for name in ['room.jpg','fridge.jpg','scene.json']:shutil.copy2(ROOT/'assets'/name,out/'assets'/name)
(out/'.nojekyll').touch()
print('Verified .blend, exporter, and both renders. Website ready in _site/.')
