from pathlib import Path

p = Path('android/app/src/main/assets/editor/index.html')
h = p.read_text(encoding='utf-8')

css_anchor = ".sliderRow{display:grid;grid-template-columns:72px 1fr;gap:6px;align-items:center;margin:5px 0;direction:ltr}.sliderRow input{width:100%}"
css_new = css_anchor + ".presetRow{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin:5px 0 8px}.presetRow button{height:28px;border:1px solid #41464e;background:#2d3137;color:#dce4ec;border-radius:5px;font-size:10px}.presetRow button.active{background:#285f86;border-color:#4ba8ec}.importStatus{font-size:10px;line-height:1.5;color:#9fc8e8;background:#171b20;border:1px solid #343a42;border-radius:5px;padding:6px;margin-top:6px;direction:ltr;text-align:left}"
if css_anchor not in h:
    raise SystemExit('V13 UI css anchor missing')
h = h.replace(css_anchor, css_new, 1)

old_world = """      <div class=\"section\">
        <div class=\"sectionTitle\">World & Light</div>
        <div class=\"sectionBody\">
          <div class=\"sliderRow\"><label>Ambient</label><input id=\"ambientInput\" type=\"range\" min=\"0\" max=\"3\" step=\"0.05\" value=\"1.0\"></div>
          <div class=\"sliderRow\"><label>Sun</label><input id=\"sunInput\" type=\"range\" min=\"0\" max=\"6\" step=\"0.05\" value=\"2.8\"></div>
          <div class=\"colorRow\"><label>الخلفية</label><input id=\"backgroundInput\" type=\"color\" value=\"#202328\"></div>
        </div>
      </div>"""
new_world = """      <div class=\"section\">
        <div class=\"sectionTitle\">World & Light</div>
        <div class=\"sectionBody\">
          <div class=\"presetRow\"><button class=\"active\" data-lightpreset=\"studio\">Studio</button><button data-lightpreset=\"sunny\">Sun</button><button data-lightpreset=\"soft\">Soft</button></div>
          <div class=\"sliderRow\"><label>Ambient</label><input id=\"ambientInput\" type=\"range\" min=\"0\" max=\"3\" step=\"0.05\" value=\"0.45\"></div>
          <div class=\"sliderRow\"><label>Sun</label><input id=\"sunInput\" type=\"range\" min=\"0\" max=\"7\" step=\"0.05\" value=\"4.0\"></div>
          <div class=\"sliderRow\"><label>Azimuth</label><input id=\"sunAzimuthInput\" type=\"range\" min=\"-180\" max=\"180\" step=\"1\" value=\"35\"></div>
          <div class=\"sliderRow\"><label>Elevation</label><input id=\"sunElevationInput\" type=\"range\" min=\"5\" max=\"85\" step=\"1\" value=\"48\"></div>
          <div class=\"colorRow\"><label>الخلفية</label><input id=\"backgroundInput\" type=\"color\" value=\"#202328\"></div>
        </div>
      </div>
      <div class=\"section\">
        <div class=\"sectionTitle\">Import</div>
        <div class=\"sectionBody\"><div id=\"importStatus\" class=\"importStatus\">GLB: ملف واحد • GLTF: اختر gltf + bin + الصور معًا</div></div>
      </div>"""
if old_world not in h:
    raise SystemExit('V13 UI world anchor missing')
h = h.replace(old_world, new_world, 1)

old_input = '<input id="fileInput" class="file" type="file" accept=".glb,.gltf,model/gltf-binary,model/gltf+json" />'
new_input = '<input id="fileInput" class="file" type="file" multiple accept=".glb,.gltf,.bin,image/*,model/gltf-binary,model/gltf+json" />'
if old_input not in h:
    raise SystemExit('V13 UI file input anchor missing')
h = h.replace(old_input, new_input, 1)

p.write_text(h, encoding='utf-8')
print('Applied V13 lighting/import UI')
