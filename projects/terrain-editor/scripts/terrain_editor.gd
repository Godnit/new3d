extends Node3D

const GRID_SIZE := 41
const CELL_SIZE := 1.0
const HALF_SIZE := (GRID_SIZE - 1) * CELL_SIZE * 0.5
const SAVE_PATH := "user://terrain_studio_map.json"
const MAX_UNDO := 12

var heights: PackedFloat32Array = PackedFloat32Array()
var vertex_colors: PackedColorArray = PackedColorArray()
var terrain_mesh := MeshInstance3D.new()
var terrain_material := StandardMaterial3D.new()
var objects_root := Node3D.new()
var camera := Camera3D.new()
var sun := DirectionalLight3D.new()
var environment_node := WorldEnvironment.new()

var current_tool := "camera"
var brush_radius := 2.5
var brush_strength := 0.35
var paint_color := Color("#4f7f3a")
var selected_variant := 0
var rng := RandomNumberGenerator.new()

var camera_target := Vector3.ZERO
var camera_yaw := deg_to_rad(38.0)
var camera_pitch := deg_to_rad(52.0)
var camera_distance := 31.0
var touches: Dictionary = {}
var pinch_last_distance := -1.0
var stroke_active := false
var mouse_dragging := false

var undo_stack: Array = []
var status_label: Label
var tool_label: Label
var variant_option: OptionButton
var color_picker: ColorPickerButton
var radius_slider: HSlider
var strength_slider: HSlider
var brush_panel: PanelContainer

func _ready() -> void:
	rng.randomize()
	_init_terrain_data()
	_build_world()
	_build_ui()
	_update_terrain_mesh()
	_update_camera()
	_show_status("جاهز — اختر أداة وابدأ التعديل")

func _init_terrain_data() -> void:
	heights.resize(GRID_SIZE * GRID_SIZE)
	vertex_colors.resize(GRID_SIZE * GRID_SIZE)
	for i in range(heights.size()):
		heights[i] = 0.0
		vertex_colors[i] = Color("#4f7f3a")

