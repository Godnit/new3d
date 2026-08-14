extends Spatial

const GRID_SIZE = 33
const CELL_SIZE = 1.15
const HALF_SIZE = (GRID_SIZE - 1) * CELL_SIZE * 0.5
const SAVE_PATH = "user://terrain_studio_legacy.json"
const MAX_UNDO = 8

var heights = []
var colors = []
var objects_data = []
var undo_stack = []

var terrain_mesh = MeshInstance.new()
var terrain_material = SpatialMaterial.new()
var objects_root = Spatial.new()
var camera = Camera.new()
var sun = DirectionalLight.new()

var current_tool = "camera"
var brush_radius = 2.6
var brush_strength = 0.35
var paint_color = Color("4f7f3a")
var selected_variant = 0
var rng = RandomNumberGenerator.new()

var camera_target = Vector3(0, 0, 0)
var camera_yaw = deg2rad(38.0)
var camera_pitch = deg2rad(52.0)
var camera_distance = 29.0
var touches = {}
var pinch_last_distance = -1.0

var status_label = null
var tool_label = null
var variant_option = null
var color_picker = null
var radius_slider = null
var strength_slider = null
var loading_label = null

func _ready():
	rng.randomize()
	_build_loading_ui()
	call_deferred("_boot_legacy")

func _build_loading_ui():
	var layer = CanvasLayer.new()
	layer.name = "LoadingLayer"
	add_child(layer)
	loading_label = Label.new()
	loading_label.text = "Terrain Studio\nجارٍ تشغيل وضع التوافق..."
	loading_label.align = Label.ALIGN_CENTER
	loading_label.valign = Label.VALIGN_CENTER
	loading_label.anchor_right = 1.0
	loading_label.anchor_bottom = 1.0
	loading_label.add_font_override("font", get_font("font", "Label"))
	layer.add_child(loading_label)

func _boot_legacy():
	_init_terrain_data()
	yield(get_tree(), "idle_frame")
	_build_world()
	yield(get_tree(), "idle_frame")
	_update_terrain_mesh()
	yield(get_tree(), "idle_frame")
	_build_ui()
	yield(get_tree(), "idle_frame")
	var loading_layer = get_node_or_null("LoadingLayer")
	if loading_layer != null:
		loading_layer.queue_free()
	_update_camera()
	_show_status("جاهز - وضع توافق GLES2")

func _init_terrain_data():
	heights.clear()
	colors.clear()
	for i in range(GRID_SIZE * GRID_SIZE):
		heights.append(0.0)
		colors.append(Color("4f7f3a"))

func _build_world():
	terrain_mesh.name = "Terrain"
	terrain_material.vertex_color_use_as_albedo = true
	terrain_material.roughness = 1.0
	terrain_material.metallic = 0.0
	terrain_mesh.material_override = terrain_material
	add_child(terrain_mesh)

	objects_root.name = "PlacedObjects"
	add_child(objects_root)

	camera.name = "EditorCamera"
	camera.fov = 58.0
	camera.near = 0.1
	camera.far = 160.0
	camera.current = true
	add_child(camera)

	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-52.0, -34.0, 0.0)
	sun.light_energy = 0.9
	sun.shadow_enabled = false
	add_child(sun)

