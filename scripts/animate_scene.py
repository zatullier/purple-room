"""Author the actual fridge camera move in the .blend, with editable keyframes."""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
scene.name='Purple Room - Camera Animation'
cam=scene.camera
scene.frame_set(1)
fridge=bpy.data.objects['Refrigerator body']
bar=bpy.data.objects['Marble breakfast bar slab']
corners=[fridge.matrix_world@Vector(c) for c in fridge.bound_box]
bar_top=max((bar.matrix_world@Vector(c)).z for c in bar.bound_box)
focus=Vector(((min(c.x for c in corners)+max(c.x for c in corners))/2,
              min(c.y for c in corners)-.03,
              (max(c.z for c in corners)+bar_top)/2))
home=cam.location.copy()
home_target=home+cam.rotation_euler.to_quaternion()@Vector((0,0,-6))
home_lens=cam.data.lens
end=Vector((focus.x-.09,focus.y-1.90,focus.z+.15))
collection=bpy.data.collections.get('10 Fridge camera animation')
if not collection:
    collection=bpy.data.collections.new('10 Fridge camera animation');scene.collection.children.link(collection)
target=bpy.data.objects.get('Fridge camera focus')
if not target:
    target=bpy.data.objects.new('Fridge camera focus',None);collection.objects.link(target)
target.empty_display_type='SPHERE';target.empty_display_size=.09
target['purpose']='Animated look-at target. Edit its keyframes with the camera to change the fridge approach.'
cam.animation_data_clear();cam.data.animation_data_clear();target.animation_data_clear()
constraint=cam.constraints.get('Fridge look-at') or cam.constraints.new('TRACK_TO')
constraint.name='Fridge look-at';constraint.target=target;constraint.track_axis='TRACK_NEGATIVE_Z';constraint.up_axis='UP_Y'
cam.data.shift_x=0;cam.data.shift_y=0
for frame,position,aim,lens in [(1,home,home_target,home_lens),(72,end,focus,28.0)]:
    cam.location=position;cam.keyframe_insert(data_path='location',frame=frame,group='Camera dolly')
    target.location=aim;target.keyframe_insert(data_path='location',frame=frame,group='Fridge focus')
    cam.data.lens=lens;cam.data.keyframe_insert(data_path='lens',frame=frame,group='Lens')
for owner,name in [(cam,'Fridge approach - camera dolly'),(target,'Fridge approach - focus'),(cam.data,'Fridge approach - focal length')]:
    action=owner.animation_data.action;action.name=name
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation='BEZIER';key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'
scene.frame_start=1;scene.frame_end=72;scene.render.fps=24;scene.render.fps_base=1
scene.timeline_markers.clear()
scene.timeline_markers.new('ROOM - click refrigerator',frame=1)
scene.timeline_markers.new('APPROACH',frame=36)
scene.timeline_markers.new('FRIDGE - hold until return',frame=72)
scene['web_home_frame']=1;scene['web_focus_frame']=72
scene['web_hotspot_object']=fridge.name
scene['web_occluder_object']=bar.name
scene['web_animation']='Camera location, focus-target location, and focal length use native Bezier keyframes. 72 frames at 24 fps.'
scene['web_playback']='The browser plays Blender-rendered forward / reverse clips; it performs no camera or image transforms.'
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.adaptive_threshold=.035;scene.cycles.use_denoising=True
scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.render.filepath='//../.render-cache/fridge/frame_'
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.overlay.show_overlays=False
if bpy.context.window and bpy.data.workspaces.get('Animation'):
    bpy.context.window.workspace=bpy.data.workspaces['Animation']
note=bpy.data.texts.get('START HERE') or bpy.data.texts.new('START HERE')
note.clear();note.write('PURPLE ROOM - NATIVE BLENDER CAMERA ANIMATION\n\nFrames 1-72: three-second camera approach to the refrigerator, 24 fps.\nPress Space in the Animation workspace to preview; scrub the timeline to inspect.\nThe camera, focal length, and Fridge camera focus object have editable Bezier keyframes.\nCollection 10 contains the look-at target; the active camera is in collection 09.\nThe website only plays movies rendered and encoded by Blender. It does not animate image scale.\nRun scripts/export_scene.py in Blender to render the clips, stills, and hotspot metadata.\nThe exporter also writes a separate Blender Video Sequencer project for forward and reverse encoding.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Purple_Room.blend'))
print('ANIMATION_AUTHORED',tuple(home),tuple(end),'frames',scene.frame_start,scene.frame_end)