func _build_world() -> void:
	terrain_mesh.name = "Terrain"
	terrain_material.vertex_color_use_as_albedo = true
	terrain_material.roughness = 0.92
	terrain_material.metallic = 0.0
	terrain_mesh.material_override = terrain_material
	add_child(terrain_mesh)

	objects_root.name = "PlacedObjects"
	add_child(objects_root)

	camera.name = "EditorCamera"
	camera.fov = 58.0
	camera.near = 0.05
	camera.far = 220.0
	add_child(camera)

	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-52.0, -34.0, 0.0)
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	add_child(sun)

	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color("#5f96cc")
	sky_mat.sky_horizon_color = Color("#b8d5ea")
	sky_mat.ground_bottom_color = Color("#4e5b4c")
	sky_mat.ground_horizon_color = Color("#b2b8a6")
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.72
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment_node.environment = env
	add_child(environment_node)

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	var top_panel := PanelContainer.new()
	top_panel.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top_panel.offset_bottom = 68.0
	layer.add_child(top_panel)

	var top_margin := MarginContainer.new()
	top_margin.add_theme_constant_override("margin_left", 14)
	top_margin.add_theme_constant_override("margin_right", 14)
	top_margin.add_theme_constant_override("margin_top", 8)
	top_margin.add_theme_constant_override("margin_bottom", 8)
	top_panel.add_child(top_margin)

	var top_row := HBoxContainer.new()
	top_row.alignment = BoxContainer.ALIGNMENT_CENTER
	top_row.add_theme_constant_override("separation", 10)
	top_margin.add_child(top_row)

	var title := Label.new()
	title.text = "TERRAIN STUDIO  •  محرر الخرائط"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 20)
	top_row.add_child(title)

	for data in [
		["↶ تراجع", Callable(self, "_undo")],
		["💾 حفظ", Callable(self, "_save_map")],
		["📂 فتح", Callable(self, "_load_map")],
		["＋ جديد", Callable(self, "_new_map")]
	]:
		var b := Button.new()
		b.text = data[0]
		b.custom_minimum_size = Vector2(108, 46)
		b.pressed.connect(data[1])
		top_row.add_child(b)

	var bottom_panel := PanelContainer.new()
	bottom_panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom_panel.offset_top = -92.0
	layer.add_child(bottom_panel)

	var bottom_margin := MarginContainer.new()
	bottom_margin.add_theme_constant_override("margin_left", 10)
	bottom_margin.add_theme_constant_override("margin_right", 10)
	bottom_margin.add_theme_constant_override("margin_top", 8)
	bottom_margin.add_theme_constant_override("margin_bottom", 8)
	bottom_panel.add_child(bottom_margin)

	var tools := HBoxContainer.new()
	tools.alignment = BoxContainer.ALIGNMENT_CENTER
	tools.add_theme_constant_override("separation", 7)
	bottom_margin.add_child(tools)

	var tool_defs := [
		["camera", "🎥 كاميرا"],
		["raise", "⛰ رفع"],
		["lower", "⤵ خفض"],
		["smooth", "〰 تنعيم"],
		["paint", "🎨 طلاء"],
		["tree", "🌳 أشجار"],
		["rock", "🪨 صخور"],
		["erase", "🗑 مسح"]
	]
	for td in tool_defs:
		var b := Button.new()
		b.text = td[1]
		b.custom_minimum_size = Vector2(128, 60)
		b.pressed.connect(_select_tool.bind(td[0]))
		tools.add_child(b)

	brush_panel = PanelContainer.new()
	brush_panel.anchor_left = 1.0
	brush_panel.anchor_right = 1.0
	brush_panel.anchor_top = 0.18
	brush_panel.anchor_bottom = 0.78
	brush_panel.offset_left = -238.0
	brush_panel.offset_right = -12.0
	layer.add_child(brush_panel)

	var side_margin := MarginContainer.new()
	side_margin.add_theme_constant_override("margin_left", 14)
	side_margin.add_theme_constant_override("margin_right", 14)
	side_margin.add_theme_constant_override("margin_top", 14)
	side_margin.add_theme_constant_override("margin_bottom", 14)
	brush_panel.add_child(side_margin)

	var side := VBoxContainer.new()
	side.add_theme_constant_override("separation", 8)
	side_margin.add_child(side)

	tool_label = Label.new()
	tool_label.text = "الأداة: كاميرا"
	tool_label.add_theme_font_size_override("font_size", 19)
	side.add_child(tool_label)

	var rlabel := Label.new()
	rlabel.text = "حجم الفرشاة"
	side.add_child(rlabel)
	radius_slider = HSlider.new()
	radius_slider.min_value = 0.6
	radius_slider.max_value = 6.0
	radius_slider.step = 0.1
	radius_slider.value = brush_radius
	radius_slider.value_changed.connect(_on_radius_changed)
	side.add_child(radius_slider)

	var slabel := Label.new()
	slabel.text = "قوة الفرشاة"
	side.add_child(slabel)
	strength_slider = HSlider.new()
	strength_slider.min_value = 0.05
	strength_slider.max_value = 1.0
	strength_slider.step = 0.05
	strength_slider.value = brush_strength
	strength_slider.value_changed.connect(_on_strength_changed)
	side.add_child(strength_slider)

	var clabel := Label.new()
	clabel.text = "لون الأرض"
	side.add_child(clabel)
	color_picker = ColorPickerButton.new()
	color_picker.color = paint_color
	color_picker.custom_minimum_size = Vector2(0, 46)
	color_picker.color_changed.connect(_on_color_changed)
	side.add_child(color_picker)

	var vlabel := Label.new()
	vlabel.text = "العنصر الجاهز"
	side.add_child(vlabel)
	variant_option = OptionButton.new()
	variant_option.custom_minimum_size = Vector2(0, 46)
	variant_option.item_selected.connect(_on_variant_selected)
	side.add_child(variant_option)
	_refresh_variant_options()

	var help := Label.new()
	help.text = "الكاميرا: اسحب للدوران\nإصبعان: تكبير/تصغير\nالأدوات: المس الأرض للتعديل"
	help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help.modulate = Color(1, 1, 1, 0.75)
	side.add_child(help)

	status_label = Label.new()
	status_label.anchor_left = 0.5
	status_label.anchor_right = 0.5
	status_label.anchor_top = 0.0
	status_label.anchor_bottom = 0.0
	status_label.offset_left = -240
	status_label.offset_right = 240
	status_label.offset_top = 78
	status_label.offset_bottom = 116
	status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status_label.add_theme_font_size_override("font_size", 17)
	layer.add_child(status_label)

