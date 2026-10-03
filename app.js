// Blender authors and renders every frame. This file only selects and plays media.
const scene = document.querySelector('#scene');
const image = document.querySelector('#room-image');
const detail = document.querySelector('#detail-image');
const forward = document.querySelector('#approach');
const reverse = document.querySelector('#return');
const fridge = document.querySelector('#fridge');
const back = document.querySelector('#back');
const hint = document.querySelector('#hint');
const status = document.querySelector('#status');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let metadata;
let view = 'room';
let playing = null;
let operation = 0;

function settle(destination, message) {
  operation++;
  for (const video of [forward, reverse]) {
    video.pause();
    video.hidden = true;
    video.onended = null;
  }
  playing = null;
  view = destination;
  scene.dataset.view = destination;
  const atRoom = destination === 'room';
  image.hidden = !atRoom;
  detail.hidden = atRoom;
  fridge.hidden = !atRoom;
  back.hidden = atRoom;
  back.disabled = false;
  hint.hidden = !atRoom;
  hint.textContent = 'Click the fridge to look closer';
  status.textContent = message ?? (atRoom ? 'Returned to the room.' : 'At the fridge. Use Back to room or Escape to return.');
  (atRoom ? fridge : back).focus({ preventScroll: true });
}

async function playMove(destination) {
  if (!metadata || playing || destination === view) return;
  if (reducedMotion.matches) { settle(destination); return; }
  const token = ++operation;
  const origin = view;
  const video = destination === 'fridge' ? forward : reverse;
  playing = video;
  scene.dataset.view = destination === 'fridge' ? 'approaching' : 'returning';
  fridge.hidden = true;
  hint.hidden = true;
  back.hidden = false;
  back.disabled = true;
  status.textContent = destination === 'fridge' ? 'Moving toward the fridge.' : 'Returning to the room.';
  video.currentTime = 0;
  video.onended = () => { if (token === operation) settle(destination); };
  video.onerror = () => {
    if (token !== operation) return;
    settle(origin, 'The animation could not play. Please try again.');
    if (origin === 'room') hint.textContent = 'Could not play the animation. Click the fridge to retry.';
  };
  try {
    // Native HTML video playback shows Blender's camera animation, not a CSS transform.
    await video.play();
    if (token === operation) video.hidden = false;
  } catch (error) {
    if (token !== operation) return;
    console.error('Animation playback failed', error);
    settle(origin, 'The animation could not play. Please try again.');
    if (origin === 'room') hint.textContent = 'Could not play the animation. Click the fridge to retry.';
  }
}

fridge.addEventListener('click', () => playMove('fridge'));
back.addEventListener('click', () => playMove('room'));
window.addEventListener('keydown', event => {
  if (event.key !== 'Escape' || (view === 'room' && !playing)) return;
  event.preventDefault();
  if (playing) settle('room', 'Camera animation cancelled. Returned to the room.');
  else playMove('room');
});
reducedMotion.addEventListener('change', () => {
  if (reducedMotion.matches && playing) settle(playing === forward ? 'fridge' : 'room');
});

try {
  const response = await fetch(new URL('./assets/scene.json', import.meta.url), { cache: 'no-cache' });
  if (!response.ok) throw new Error(`Scene metadata: ${response.status}`);
  metadata = await response.json();
  if (!metadata.animation?.forward || !metadata.animation?.reverse) throw new Error('Blender animation assets missing');
  if (!(metadata.width > 0 && metadata.height > 0)) throw new Error('Invalid Blender render dimensions');
  scene.style.setProperty('--scene-aspect', metadata.width / metadata.height);
  const [x, y, w, h] = metadata.fridge.bounds;
  if (![x, y, w, h].every(Number.isFinite) || w <= 0 || h <= 0) throw new Error('Invalid fridge bounds');
  Object.assign(fridge.style, { left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%` });
  const version = metadata.sourceSha256.slice(0, 12);
  const url = path => new URL(`./${path}?v=${version}`, import.meta.url).href;
  image.src = url(metadata.room);
  detail.src = url(metadata.detail);
  // Both directions are authored/exported by Blender. The browser does not reverse or tween frames.
  forward.src = url(metadata.animation.forward);
  reverse.src = url(metadata.animation.reverse);
  await Promise.all([image.decode(), detail.decode()]);
  fridge.disabled = false;
} catch (error) {
  console.error(error);
  hint.textContent = 'The room could not finish loading. Please refresh to try again.';
  status.textContent = hint.textContent;
}
