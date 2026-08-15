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
renderer.domElement.style.touchAction = 'none';
host.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x25282d);

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
transform.setSize(0.9);
scene.add(transform);
transform.addEventListener('dragging-changed', e => { orbit.enabled = !e.value; });
transform.addEventListener('objectChange', () => { updateSelectionUi(); updateBox(); });

const hemi = new THREE.HemisphereLight(0xbfd8ff, 0x26211c, 1.35);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff0d4, 2.15);
sun.position.set(10, 18, 8);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -30; sun.shadow.camera.right = 30;
sun.shadow.camera.top = 30; sun.shadow.camera.bottom = -30;
sun.shadow.camera.near = 0.1; sun.shadow.camera.far = 100;
scene.add(sun);

// Blender-like fixed world grid: fine near origin plus a large coarse grid.
const fineGrid = new THREE.GridHelper(200, 200, 0x4a4f56, 0x34383e);
fineGrid.position.y = -0.002;
scene.add(fineGrid);
const coarseGrid = new THREE.GridHelper(4000, 80, 0x555b63, 0x2d3035);
coarseGrid.position.y = -0.006;
scene.add(coarseGrid);
const axes = new THREE.AxesHelper(1000);
axes.material.depthTest = false;
axes.renderOrder = 1;
scene.add(axes);

const editable = [];
let selected = null;
let box = new THREE.BoxHelper(undefined, 0xffa62b);
box.visible = false;
box.material.depthTest = false;
box.renderOrder = 20;
scene.add(box);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let downX = 0, downY = 0, clickCandidate = false, pressedOnGizmo = false;

function material(color = 0x9aa0a6) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.72, metalness: 0.02, side: THREE.DoubleSide });
}
function markRoot(root, type) {
  root.userData.editorObject = true;
  root.userData.kind = type;
  root.name = root.name || type;
  root.traverse(o => {
    o.userData.editorRoot = root;
    if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
  });
  editable.push(root);
  scene.add(root);
  rebuildOutliner();
  selectObject(root);
}
function addPrimitive(type) {
  let geometry;
  let color = 0xa8adb3;
  switch (type) {
    case 'Cube': geometry = new THREE.BoxGeometry(2, 2, 2); break;
    case 'Sphere': geometry = new THREE.SphereGeometry(1.15, 32, 20); break;
    case 'Cylinder': geometry = new THREE.CylinderGeometry(1, 1, 2.5, 32); break;
    case 'Cone': geometry = new THREE.ConeGeometry(1.2, 2.6, 32); color = 0xc58a45; break;
    case 'Torus': geometry = new THREE.TorusGeometry(1.15, 0.35, 16, 48); break;
    case 'Plane': geometry = new THREE.PlaneGeometry(10, 10, 12, 12); color = 0x66766b; break;
    default: geometry = new THREE.BoxGeometry(2, 2, 2);
  }
  const mesh = new THREE.Mesh(geometry, material(color));
  if (type === 'Plane') mesh.rotation.x = -Math.PI / 2;
  else mesh.position.y = type === 'Cone' ? 1.3 : (type === 'Cylinder' ? 1.25 : 1.05);
  markRoot(mesh, type);
}

function selectObject(obj) {
  selected = obj || null;
  if (selected) {
    transform.attach(selected);
    box.setFromObject(selected);
    box.visible = true;
  } else {
    transform.detach();
    box.visible = false;
  }
  updateSelectionUi();
  rebuildOutliner();
}
function updateBox() {
  if (!selected) { box.visible = false; return; }
  box.setFromObject(selected); box.visible = true;
}
function pickAt(clientX, clientY) {
  const r = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - r.left) / r.width) * 2 - 1;
  pointer.y = -((clientY - r.top) / r.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(editable, true);
  if (!hits.length) return null;
  let o = hits[0].object;
  return o.userData.editorRoot || null;
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
  if (pressedOnGizmo || transform.dragging) { pressedOnGizmo = false; clickCandidate = false; return; }
  if (!clickCandidate) return;
  const hit = pickAt(e.clientX, e.clientY);
  selectObject(hit);
  clickCandidate = false;
}, false);