func _select_tool(tool: String) -> void:
	current_tool = tool
	stroke_active = false
	selected_variant = 0
	var names := {
		"camera": "كاميرا",
		"raise": "رفع التضاريس",
		"lower": "خفض التضاريس",
		"smooth": "تنعيم",
		"paint": "طلاء الأرض",
		"tree": "أشجار جاهزة",
		"rock": "صخور جاهزة",
		"erase": "مسح عناصر"
	}
	tool_label.text = "الأداة: " + names.get(tool, tool)
	_refresh_variant_options()
	_show_status("تم اختيار: " + names.get(tool, tool))

func _refresh_variant_options() -> void:
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
		variant_option.add_item("—")
		variant_option.disabled = true

func _on_radius_changed(value: float) -> void:
	brush_radius = value

func _on_strength_changed(value: float) -> void:
	brush_strength = value

func _on_color_changed(value: Color) -> void:
	paint_color = value

func _on_variant_selected(index: int) -> void:
	selected_variant = index

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		_handle_touch(event)
	elif event is InputEventScreenDrag:
		_handle_drag(event)
	elif event is InputEventMouseButton:
		_handle_mouse_button(event)
	elif event is InputEventMouseMotion and mouse_dragging:
		_handle_mouse_motion(event)

func _handle_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		touches[event.index] = event.position
		pinch_last_distance = -1.0
		if touches.size() == 1 and current_tool != "camera":
			_push_undo_state()
			stroke_active = true
			_apply_tool_at_screen(event.position, true)
	else:
		touches.erase(event.index)
		pinch_last_distance = -1.0
		if touches.is_empty():
			stroke_active = false

func _handle_drag(event: InputEventScreenDrag) -> void:
	touches[event.index] = event.position
	if touches.size() >= 2:
		var points := touches.values()
		var dist: float = points[0].distance_to(points[1])
		if pinch_last_distance > 0.0:
			camera_distance = clamp(camera_distance - (dist - pinch_last_distance) * 0.035, 8.0, 58.0)
			_update_camera()
		pinch_last_distance = dist
		return

	if current_tool == "camera":
		camera_yaw -= event.relative.x * 0.006
		camera_pitch = clamp(camera_pitch - event.relative.y * 0.0045, deg_to_rad(22.0), deg_to_rad(78.0))
		_update_camera()
	else:
		_apply_tool_at_screen(event.position, false)

func _handle_mouse_button(event: InputEventMouseButton) -> void:
	if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
		camera_distance = max(8.0, camera_distance - 2.0)
		_update_camera()
		return
	if event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
		camera_distance = min(58.0, camera_distance + 2.0)
		_update_camera()
		return
	if event.button_index != MOUSE_BUTTON_LEFT:
		return
	mouse_dragging = event.pressed
	if event.pressed and current_tool != "camera":
		_push_undo_state()
		stroke_active = true
		_apply_tool_at_screen(event.position, true)
	elif not event.pressed:
		stroke_active = false

func _handle_mouse_motion(event: InputEventMouseMotion) -> void:
	if current_tool == "camera":
		camera_yaw -= event.relative.x * 0.006
		camera_pitch = clamp(camera_pitch - event.relative.y * 0.0045, deg_to_rad(22.0), deg_to_rad(78.0))
		_update_camera()
	else:
		_apply_tool_at_screen(event.position, false)

func _apply_tool_at_screen(screen_pos: Vector2, first_touch: bool) -> void:
	var world := _screen_to_terrain(screen_pos)
	if world == null:
		return
	var p: Vector3 = world
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

