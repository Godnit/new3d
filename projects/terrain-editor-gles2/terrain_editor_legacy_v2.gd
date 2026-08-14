extends Spatial

const GRID_SIZE = 29
const CELL_SIZE = 1.25
const HALF_SIZE = (GRID_SIZE - 1) * CELL_SIZE * 0.5
const SAVE_PATH = "user://terrain_studio_legacy_v2.json"
const MAX_UNDO = 8

var heights = []
var vertex_colors = []
var undo_stack = []

var terrain_mesh = MeshInstance.new()
var terrain_material = SpatialMaterial.new()
var objects_root = Spatial.new()
var camera = Camera.new()
var sun = DirectionalLight.new()

var current_tool = "camera"
var brush_radius = 2.7
var brush_strength = 0.35
var paint_color = Color("4f7f3a")
var selected_variant = 0
var rng = RandomNumberGenerator.new()

var camera_target = Vector3(0, 0, 0)
var camera_yaw = deg2rad(38.0)
var camera_pitch = deg2rad(52.0)
var camera_distance = 27.0
var touches = {}
var pinch_last_distance = -1.0
var mouse_dragging = false

var status_label = null
var tool_label = null
var variant_option = null
var color_picker = null
var radius_slider = null
var strength_slider = null

func _ready():
	rng.randomize()
	_build_loading_screen()
	call_deferred("_boot")

func _build_loading_screen():
	var layer = CanvasLayer.new()
	layer.name = "LoadingLayer"
	add_child(layer)
	var bg = ColorRect.new()
	bg.color = Color("263748")
	bg.anchor_right = 1.0
	bg.anchor_bottom = 1.0
	layer.add_child(bg)
	var label = Label.new()
	label.text = "Terrain Studio Legacy\nLoading compatibility mode..."
	label.align = Label.ALIGN_CENTER
	label.valign = Label.VALIGN_CENTER
	label.anchor_right = 1.0
	label.anchor_bottom = 1.0
	layer.add_child(label)

func _boot():
	_init_terrain_data()
	_build_world()
	_update_terrain_mesh()
	_build_ui()
	_update_camera()
	var loading = get_node_or_null("LoadingLayer")
	if loading != null:
		loading.queue_free()
	_show_status("جاهز - وضع التوافق GLES2")

func _init_terrain_data():
	heights.clear()
	vertex_colors.clear()
	for i in range(GRID_SIZE * GRID_SIZE):
		heights.append(0.0)
		vertex_colors.append(Color("4f7f3a"))

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
	camera.far = 140.0
	camera.current = true
	add_child(camera)

	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-50.0, -32.0, 0.0)
	sun.light_energy = 0.9
	sun.shadow_enabled = false
	add_child(sun)

func _build_ui():
	var layer = CanvasLayer.new()
	layer.name = "UILayer"
	add_child(layer)

	var top = PanelContainer.new()
	top.anchor_right = 1.0
	top.margin_bottom = 56
	layer.add_child(top)
	var top_row = HBoxContainer.new()
	top_row.add_constant_override("separation", 5)
	top.add_child(top_row)

	var title = Label.new()
	title.text = "Terrain Studio Legacy"
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
	bottom.margin_top = -70
	layer.add_child(bottom)
	var tool_row = HBoxContainer.new()
	tool_row.alignment = BoxContainer.ALIGN_CENTER
	tool_row.add_constant_override("separation", 3)
	bottom.add_child(tool_row)

	var tools = [
		["camera", "كاميرا"], ["raise", "رفع"], ["lower", "خفض"],
		["smooth", "تنعيم"], ["paint", "طلاء"], ["tree", "شجر"],
		["rock", "صخر"], ["erase", "حذف"]
	]
	for item in tools:
		var b = Button.new()
		b.text = item[1]
		b.rect_min_size = Vector2(78, 48)
		b.connect("pressed", self, "_select_tool", [item[0]])
		tool_row.add_child(b)

	var side = PanelContainer.new()
	side.anchor_left = 1.0
	side.anchor_right = 1.0
	side.anchor_top = 0.17
	side.anchor_bottom = 0.79
	side.margin_left = -190
	side.margin_right = -6
	layer.add_child(side)
	var box = VBoxContainer.new()
	box.add_constant_override("separation", 4)
	side.add_child(box)

	tool_label = Label.new()
	tool_label.text = "الأداة: كاميرا"
	box.add_child(tool_label)

	var rlabel = Label.new()
	rlabel.text = "حجم الفرشاة"
	box.add_child(rlabel)
	radius_slider = HSlider.new()
	radius_slider.min_value = 0.8
	radius_slider.max_value = 5.5
	radius_slider.step = 0.1
	radius_slider.value = brush_radius
	radius_slider.connect("value_changed", self, "_on_radius_changed")
	box.add_child(radius_slider)

	var slabel = Label.new()
	slabel.text = "قوة الفرشاة"
	box.add_child(slabel)
	strength_slider = HSlider.new()
	strength_slider.min_value = 0.05
	strength_slider.max_value = 1.0
	strength_slider.step = 0.05
	strength_slider.value = brush_strength
	strength_slider.connect("value_changed", self, "_on_strength_changed")
	box.add_child(strength_slider)

	var clabel = Label.new()
	clabel.text = "لون الأرض"
	box.add_child(clabel)
	color_picker = ColorPickerButton.new()
	color_picker.color = paint_color
	color_picker.rect_min_size = Vector2(0, 36)
	color_picker.connect("color_changed", self, "_on_color_changed")
	box.add_child(color_picker)

	var vlabel = Label.new()
	vlabel.text = "العنصر"
	box.add_child(vlabel)
	variant_option = OptionButton.new()
	variant_option.connect("item_selected", self, "_on_variant_selected")
	box.add_child(variant_option)
	_refresh_variant_options()

	var help = Label.new()
	help.text = "اسحب للدوران\nإصبعان للتكبير\nالمس الأرض للتعديل"
	box.add_child(help)

	status_label = Label.new()
	status_label.anchor_left = 0.5
	status_label.anchor_right = 0.5
	status_label.margin_left = -190
	status_label.margin_right = 190
	status_label.margin_top = 60
	status_label.margin_bottom = 88
	status_label.align = Label.ALIGN_CENTER
	layer.add_child(status_label)