func _build_ui():
	var layer = CanvasLayer.new()
	layer.name = "UILayer"
	add_child(layer)

	var top = PanelContainer.new()
	top.anchor_right = 1.0
	top.margin_bottom = 58
	layer.add_child(top)
	var top_row = HBoxContainer.new()
	top_row.add_constant_override("separation", 6)
	top.add_child(top_row)

	var title = Label.new()
	title.text = "Terrain Studio - محرر الخرائط"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.valign = Label.VALIGN_CENTER
	top_row.add_child(title)

	_add_top_button(top_row, "تراجع", "_undo")
	_add_top_button(top_row, "حفظ", "_save_map")
	_add_top_button(top_row, "فتح", "_load_map")
	_add_top_button(top_row, "جديد", "_new_map")

	var bottom = PanelContainer.new()
	bottom.anchor_top = 1.0
	bottom.anchor_right = 1.0
	bottom.anchor_bottom = 1.0
	bottom.margin_top = -74
	layer.add_child(bottom)
	var tool_row = HBoxContainer.new()
	tool_row.alignment = BoxContainer.ALIGN_CENTER
	tool_row.add_constant_override("separation", 4)
	bottom.add_child(tool_row)

	var defs = [
		["camera", "كاميرا"], ["raise", "رفع"], ["lower", "خفض"],
		["smooth", "تنعيم"], ["paint", "طلاء"], ["tree", "أشجار"],
		["rock", "صخور"], ["erase", "حذف"]
	]
	for d in defs:
		var b = Button.new()
		b.text = d[1]
		b.rect_min_size = Vector2(90, 52)
		b.connect("pressed", self, "_select_tool", [d[0]])
		tool_row.add_child(b)

	var side = PanelContainer.new()
	side.anchor_left = 1.0
	side.anchor_right = 1.0
	side.anchor_top = 0.18
	side.anchor_bottom = 0.78
	side.margin_left = -210
	side.margin_right = -8
	layer.add_child(side)
	var vb = VBoxContainer.new()
	vb.add_constant_override("separation", 5)
	side.add_child(vb)

	tool_label = Label.new()
	tool_label.text = "الأداة: كاميرا"
	vb.add_child(tool_label)

	var rlabel = Label.new()
	rlabel.text = "حجم الفرشاة"
	vb.add_child(rlabel)
	radius_slider = HSlider.new()
	radius_slider.min_value = 0.7
	radius_slider.max_value = 5.5
	radius_slider.step = 0.1
	radius_slider.value = brush_radius
	radius_slider.connect("value_changed", self, "_on_radius_changed")
	vb.add_child(radius_slider)

	var slabel = Label.new()
	slabel.text = "قوة الفرشاة"
	vb.add_child(slabel)
	strength_slider = HSlider.new()
	strength_slider.min_value = 0.05
	strength_slider.max_value = 1.0
	strength_slider.step = 0.05
	strength_slider.value = brush_strength
	strength_slider.connect("value_changed", self, "_on_strength_changed")
	vb.add_child(strength_slider)

	var clabel = Label.new()
	clabel.text = "لون الأرض"
	vb.add_child(clabel)
	color_picker = ColorPickerButton.new()
	color_picker.color = paint_color
	color_picker.rect_min_size = Vector2(0, 38)
	color_picker.connect("color_changed", self, "_on_color_changed")
	vb.add_child(color_picker)

	var vlabel = Label.new()
	vlabel.text = "العنصر الجاهز"
	vb.add_child(vlabel)
	variant_option = OptionButton.new()
	variant_option.connect("item_selected", self, "_on_variant_selected")
	vb.add_child(variant_option)
	_refresh_variant_options()

	var help = Label.new()
	help.text = "اسحب: تدوير\nإصبعان: تكبير\nالمس الأرض: تعديل"
	vb.add_child(help)

	status_label = Label.new()
	status_label.anchor_left = 0.5
	status_label.anchor_right = 0.5
	status_label.margin_left = -180
	status_label.margin_right = 180
	status_label.margin_top = 64
	status_label.margin_bottom = 94
	status_label.align = Label.ALIGN_CENTER
	layer.add_child(status_label)

func _add_top_button(parent, text, method):
	var b = Button.new()
	b.text = text
	b.rect_min_size = Vector2(82, 48)
	b.connect("pressed", self, method)
	parent.add_child(b)

func _select_tool(tool):
	current_tool = tool
	selected_variant = 0
	var names = {
		"camera":"كاميرا", "raise":"رفع التضاريس", "lower":"خفض التضاريس",
		"smooth":"تنعيم", "paint":"طلاء الأرض", "tree":"أشجار جاهزة",
		"rock":"صخور جاهزة", "erase":"حذف عناصر"
	}
	tool_label.text = "الأداة: " + str(names.get(tool, tool))
	_refresh_variant_options()
	_show_status("تم اختيار " + str(names.get(tool, tool)))

func _refresh_variant_options():
	if variant_option == null:
		return
	variant_option.clear()
	if current_tool == "tree":
		variant_option.add_item("شجرة عريضة")
		variant_option.add_item("صنوبر")
		variant_option.add_item("شجيرة")
		variant_option.disabled = false
	elif current_tool == "rock":
		variant_option.add_item("صخرة كبيرة")
		variant_option.add_item("صخرة مسطحة")
		variant_option.add_item("حجر صغير")
		variant_option.disabled = false
	else:
		variant_option.add_item("-")
		variant_option.disabled = true

func _on_radius_changed(v):
	brush_radius = float(v)

func _on_strength_changed(v):
	brush_strength = float(v)