func _screen_to_terrain(screen_pos: Vector2):
	var origin := camera.project_ray_origin(screen_pos)
	var dir := camera.project_ray_normal(screen_pos)
	if abs(dir.y) < 0.0001:
		return null
	var estimate_y := 0.0
	var result := Vector3.ZERO
	for _i in range(3):
		var t := (estimate_y - origin.y) / dir.y
		if t < 0.0:
			return null
		result = origin + dir * t
		estimate_y = _terrain_height_at(result.x, result.z)
	return result

func _sculpt(center: Vector3, direction: float) -> void:
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx := x * CELL_SIZE - HALF_SIZE
			var wz := z * CELL_SIZE - HALF_SIZE
			var d := Vector2(wx - center.x, wz - center.z).length()
			if d <= brush_radius:
				var falloff := pow(1.0 - d / brush_radius, 1.6)
				var idx := _idx(x, z)
				heights[idx] = clamp(heights[idx] + direction * brush_strength * 0.22 * falloff, -7.0, 14.0)
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _smooth(center: Vector3) -> void:
	var source := heights.duplicate()
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx := x * CELL_SIZE - HALF_SIZE
			var wz := z * CELL_SIZE - HALF_SIZE
			var d := Vector2(wx - center.x, wz - center.z).length()
			if d > brush_radius:
				continue
			var sum := 0.0
			var count := 0
			for oz in range(-1, 2):
				for ox in range(-1, 2):
					var nx := x + ox
					var nz := z + oz
					if nx >= 0 and nx < GRID_SIZE and nz >= 0 and nz < GRID_SIZE:
						sum += source[_idx(nx, nz)]
						count += 1
			var avg := sum / max(1, count)
			var falloff := 1.0 - d / brush_radius
			var idx := _idx(x, z)
			heights[idx] = lerp(source[idx], avg, clamp(brush_strength * 0.55 * falloff, 0.0, 1.0))
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _paint(center: Vector3) -> void:
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx := x * CELL_SIZE - HALF_SIZE
			var wz := z * CELL_SIZE - HALF_SIZE
			var d := Vector2(wx - center.x, wz - center.z).length()
			if d <= brush_radius:
				var falloff := pow(1.0 - d / brush_radius, 1.4)
				var idx := _idx(x, z)
				vertex_colors[idx] = vertex_colors[idx].lerp(paint_color, clamp(brush_strength * 0.45 * falloff, 0.0, 1.0))
	_update_terrain_mesh()

func _update_terrain_mesh() -> void:
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var indices := PackedInt32Array()
	vertices.resize(GRID_SIZE * GRID_SIZE)
	normals.resize(GRID_SIZE * GRID_SIZE)

	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var idx := _idx(x, z)
			vertices[idx] = Vector3(x * CELL_SIZE - HALF_SIZE, heights[idx], z * CELL_SIZE - HALF_SIZE)

	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var xl := max(0, x - 1)
			var xr := min(GRID_SIZE - 1, x + 1)
			var zd := max(0, z - 1)
			var zu := min(GRID_SIZE - 1, z + 1)
			var dx := heights[_idx(xl, z)] - heights[_idx(xr, z)]
			var dz := heights[_idx(x, zd)] - heights[_idx(x, zu)]
			normals[_idx(x, z)] = Vector3(dx, 2.0 * CELL_SIZE, dz).normalized()

	for z in range(GRID_SIZE - 1):
		for x in range(GRID_SIZE - 1):
			var a := _idx(x, z)
			var b := _idx(x + 1, z)
			var c := _idx(x, z + 1)
			var d := _idx(x + 1, z + 1)
			indices.append_array(PackedInt32Array([a, c, b, b, c, d]))

	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = vertex_colors
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	terrain_mesh.mesh = mesh

