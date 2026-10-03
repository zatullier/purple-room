# The Purple Room

[Open the website](https://zatullier.github.io/purple-room/)

Click the fridge to play a camera approach authored and rendered in **Blender**. The camera physically moves through the scene, with a small lens change and an animated focus target. Back to room plays a Blender-encoded return clip. The browser performs no image scaling, camera interpolation, or CSS zoom.

## Edit the animation in Blender

Open `blender/Purple_Room.blend` in Blender 5.2 or newer. It opens in the **Animation** workspace. Press Space to preview, or scrub the timeline:

- Frame 1: the original room view.
- Frame 36: the approach.
- Frame 72: the fridge close-up.

The active camera has location and focal-length keyframes in its object and camera-data action slots. `Fridge camera focus` in collection **10 Fridge camera animation** is the animated look-at target. These channels use native Bezier keyframes with clamped handles. Edit the keyframes to change the move; the scene's frame range, frame rate, resolution, and Cycles settings control the export. The default is 72 frames at 24 fps, 1280 × 960.

The fridge object and foreground occluder are selected by the scene's `web_hotspot_object` and `web_occluder_object` custom properties. Their geometry and the home camera determine the clickable area. Textures are packed in the source file.

## Export: all image and animation work happens inside Blender

From this repository's directory:

```powershell
& 'C:\Users\zacha\AppData\Local\Programs\Blender\5.2\blender.exe' --background blender/Purple_Room.blend --python scripts/export_scene.py
python scripts/build.py
```

Substitute your Blender executable on another machine. The exporter:

1. Evaluates the saved Blender camera action for every frame.
2. Renders the sequence with Cycles, using CUDA when available and CPU otherwise.
3. Uses **Blender's Video Sequencer** to encode H.264 MP4 approach and return clips. The return clip reverses the rendered frame sequence inside Blender.
4. Exports matching endpoint JPEGs and projects the fridge's click area from scene geometry.
5. Records the source hash, asset hashes, evaluated camera poses, and animation settings in `assets/scene.json`.

Renders resume from `.render-cache/<source hash>/`. An editable `Video_Sequencer.blend` is saved beside the cached PNG frames. These large intermediate files remain local and can be regenerated. The canonical `blender/Purple_Room.blend` is never modified by exporting.

`scripts/animate_scene.py` is the original camera-authoring script. Run it only to recreate the initial animation; it replaces the camera's existing actions. Normal edits require only the export command above. `scripts/preview_animation.py` renders three quick camera checkpoints without modifying the source.

## Website and publishing

The website only handles clicks, keyboard input, and native video playback. Reduced-motion users receive an immediate switch between Blender's endpoint renders. Escape returns to the room, or cancels a move already in progress. Playback failures are reported instead of substituting a CSS zoom.

```sh
python scripts/build.py
python -m http.server 4173 --directory _site
```

Open http://localhost:4173 to preview. There are no npm packages, external fonts, trackers, or third-party runtime services.

The build verifies the .blend, exporter, images, and clips against their hashes. Changing the Blender file without exporting again fails the build, preventing stale animation from being published. Push the updated .blend and generated assets to `main` to deploy through GitHub Actions and GitHub Pages. Only web files are deployed; the .blend and scripts remain in the repository.
