import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const host = document.getElementById('viewport');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
renderer.setSize(host.clientWidth, host.clientHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.domElement.style.touchAction = 'none';
host.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x202328);

const camera = new THREE.PerspectiveCamera(50, host.clientWidth / Math.max(1, host.clientHeight), 0.01, 1000000);
camera.position.set(8, 7, 10);

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(0, 0.7, 0);
orbit.enableDamping = true;
orbit.dampingFactor = 0.08;
orbit.minDistance = 0.05;
orbit.maxDistance = 500000;
orbit.screenSpacePanning = true;
orbit.update();

const transform = new TransformControls(camera, renderer.domElement);
transform.setMode('translate');
transform.setSpace('world');
transform.setSize(0.88);
scene.add(transform);
transform.addEventListener('dragging-changed', e => { orbit.enabled = !e.value; });
transform.addEventListener('objectChange', () => {
  updateSelectionUi();
  updateMaterialUi();
});

const ambient = new THREE.AmbientLight(0xffffff, 0.62);
scene.add(ambient);
const hemi = new THREE.HemisphereLight(0xcfe4ff, 0x3b3128, 1.25);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1da, 2.05);
sun.position.set(10, 18, 8);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -40; sun.shadow.camera.right = 40;
sun.shadow.camera.top = 40; sun.shadow.camera.bottom = -40;
sun.shadow.camera.near = 0.1; sun.shadow.camera.far = 150;
scene.add(sun);

const fineGrid = new THREE.GridHelper(120, 120, 0x51565d, 0x34383e);
fineGrid.position.y = -0.002;
fineGrid.material.transparent = true;
fineGrid.material.opacity = 0.78;
scene.add(fineGrid);

const coarseGrid = new THREE.GridHelper(6000, 300, 0x555b63, 0x2d3136);
coarseGrid.position.y = -0.006;
coarseGrid.material.transparent = true;
coarseGrid.material.opacity = 0.52;
scene.add(coarseGrid);

function worldAxis(a, b, color) {
  const g = new THREE.BufferGeometry().setFromPoints([a, b]);
  const m = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.9, depthTest: false });
  const line = new THREE.Line(g, m);
  line.renderOrder = 2;
  scene.add(line);
}
worldAxis(new THREE.Vector3(-3000, 0.004, 0), new THREE.Vector3(3000, 0.004, 0), 0xc94a4a);
worldAxis(new THREE.Vector3(0, 0.004, -3000), new THREE.Vector3(0, 0.004, 3000), 0x4b78d1);

const editable = [];
let selected = null;
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let downX = 0, downY = 0, clickCandidate = false, pressedOnGizmo = false;

const primitiveColors = {
  Cube: 0x4f8fe8,
  Sphere: 0x65c982,
  Cylinder: 0xe3ad57,
  Cone: 0xe97855,
  Torus: 0xa875e8,
  Plane: 0x6f9674,
  Pyramid: 0xd98b55,
  Icosphere: 0x56b8c9
};

function material(color = 0x8ea6bd) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.56, metalness: 0.05, side: THREE.DoubleSide });
}

function cloneMaterials(root) {
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    if (Array.isArray(o.material)) o.material = o.material.map(m => m.clone());
    else o.material = o.material.clone();
    o.castShadow = true;
    o.receiveShadow = true;
  });
}

function markRoot(root, type) {
  root.userData.editorObject = true;
  root.userData.kind = type;
  root.userData.locked = !!root.userData.locked;
  root.name = root.name || type;
  cloneMaterials(root);
  root.traverse(o => { o.userData.editorRoot = root; });
  editable.push(root);
  scene.add(root);
  rebuildOutliner();
  selectObject(root);
}

function addPrimitive(type) {
  let geometry;
  switch (type) {
    case 'Cube': geometry = new THREE.BoxGeometry(2, 2, 2); break;
    case 'Sphere': geometry = new THREE.SphereGeometry(1.15, 32, 20); break;
    case 'Cylinder': geometry = new THREE.CylinderGeometry(1, 1, 2.5, 32); break;
    case 'Cone': geometry = new THREE.ConeGeometry(1.2, 2.6, 32); break;
    case 'Torus': geometry = new THREE.TorusGeometry(1.15, 0.35, 16, 48); break;
    case 'Plane': geometry = new THREE.PlaneGeometry(10, 10, 12, 12); break;
    case 'Pyramid': geometry = new THREE.ConeGeometry(1.35, 2.5, 4); break;
    case 'Icosphere': geometry = new THREE.IcosahedronGeometry(1.2, 2); break;
    default: geometry = new THREE.BoxGeometry(2, 2, 2);
  }
  const mesh = new THREE.Mesh(geometry, material(primitiveColors[type] || 0x8ea6bd));
  if (type === 'Plane') mesh.rotation.x = -Math.PI / 2;
  else if (type === 'Cone' || type === 'Pyramid') mesh.position.y = 1.3;
  else if (type === 'Cylinder') mesh.position.y = 1.25;
  else mesh.position.y = 1.05;
  markRoot(mesh, type);
}