func _on_color_changed(v):
	paint_color = v

func _on_variant_selected(i):
	selected_variant = int(i)

func _unhandled_input(event):
	if event is InputEventScreenTouch:
		_handle_touch(event)
	elif event is InputEventScreenDrag:
		_handle_drag(event)
	elif event is InputEventMouseButton:
		_handle_mouse_button(event)
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(BUTTON_LEFT):
		_handle_mouse_motion(event)

func _handle_touch(event):
	if event.pressed:
		touches[event.index] = event.position
		pinch_last_distance = -1.0
		if touches.size() == 1 and current_tool != "camera":
			_push_undo_state()
			_apply_tool_at_screen(event.position, true)
	else:
		touches.erase(event.index)
		pinch_last_distance = -1.0

func _handle_drag(event):
	touches[event.index] = event.position
	if touches.size() >= 2:
		var pts = touches.values()
		var dist = pts[0].distance_to(pts[1])
		if pinch_last_distance > 0.0:
			camera_distance = clamp(camera_distance - (dist - pinch_last_distance) * 0.035, 8.0, 52.0)
			_update_camera()
		pinch_last_distance = dist
		return
	if current_tool == "camera":
		camera_yaw -= event.relative.x * 0.006
		camera_pitch = clamp(camera_pitch - event.relative.y * 0.0045, deg2rad(22.0), deg2rad(78.0))
		_update_camera()
	else:
		_apply_tool_at_screen(event.position, false)

func _handle_mouse_button(event):
	if not event.pressed:
		return
	if event.button_index == BUTTON_WHEEL_UP:
		camera_distance = max(8.0, camera_distance - 2.0)
		_update_camera()
	elif event.button_index == BUTTON_WHEEL_DOWN:
		camera_distance = min(52.0, camera_distance + 2.0)
		_update_camera()
	elif event.button_index == BUTTON_LEFT and current_tool != "camera":
		_push_undo_state()
		_apply_tool_at_screen(event.position, true)

func _handle_mouse_motion(event):
	if current_tool == "camera":
		camera_yaw -= event.relative.x * 0.006
		camera_pitch = clamp(camera_pitch - event.relative.y * 0.0045, deg2rad(22.0), deg2rad(78.0))
		_update_camera()
	else:
		_apply_tool_at_screen(event.position, false)

func _apply_tool_at_screen(screen_pos, first_touch):
	var p = _screen_to_terrain(screen_pos)
	if p == null:
		return
	if abs(p.x) > HALF_SIZE + 1.0 or abs(p.z) > HALF_SIZE + 1.0:
		return
	match current_tool:
		"raise":
			_sculpt(p, 1.0)
		"lower":
			_sculpt(p, -1.0)
		"smooth":
			_smooth(p)
		"paint":
			_paint(p)
		"tree":
			if first_touch:
				_place_tree(p, selected_variant)
		"rock":
			if first_touch:
				_place_rock(p, selected_variant)
		"erase":
			if first_touch:
				_erase_nearest(p)

func _screen_to_terrain(screen_pos):
	var origin = camera.project_ray_origin(screen_pos)
	var dir = camera.project_ray_normal(screen_pos)
	if abs(dir.y) < 0.0001:
		return null
	var estimate_y = 0.0
	var result = Vector3()
	for i in range(3):
		var t = (estimate_y - origin.y) / dir.y
		if t < 0.0:
			return null
		result = origin + dir * t
		estimate_y = _terrain_height_at(result.x, result.z)
	return result