func _add_top_button(parent, text, method_name):
	var b = Button.new()
	b.text = text
	b.rect_min_size = Vector2(74, 44)
	b.connect("pressed", self, method_name)
	parent.add_child(b)

func _select_tool(tool):
	current_tool = str(tool)
	selected_variant = 0
	var names = {
		"camera": "كاميرا", "raise": "رفع التضاريس", "lower": "خفض التضاريس",
		"smooth": "تنعيم", "paint": "طلاء الأرض", "tree": "أشجار",
		"rock": "صخور", "erase": "حذف"
	}
	tool_label.text = "الأداة: " + str(names.get(current_tool, current_tool))
	_refresh_variant_options()
	_show_status("تم اختيار " + str(names.get(current_tool, current_tool)))

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

func _on_radius_changed(value):
	brush_radius = float(value)

func _on_strength_changed(value):
	brush_strength = float(value)

func _on_color_changed(value):
	paint_color = value

func _on_variant_selected(index):
	selected_variant = int(index)

func _unhandled_input(event):
	if event is InputEventScreenTouch:
		_handle_touch(event)
	elif event is InputEventScreenDrag:
		_handle_drag(event)
	elif event is InputEventMouseButton:
		_handle_mouse_button(event)
	elif event is InputEventMouseMotion and mouse_dragging:
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
			camera_distance = clamp(camera_distance - (dist - pinch_last_distance) * 0.035, 8.0, 48.0)
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
	if event.button_index == BUTTON_WHEEL_UP and event.pressed:
		camera_distance = max(8.0, camera_distance - 2.0)
		_update_camera()
		return
	if event.button_index == BUTTON_WHEEL_DOWN and event.pressed:
		camera_distance = min(48.0, camera_distance + 2.0)
		_update_camera()
		return
	if event.button_index != BUTTON_LEFT:
		return
	mouse_dragging = event.pressed
	if event.pressed and current_tool != "camera":
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
	var point = _screen_to_terrain(screen_pos)
	if point == null:
		return
	if abs(point.x) > HALF_SIZE + 1.0 or abs(point.z) > HALF_SIZE + 1.0:
		return
	match current_tool:
		"raise":
			_sculpt(point, 1.0)
		"lower":
			_sculpt(point, -1.0)
		"smooth":
			_smooth(point)
		"paint":
			_paint(point)
		"tree":
			if first_touch:
				_place_tree(point, selected_variant)
		"rock":
			if first_touch:
				_place_rock(point, selected_variant)
		"erase":
			if first_touch:
				_erase_nearest(point)

func _screen_to_terrain(screen_pos):
	var origin = camera.project_ray_origin(screen_pos)
	var direction = camera.project_ray_normal(screen_pos)
	if abs(direction.y) < 0.0001:
		return null
	var estimated_y = 0.0
	var result = Vector3()
	for i in range(3):
		var distance = (estimated_y - origin.y) / direction.y
		if distance < 0.0:
			return null
		result = origin + direction * distance
		estimated_y = _terrain_height_at(result.x, result.z)
	return result