function canTransform(obj) {
  return !!obj && !obj.userData.locked && obj.visible;
}

function selectObject(obj) {
  selected = obj || null;
  transform.detach();
  if (canTransform(selected)) transform.attach(selected);
  updateSelectionUi();
  updateMaterialUi();
  rebuildOutliner();
}

function pickAt(clientX, clientY) {
  const r = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - r.left) / r.width) * 2 - 1;
  pointer.y = -((clientY - r.top) / r.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const candidates = editable.filter(o => o.visible);
  const hits = raycaster.intersectObjects(candidates, true);
  if (!hits.length) return null;
  return hits[0].object.userData.editorRoot || null;
}

renderer.domElement.addEventListener('pointerdown', e => {
  downX = e.clientX; downY = e.clientY;
  pressedOnGizmo = transform.axis !== null;
  clickCandidate = !pressedOnGizmo;
}, false);
renderer.domElement.addEventListener('pointermove', e => {
  if (Math.hypot(e.clientX - downX, e.clientY - downY) > 8) clickCandidate = false;
}, false);
renderer.domElement.addEventListener('pointerup', e => {
  if (pressedOnGizmo || transform.dragging) {
    pressedOnGizmo = false;
    clickCandidate = false;
    return;
  }
  if (!clickCandidate) return;
  selectObject(pickAt(e.clientX, e.clientY));
  clickCandidate = false;
}, false);

function setMode(mode) {
  if (!['translate', 'rotate', 'scale'].includes(mode)) return;
  transform.setMode(mode);
  document.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  document.getElementById('modeName').textContent = mode === 'translate' ? 'تحريك' : mode === 'rotate' ? 'تدوير' : 'حجم';
}

function setSpace(space) {
  transform.setSpace(space);
  document.getElementById('spaceBtn').textContent = space === 'world' ? 'Global' : 'Local';
}

let snapOn = false;
function applySnap() {
  transform.setTranslationSnap(snapOn ? 0.5 : null);
  transform.setRotationSnap(snapOn ? THREE.MathUtils.degToRad(15) : null);
  transform.setScaleSnap(snapOn ? 0.1 : null);
  document.getElementById('snapBtn').classList.toggle('active', snapOn);
}

function duplicateSelected() {
  if (!selected) return;
  const c = selected.clone(true);
  c.position.x += 1;
  c.position.z += 1;
  c.name = (selected.name || 'Object') + ' Copy';
  c.userData.locked = false;
  markRoot(c, selected.userData.kind || 'Object');
}

function deleteSelected() {
  if (!selected) return;
  const doomed = selected;
  const i = editable.indexOf(doomed);
  if (i >= 0) editable.splice(i, 1);
  transform.detach();
  scene.remove(doomed);
  selected = null;
  rebuildOutliner();
  updateSelectionUi();
  updateMaterialUi();
}

function newScene() {
  selectObject(null);
  while (editable.length) scene.remove(editable.pop());
  rebuildOutliner();
}

function objectBounds(obj) { return new THREE.Box3().setFromObject(obj); }

function focusSelected() {
  if (!selected) return;
  const b = objectBounds(selected);
  const s = b.getSize(new THREE.Vector3());
  const c = b.getCenter(new THREE.Vector3());
  const radius = Math.max(s.x, s.y, s.z, 0.2);
  orbit.target.copy(c);
  const dir = new THREE.Vector3().subVectors(camera.position, orbit.target).normalize();
  if (dir.lengthSq() < 0.01) dir.set(1, 0.8, 1).normalize();
  camera.position.copy(c).addScaledVector(dir, radius * 3.2);
  camera.up.set(0, 1, 0);
  orbit.update();
}

function currentViewTarget() {
  if (selected) return objectBounds(selected).getCenter(new THREE.Vector3());
  return orbit.target.clone();
}