func _sculpt(center, direction):
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx = x * CELL_SIZE - HALF_SIZE
			var wz = z * CELL_SIZE - HALF_SIZE
			var d = Vector2(wx - center.x, wz - center.z).length()
			if d <= brush_radius:
				var falloff = pow(1.0 - d / brush_radius, 1.5)
				var idx = _idx(x, z)
				heights[idx] = clamp(float(heights[idx]) + direction * brush_strength * 0.22 * falloff, -6.0, 12.0)
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _smooth(center):
	var src = heights.duplicate()
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx = x * CELL_SIZE - HALF_SIZE
			var wz = z * CELL_SIZE - HALF_SIZE
			var d = Vector2(wx - center.x, wz - center.z).length()
			if d > brush_radius:
				continue
			var sum = 0.0
			var count = 0
			for oz in range(-1, 2):
				for ox in range(-1, 2):
					var nx = x + ox
					var nz = z + oz
					if nx >= 0 and nx < GRID_SIZE and nz >= 0 and nz < GRID_SIZE:
						sum += float(src[_idx(nx, nz)])
						count += 1
			var avg = sum / max(1, count)
			var f = 1.0 - d / brush_radius
			var idx = _idx(x, z)
			heights[idx] = lerp(float(src[idx]), avg, clamp(brush_strength * 0.5 * f, 0.0, 1.0))
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _paint(center):
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx = x * CELL_SIZE - HALF_SIZE
			var wz = z * CELL_SIZE - HALF_SIZE
			var d = Vector2(wx - center.x, wz - center.z).length()
			if d <= brush_radius:
				var f = pow(1.0 - d / brush_radius, 1.3)
				var idx = _idx(x, z)
				colors[idx] = colors[idx].linear_interpolate(paint_color, clamp(brush_strength * 0.45 * f, 0.0, 1.0))
	_update_terrain_mesh()

func _update_terrain_mesh():
	var st = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in range(GRID_SIZE - 1):
		for x in range(GRID_SIZE - 1):
			var a = _idx(x, z)
			var b = _idx(x + 1, z)
			var c = _idx(x, z + 1)
			var d = _idx(x + 1, z + 1)
			_add_vertex(st, x, z, a)
			_add_vertex(st, x, z + 1, c)
			_add_vertex(st, x + 1, z, b)
			_add_vertex(st, x + 1, z, b)
			_add_vertex(st, x, z + 1, c)
			_add_vertex(st, x + 1, z + 1, d)
	st.generate_normals()
	terrain_mesh.mesh = st.commit()

func _add_vertex(st, x, z, idx):
	st.add_color(colors[idx])
	st.add_vertex(Vector3(x * CELL_SIZE - HALF_SIZE, float(heights[idx]), z * CELL_SIZE - HALF_SIZE))

func _place_tree(point, variant):
	var root = Spatial.new()
	root.name = "Tree"
	root.set_meta("kind", "tree")
	root.set_meta("variant", variant)
	root.translation = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, PI * 2.0)
	objects_root.add_child(root)

	var trunk = MeshInstance.new()
	var trunk_mesh = CubeMesh.new()
	trunk_mesh.size = Vector3(0.35, 2.0 if variant != 2 else 0.9, 0.35)
	trunk.mesh = trunk_mesh
	trunk.material_override = _material(Color("70482f"))
	trunk.translation.y = trunk_mesh.size.y * 0.5
	root.add_child(trunk)

	var crown = MeshInstance.new()
	var crown_mesh = CubeMesh.new()
	if variant == 0:
		crown_mesh.size = Vector3(2.4, 1.8, 2.4)
		crown.translation.y = 2.35
	elif variant == 1:
		crown_mesh.size = Vector3(1.6, 2.4, 1.6)
		crown.translation.y = 2.35
	else:
		crown_mesh.size = Vector3(1.8, 1.0, 1.8)
		crown.translation.y = 1.0
	crown.mesh = crown_mesh
	crown.material_override = _material(Color("39733b") if variant != 1 else Color("285d37"))
	root.add_child(crown)

func _place_rock(point, variant):
	var root = Spatial.new()
	root.name = "Rock"
	root.set_meta("kind", "rock")
	root.set_meta("variant", variant)
	root.translation = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, PI * 2.0)
	objects_root.add_child(root)
	var rock = MeshInstance.new()
	var mesh = CubeMesh.new()
	if variant == 0:
		mesh.size = Vector3(1.5, 0.9, 1.25)
		rock.translation.y = 0.45
	elif variant == 1:
		mesh.size = Vector3(1.7, 0.45, 1.2)
		rock.translation.y = 0.23
	else:
		mesh.size = Vector3(0.65, 0.5, 0.6)
		rock.translation.y = 0.25
	rock.mesh = mesh
	rock.rotation_degrees = Vector3(0, 0, rng.randf_range(-12.0, 12.0))
	rock.material_override = _material(Color("77766f"))
	root.add_child(rock)

func _erase_nearest(point):
	var nearest = null
	var best = brush_radius
	for child in objects_root.get_children():
		var d = Vector2(child.translation.x - point.x, child.translation.z - point.z).length()
		if d < best:
			best = d
			nearest = child
	if nearest != null:
		nearest.queue_free()
		_show_status("تم حذف العنصر")

