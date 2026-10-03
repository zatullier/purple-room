import bpy
from pathlib import Path
scene=bpy.context.scene
root=Path(__file__).resolve().parents[1]
out=root/'.render-cache/preview';out.mkdir(parents=True,exist_ok=True)
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
for d in p.devices:d.use=d.type=='CUDA'
scene.cycles.device='GPU';scene.cycles.samples=32
scene.render.resolution_x=720;scene.render.resolution_y=540
scene.render.image_settings.file_format='PNG'
for frame in [1,36,72]:
    scene.frame_set(frame);scene.render.filepath=str(out/f'{frame:04d}.png');bpy.ops.render.render(write_still=True)
    print('PREVIEW_FRAME',frame,tuple(scene.camera.location),flush=True)
