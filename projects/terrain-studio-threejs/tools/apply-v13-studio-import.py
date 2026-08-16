from pathlib import Path
import re

p = Path('src/editor.js')
s = p.read_text(encoding='utf-8')

# Stronger, more directional studio lighting instead of flat ambient lighting.
s = s.replace("const ambient = new THREE.AmbientLight(0xffffff, 1.0);", "const ambient = new THREE.AmbientLight(0xffffff, 0.45);", 1)
s = s.replace("const hemi = new THREE.HemisphereLight(0xdbeaff, 0x4a4138, 1.45);", "const hemi = new THREE.HemisphereLight(0xdbeaff, 0x4a4138, 0.75);", 1)
s = s.replace("const sun = new THREE.DirectionalLight(0xfff1da, 2.8);", "const sun = new THREE.DirectionalLight(0xfff1da, 4.0);", 1)
s = s.replace("sun.position.set(12, 20, 10);", "sun.position.set(18, 28, 14);", 1)

# Improve directional shadow definition.
shadow_anchor = "sun.shadow.camera.near = 0.1; sun.shadow.camera.far = 150;"
shadow_new = "sun.shadow.camera.near = 0.1; sun.shadow.camera.far = 180;\nsun.shadow.bias = -0.00035;\nsun.shadow.normalBias = 0.035;"
if shadow_anchor not in s:
    raise SystemExit('V13 shadow anchor missing')
s = s.replace(shadow_anchor, shadow_new, 1)

# Keep the light icon near the active viewport target rather than far outside view.
s = s.replace("sunGizmo.position.copy(sun.position);\nsunGizmo.scale.setScalar(1.6);", "sunGizmo.position.set(4, 6, 3);\nsunGizmo.scale.setScalar(0.8);", 1)

# Studio fill + rim lights. These make form and volume visible even on older WebView GPUs.
anchor = "scene.add(sunGizmo);\n"
insert = """scene.add(sunGizmo);

const fillLight = new THREE.PointLight(0xe8f2ff, 1.8, 0, 1.4);
scene.add(fillLight);
const rimLight = new THREE.DirectionalLight(0x9fc8ff, 1.15);
rimLight.castShadow = false;
scene.add(rimLight);
scene.add(rimLight.target);
scene.add(sun.target);

let sunAzimuth = 35;
let sunElevation = 48;
function updateSunRig() {
  const az = THREE.MathUtils.degToRad(sunAzimuth);
  const el = THREE.MathUtils.degToRad(sunElevation);
  const c = Math.cos(el);
  const dir = new THREE.Vector3(c * Math.cos(az), Math.sin(el), c * Math.sin(az)).normalize();
  sun.target.position.copy(orbit.target);
  sun.position.copy(orbit.target).addScaledVector(dir, 45);
  sunGizmo.position.copy(orbit.target).addScaledVector(dir, 6.2);
  fillLight.position.copy(camera.position);
  rimLight.target.position.copy(orbit.target);
  rimLight.position.copy(orbit.target).addScaledVector(dir, -28).add(new THREE.Vector3(0, 10, 0));
}
"""
if anchor not in s:
    raise SystemExit('V13 light rig anchor missing')
s = s.replace(anchor, insert, 1)

# Imported models: use an unlit compatibility material so textures/colors cannot turn black
# merely because the old WebView has trouble with a PBR lighting shader.
pattern = re.compile(r"function compatibleImportedMaterial\(oldMat\) \{.*?\n\}\n\nfunction makeImportedMaterialsCompatible", re.S)
replacement = """function compatibleImportedMaterial(oldMat) {
  if (!oldMat) return new THREE.MeshBasicMaterial({ color: 0xb8bec6, toneMapped: false });
  const baseColor = oldMat.color ? oldMat.color.clone() : new THREE.Color(0xffffff);
  const hasMap = !!oldMat.map;
  if (hasMap && (baseColor.r + baseColor.g + baseColor.b) < 0.04) baseColor.set(0xffffff);
  if (oldMat.vertexColors && !hasMap && (baseColor.r + baseColor.g + baseColor.b) < 0.04) baseColor.set(0xffffff);
  const alpha = Number.isFinite(oldMat.opacity) ? oldMat.opacity : 1;
  const actuallyTransparent = !!oldMat.transparent && alpha < 0.98;
  const m = new THREE.MeshBasicMaterial({
    color: baseColor,
    map: oldMat.map || null,
    alphaMap: oldMat.alphaMap || null,
    vertexColors: !!oldMat.vertexColors,
    transparent: actuallyTransparent,
    opacity: actuallyTransparent ? alpha : 1,
    alphaTest: oldMat.alphaTest || 0,
    side: oldMat.side !== undefined ? oldMat.side : THREE.FrontSide,
    depthTest: true,
    depthWrite: !actuallyTransparent,
    toneMapped: false
  });
  if (m.map) {
    m.map.colorSpace = THREE.SRGBColorSpace;
    m.map.flipY = false;
    m.map.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
    m.map.needsUpdate = true;
  }
  m.needsUpdate = true;
  return m;
}

function makeImportedMaterialsCompatible"""
s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('V13 imported material function anchor missing')
s = s2