func _place_tree(point: Vector3, variant: int) -> void:
	var root := Node3D.new()
	root.name = "Tree"
	root.set_meta("kind", "tree")
	root.set_meta("variant", variant)
	root.position = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, TAU)
	var random_scale := rng.randf_range(0.85, 1.18)
	root.scale = Vector3.ONE * random_scale
	objects_root.add_child(root)

	var trunk_mat := _material(Color("#70482f"), 1.0)
	var leaf_mat := _material(Color("#39733b") if variant != 1 else Color("#285d37"), 0.95)

	var trunk := MeshInstance3D.new()
	var trunk_mesh := CylinderMesh.new()
	trunk_mesh.top_radius = 0.16 if variant != 2 else 0.11
	trunk_mesh.bottom_radius = 0.22 if variant != 2 else 0.14
	trunk_mesh.height = 2.25 if variant != 2 else 1.05
	trunk.mesh = trunk_mesh
	trunk.material_override = trunk_mat
	trunk.position.y = trunk_mesh.height * 0.5
	root.add_child(trunk)

	if variant == 0:
		for data in [[Vector3(0, 2.4, 0), Vector3(1.45, 1.2, 1.45)], [Vector3(0.45, 2.7, 0.1), Vector3(1.0, 0.9, 1.0)], [Vector3(-0.5, 2.6, -0.15), Vector3(0.95, 0.85, 0.95)]]:
			var crown := MeshInstance3D.new()
			crown.mesh = SphereMesh.new()
			crown.material_override = leaf_mat
			crown.position = data[0]
			crown.scale = data[1]
			root.add_child(crown)
	elif variant == 1:
		for i in range(3):
			var crown := MeshInstance3D.new()
			var cone := CylinderMesh.new()
			cone.top_radius = 0.05
			cone.bottom_radius = 1.25 - i * 0.18
			cone.height = 1.7
			crown.mesh = cone
			crown.material_override = leaf_mat
			crown.position.y = 1.65 + i * 0.72
			root.add_child(crown)
	else:
		var crown := MeshInstance3D.new()
		crown.mesh = SphereMesh.new()
		crown.material_override = leaf_mat
		crown.position.y = 1.0
		crown.scale = Vector3(1.25, 0.75, 1.25)
		root.add_child(crown)

func _place_rock(point: Vector3, variant: int) -> void:
	var root := Node3D.new()
	root.name = "Rock"
	root.set_meta("kind", "rock")
	root.set_meta("variant", variant)
	root.position = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, TAU)
	objects_root.add_child(root)

	var rock := MeshInstance3D.new()
	rock.mesh = SphereMesh.new()
	rock.material_override = _material(Color("#77766f"), 0.98)
	if variant == 0:
		rock.scale = Vector3(rng.randf_range(0.9, 1.35), rng.randf_range(0.55, 0.95), rng.randf_range(0.8, 1.25))
		rock.position.y = 0.45
	elif variant == 1:
		rock.scale = Vector3(1.35, 0.38, 1.0)
		rock.position.y = 0.28
	else:
		rock.scale = Vector3(0.52, 0.42, 0.48)
		rock.position.y = 0.24
	root.add_child(rock)

func _erase_nearest(point: Vector3) -> void:
	var nearest: Node3D = null
	var best := brush_radius
	for child in objects_root.get_children():
		var d := Vector2(child.position.x - point.x, child.position.z - point.z).length()
		if d < best:
			best = d
			nearest = child
	if nearest != null:
		objects_root.remove_child(nearest)
		nearest.free()
		_show_status("تم حذف العنصر")
	else:
		_show_status("لا يوجد عنصر قريب داخل الفرشاة")

