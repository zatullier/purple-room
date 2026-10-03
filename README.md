# The Purple Room

A GitHub Pages website built from `blender/Purple_Room.blend`. The room is the entire page. Click or tap the fridge to zoom in; Back to room or Escape reverses the zoom. Keyboard users can Tab to the fridge and press Enter. Reduced-motion preferences are respected.

The website uses **Blender-rendered views**, preserving the scene's Cycles lighting, materials, and translucent mesh. It does not run a live 3D renderer in the browser. A smooth image-space camera zoom transitions to a sharper Blender render of exactly the same view.

## Blender is the source

`scripts/export_scene.py` loads the active camera and the `Refrigerator body` object from the .blend. It projects that object's visible bounds into the image, renders both views, and writes `assets/scene.json`. No fridge coordinates are hand-positioned in the website.

`scripts/build.py` verifies SHA-256 hashes of the .blend, exporter, and images before publishing. Editing the Blender file without regenerating the website images fails the build instead of publishing stale renders. All textures are packed in the .blend.

After editing the Blender scene, export again:

```powershell
& 'C:\Users\zacha\AppData\Local\Programs\Blender\5.2\blender.exe' --background blender/Purple_Room.blend --python scripts/export_scene.py
python scripts/build.py
```

On another machine, substitute its Blender executable. Blender 5.2 or newer is required for this source file. Rendering uses CUDA when available and otherwise CPU. Exporting never saves changes to the source .blend.

## Preview

```sh
python scripts/build.py
python -m http.server 4173 --directory _site
```

Open http://localhost:4173. There are no npm packages, external fonts, trackers, or third-party runtime services.

## GitHub Pages

Push to `main`. In repository **Settings → Pages**, select **GitHub Actions** as the source. The included workflow verifies the Blender dependencies and publishes `_site` using the [official GitHub Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

The .blend and build scripts stay in the repository; only the website and rendered assets are deployed to Pages.