func _sculpt(center, direction):
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx = x * CELL_SIZE - HALF_SIZE
			var wz = z * CELL_SIZE - HALF_SIZE
			var d = Vector2(wx - center.x, wz - center.z).length()
			if d <= brush_radius:
				var falloff = pow(1.0 - d / brush_radius, 1.5)
				var index = _idx(x, z)
				heights[index] = clamp(float(heights[index]) + direction * brush_strength * 0.22 * falloff, -6.0, 12.0)
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _smooth(center):
	var source = heights.duplicate()
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx = x * CELL_SIZE - HALF_SIZE
			var wz = z * CELL_SIZE - HALF_SIZE
			var d = Vector2(wx - center.x, wz - center.z).length()
			if d > brush_radius:
				continue
			var total = 0.0
			var count = 0
			for oz in range(-1, 2):
				for ox in range(-1, 2):
					var nx = x + ox
					var nz = z + oz
					if nx >= 0 and nx < GRID_SIZE and nz >= 0 and nz < GRID_SIZE:
						total += float(source[_idx(nx, nz)])
						count += 1
			var average = total / max(1, count)
			var falloff = 1.0 - d / brush_radius
			var index = _idx(x, z)
			heights[index] = lerp(float(source[index]), average, clamp(brush_strength * 0.5 * falloff, 0.0, 1.0))
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _paint(center):
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx = x * CELL_SIZE - HALF_SIZE
			var wz = z * CELL_SIZE - HALF_SIZE
			var d = Vector2(wx - center.x, wz - center.z).length()
			if d <= brush_radius:
				var falloff = pow(1.0 - d / brush_radius, 1.3)
				var index = _idx(x, z)
				vertex_colors[index] = vertex_colors[index].linear_interpolate(paint_color, clamp(brush_strength * 0.45 * falloff, 0.0, 1.0))
	_update_terrain_mesh()

func _update_terrain_mesh():
	var surface = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in range(GRID_SIZE - 1):
		for x in range(GRID_SIZE - 1):
			var a = _idx(x, z)
			var b = _idx(x + 1, z)
			var c = _idx(x, z + 1)
			var d = _idx(x + 1, z + 1)
			_add_terrain_vertex(surface, x, z, a)
			_add_terrain_vertex(surface, x, z + 1, c)
			_add_terrain_vertex(surface, x + 1, z, b)
			_add_terrain_vertex(surface, x + 1, z, b)
			_add_terrain_vertex(surface, x, z + 1, c)
			_add_terrain_vertex(surface, x + 1, z + 1, d)
	surface.generate_normals()
	terrain_mesh.mesh = surface.commit()

func _add_terrain_vertex(surface, x, z, index):
	surface.add_color(vertex_colors[index])
	surface.add_vertex(Vector3(x * CELL_SIZE - HALF_SIZE, float(heights[index]), z * CELL_SIZE - HALF_SIZE))

func _place_tree(point, variant):
	var root = Spatial.new()
	root.name = "Tree"
	root.set_meta("kind", "tree")
	root.set_meta("variant", int(variant))
	root.translation = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, PI * 2.0)
	objects_root.add_child(root)

	var trunk = MeshInstance.new()
	var trunk_mesh = CubeMesh.new()
	if int(variant) == 2:
		trunk_mesh.size = Vector3(0.3, 0.8, 0.3)
	else:
		trunk_mesh.size = Vector3(0.32, 1.8, 0.32)
	trunk.mesh = trunk_mesh
	trunk.translation.y = trunk_mesh.size.y * 0.5
	trunk.material_override = _make_material(Color("70482f"))
	root.add_child(trunk)

	var crown = MeshInstance.new()
	var crown_mesh = CubeMesh.new()
	if int(variant) == 0:
		crown_mesh.size = Vector3(2.2, 1.6, 2.2)
		crown.translation.y = 2.05
	elif int(variant) == 1:
		crown_mesh.size = Vector3(1.5, 2.2, 1.5)
		crown.translation.y = 2.15
	else:
		crown_mesh.size = Vector3(1.7, 0.9, 1.7)
		crown.translation.y = 0.85
	crown.mesh = crown_mesh
	if int(variant) == 1:
		crown.material_override = _make_material(Color("285d37"))
	else:
		crown.material_override = _make_material(Color("39733b"))
	root.add_child(crown)

