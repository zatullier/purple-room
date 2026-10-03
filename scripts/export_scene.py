"""Blender owns the camera action, rendering, stills, hit area, and video encoding.

Run: blender -b blender/Purple_Room.blend -P scripts/export_scene.py
Frame renders are resumable. This script never saves over the source .blend.
"""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets';OUT.mkdir(exist_ok=True)
source=Path(bpy.data.filepath)
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
scene=bpy.context.scene
cam=scene.camera
assert cam and cam.animation_data and cam.animation_data.action, 'Author the native camera animation first.'
start=scene.frame_start;end=scene.frame_end
assert end>start
fps=scene.render.fps/scene.render.fps_base
width=scene.render.resolution_x; height=scene.render.resolution_y
cache=ROOT/'.render-cache'/source_hash[:16];cache.mkdir(parents=True,exist_ok=True)
scene.frame_set(start);bpy.context.view_layer.update()
fridge=bpy.data.objects[scene['web_hotspot_object']]
bar=bpy.data.objects[scene['web_occluder_object']]
corners=[fridge.matrix_world@Vector(c) for c in fridge.bound_box]
x0,x1=min(p.x for p in corners),max(p.x for p in corners)
y0=min(p.y for p in corners)-.075
z0=max(min(p.z for p in corners),max((bar.matrix_world@Vector(c)).z for c in bar.bound_box)+.02)
z1=max(p.z for p in corners)
projected=[world_to_camera_view(scene,cam,Vector((x,y0,z))) for x,z in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]]
polygon=[[round(p.x,7),round(1-p.y,7)] for p in projected]
left,right=min(p[0] for p in polygon),max(p[0] for p in polygon)
top,bottom=min(p[1] for p in polygon),max(p[1] for p in polygon)
scene.cycles.device='CPU'
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    if any(d.type=='CUDA' for d in prefs.devices):
        for d in prefs.devices:d.use=d.type=='CUDA'
        scene.cycles.device='GPU'
except Exception:pass
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.resolution_percentage=100;scene.render.use_border=False
poses=[];frames=[]
for frame in range(start,end+1):
    scene.frame_set(frame);bpy.context.view_layer.update()
    path=cache/f'{frame:04d}.png';frames.append(path)
    poses.append({'frame':frame,'location':[round(v,6) for v in cam.matrix_world.translation],
                  'quaternion':[round(v,7) for v in cam.matrix_world.to_quaternion()], 'lens':round(cam.data.lens,6)})
    if not path.exists():
        scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    print(f'FRAME_READY {frame-start+1}/{end-start+1}',flush=True)
assert (Vector(poses[-1]['location'])-Vector(poses[0]['location'])).length>1, 'Expected a real camera dolly.'

# Native Blender Video Sequencer encodes the rendered frame sequences in both directions.
encode=bpy.data.scenes.new('Web clips - Blender Video Sequencer')
encode.render.resolution_x=width;encode.render.resolution_y=height;encode.render.resolution_percentage=100
encode.render.fps=scene.render.fps;encode.render.fps_base=scene.render.fps_base
encode.frame_start=1;encode.frame_end=len(frames)
encode.view_settings.view_transform='Standard';encode.view_settings.look='None';encode.view_settings.exposure=0;encode.view_settings.gamma=1
encode.sequencer_colorspace_settings.name='sRGB'
encode.render.image_settings.media_type='VIDEO';encode.render.image_settings.file_format='FFMPEG'
encode.render.ffmpeg.format='MPEG4';encode.render.ffmpeg.codec='H264'
encode.render.ffmpeg.constant_rate_factor='HIGH';encode.render.ffmpeg.ffmpeg_preset='GOOD'
encode.render.ffmpeg.gopsize=12;encode.render.ffmpeg.audio_codec='NONE'
encode.render.use_sequencer=True
editor=encode.sequence_editor_create()
for name,sequence in [('fridge-in',frames),('fridge-out',list(reversed(frames)))]:
    for strip in list(editor.strips):editor.strips.remove(strip)
    strip=editor.strips.new_image(name,filepath=str(sequence[0]),channel=1,frame_start=1)
    for path in sequence[1:]:strip.elements.append(path.name)
    strip.frame_final_duration=len(sequence)
    encode.render.filepath=str(OUT/(name+'.mp4'))
    bpy.ops.render.render(animation=True,scene=encode.name)
    destination=OUT/(name+'.mp4')
    if not destination.exists():
        candidates=list(OUT.glob(name+'*.mp4'))
        assert len(candidates)==1,f'Unexpected Blender video output: {candidates}'
        candidates[0].replace(destination)
    assert destination.stat().st_size>10000,'Video encoding produced no usable clip.'
    print('BLENDER_VIDEO_ENCODED',destination.name,destination.stat().st_size,flush=True)
# Exact endpoints make still-to-video transitions seamless.
encode.render.image_settings.media_type='IMAGE';encode.render.image_settings.file_format='JPEG';encode.render.image_settings.color_mode='RGB';encode.render.image_settings.quality=95
for name,path in [('room.jpg',frames[0]),('fridge.jpg',frames[-1])]:
    image=bpy.data.images.load(str(path),check_existing=True)
    image.save_render(filepath=str(OUT/name),scene=encode)
    bpy.data.images.remove(image)
scene.frame_set(start)
if bpy.context.window:bpy.context.window.scene=encode
encode.render.image_settings.media_type='VIDEO';encode.render.image_settings.file_format='FFMPEG'
bpy.ops.wm.save_as_mainfile(filepath=str(cache/'Video_Sequencer.blend'),copy=True)
assets=['room.jpg','fridge.jpg','fridge-in.mp4','fridge-out.mp4']
manifest={'source':'blender/Purple_Room.blend','sourceSha256':source_hash,
    'exporterSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'blenderVersion':bpy.app.version_string,'camera':cam.name,'width':width,'height':height,
    'room':'assets/room.jpg','detail':'assets/fridge.jpg',
    'fridge':{'object':fridge.name,'polygon':polygon,'bounds':[left,top,right-left,bottom-top]},
    'animation':{'renderer':'Blender Cycles','encoder':'Blender Video Sequencer / H.264',
        'action':cam.animation_data.action.name,'startFrame':start,'endFrame':end,'fps':fps,
        'duration':len(frames)/fps,'frameCount':len(frames),
        'forward':'assets/fridge-in.mp4','reverse':'assets/fridge-out.mp4','cameraPoses':poses},
    'assetSha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in assets}}
(OUT/'scene.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('BLENDER_ANIMATION_EXPORT_COMPLETE',len(frames),'frames',flush=True)
