from pathlib import Path

p = Path('src/editor.js')
s = p.read_text(encoding='utf-8')

# Renderer / lighting compatibility
s = s.replace(
    "renderer.shadowMap.type = THREE.PCFSoftShadowMap;\nrenderer.toneMapping = THREE.NoToneMapping;",
    "renderer.shadowMap.type = THREE.PCFSoftShadowMap;\nrenderer.toneMapping = THREE.NoToneMapping;\nrenderer.outputColorSpace = THREE.SRGBColorSpace;",
    1,
)

s = s.replace(
    "const ambient = new THREE.AmbientLight(0xffffff, 0.62);",
    "const ambient = new THREE.AmbientLight(0xffffff, 1.0);",
    1,
)
s = s.replace(
    "const hemi = new THREE.HemisphereLight(0xcfe4ff, 0x3b3128, 1.25);",
    "const hemi = new THREE.HemisphereLight(0xdbeaff, 0x4a4138, 1.45);",
    1,
)
s = s.replace(
    "const sun = new THREE.DirectionalLight(0xfff1da, 2.05);",
    "const sun = new THREE.DirectionalLight(0xfff1da, 2.8);",
    1,
)
s = s.replace(
    "sun.position.set(10, 18, 8);",
    "sun.position.set(12, 20, 10);",
    1,
)

# Primitive material: fully opaque, brighter and compatible
old = """function material(color = 0x8ea6bd) {
  const base = new THREE.Color(color);
  return new THREE.MeshPhongMaterial({
    color: base,
    emissive: base.clone().multiplyScalar(0.12),
    shininess: 38,
    specular: new THREE.Color(0x333333),
    side: THREE.DoubleSide
  });
}"""
new = """function material(color = 0x8ea6bd) {
  const base = new THREE.Color(color);
  return new THREE.MeshPhongMaterial({
    color: base,
    emissive: base.clone().multiplyScalar(0.07),
    shininess: 44,
    specular: new THREE.Color(0x444444),
    side: THREE.FrontSide,
    transparent: false,
    opacity: 1,
    depthWrite: true,
    depthTest: true
  });
}"""
if old not in s:
    raise SystemExit('V12 material anchor missing')
s = s.replace(old, new, 1)

# Make imported PBR materials compatible with older WebView while keeping maps/colors.
old = """function cloneMaterials(root) {
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    if (Array.isArray(o.material)) o.material = o.material.map(m => m.clone());
    else o.material = o.material.clone();
    o.castShadow = true;
    o.receiveShadow = true;
  });
}"""
new = """function cloneMaterials(root) {
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    if (Array.isArray(o.material)) o.material = o.material.map(m => m.clone());
    else o.material = o.material.clone();
    o.castShadow = true;
    o.receiveShadow = true;
  });
}

function compatibleImportedMaterial(oldMat) {
  if (!oldMat) return material(0xb8bec6);
  if (oldMat.isMeshPhongMaterial || oldMat.isMeshBasicMaterial || oldMat.isMeshLambertMaterial) {
    const c = oldMat.clone();
    c.depthTest = true;
    c.depthWrite = c.transparent ? c.opacity >= 0.98 : true;
    c.needsUpdate = true;
    return c;
  }
  const baseColor = oldMat.color ? oldMat.color.clone() : new THREE.Color(0xffffff);
  if (oldMat.map && baseColor.getHex() === 0x000000) baseColor.set(0xffffff);
  const alpha = Number.isFinite(oldMat.opacity) ? oldMat.opacity : 1;
  const actuallyTransparent = !!oldMat.transparent && alpha < 0.98;
  const m = new THREE.MeshPhongMaterial({
    color: baseColor,
    map: oldMat.map || null,
    emissive: oldMat.emissive ? oldMat.emissive.clone().multiplyScalar(0.55) : baseColor.clone().multiplyScalar(0.035),
    emissiveMap: oldMat.emissiveMap || null,
    normalMap: oldMat.normalMap || null,
    alphaMap: oldMat.alphaMap || null,
    aoMap: oldMat.aoMap || null,
    specularMap: oldMat.specularMap || null,
    vertexColors: !!oldMat.vertexColors,
    transparent: actuallyTransparent,
    opacity: actuallyTransparent ? alpha : 1,
    alphaTest: oldMat.alphaTest || 0,
    side: oldMat.side !== undefined ? oldMat.side : THREE.FrontSide,
    shininess: 36,
    specular: new THREE.Color(0x3f3f3f),
    depthTest: true,
    depthWrite: !actuallyTransparent
  });
  if (m.map) {
    m.map.colorSpace = THREE.SRGBColorSpace;
    m.map.needsUpdate = true;
  }
  m.needsUpdate = true;
  return m;
}

function makeImportedMaterialsCompatible(root) {
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    const src = Array.isArray(o.material) ? o.material : [o.material];
    const converted = src.map(compatibleImportedMaterial);
    o.material = Array.isArray(o.material) ? converted : converted[0];
    o.castShadow = true;
    o.receiveShadow = true;
  });
}"""
if old not in s:
    raise SystemExit('V12 clone anchor missing')