func _material(color: Color, roughness: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = roughness
	return mat

func _snap_objects_to_terrain() -> void:
	for child in objects_root.get_children():
		child.position.y = _terrain_height_at(child.position.x, child.position.z)

func _terrain_height_at(wx: float, wz: float) -> float:
	var gx := clamp((wx + HALF_SIZE) / CELL_SIZE, 0.0, GRID_SIZE - 1.001)
	var gz := clamp((wz + HALF_SIZE) / CELL_SIZE, 0.0, GRID_SIZE - 1.001)
	var x0 := int(floor(gx))
	var z0 := int(floor(gz))
	var x1 := min(GRID_SIZE - 1, x0 + 1)
	var z1 := min(GRID_SIZE - 1, z0 + 1)
	var tx := gx - x0
	var tz := gz - z0
	var h0 := lerp(heights[_idx(x0, z0)], heights[_idx(x1, z0)], tx)
	var h1 := lerp(heights[_idx(x0, z1)], heights[_idx(x1, z1)], tx)
	return lerp(h0, h1, tz)

func _idx(x: int, z: int) -> int:
	return z * GRID_SIZE + x

func _update_camera() -> void:
	var horizontal := cos(camera_pitch) * camera_distance
	var offset := Vector3(
		sin(camera_yaw) * horizontal,
		sin(camera_pitch) * camera_distance,
		cos(camera_yaw) * horizontal
	)
	camera.position = camera_target + offset
	camera.look_at(camera_target, Vector3.UP)

func _push_undo_state() -> void:
	undo_stack.append({
		"heights": heights.duplicate(),
		"colors": vertex_colors.duplicate(),
		"objects": _serialize_objects()
	})
	while undo_stack.size() > MAX_UNDO:
		undo_stack.pop_front()

func _undo() -> void:
	if undo_stack.is_empty():
		_show_status("لا يوجد تعديل للتراجع عنه")
		return
	var state: Dictionary = undo_stack.pop_back()
	heights = state["heights"].duplicate()
	vertex_colors = state["colors"].duplicate()
	_restore_objects(state["objects"])
	_update_terrain_mesh()
	_show_status("تم التراجع")

func _serialize_objects() -> Array:
	var result: Array = []
	for child in objects_root.get_children():
		if not child.has_meta("kind"):
			continue
		result.append({
			"kind": str(child.get_meta("kind")),
			"variant": int(child.get_meta("variant")),
			"x": child.position.x,
			"z": child.position.z,
			"rotation_y": child.rotation.y,
			"scale": child.scale.x
		})
	return result

func _restore_objects(items: Array) -> void:
	for child in objects_root.get_children():
		objects_root.remove_child(child)
		child.free()
	for item in items:
		var p := Vector3(float(item.get("x", 0.0)), 0.0, float(item.get("z", 0.0)))
		var kind := str(item.get("kind", "tree"))
		var variant := int(item.get("variant", 0))
		if kind == "rock":
			_place_rock(p, variant)
		else:
			_place_tree(p, variant)
		var child := objects_root.get_child(objects_root.get_child_count() - 1)
		child.rotation.y = float(item.get("rotation_y", child.rotation.y))
		var sc := float(item.get("scale", child.scale.x))
		child.scale = Vector3.ONE * sc

func _save_map() -> void:
	var h: Array = []
	var c: Array = []
	for value in heights:
		h.append(value)
	for value in vertex_colors:
		c.append(value.to_html(true))
	var data := {
		"version": 1,
		"grid_size": GRID_SIZE,
		"heights": h,
		"colors": c,
		"objects": _serialize_objects()
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		_show_status("تعذر حفظ الخريطة")
		return
	file.store_string(JSON.stringify(data))
	file.close()
	_show_status("تم حفظ الخريطة على الهاتف ✓")

func _load_map() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		_show_status("لا يوجد ملف محفوظ بعد")
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		_show_status("تعذر فتح ملف الخريطة")
		return
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		_show_status("ملف الحفظ غير صالح")
		return
	_push_undo_state()
	var hs: Array = parsed.get("heights", [])
	var cs: Array = parsed.get("colors", [])
	if hs.size() != heights.size():
		_show_status("حجم الخريطة المحفوظة غير متوافق")
		return
	for i in range(heights.size()):
		heights[i] = float(hs[i])
		if i < cs.size():
			vertex_colors[i] = Color.from_string(str(cs[i]), Color("#4f7f3a"))
	_restore_objects(parsed.get("objects", []))
	_update_terrain_mesh()
	_show_status("تم فتح الخريطة ✓")

func _new_map() -> void:
	_push_undo_state()
	_init_terrain_data()
	_restore_objects([])
	_update_terrain_mesh()
	_show_status("تم إنشاء خريطة جديدة")

func _show_status(text: String) -> void:
	if status_label != null:
		status_label.text = text
