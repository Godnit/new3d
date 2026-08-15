from pathlib import Path

p = Path('src/editor.js')
s = p.read_text(encoding='utf-8')

repls = [
    (
        "renderer.toneMapping = THREE.ACESFilmicToneMapping;\nrenderer.toneMappingExposure = 1.15;",
        "renderer.toneMapping = THREE.NoToneMapping;"
    ),
    (
        "function material(color = 0x8ea6bd) {\n  return new THREE.MeshStandardMaterial({ color, roughness: 0.56, metalness: 0.05, side: THREE.DoubleSide });\n}",
        "function material(color = 0x8ea6bd) {\n  const base = new THREE.Color(color);\n  return new THREE.MeshPhongMaterial({\n    color: base,\n    emissive: base.clone().multiplyScalar(0.12),\n    shininess: 38,\n    specular: new THREE.Color(0x333333),\n    side: THREE.DoubleSide\n  });\n}"
    ),
    (
        "  roughnessInput.value = mat.roughness !== undefined ? mat.roughness : 0.5;\n  metalnessInput.value = mat.metalness !== undefined ? mat.metalness : 0;",
        "  roughnessInput.value = mat.roughness !== undefined ? mat.roughness : (mat.shininess !== undefined ? Math.max(0, Math.min(1, 1 - mat.shininess / 128)) : 0.5);\n  metalnessInput.value = mat.metalness !== undefined ? mat.metalness : (mat.specular ? Math.max(mat.specular.r, mat.specular.g, mat.specular.b) : 0);"
    ),
    (
        "  eachMaterial(selected, m => { if (m.color) m.color.set(hex); if ('needsUpdate' in m) m.needsUpdate = true; });",
        "  eachMaterial(selected, m => {\n    if (m.color) m.color.set(hex);\n    if (m.isMeshPhongMaterial && m.emissive && m.color) m.emissive.copy(m.color).multiplyScalar(0.12);\n    if ('needsUpdate' in m) m.needsUpdate = true;\n  });"
    ),
    (
        "  eachMaterial(selected, m => { if (m.roughness !== undefined) { m.roughness = v; m.needsUpdate = true; } });",
        "  eachMaterial(selected, m => {\n    if (m.roughness !== undefined) m.roughness = v;\n    else if (m.shininess !== undefined) m.shininess = Math.max(1, (1 - v) * 128);\n    m.needsUpdate = true;\n  });"
    ),
    (
        "  eachMaterial(selected, m => { if (m.metalness !== undefined) { m.metalness = v; m.needsUpdate = true; } });",
        "  eachMaterial(selected, m => {\n    if (m.metalness !== undefined) m.metalness = v;\n    else if (m.specular) m.specular.setRGB(v * 0.55, v * 0.55, v * 0.55);\n    m.needsUpdate = true;\n  });"
    ),
]

for old, new in repls:
    if old not in s:
        raise SystemExit('V11 patch anchor missing: ' + old[:80])
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Applied V11 color compatibility patch')