func _material(color):
	var mat = SpatialMaterial.new()
	mat.albedo_color = color
	mat.roughness = 1.0
	return mat

func _snap_objects_to_terrain():
	for child in objects_root.get_children():
		child.translation.y = _terrain_height_at(child.translation.x, child.translation.z)

func _terrain_height_at(wx, wz):
	var gx = clamp((wx + HALF_SIZE) / CELL_SIZE, 0.0, GRID_SIZE - 1.001)
	var gz = clamp((wz + HALF_SIZE) / CELL_SIZE, 0.0, GRID_SIZE - 1.001)
	var x0 = int(floor(gx))
	var z0 = int(floor(gz))
	var x1 = min(GRID_SIZE - 1, x0 + 1)
	var z1 = min(GRID_SIZE - 1, z0 + 1)
	var tx = gx - x0
	var tz = gz - z0
	var h0 = lerp(float(heights[_idx(x0, z0)]), float(heights[_idx(x1, z0)]), tx)
	var h1 = lerp(float(heights[_idx(x0, z1)]), float(heights[_idx(x1, z1)]), tx)
	return lerp(h0, h1, tz)

func _idx(x, z):
	return z * GRID_SIZE + x

func _update_camera():
	var horizontal = cos(camera_pitch) * camera_distance
	var offset = Vector3(sin(camera_yaw) * horizontal, sin(camera_pitch) * camera_distance, cos(camera_yaw) * horizontal)
	camera.translation = camera_target + offset
	camera.look_at(camera_target, Vector3.UP)

func _push_undo_state():
	var snap = {"heights": heights.duplicate(), "colors": colors.duplicate(), "objects": _serialize_objects()}
	undo_stack.append(snap)
	if undo_stack.size() > MAX_UNDO:
		undo_stack.pop_front()

func _undo():
	if undo_stack.empty():
		_show_status("لا توجد خطوة للتراجع")
		return
	var snap = undo_stack.pop_back()
	heights = snap["heights"].duplicate()
	colors = snap["colors"].duplicate()
	_restore_objects(snap["objects"])
	_update_terrain_mesh()
	_show_status("تم التراجع")

func _serialize_objects():
	var arr = []
	for child in objects_root.get_children():
		arr.append({
			"kind": str(child.get_meta("kind")),
			"variant": int(child.get_meta("variant")),
			"x": child.translation.x,
			"z": child.translation.z,
			"rot": child.rotation.y
		})
	return arr

func _restore_objects(arr):
	for child in objects_root.get_children():
		child.queue_free()
	yield(get_tree(), "idle_frame")
	for item in arr:
		var p = Vector3(float(item["x"]), _terrain_height_at(float(item["x"]), float(item["z"])), float(item["z"]))
		if item["kind"] == "tree":
			_place_tree(p, int(item["variant"]))
		else:
			_place_rock(p, int(item["variant"]))
		var last = objects_root.get_child(objects_root.get_child_count() - 1)
		last.rotation.y = float(item["rot"])

func _save_map():
	var file = File.new()
	if file.open(SAVE_PATH, File.WRITE) != OK:
		_show_status("تعذر الحفظ")
		return
	var c = []
	for col in colors:
		c.append(col.to_html(true))
	var data = {"heights": heights, "colors": c, "objects": _serialize_objects()}
	file.store_string(JSON.print(data))
	file.close()
	_show_status("تم حفظ الخريطة")

func _load_map():
	var file = File.new()
	if not file.file_exists(SAVE_PATH):
		_show_status("لا توجد خريطة محفوظة")
		return
	if file.open(SAVE_PATH, File.READ) != OK:
		_show_status("تعذر فتح الملف")
		return
	var parsed = JSON.parse(file.get_as_text())
	file.close()
	if parsed.error != OK:
		_show_status("ملف الحفظ غير صالح")
		return
	var data = parsed.result
	if not data.has("heights"):
		return
	heights = data["heights"].duplicate()
	colors.clear()
	for s in data["colors"]:
		colors.append(Color(str(s)))
	_restore_objects(data.get("objects", []))
	_update_terrain_mesh()
	_show_status("تم فتح الخريطة")

func _new_map():
	_push_undo_state()
	_init_terrain_data()
	for child in objects_root.get_children():
		child.queue_free()
	_update_terrain_mesh()
	_show_status("خريطة جديدة")

func _show_status(text):
	if status_label != null:
		status_label.text = text