s = s.replace(old, new, 1)

# Sun gizmo visible like a light object in DCC tools.
anchor = "scene.add(sun);\n"
insert = """scene.add(sun);

const sunGizmo = new THREE.Group();
sunGizmo.name = 'Sun';
const sunCore = new THREE.Mesh(
  new THREE.SphereGeometry(0.28, 16, 12),
  new THREE.MeshBasicMaterial({ color: 0xffd45a, depthTest: false })
);
sunCore.renderOrder = 50;
sunGizmo.add(sunCore);
for (let i = 0; i < 8; i++) {
  const a = (i / 8) * Math.PI * 2;
  const g = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(Math.cos(a) * 0.38, Math.sin(a) * 0.38, 0),
    new THREE.Vector3(Math.cos(a) * 0.62, Math.sin(a) * 0.62, 0)
  ]);
  const ray = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0xffd45a, depthTest: false }));
  ray.renderOrder = 50;
  sunGizmo.add(ray);
}
sunGizmo.position.copy(sun.position);
sunGizmo.scale.setScalar(1.6);
scene.add(sunGizmo);
"""
if anchor not in s:
    raise SystemExit('V12 sun anchor missing')
s = s.replace(anchor, insert, 1)

# Import conversion before markRoot
old = """    const root = gltf.scene;
    root.name = f.name.replace(/\\.(glb|gltf)$/i, '') || 'GLB';
    markRoot(root, 'GLB');"""
new = """    const root = gltf.scene;
    root.name = f.name.replace(/\\.(glb|gltf)$/i, '') || 'GLB';
    makeImportedMaterialsCompatible(root);
    markRoot(root, 'GLB');"""
if old not in s:
    raise SystemExit('V12 import anchor missing')
s = s.replace(old, new, 1)

# Add viewport shading/grid/light toggles.
anchor = "document.getElementById('backgroundInput').addEventListener('input', e => { scene.background.set(e.target.value); });\n"
extra = """document.getElementById('backgroundInput').addEventListener('input', e => { scene.background.set(e.target.value); });

let shadingMode = 'material';
function applyShadingToRoot(root) {
  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    mats.forEach(m => {
      if (m.userData.baseMap === undefined) m.userData.baseMap = m.map || null;
      if (shadingMode === 'wire') {
        m.wireframe = true;
      } else {
        m.wireframe = false;
        if (shadingMode === 'material' && m.userData.baseMap) m.map = m.userData.baseMap;
        if (shadingMode === 'solid' && m.userData.baseMap) m.map = null;
      }
      m.needsUpdate = true;
    });
  });
}
function setShadingMode(mode) {
  shadingMode = mode;
  editable.forEach(applyShadingToRoot);
  document.querySelectorAll('[data-shading]').forEach(b => b.classList.toggle('active', b.dataset.shading === mode));
}

document.querySelectorAll('[data-shading]').forEach(b => b.onclick = () => setShadingMode(b.dataset.shading));
document.getElementById('gridBtn').onclick = () => {
  const visible = !(fineGrid.visible && coarseGrid.visible);
  fineGrid.visible = visible;
  coarseGrid.visible = visible;
  document.getElementById('gridBtn').classList.toggle('active', visible);
};
document.getElementById('sunVisibleBtn').onclick = () => {
  const visible = !sun.visible;
  sun.visible = visible;
  sunGizmo.visible = visible;
  document.getElementById('sunVisibleBtn').classList.toggle('active', visible);
};
document.getElementById('shadowsBtn').onclick = () => {
  renderer.shadowMap.enabled = !renderer.shadowMap.enabled;
  renderer.shadowMap.needsUpdate = true;
  document.getElementById('shadowsBtn').classList.toggle('active', renderer.shadowMap.enabled);
};
"""
if anchor not in s:
    raise SystemExit('V12 UI anchor missing')
s = s.replace(anchor, extra, 1)

# Newly created/imported objects obey current shading mode.
old = """  editable.push(root);
  scene.add(root);
  rebuildOutliner();
  selectObject(root);"""
new = """  editable.push(root);
  scene.add(root);
  if (typeof applyShadingToRoot === 'function') applyShadingToRoot(root);
  rebuildOutliner();
  selectObject(root);"""
if old not in s:
    raise SystemExit('V12 markRoot anchor missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Applied V12 lighting/import compatibility + viewport tools')