# Add import statistics so a screenshot can tell us whether textures were actually loaded.
old = """function makeImportedMaterialsCompatible(root) {
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    const src = Array.isArray(o.material) ? o.material : [o.material];
    const converted = src.map(compatibleImportedMaterial);
    o.material = Array.isArray(o.material) ? converted : converted[0];
    o.castShadow = true;
    o.receiveShadow = true;
  });
}"""
new = """function makeImportedMaterialsCompatible(root) {
  let meshCount = 0, materialCount = 0, textureCount = 0;
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    meshCount++;
    const src = Array.isArray(o.material) ? o.material : [o.material];
    materialCount += src.length;
    textureCount += src.filter(m => m && m.map).length;
    const converted = src.map(compatibleImportedMaterial);
    o.material = Array.isArray(o.material) ? converted : converted[0];
    o.castShadow = true;
    o.receiveShadow = true;
  });
  const status = document.getElementById('importStatus');
  if (status) status.textContent = `Meshes ${meshCount} • Materials ${materialCount} • Textures ${textureCount}`;
}"""
if old not in s:
    raise SystemExit('V13 import stats anchor missing')
s = s.replace(old, new, 1)

# Robust GLTF import: support GLB and multi-file .gltf + .bin + texture images selected together.
file_pattern = re.compile(r"const loader = new GLTFLoader\(\);\nconst fileInput = document.getElementById\('fileInput'\);\nfileInput.addEventListener\('change', \(\) => \{.*?\n\}\);", re.S)
file_replacement = """const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', () => {
  const files = Array.from(fileInput.files || []);
  if (!files.length) return;
  const main = files.find(f => /\\.(glb|gltf)$/i.test(f.name));
  if (!main) { fileInput.value = ''; return; }

  const urls = new Map();
  files.forEach(f => urls.set(f.name, URL.createObjectURL(f)));
  const manager = new THREE.LoadingManager();
  manager.setURLModifier(url => {
    const clean = decodeURIComponent(url.split('?')[0].split('#')[0].split('/').pop());
    return urls.get(clean) || url;
  });
  const localLoader = new GLTFLoader(manager);
  const status = document.getElementById('importStatus');
  if (status) status.textContent = 'جاري تحميل المجسم...';

  const cleanup = () => urls.forEach(u => URL.revokeObjectURL(u));
  localLoader.load(urls.get(main.name), gltf => {
    const root = gltf.scene;
    root.name = main.name.replace(/\\.(glb|gltf)$/i, '') || 'GLB';
    makeImportedMaterialsCompatible(root);
    markRoot(root, 'GLB');
    focusSelected();
    cleanup();
  }, undefined, err => {
    console.error(err);
    if (status) status.textContent = 'فشل تحميل بعض ملفات المجسم أو الخامات';
    cleanup();
  });
  fileInput.value = '';
});"""
s2, n = file_pattern.subn(file_replacement, s, count=1)
if n != 1:
    raise SystemExit('V13 file input handler anchor missing')
s = s2

# Lighting presets + sun direction controls.
ui_anchor = "document.getElementById('sunInput').addEventListener('input', e => { sun.intensity = parseFloat(e.target.value); });\n"
ui_insert = """document.getElementById('sunInput').addEventListener('input', e => { sun.intensity = parseFloat(e.target.value); });
const azimuthInput = document.getElementById('sunAzimuthInput');
const elevationInput = document.getElementById('sunElevationInput');
if (azimuthInput) azimuthInput.addEventListener('input', e => { sunAzimuth = parseFloat(e.target.value); });
if (elevationInput) elevationInput.addEventListener('input', e => { sunElevation = parseFloat(e.target.value); });
function applyLightPreset(name) {
  if (name === 'studio') {
    ambient.intensity = 0.45; hemi.intensity = 0.75; sun.intensity = 4.0; fillLight.intensity = 1.8; rimLight.intensity = 1.15;
    sunAzimuth = 35; sunElevation = 48;
  } else if (name === 'sunny') {
    ambient.intensity = 0.22; hemi.intensity = 0.38; sun.intensity = 5.2; fillLight.intensity = 0.65; rimLight.intensity = 0.75;
    sunAzimuth = 28; sunElevation = 38;
  } else if (name === 'soft') {
    ambient.intensity = 0.72; hemi.intensity = 1.05; sun.intensity = 2.4; fillLight.intensity = 2.2; rimLight.intensity = 0.55;
    sunAzimuth = 55; sunElevation = 58;
  }
  document.getElementById('ambientInput').value = ambient.intensity;
  document.getElementById('sunInput').value = sun.intensity;
  if (azimuthInput) azimuthInput.value = sunAzimuth;
  if (elevationInput) elevationInput.value = sunElevation;
  document.querySelectorAll('[data-lightpreset]').forEach(b => b.classList.toggle('active', b.dataset.lightpreset === name));
}
document.querySelectorAll('[data-lightpreset]').forEach(b => b.onclick = () => applyLightPreset(b.dataset.lightpreset));
applyLightPreset('studio');
"""
if ui_anchor not in s:
    raise SystemExit('V13 light UI anchor missing')
s = s.replace(ui_anchor, ui_insert, 1)

# Keep the studio rig following the camera/target each frame.
animate_anchor = """function animate() {
  requestAnimationFrame(animate);
  orbit.update();
  renderer.render(scene, camera);
}"""
animate_new = """function animate() {
  requestAnimationFrame(animate);
  orbit.update();
  updateSunRig();
  renderer.render(scene, camera);
}"""
if animate_anchor not in s:
    raise SystemExit('V13 animate anchor missing')
s = s.replace(animate_anchor, animate_new, 1)

p.write_text(s, encoding='utf-8')
print('Applied V13 studio lighting + robust GLTF import')