function setView(view) {
  const t = currentViewTarget();
  let d = Math.max(camera.position.distanceTo(orbit.target), 8);
  if (selected) {
    const size = objectBounds(selected).getSize(new THREE.Vector3());
    d = Math.max(d, Math.max(size.x, size.y, size.z, 1) * 2.7);
  }
  camera.up.set(0, 1, 0);
  if (view === 'front') camera.position.set(t.x, t.y, t.z + d);
  if (view === 'back') camera.position.set(t.x, t.y, t.z - d);
  if (view === 'right') camera.position.set(t.x + d, t.y, t.z);
  if (view === 'left') camera.position.set(t.x - d, t.y, t.z);
  if (view === 'top') { camera.up.set(0, 0, -1); camera.position.set(t.x, t.y + d, t.z); }
  if (view === 'bottom') { camera.up.set(0, 0, 1); camera.position.set(t.x, t.y - d, t.z); }
  if (view === 'iso') camera.position.copy(t).add(new THREE.Vector3(d, d * 0.78, d).normalize().multiplyScalar(d));
  orbit.target.copy(t);
  camera.lookAt(t);
  orbit.update();
}

const fields = {};
['px', 'py', 'pz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'].forEach(id => { fields[id] = document.getElementById(id); });
function fmt(v) { return Number.isFinite(v) ? (+v.toFixed(3)).toString() : '0'; }
function read(id, fallback) { const n = parseFloat(fields[id].value); return Number.isFinite(n) ? n : fallback; }

function updateSelectionUi() {
  const label = document.getElementById('selectionName');
  const objSection = document.getElementById('objectSection');
  const nameInput = document.getElementById('nameInput');
  if (!selected) {
    label.textContent = 'لا يوجد تحديد';
    objSection.classList.add('disabled');
    nameInput.value = '';
    Object.values(fields).forEach(i => i.disabled = true);
    return;
  }
  objSection.classList.remove('disabled');
  label.textContent = (selected.userData.locked ? '🔒 ' : '') + (selected.name || selected.userData.kind || 'Object');
  nameInput.value = selected.name || '';
  Object.values(fields).forEach(i => i.disabled = !!selected.userData.locked);
  fields.px.value = fmt(selected.position.x); fields.py.value = fmt(selected.position.y); fields.pz.value = fmt(selected.position.z);
  fields.rx.value = fmt(THREE.MathUtils.radToDeg(selected.rotation.x)); fields.ry.value = fmt(THREE.MathUtils.radToDeg(selected.rotation.y)); fields.rz.value = fmt(THREE.MathUtils.radToDeg(selected.rotation.z));
  fields.sx.value = fmt(selected.scale.x); fields.sy.value = fmt(selected.scale.y); fields.sz.value = fmt(selected.scale.z);
}

function applyFields() {
  if (!canTransform(selected)) return;
  selected.position.set(read('px', selected.position.x), read('py', selected.position.y), read('pz', selected.position.z));
  selected.rotation.set(
    THREE.MathUtils.degToRad(read('rx', THREE.MathUtils.radToDeg(selected.rotation.x))),
    THREE.MathUtils.degToRad(read('ry', THREE.MathUtils.radToDeg(selected.rotation.y))),
    THREE.MathUtils.degToRad(read('rz', THREE.MathUtils.radToDeg(selected.rotation.z)))
  );
  selected.scale.set(read('sx', selected.scale.x), read('sy', selected.scale.y), read('sz', selected.scale.z));
}
Object.values(fields).forEach(i => i.addEventListener('change', applyFields));

document.getElementById('nameInput').addEventListener('change', e => {
  if (!selected) return;
  const value = e.target.value.trim();
  if (value) selected.name = value;
  updateSelectionUi();
  rebuildOutliner();
});

function eachMaterial(root, fn) {
  if (!root) return;
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    mats.forEach(m => fn(m));
  });
}
function firstEditableMaterial(root) {
  let found = null;
  if (!root) return null;
  root.traverse(o => {
    if (found || !o.isMesh || !o.material) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    found = mats.find(m => m && m.color) || null;
  });
  return found;
}