function setMode(mode) {
  if (!['translate','rotate','scale'].includes(mode)) return;
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
  markRoot(c, selected.userData.kind || 'Object');
}
function deleteSelected() {
  if (!selected) return;
  const i = editable.indexOf(selected);
  if (i >= 0) editable.splice(i, 1);
  scene.remove(selected);
  selectObject(null);
}
function newScene() {
  selectObject(null);
  while (editable.length) scene.remove(editable.pop());
  rebuildOutliner();
}
function focusSelected() {
  if (!selected) return;
  const b = new THREE.Box3().setFromObject(selected);
  const s = b.getSize(new THREE.Vector3());
  const c = b.getCenter(new THREE.Vector3());
  const radius = Math.max(s.x, s.y, s.z, 0.2);
  orbit.target.copy(c);
  const dir = new THREE.Vector3().subVectors(camera.position, orbit.target).normalize();
  camera.position.copy(c).addScaledVector(dir, radius * 3.2);
  orbit.update();
}

const fields = {};
['px','py','pz','rx','ry','rz','sx','sy','sz'].forEach(id => fields[id] = document.getElementById(id));
function updateSelectionUi() {
  const label = document.getElementById('selectionName');
  const panel = document.getElementById('transformPanel');
  if (!selected) { label.textContent = 'لا يوجد تحديد'; panel.classList.add('disabled'); return; }
  panel.classList.remove('disabled');
  label.textContent = selected.name || selected.userData.kind || 'Object';
  fields.px.value = fmt(selected.position.x); fields.py.value = fmt(selected.position.y); fields.pz.value = fmt(selected.position.z);
  fields.rx.value = fmt(THREE.MathUtils.radToDeg(selected.rotation.x)); fields.ry.value = fmt(THREE.MathUtils.radToDeg(selected.rotation.y)); fields.rz.value = fmt(THREE.MathUtils.radToDeg(selected.rotation.z));
  fields.sx.value = fmt(selected.scale.x); fields.sy.value = fmt(selected.scale.y); fields.sz.value = fmt(selected.scale.z);
}
function fmt(v) { return Number.isFinite(v) ? (+v.toFixed(3)).toString() : '0'; }
function read(id, fallback) { const n = parseFloat(fields[id].value); return Number.isFinite(n) ? n : fallback; }
function applyFields() {
  if (!selected) return;
  selected.position.set(read('px', selected.position.x), read('py', selected.position.y), read('pz', selected.position.z));
  selected.rotation.set(THREE.MathUtils.degToRad(read('rx',0)), THREE.MathUtils.degToRad(read('ry',0)), THREE.MathUtils.degToRad(read('rz',0)));
  selected.scale.set(read('sx',1), read('sy',1), read('sz',1));
  updateBox();
}
Object.values(fields).forEach(i => i.addEventListener('change', applyFields));

function rebuildOutliner() {
  const list = document.getElementById('outlinerList');
  list.innerHTML = '';
  editable.forEach((o, i) => {
    const b = document.createElement('button');
    b.className = 'outlinerItem' + (o === selected ? ' active' : '');
    b.textContent = `${i+1}. ${o.name || o.userData.kind || 'Object'}`;
    b.onclick = () => selectObject(o);
    list.appendChild(b);
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
document.getElementById('addBtn').onclick = () => showAddMenu(!document.getElementById('addMenu').classList.contains('open'));
document.querySelectorAll('[data-add]').forEach(b => b.onclick = () => { addPrimitive(b.dataset.add); showAddMenu(false); });
document.getElementById('importBtn').onclick = () => fileInput.click();
document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => setMode(b.dataset.mode));
document.getElementById('spaceBtn').onclick = () => setSpace(transform.space === 'world' ? 'local' : 'world');
document.getElementById('snapBtn').onclick = () => { snapOn = !snapOn; applySnap(); };
document.getElementById('duplicateBtn').onclick = duplicateSelected;
document.getElementById('deleteBtn').onclick = deleteSelected;
document.getElementById('newBtn').onclick = newScene;
document.getElementById('focusBtn').onclick = focusSelected;
document.getElementById('outlinerBtn').onclick = () => document.getElementById('outliner').classList.toggle('open');

function resize() {
  const w = host.clientWidth, h = Math.max(1, host.clientHeight);
  camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false);
}
window.addEventListener('resize', resize);
resize();
setMode('translate');
updateSelectionUi();
rebuildOutliner();

function animate() {
  requestAnimationFrame(animate);
  orbit.update();
  if (selected) box.setFromObject(selected);
  renderer.render(scene, camera);
}
animate();
