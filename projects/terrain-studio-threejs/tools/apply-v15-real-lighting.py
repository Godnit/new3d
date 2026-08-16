from pathlib import Path
import re

p = Path('src/editor.js')
s = p.read_text(encoding='utf-8')

# Restore V13 imported-material appearance exactly: keep imported colors/textures unlit,
# but allow imported meshes to CAST shadows onto the viewport shadow catcher.
pattern = re.compile(r"function compatibleImportedMaterial\(oldMat\) \{.*?\n\}\n\nfunction makeImportedMaterialsCompatible", re.S)
replacement = """function compatibleImportedMaterial(oldMat) {
  if (!oldMat) return new THREE.MeshBasicMaterial({ color: 0xb8bec6, toneMapped: false, side: THREE.DoubleSide });
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
    side: oldMat.side !== undefined ? oldMat.side : THREE.DoubleSide,
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
    raise SystemExit('V15 imported material anchor missing')
s = s2

# Make built-in primitives visibly react to the sun: remove the self-lighting that flattened them.
s = s.replace("emissive: base.clone().multiplyScalar(0.07),", "emissive: new THREE.Color(0x000000),", 1)

# Strong directional lighting with low ambient so faces clearly separate into light/shadow.
s = s.replace("ambient.intensity = 0.24; hemi.intensity = 0.42; sun.intensity = 4.8; fillLight.intensity = 0.55; rimLight.intensity = 0.85;",
              "ambient.intensity = 0.12; hemi.intensity = 0.22; sun.intensity = 4.6; fillLight.intensity = 0.16; rimLight.intensity = 0.28;", 1)
s = s.replace("ambient.intensity = 0.15; hemi.intensity = 0.28; sun.intensity = 5.6; fillLight.intensity = 0.35; rimLight.intensity = 0.65;",
              "ambient.intensity = 0.08; hemi.intensity = 0.16; sun.intensity = 5.4; fillLight.intensity = 0.10; rimLight.intensity = 0.22;", 1)
s = s.replace("ambient.intensity = 0.72; hemi.intensity = 1.05; sun.intensity = 2.4; fillLight.intensity = 2.2; rimLight.intensity = 0.55;",
              "ambient.intensity = 0.38; hemi.intensity = 0.55; sun.intensity = 2.8; fillLight.intensity = 0.72; rimLight.intensity = 0.34;", 1)

# Remove the fake sun icon; keep only the real DirectionalLight effect.
s = s.replace("sunGizmo.visible = visible;", "sunGizmo.visible = false;", 1)
anchor = "scene.add(sunGizmo);\n"
if anchor not in s:
    raise SystemExit('V15 sun gizmo anchor missing')
s = s.replace(anchor, "scene.add(sunGizmo);\nsunGizmo.visible = false;\n", 1)

# Add an invisible shadow catcher on the grid plane. It displays only shadows, not a solid floor.
anchor = "sunGizmo.visible = false;\n\nconst fillLight"
shadow_code = """sunGizmo.visible = false;

const shadowCatcher = new THREE.Mesh(
  new THREE.PlaneGeometry(20000, 20000),
  new THREE.ShadowMaterial({ color: 0x000000, opacity: 0.42 })
);
shadowCatcher.rotation.x = -Math.PI / 2;
shadowCatcher.position.y = 0.003;
shadowCatcher.receiveShadow = true;
shadowCatcher.castShadow = false;
shadowCatcher.material.depthWrite = false;
shadowCatcher.renderOrder = 2;
scene.add(shadowCatcher);

const fillLight"""
if anchor not in s:
    raise SystemExit('V15 shadow catcher anchor missing')
s = s.replace(anchor, shadow_code, 1)

# Prefer a compact, camera-centred shadow frustum for strong visible shadows on mobile.
pattern = re.compile(r"function sceneShadowRange\(\) \{.*?\n\}\nfunction updateShadowFrustum\(force = false\) \{.*?\n\}", re.S)
replacement = """function sceneShadowRange() {
  const d = camera.position.distanceTo(orbit.target);
  return THREE.MathUtils.clamp(d * 1.55, 14, 180);
}
function updateShadowFrustum(force = false) {
  shadowBoundsFrame++;
  if (!force && shadowBoundsFrame % 12 !== 0) return;
  cachedShadowRange = sceneShadowRange();
  const c = sun.shadow.camera;
  c.left = -cachedShadowRange; c.right = cachedShadowRange;
  c.top = cachedShadowRange; c.bottom = -cachedShadowRange;
  c.near = 0.5; c.far = Math.max(140, cachedShadowRange * 5.5);
  c.updateProjectionMatrix();
  sun.shadow.needsUpdate = true;
}"""
s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('V15 shadow frustum anchor missing')
s = s2

s = s.replace("sun.position.copy(orbit.target).addScaledVector(dir, Math.max(45, cachedShadowRange * 2.2));",
              "sun.position.copy(orbit.target).addScaledVector(dir, Math.max(35, cachedShadowRange * 1.65));", 1)
s = s.replace("sun.shadow.mapSize.set(1536, 1536);", "sun.shadow.mapSize.set(1024, 1024);", 1)

# Make the shadow toggle control both real shadow rendering and the catcher.
old = """document.getElementById('shadowsBtn').onclick = () => {
  renderer.shadowMap.enabled = !renderer.shadowMap.enabled;
  renderer.shadowMap.needsUpdate = true;
  document.getElementById('shadowsBtn').classList.toggle('active', renderer.shadowMap.enabled);
};"""
new = """document.getElementById('shadowsBtn').onclick = () => {
  renderer.shadowMap.enabled = !renderer.shadowMap.enabled;
  shadowCatcher.visible = renderer.shadowMap.enabled;
  renderer.shadowMap.needsUpdate = true;
  updateShadowFrustum(true);
  document.getElementById('shadowsBtn').classList.toggle('active', renderer.shadowMap.enabled);
};"""
if old not in s:
    raise SystemExit('V15 shadow button anchor missing')
s = s.replace(old, new, 1)

# Ensure imported meshes cast real shadows even though their visible material is MeshBasicMaterial.
old = """    o.castShadow = true;
    o.receiveShadow = true;
  });
  const status"""
new = """    o.castShadow = true;
    o.receiveShadow = false;
  });
  const status"""
if old not in s:
    raise SystemExit('V15 import shadow flags anchor missing')
s = s.replace(old, new, 1)

# Force the startup state to real shadows ON and catcher visible.
s = s.replace("renderer.shadowMap.enabled = true;\nupdateShadowFrustum(true);",
              "renderer.shadowMap.enabled = true;\nshadowCatcher.visible = true;\nrenderer.shadowMap.needsUpdate = true;\nupdateShadowFrustum(true);", 1)

p.write_text(s, encoding='utf-8')
print('Applied V15 real directional lighting + shadow catcher + V13 import colors')