const colorPicker = document.getElementById('colorPicker');
const roughnessInput = document.getElementById('roughnessInput');
const metalnessInput = document.getElementById('metalnessInput');
function updateMaterialUi() {
  const section = document.getElementById('materialSection');
  const mat = firstEditableMaterial(selected);
  if (!mat) { section.classList.add('disabled'); return; }
  section.classList.remove('disabled');
  if (mat.color) colorPicker.value = '#' + mat.color.getHexString();
  roughnessInput.value = mat.roughness !== undefined ? mat.roughness : 0.5;
  metalnessInput.value = mat.metalness !== undefined ? mat.metalness : 0;
}
function setSelectedColor(hex) {
  if (!selected) return;
  eachMaterial(selected, m => { if (m.color) m.color.set(hex); if ('needsUpdate' in m) m.needsUpdate = true; });
  updateMaterialUi();
}
colorPicker.addEventListener('input', e => setSelectedColor(e.target.value));
document.querySelectorAll('[data-color]').forEach(b => b.addEventListener('click', () => setSelectedColor(b.dataset.color)));
roughnessInput.addEventListener('input', e => {
  const v = parseFloat(e.target.value);
  eachMaterial(selected, m => { if (m.roughness !== undefined) { m.roughness = v; m.needsUpdate = true; } });
});
metalnessInput.addEventListener('input', e => {
  const v = parseFloat(e.target.value);
  eachMaterial(selected, m => { if (m.metalness !== undefined) { m.metalness = v; m.needsUpdate = true; } });
});

function rebuildOutliner() {
  const list = document.getElementById('outlinerList');
  list.innerHTML = '';
  editable.forEach((o, i) => {
    const row = document.createElement('div');
    row.className = 'outlinerRow' + (o === selected ? ' active' : '');
    const name = document.createElement('button');
    name.className = 'outlinerName';
    name.textContent = `${i + 1}. ${o.name || o.userData.kind || 'Object'}`;
    name.onclick = () => selectObject(o);
    const eye = document.createElement('button');
    eye.className = 'outlinerIcon'; eye.textContent = o.visible ? '👁' : '◌'; eye.title = 'إظهار / إخفاء';
    eye.onclick = e => { e.stopPropagation(); o.visible = !o.visible; if (!o.visible && selected === o) selectObject(null); rebuildOutliner(); };
    const lock = document.createElement('button');
    lock.className = 'outlinerIcon'; lock.textContent = o.userData.locked ? '🔒' : '🔓'; lock.title = 'قفل / فتح';
    lock.onclick = e => { e.stopPropagation(); o.userData.locked = !o.userData.locked; if (selected === o) selectObject(o); else rebuildOutliner(); };
    row.append(name, eye, lock);
    list.appendChild(row);
  });
}

const loader = new GLTFLoader();
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', () => {
  const f = fileInput.files && fileInput.files[0];
  if (!f) return;
  const url = URL.createObjectURL(f);
  loader.load(url, gltf => {
    const root = gltf.scene;
    root.name = f.name.replace(/\.(glb|gltf)$/i, '') || 'GLB';
    markRoot(root, 'GLB');
    focusSelected();
    URL.revokeObjectURL(url);
  }, undefined, err => { console.error(err); URL.revokeObjectURL(url); });
  fileInput.value = '';
});

function showAddMenu(show) { document.getElementById('addMenu').classList.toggle('open', show); }
document.getElementById('addBtn').onclick = () => { const m = document.getElementById('addMenu'); showAddMenu(!m.classList.contains('open')); };
document.querySelectorAll('[data-add]').forEach(b => { b.onclick = () => { addPrimitive(b.dataset.add); showAddMenu(false); }; });
document.getElementById('importBtn').onclick = () => fileInput.click();
document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => setMode(b.dataset.mode));
document.getElementById('spaceBtn').onclick = () => setSpace(transform.space === 'world' ? 'local' : 'world');
document.getElementById('snapBtn').onclick = () => { snapOn = !snapOn; applySnap(); };
document.getElementById('duplicateBtn').onclick = duplicateSelected;
document.getElementById('deleteBtn').onclick = deleteSelected;
document.getElementById('newBtn').onclick = newScene;
document.getElementById('focusBtn').onclick = focusSelected;
document.getElementById('outlinerBtn').onclick = () => document.getElementById('outliner').classList.toggle('open');
document.getElementById('propertiesBtn').onclick = () => document.getElementById('properties').classList.toggle('open');
document.getElementById('propertiesClose').onclick = () => document.getElementById('properties').classList.remove('open');
document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => setView(b.dataset.view));
document.getElementById('ambientInput').addEventListener('input', e => { ambient.intensity = parseFloat(e.target.value); });
document.getElementById('sunInput').addEventListener('input', e => { sun.intensity = parseFloat(e.target.value); });
document.getElementById('backgroundInput').addEventListener('input', e => { scene.background.set(e.target.value); });

function resize() {
  const w = host.clientWidth, h = Math.max(1, host.clientHeight);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h, false);
}
window.addEventListener('resize', resize);
resize();
setMode('translate');
updateSelectionUi();
updateMaterialUi();
rebuildOutliner();

function animate() {
  requestAnimationFrame(animate);
  orbit.update();
  renderer.render(scene, camera);
}
animate();