func _place_rock(point, variant):
	var root = Spatial.new()
	root.name = "Rock"
	root.set_meta("kind", "rock")
	root.set_meta("variant", int(variant))
	root.translation = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, PI * 2.0)
	objects_root.add_child(root)

	var rock = MeshInstance.new()
	var mesh = CubeMesh.new()
	if int(variant) == 0:
		mesh.size = Vector3(1.4, 0.85, 1.2)
		rock.translation.y = 0.425
	elif int(variant) == 1:
		mesh.size = Vector3(1.6, 0.4, 1.1)
		rock.translation.y = 0.2
	else:
		mesh.size = Vector3(0.6, 0.45, 0.55)
		rock.translation.y = 0.225
	rock.mesh = mesh
	rock.rotation_degrees = Vector3(0, 0, rng.randf_range(-10.0, 10.0))
	rock.material_override = _make_material(Color("77766f"))
	root.add_child(rock)

func _erase_nearest(point):
	var nearest = null
	var best_distance = brush_radius
	for child in objects_root.get_children():
		var d = Vector2(child.translation.x - point.x, child.translation.z - point.z).length()
		if d < best_distance:
			best_distance = d
			nearest = child
	if nearest != null:
		objects_root.remove_child(nearest)
		nearest.free()
		_show_status("تم حذف العنصر")
	else:
		_show_status("لا يوجد عنصر قريب")

func _make_material(color):
	var material = SpatialMaterial.new()
	material.albedo_color = color
	material.roughness = 1.0
	return material

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
	return int(z) * GRID_SIZE + int(x)

func _update_camera():
	var horizontal = cos(camera_pitch) * camera_distance
	var offset = Vector3(
		sin(camera_yaw) * horizontal,
		sin(camera_pitch) * camera_distance,
		cos(camera_yaw) * horizontal
	)
	camera.translation = camera_target + offset
	camera.look_at(camera_target, Vector3.UP)

func _push_undo_state():
	var snapshot = {
		"heights": heights.duplicate(),
		"colors": vertex_colors.duplicate(),
		"objects": _serialize_objects()
	}
	undo_stack.append(snapshot)
	if undo_stack.size() > MAX_UNDO:
		undo_stack.pop_front()

func _undo():
	if undo_stack.empty():
		_show_status("لا توجد خطوة للتراجع")
		return
	var snapshot = undo_stack.pop_back()
	heights = snapshot["heights"].duplicate()
	vertex_colors = snapshot["colors"].duplicate()
	_restore_objects(snapshot["objects"])
	_update_terrain_mesh()
	_show_status("تم التراجع")

func _serialize_objects():
	var data = []
	for child in objects_root.get_children():
		data.append({
			"kind": str(child.get_meta("kind")),
			"variant": int(child.get_meta("variant")),
			"x": child.translation.x,
			"z": child.translation.z,
			"rot": child.rotation.y
		})
	return data

func _restore_objects(data):
	for child in objects_root.get_children():
		objects_root.remove_child(child)
		child.free()
	for item in data:
		var px = float(item["x"])
		var pz = float(item["z"])
		var p = Vector3(px, _terrain_height_at(px, pz), pz)
		if str(item["kind"]) == "tree":
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
	var color_strings = []
	for color in vertex_colors:
		color_strings.append(color.to_html(true))
	var data = {
		"heights": heights,
		"colors": color_strings,
		"objects": _serialize_objects()
	}
	file.store_string(JSON.print(data))
	file.close()
	_show_status("تم حفظ الخريطة")

func _load_map():
	var file = File.new()
	if not file.file_exists(SAVE_PATH):
		_show_status("لا توجد خريطة محفوظة")
		return
	if file.open(SAVE_PATH, File.READ) != OK:
		_show_status("تعذر فتح الحفظ")
		return
	var parsed = JSON.parse(file.get_as_text())
	file.close()
	if parsed.error != OK:
		_show_status("ملف الحفظ غير صالح")
		return
	var data = parsed.result
	if not data.has("heights") or not data.has("colors"):
		_show_status("ملف الحفظ ناقص")
		return
	heights = data["heights"].duplicate()
	vertex_colors.clear()
	for value in data["colors"]:
		vertex_colors.append(Color(str(value)))
	_restore_objects(data.get("objects", []))
	_update_terrain_mesh()
	_show_status("تم فتح الخريطة")

func _new_map():
	_push_undo_state()
	_init_terrain_data()
	for child in objects_root.get_children():
		objects_root.remove_child(child)
		child.free()
	_update_terrain_mesh()
	_show_status("خريطة جديدة")

func _show_status(text):
	if status_label != null:
		status_label.text = str(text)
