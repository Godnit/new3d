from pathlib import Path
import re

p = Path('src/editor.js')
s = p.read_text(encoding='utf-8')

pattern = re.compile(r"function compatibleImportedMaterial\(oldMat\) \{.*?\n\}\n\nfunction makeImportedMaterialsCompatible", re.S)
replacement = """function compatibleImportedMaterial(oldMat) {
  if (!oldMat) return new THREE.MeshLambertMaterial({ color: 0xb8bec6, side: THREE.DoubleSide });
  const baseColor = oldMat.color ? oldMat.color.clone() : new THREE.Color(0xffffff);
  const hasMap = !!oldMat.map;
  if (hasMap && (baseColor.r + baseColor.g + baseColor.b) < 0.04) baseColor.set(0xffffff);
  if (oldMat.vertexColors && !hasMap && (baseColor.r + baseColor.g + baseColor.b) < 0.04) baseColor.set(0xffffff);
  const alpha = Number.isFinite(oldMat.opacity) ? oldMat.opacity : 1;
  const actuallyTransparent = !!oldMat.transparent && alpha < 0.98;
  const m = new THREE.MeshLambertMaterial({
    color: baseColor,
    map: oldMat.map || null,
    emissive: oldMat.emissive ? oldMat.emissive.clone().multiplyScalar(0.22) : new THREE.Color(0x000000),
    emissiveMap: oldMat.emissiveMap || null,
    alphaMap: oldMat.alphaMap || null,
    aoMap: oldMat.aoMap || null,
    vertexColors: !!oldMat.vertexColors,
    transparent: actuallyTransparent,
    opacity: actuallyTransparent ? alpha : 1,
    alphaTest: oldMat.alphaTest || 0,
    side: oldMat.side !== undefined ? oldMat.side : THREE.DoubleSide,
    depthTest: true,
    depthWrite: !actuallyTransparent
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
    raise SystemExit('V14 imported material anchor missing')
s = s2

s = s.replace("ambient.intensity = 0.45; hemi.intensity = 0.75; sun.intensity = 4.0; fillLight.intensity = 1.8; rimLight.intensity = 1.15;",
              "ambient.intensity = 0.24; hemi.intensity = 0.42; sun.intensity = 4.8; fillLight.intensity = 0.55; rimLight.intensity = 0.85;", 1)
s = s.replace("ambient.intensity = 0.22; hemi.intensity = 0.38; sun.intensity = 5.2; fillLight.intensity = 0.65; rimLight.intensity = 0.75;",
              "ambient.intensity = 0.15; hemi.intensity = 0.28; sun.intensity = 5.6; fillLight.intensity = 0.35; rimLight.intensity = 0.65;", 1)

anchor = "let sunAzimuth = 35;\nlet sunElevation = 48;\nfunction updateSunRig() {"
insert = """let sunAzimuth = 35;
let sunElevation = 48;
let cachedShadowRange = 30;
let shadowBoundsFrame = 0;
function sceneShadowRange() {
  const box = new THREE.Box3();
  let has = false;
  editable.forEach(o => {
    if (!o.visible) return;
    const b = new THREE.Box3().setFromObject(o);
    if (b.isEmpty()) return;
    if (!has) { box.copy(b); has = true; } else box.union(b);
  });
  if (!has) return 30;
  const size = box.getSize(new THREE.Vector3());
  const r = Math.max(size.x, size.y, size.z, 2) * 0.75;
  return THREE.MathUtils.clamp(r, 18, 3000);
}
function updateShadowFrustum(force = false) {
  shadowBoundsFrame++;
  if (!force && shadowBoundsFrame % 20 !== 0) return;
  cachedShadowRange = sceneShadowRange();
  const c = sun.shadow.camera;
  c.left = -cachedShadowRange; c.right = cachedShadowRange;
  c.top = cachedShadowRange; c.bottom = -cachedShadowRange;
  c.near = 0.1; c.far = cachedShadowRange * 5.0;
  c.updateProjectionMatrix();
  sun.shadow.needsUpdate = true;
}
function updateSunRig() {"""
if anchor not in s:
    raise SystemExit('V14 sun rig anchor missing')
s = s.replace(anchor, insert, 1)

old = """  sun.target.position.copy(orbit.target);
  sun.position.copy(orbit.target).addScaledVector(dir, 45);
  sunGizmo.position.copy(orbit.target).addScaledVector(dir, 6.2);
  fillLight.position.copy(camera.position);"""
new = """  updateShadowFrustum(false);
  sun.target.position.copy(orbit.target);
  sun.position.copy(orbit.target).addScaledVector(dir, Math.max(45, cachedShadowRange * 2.2));
  sunGizmo.position.copy(orbit.target).addScaledVector(dir, Math.min(8.0, Math.max(4.5, cachedShadowRange * 0.18)));
  fillLight.position.copy(camera.position);"""
if old not in s:
    raise SystemExit('V14 sun update anchor missing')
s = s.replace(old, new, 1)

s = s.replace("sun.shadow.mapSize.set(1024, 1024);", "sun.shadow.mapSize.set(1536, 1536);", 1)

pattern = re.compile(r"function duplicateSelected\(\) \{.*?\n\}", re.S)
replacement = """function duplicateSelected() {
  if (!selected) return;
  const source = selected;
  const b = objectBounds(source);
  const size = b.getSize(new THREE.Vector3());
  const offsetDistance = Math.max(size.x, size.y, size.z, 1) * 0.72;
  const cameraRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  cameraRight.y = 0;
  if (cameraRight.lengthSq() < 0.001) cameraRight.set(1, 0, 0);
  cameraRight.normalize();
  const c = source.clone(true);
  c.position.copy(source.position).addScaledVector(cameraRight, offsetDistance);
  c.name = (source.name || 'Object') + ' Copy';
  c.userData = { ...source.userData, locked: false };
  cloneMaterials(c);
  markRoot(c, source.userData.kind || 'Object');
  selectObject(c);
  updateShadowFrustum(true);
}"""
s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('V14 duplicate function anchor missing')
s = s2

old = "applyLightPreset('studio');\n"
new = "applyLightPreset('studio');\nrenderer.shadowMap.enabled = true;\nupdateShadowFrustum(true);\n"
if old not in s:
    raise SystemExit('V14 startup anchor missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Applied V14 lit import materials + dynamic shadows + visible duplicate')
