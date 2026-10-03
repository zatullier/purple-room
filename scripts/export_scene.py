"""Run inside Blender. The .blend is the sole source for both views and the hotspot."""
import bpy, json, hashlib, os, sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'
OUT.mkdir(exist_ok=True)
scene=bpy.context.scene
cam=scene.camera
assert cam, 'The Blender scene needs an active camera.'
source=Path(bpy.data.filepath)
assert source.is_file(), 'Open the source .blend before exporting.'
fridge=bpy.data.objects.get('Refrigerator body')
assert fridge, 'Missing Blender object: Refrigerator body'
world=[fridge.matrix_world@Vector(c) for c in fridge.bound_box]
x0,x1=min(p.x for p in world),max(p.x for p in world)
y0=min(p.y for p in world)-.075
z0=max(min(p.z for p in world),1.10) # The breakfast bar occludes the lower door.
z1=max(p.z for p in world)
corners=[world_to_camera_view(scene,cam,Vector((x,y0,z))) for x,z in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]]
polygon=[[round(p.x,7),round(1-p.y,7)] for p in corners]
left,right=min(p[0] for p in polygon),max(p[0] for p in polygon)
top,bottom=min(p[1] for p in polygon),max(p[1] for p in polygon)
center=[(left+right)/2,(top+bottom)/2]
zoom=3.25
scene.render.engine='CYCLES'
scene.cycles.samples=160
scene.cycles.adaptive_threshold=.018
scene.cycles.use_denoising=True
scene.cycles.device='CPU'
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    if any(d.type=='CUDA' for d in prefs.devices):
        for d in prefs.devices:d.use=d.type=='CUDA'
        scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1824;scene.render.resolution_y=1368;scene.render.resolution_percentage=100
scene.render.use_border=False
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.color_mode='RGB';scene.render.image_settings.quality=94
scene.render.filepath=str(OUT/'room.jpg')
bpy.ops.render.render(write_still=True)
# Same perspective, narrower field of view and an off-axis crop: the CSS zoom and
# detailed render align exactly, with no cut to a different camera angle.
cam.data.lens*=zoom
cam.data.shift_x=cam.data.shift_x*zoom+(center[0]-.5)*zoom
cam.data.shift_y=cam.data.shift_y*zoom+(.5-center[1])*zoom*.75
scene.render.filepath=str(OUT/'fridge.jpg')
bpy.ops.render.render(write_still=True)
manifest={
    'source':'blender/Purple_Room.blend',
    'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'exporterSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'blenderVersion':bpy.app.version_string,
    'camera':cam.name,
    'width':1824,'height':1368,
    'room':'assets/room.jpg','detail':'assets/fridge.jpg',
    'fridge':{'object':fridge.name,'polygon':polygon,'bounds':[left,top,right-left,bottom-top],'center':center,'zoom':zoom},
    'assetSha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['room.jpg','fridge.jpg']}
}
(OUT/'scene.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('WEB_ASSETS_EXPORTED',json.dumps(manifest))
# Do not save: exporting must never alter the source camera or original .blend.
