const scene = document.querySelector('#scene');
const image = document.querySelector('#room-image');
const detail = document.querySelector('#detail-image');
const fridge = document.querySelector('#fridge');
const back = document.querySelector('#back');
const hint = document.querySelector('#hint');
const status = document.querySelector('#status');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let metadata;
let view = 'room';
let transitionTimer;
let detailLoaded = false;
let transitionFinished = false;

function revealDetail() {
  if (view === 'fridge' && detailLoaded && transitionFinished) detail.classList.add('ready');
}

function zoomIn() {
  if (!metadata || view !== 'room') return;
  view = 'fridge';
  transitionFinished = false;
  const { center: [x, y], zoom } = metadata.fridge;
  image.style.transform = `translate(${(0.5 - x) * zoom * 100}%, ${(0.5 - y) * zoom * 100}%) scale(${zoom})`;
  scene.dataset.view = 'fridge';
  fridge.hidden = true;
  hint.hidden = true;
  back.hidden = false;
  back.focus({ preventScroll: true });
  detail.setAttribute('aria-hidden', 'false');
  image.setAttribute('aria-hidden', 'true');
  status.textContent = 'Zoomed in on the fridge. Use Back to room or press Escape to return.';
  clearTimeout(transitionTimer);
  transitionTimer = setTimeout(() => { transitionFinished = true; revealDetail(); }, reducedMotion.matches ? 0 : 1400);
}

function zoomOut() {
  if (view !== 'fridge') return;
  view = 'room';
  clearTimeout(transitionTimer);
  transitionFinished = false;
  detail.classList.remove('ready');
  scene.dataset.view = 'room';
  image.style.transform = 'none';
  fridge.hidden = false;
  back.hidden = true;
  hint.hidden = false;
  detail.setAttribute('aria-hidden', 'true');
  image.setAttribute('aria-hidden', 'false');
  fridge.focus({ preventScroll: true });
  status.textContent = 'Returned to the room.';
}

fridge.addEventListener('click', zoomIn);
back.addEventListener('click', zoomOut);
window.addEventListener('keydown', event => {
  if (event.key === 'Escape' && view === 'fridge') { event.preventDefault(); zoomOut(); }
});

try {
  const response = await fetch(new URL('./assets/scene.json', import.meta.url));
  if (!response.ok) throw new Error(`Scene metadata: ${response.status}`);
  metadata = await response.json();
  const { bounds: [x, y, w, h] } = metadata.fridge;
  if (![x, y, w, h, metadata.fridge.zoom].every(Number.isFinite) || w <= 0 || h <= 0) throw new Error('Invalid fridge bounds');
  Object.assign(fridge.style, { left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%` });
  fridge.disabled = false;
  detail.addEventListener('load', async () => {
    try { await detail.decode(); } catch { /* The loaded image remains usable. */ }
    detailLoaded = true;
    revealDetail();
  }, { once: true });
  // If this optional detailed image fails, the main render still provides the zoom.
  detail.addEventListener('error', () => { detailLoaded = false; }, { once: true });
  detail.src = new URL(`./${metadata.detail}`, import.meta.url).href;
} catch (error) {
  console.error(error);
  hint.textContent = 'The room could not finish loading. Please refresh to try again.';
  status.textContent = hint.textContent;
}
