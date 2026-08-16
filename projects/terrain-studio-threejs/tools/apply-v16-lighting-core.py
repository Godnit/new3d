from pathlib import Path
import re

p = Path('src/editor.js')
s = p.read_text(encoding='utf-8')

pattern = re.compile(r"function compatibleImportedMaterial\(oldMat\) \{.*?\n\}\n\nfunction makeImportedMaterialsCompatible", re.S)
replacement = """function compatibleImportedMaterial(oldMat) {
  if (!oldMat) {
    const fallback = new THREE.Color(0xb8bec6);
    return new THREE.MeshLambertMaterial({ color: fallback, emissive: fallback.clone().multiplyScalar(0.16), side: THREE.DoubleSide });
  }
  const baseColor = oldMat.color ? oldMat.color.clone() : new THREE.Color(0xffffff);
  const hasMap = !!oldMat.map;
  if (hasMap && (baseColor.r + baseColor.g + baseColor.b) < 0.04) baseColor.set(0xffffff);
  if (oldMat.vertexColors && !hasMap && (baseColor.r + baseColor.g + baseColor.b) < 0.04) baseColor.set(0xffffff);
  const alpha = Number.isFinite(oldMat.opacity) ? oldMat.opacity : 1;
  const actuallyTransparent = !!oldMat.transparent && alpha < 0.98;
  const originalEmissive = oldMat.emissive ? oldMat.emissive.clone() : new THREE.Color(0x000000);
  originalEmissive.add(baseColor.clone().multiplyScalar(0.18));
  const m = new THREE.MeshLambertMaterial({
    color: baseColor,
    map: oldMat.map || null,
    emissive: originalEmissive,
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
if n != 1: raise SystemExit('V16 imported material anchor missing')
s = s2

old = """  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    meshCount++;
    const src = Array.isArray(o.material) ? o.material : [o.material];
    materialCount += src.length;
    textureCount += src.filter(m => m && m.map).length;
    const converted = src.map(compatibleImportedMaterial);
    o.material = Array.isArray(o.material) ? converted : converted[0];
    o.castShadow = true;
    o.receiveShadow = false;
  });"""
new = """  root.traverse(o => {
    if (!o.isMesh || !o.material) return;
    meshCount++;
    if (o.geometry && !o.geometry.getAttribute('normal')) {
      try { o.geometry.computeVertexNormals(); } catch (_) {}
    }
    const src = Array.isArray(o.material) ? o.material : [o.material];
    materialCount += src.length;
    textureCount += src.filter(m => m && m.map).length;
    const converted = src.map(compatibleImportedMaterial);
    o.material = Array.isArray(o.material) ? converted : converted[0];
    o.castShadow = true;
    o.receiveShadow = true;
    o.frustumCulled = true;
  });"""
if old not in s: raise SystemExit('V16 import traversal anchor missing')
s = s.replace(old, new, 1)

s = s.replace("ambient.intensity = 0.12; hemi.intensity = 0.22; sun.intensity = 4.6; fillLight.intensity = 0.16; rimLight.intensity = 0.28;", "ambient.intensity = 0.38; hemi.intensity = 0.48; sun.intensity = 3.15; fillLight.intensity = 0.32; rimLight.intensity = 0.42;", 1)
s = s.replace("ambient.intensity = 0.08; hemi.intensity = 0.16; sun.intensity = 5.4; fillLight.intensity = 0.10; rimLight.intensity = 0.22;", "ambient.intensity = 0.22; hemi.intensity = 0.30; sun.intensity = 4.35; fillLight.intensity = 0.18; rimLight.intensity = 0.28;", 1)
s = s.replace("ambient.intensity = 0.38; hemi.intensity = 0.55; sun.intensity = 2.8; fillLight.intensity = 0.72; rimLight.intensity = 0.34;", "ambient.intensity = 0.62; hemi.intensity = 0.78; sun.intensity = 2.15; fillLight.intensity = 0.72; rimLight.intensity = 0.34;", 1)

s = s.replace("sun.shadow.mapSize.set(1024, 1024);", "sun.shadow.mapSize.set(1536, 1536);", 1)
s = s.replace("sun.shadow.bias = -0.00035;", "sun.shadow.bias = -0.00018;", 1)
s = s.replace("sun.shadow.normalBias = 0.035;", "sun.shadow.normalBias = 0.018;", 1)

pattern = re.compile(r"function sceneShadowRange\(\) \{.*?\n\}\nfunction updateShadowFrustum\(force = false\) \{.*?\n\}", re.S)
replacement = """function sceneShadowBounds() {
  const box = new THREE.Box3();
  let has = false;
  editable.forEach(o => {
    if (!o || !o.visible) return;
    const b = new THREE.Box3().setFromObject(o);
    if (b.isEmpty()) return;
    if (!has) { box.copy(b); has = true; } else box.union(b);
  });
  if (!has) return { center: orbit.target.clone(), range: 24 };
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const range = THREE.MathUtils.clamp(Math.max(size.x, size.y, size.z) * 0.72 + 6, 16, 650);
  return { center, range };
}
function sceneShadowRange() { return sceneShadowBounds().range; }
function updateShadowFrustum(force = false) {
  shadowBoundsFrame++;
  if (!force && shadowBoundsFrame % 10 !== 0) return;
  const info = sceneShadowBounds();
  cachedShadowRange = info.range;
  const c = sun.shadow.camera;
  c.left = -cachedShadowRange; c.right = cachedShadowRange;
  c.top = cachedShadowRange; c.bottom = -cachedShadowRange;
  c.near = 0.25; c.far = Math.max(180, cachedShadowRange * 6.5);
  c.updateProjectionMatrix();
  sun.shadow.needsUpdate = true;
}"""
s2, n = pattern.subn(replacement, s, count=1)
if n != 1: raise SystemExit('V16 shadow frustum anchor missing')
s = s2

old = """  updateShadowFrustum(false);
  sun.target.position.copy(orbit.target);
  sun.position.copy(orbit.target).addScaledVector(dir, Math.max(35, cachedShadowRange * 1.65));
  sunGizmo.position.copy(orbit.target).addScaledVector(dir, Math.min(8.0, Math.max(4.5, cachedShadowRange * 0.18)));
  fillLight.position.copy(camera.position);
  rimLight.target.position.copy(orbit.target);
  rimLight.position.copy(orbit.target).addScaledVector(dir, -28).add(new THREE.Vector3(0, 10, 0));"""
new = """  updateShadowFrustum(false);
  const shadowInfo = sceneShadowBounds();
  const lightCenter = shadowInfo.center;
  sun.target.position.copy(lightCenter);
  sun.target.updateMatrixWorld();
  sun.position.copy(lightCenter).addScaledVector(dir, Math.max(42, cachedShadowRange * 2.35));
  sunGizmo.position.copy(lightCenter).addScaledVector(dir, Math.min(8.0, Math.max(4.5, cachedShadowRange * 0.18)));
  fillLight.position.copy(camera.position);
  rimLight.target.position.copy(lightCenter);
  rimLight.target.updateMatrixWorld();
  rimLight.position.copy(lightCenter).addScaledVector(dir, -28).add(new THREE.Vector3(0, 10, 0));"""
if old not in s: raise SystemExit('V16 sun rig anchor missing')
s = s.replace(old, new, 1)

s = s.replace("new THREE.ShadowMaterial({ color: 0x000000, opacity: 0.42 })", "new THREE.ShadowMaterial({ color: 0x000000, opacity: 0.30 })", 1)

startup = "renderer.shadowMap.enabled = true;\nshadowCatcher.visible = true;\nrenderer.shadowMap.needsUpdate = true;\nupdateShadowFrustum(true);"
startup_new = "renderer.shadowMap.enabled = true;\nrenderer.shadowMap.autoUpdate = true;\nshadowCatcher.visible = true;\nrenderer.shadowMap.needsUpdate = true;\nupdateShadowFrustum(true);"
if startup not in s: raise SystemExit('V16 startup shadow anchor missing')
s = s.replace(startup, startup_new, 1)

anchor = "transform.addEventListener('dragging-changed', e => { orbit.enabled = !e.value; });"
if anchor in s:
    s = s.replace(anchor, anchor + "\ntransform.addEventListener('objectChange', () => { updateShadowFrustum(true); renderer.shadowMap.needsUpdate = true; });", 1)

p.write_text(s, encoding='utf-8')
print('Applied V16 real lit imported materials + object-to-object shadows')
