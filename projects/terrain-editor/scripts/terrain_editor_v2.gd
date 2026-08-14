extends Node3D

const GRID_SIZE: int = 41
const CELL_SIZE: float = 1.0
const HALF_SIZE: float = 20.0
const SAVE_PATH: String = "user://terrain_studio_map.json"
const MAX_UNDO: int = 12
const INVALID_POINT: Vector3 = Vector3(999999.0, 999999.0, 999999.0)

var heights: PackedFloat32Array = PackedFloat32Array()
var vertex_colors: PackedColorArray = PackedColorArray()

var terrain_mesh: MeshInstance3D = MeshInstance3D.new()
var terrain_material: StandardMaterial3D = StandardMaterial3D.new()
var objects_root: Node3D = Node3D.new()
var camera: Camera3D = Camera3D.new()
var sun: DirectionalLight3D = DirectionalLight3D.new()
var world_environment: WorldEnvironment = WorldEnvironment.new()
var rng: RandomNumberGenerator = RandomNumberGenerator.new()

var current_tool: String = "camera"
var brush_radius: float = 2.5
var brush_strength: float = 0.35
var paint_color: Color = Color("#4f7f3a")
var selected_variant: int = 0

var camera_target: Vector3 = Vector3.ZERO
var camera_yaw: float = deg_to_rad(38.0)
var camera_pitch: float = deg_to_rad(52.0)
var camera_distance: float = 31.0
var touches: Dictionary = {}
var pinch_last_distance: float = -1.0
var mouse_dragging: bool = false

var undo_heights: Array[PackedFloat32Array] = []
var undo_colors: Array[PackedColorArray] = []
var undo_objects: Array = []

var status_label: Label
var tool_label: Label
var variant_option: OptionButton
var color_picker: ColorPickerButton
var radius_slider: HSlider
var strength_slider: HSlider

func _ready() -> void:
	rng.randomize()
	_init_terrain_data()
	_build_world()
	_build_ui()
	_update_terrain_mesh()
	_update_camera()
	_show_status("جاهز — اختر أداة وابدأ التعديل")

func _init_terrain_data() -> void:
	var count: int = GRID_SIZE * GRID_SIZE
	heights = PackedFloat32Array()
	heights.resize(count)
	vertex_colors = PackedColorArray()
	vertex_colors.resize(count)
	for i in range(count):
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

	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky: Sky = Sky.new()
	var sky_mat: ProceduralSkyMaterial = ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color("#5f96cc")
	sky_mat.sky_horizon_color = Color("#b8d5ea")
	sky_mat.ground_bottom_color = Color("#4e5b4c")
	sky_mat.ground_horizon_color = Color("#b2b8a6")
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.72
	world_environment.environment = env
	add_child(world_environment)

func _build_ui() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	add_child(layer)

	var top_panel: PanelContainer = PanelContainer.new()
	top_panel.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top_panel.offset_bottom = 68.0
	layer.add_child(top_panel)

	var top_margin: MarginContainer = MarginContainer.new()
	top_margin.add_theme_constant_override("margin_left", 14)
	top_margin.add_theme_constant_override("margin_right", 14)
	top_margin.add_theme_constant_override("margin_top", 8)
	top_margin.add_theme_constant_override("margin_bottom", 8)
	top_panel.add_child(top_margin)

	var top_row: HBoxContainer = HBoxContainer.new()
	top_row.alignment = BoxContainer.ALIGNMENT_CENTER
	top_row.add_theme_constant_override("separation", 10)
	top_margin.add_child(top_row)

	var title: Label = Label.new()
	title.text = "TERRAIN STUDIO  •  محرر الخرائط"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 20)
	top_row.add_child(title)

	_add_action_button(top_row, "↶ تراجع", Callable(self, "_undo"))
	_add_action_button(top_row, "💾 حفظ", Callable(self, "_save_map"))
	_add_action_button(top_row, "📂 فتح", Callable(self, "_load_map"))
	_add_action_button(top_row, "＋ جديد", Callable(self, "_new_map"))

	var bottom_panel: PanelContainer = PanelContainer.new()
	bottom_panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom_panel.offset_top = -92.0
	layer.add_child(bottom_panel)

	var bottom_margin: MarginContainer = MarginContainer.new()
	bottom_margin.add_theme_constant_override("margin_left", 10)
	bottom_margin.add_theme_constant_override("margin_right", 10)
	bottom_margin.add_theme_constant_override("margin_top", 8)
	bottom_margin.add_theme_constant_override("margin_bottom", 8)
	bottom_panel.add_child(bottom_margin)

	var tools: HBoxContainer = HBoxContainer.new()
	tools.alignment = BoxContainer.ALIGNMENT_CENTER
	tools.add_theme_constant_override("separation", 7)
	bottom_margin.add_child(tools)
	_add_tool_button(tools, "camera", "🎥 كاميرا")
	_add_tool_button(tools, "raise", "⛰ رفع")
	_add_tool_button(tools, "lower", "⤵ خفض")
	_add_tool_button(tools, "smooth", "〰 تنعيم")
	_add_tool_button(tools, "paint", "🎨 طلاء")
	_add_tool_button(tools, "tree", "🌳 أشجار")
	_add_tool_button(tools, "rock", "🪨 صخور")
	_add_tool_button(tools, "erase", "🗑 مسح")

	var side_panel: PanelContainer = PanelContainer.new()
	side_panel.anchor_left = 1.0
	side_panel.anchor_right = 1.0
	side_panel.anchor_top = 0.17
	side_panel.anchor_bottom = 0.79
	side_panel.offset_left = -238.0
	side_panel.offset_right = -12.0
	layer.add_child(side_panel)

	var side_margin: MarginContainer = MarginContainer.new()
	side_margin.add_theme_constant_override("margin_left", 14)
	side_margin.add_theme_constant_override("margin_right", 14)
	side_margin.add_theme_constant_override("margin_top", 14)
	side_margin.add_theme_constant_override("margin_bottom", 14)
	side_panel.add_child(side_margin)

	var side: VBoxContainer = VBoxContainer.new()
	side.add_theme_constant_override("separation", 8)
	side_margin.add_child(side)

	tool_label = Label.new()
	tool_label.text = "الأداة: كاميرا"
	tool_label.add_theme_font_size_override("font_size", 19)
	side.add_child(tool_label)

	var radius_label: Label = Label.new()
	radius_label.text = "حجم الفرشاة"
	side.add_child(radius_label)
	radius_slider = HSlider.new()
	radius_slider.min_value = 0.6
	radius_slider.max_value = 6.0
	radius_slider.step = 0.1
	radius_slider.value = brush_radius
	radius_slider.value_changed.connect(_on_radius_changed)
	side.add_child(radius_slider)

	var strength_label: Label = Label.new()
	strength_label.text = "قوة الفرشاة"
	side.add_child(strength_label)
	strength_slider = HSlider.new()
	strength_slider.min_value = 0.05
	strength_slider.max_value = 1.0
	strength_slider.step = 0.05
	strength_slider.value = brush_strength
	strength_slider.value_changed.connect(_on_strength_changed)
	side.add_child(strength_slider)

	var color_label: Label = Label.new()
	color_label.text = "لون الأرض"
	side.add_child(color_label)
	color_picker = ColorPickerButton.new()
	color_picker.color = paint_color
	color_picker.custom_minimum_size = Vector2(0.0, 46.0)
	color_picker.color_changed.connect(_on_color_changed)
	side.add_child(color_picker)

	var variant_label: Label = Label.new()
	variant_label.text = "العنصر الجاهز"
	side.add_child(variant_label)
	variant_option = OptionButton.new()
	variant_option.custom_minimum_size = Vector2(0.0, 46.0)
	variant_option.item_selected.connect(_on_variant_selected)
	side.add_child(variant_option)
	_refresh_variant_options()

	var help: Label = Label.new()
	help.text = "الكاميرا: اسحب للدوران\nإصبعان: تكبير/تصغير\nالأدوات: المس الأرض للتعديل"
	help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help.modulate = Color(1.0, 1.0, 1.0, 0.75)
	side.add_child(help)

	status_label = Label.new()
	status_label.anchor_left = 0.5
	status_label.anchor_right = 0.5
	status_label.offset_left = -250.0
	status_label.offset_right = 250.0
	status_label.offset_top = 78.0
	status_label.offset_bottom = 116.0
	status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status_label.add_theme_font_size_override("font_size", 17)
	layer.add_child(status_label)

func _add_action_button(parent: HBoxContainer, text_value: String, callback: Callable) -> void:
	var button: Button = Button.new()
	button.text = text_value
	button.custom_minimum_size = Vector2(108.0, 46.0)
	button.pressed.connect(callback)
	parent.add_child(button)

func _add_tool_button(parent: HBoxContainer, tool: String, text_value: String) -> void:
	var button: Button = Button.new()
	button.text = text_value
	button.custom_minimum_size = Vector2(128.0, 60.0)
	button.pressed.connect(_select_tool.bind(tool))
	parent.add_child(button)

func _select_tool(tool: String) -> void:
	current_tool = tool
	selected_variant = 0
	var display_name: String = tool
	match tool:
		"camera": display_name = "كاميرا"
		"raise": display_name = "رفع التضاريس"
		"lower": display_name = "خفض التضاريس"
		"smooth": display_name = "تنعيم"
		"paint": display_name = "طلاء الأرض"
		"tree": display_name = "أشجار جاهزة"
		"rock": display_name = "صخور جاهزة"
		"erase": display_name = "مسح عناصر"
	tool_label.text = "الأداة: " + display_name
	_refresh_variant_options()
	_show_status("تم اختيار: " + display_name)

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
		_handle_touch(event as InputEventScreenTouch)
	elif event is InputEventScreenDrag:
		_handle_drag(event as InputEventScreenDrag)
	elif event is InputEventMouseButton:
		_handle_mouse_button(event as InputEventMouseButton)
	elif event is InputEventMouseMotion and mouse_dragging:
		_handle_mouse_motion(event as InputEventMouseMotion)

func _handle_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		touches[event.index] = event.position
		pinch_last_distance = -1.0
		if touches.size() == 1 and current_tool != "camera":
			_push_undo_state()
			_apply_tool_at_screen(event.position, true)
	else:
		touches.erase(event.index)
		pinch_last_distance = -1.0

func _handle_drag(event: InputEventScreenDrag) -> void:
	touches[event.index] = event.position
	if touches.size() >= 2:
		var points: Array = touches.values()
		var p0: Vector2 = points[0]
		var p1: Vector2 = points[1]
		var distance_now: float = p0.distance_to(p1)
		if pinch_last_distance > 0.0:
			camera_distance = clampf(camera_distance - (distance_now - pinch_last_distance) * 0.035, 8.0, 58.0)
			_update_camera()
		pinch_last_distance = distance_now
		return

	if current_tool == "camera":
		camera_yaw -= event.relative.x * 0.006
		camera_pitch = clampf(camera_pitch - event.relative.y * 0.0045, deg_to_rad(22.0), deg_to_rad(78.0))
		_update_camera()
	else:
		_apply_tool_at_screen(event.position, false)

func _handle_mouse_button(event: InputEventMouseButton) -> void:
	if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
		camera_distance = maxf(8.0, camera_distance - 2.0)
		_update_camera()
		return
	if event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
		camera_distance = minf(58.0, camera_distance + 2.0)
		_update_camera()
		return
	if event.button_index != MOUSE_BUTTON_LEFT:
		return
	mouse_dragging = event.pressed
	if event.pressed and current_tool != "camera":
		_push_undo_state()
		_apply_tool_at_screen(event.position, true)

func _handle_mouse_motion(event: InputEventMouseMotion) -> void:
	if current_tool == "camera":
		camera_yaw -= event.relative.x * 0.006
		camera_pitch = clampf(camera_pitch - event.relative.y * 0.0045, deg_to_rad(22.0), deg_to_rad(78.0))
		_update_camera()
	else:
		_apply_tool_at_screen(event.position, false)

func _apply_tool_at_screen(screen_pos: Vector2, first_touch: bool) -> void:
	var point: Vector3 = _screen_to_terrain(screen_pos)
	if point == INVALID_POINT:
		return
	if absf(point.x) > HALF_SIZE + 1.0 or absf(point.z) > HALF_SIZE + 1.0:
		return
	match current_tool:
		"raise": _sculpt(point, 1.0)
		"lower": _sculpt(point, -1.0)
		"smooth": _smooth(point)
		"paint": _paint(point)
		"tree":
			if first_touch:
				_place_tree(point, selected_variant)
		"rock":
			if first_touch:
				_place_rock(point, selected_variant)
		"erase":
			if first_touch:
				_erase_nearest(point)

func _screen_to_terrain(screen_pos: Vector2) -> Vector3:
	var origin: Vector3 = camera.project_ray_origin(screen_pos)
	var direction: Vector3 = camera.project_ray_normal(screen_pos)
	if absf(direction.y) < 0.0001:
		return INVALID_POINT
	var estimate_y: float = 0.0
	var result: Vector3 = Vector3.ZERO
	for _i in range(3):
		var t: float = (estimate_y - origin.y) / direction.y
		if t < 0.0:
			return INVALID_POINT
		result = origin + direction * t
		estimate_y = _terrain_height_at(result.x, result.z)
	return result

func _sculpt(center: Vector3, direction: float) -> void:
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx: float = float(x) * CELL_SIZE - HALF_SIZE
			var wz: float = float(z) * CELL_SIZE - HALF_SIZE
			var distance: float = Vector2(wx - center.x, wz - center.z).length()
			if distance <= brush_radius:
				var falloff: float = pow(1.0 - distance / brush_radius, 1.6)
				var index: int = _idx(x, z)
				heights[index] = clampf(heights[index] + direction * brush_strength * 0.22 * falloff, -7.0, 14.0)
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _smooth(center: Vector3) -> void:
	var source: PackedFloat32Array = heights.duplicate()
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx: float = float(x) * CELL_SIZE - HALF_SIZE
			var wz: float = float(z) * CELL_SIZE - HALF_SIZE
			var distance: float = Vector2(wx - center.x, wz - center.z).length()
			if distance > brush_radius:
				continue
			var total: float = 0.0
			var count: int = 0
			for oz in range(-1, 2):
				for ox in range(-1, 2):
					var nx: int = x + ox
					var nz: int = z + oz
					if nx >= 0 and nx < GRID_SIZE and nz >= 0 and nz < GRID_SIZE:
						total += source[_idx(nx, nz)]
						count += 1
			var average: float = total / float(maxi(1, count))
			var falloff: float = 1.0 - distance / brush_radius
			var index: int = _idx(x, z)
			heights[index] = lerpf(source[index], average, clampf(brush_strength * 0.55 * falloff, 0.0, 1.0))
	_update_terrain_mesh()
	_snap_objects_to_terrain()

func _paint(center: Vector3) -> void:
	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var wx: float = float(x) * CELL_SIZE - HALF_SIZE
			var wz: float = float(z) * CELL_SIZE - HALF_SIZE
			var distance: float = Vector2(wx - center.x, wz - center.z).length()
			if distance <= brush_radius:
				var falloff: float = pow(1.0 - distance / brush_radius, 1.4)
				var index: int = _idx(x, z)
				var weight: float = clampf(brush_strength * 0.45 * falloff, 0.0, 1.0)
				vertex_colors[index] = vertex_colors[index].lerp(paint_color, weight)
	_update_terrain_mesh()

func _update_terrain_mesh() -> void:
	var vertices: PackedVector3Array = PackedVector3Array()
	var normals: PackedVector3Array = PackedVector3Array()
	var indices: PackedInt32Array = PackedInt32Array()
	var count: int = GRID_SIZE * GRID_SIZE
	vertices.resize(count)
	normals.resize(count)

	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var index: int = _idx(x, z)
			vertices[index] = Vector3(float(x) * CELL_SIZE - HALF_SIZE, heights[index], float(z) * CELL_SIZE - HALF_SIZE)

	for z in range(GRID_SIZE):
		for x in range(GRID_SIZE):
			var xl: int = maxi(0, x - 1)
			var xr: int = mini(GRID_SIZE - 1, x + 1)
			var zd: int = maxi(0, z - 1)
			var zu: int = mini(GRID_SIZE - 1, z + 1)
			var dx: float = heights[_idx(xl, z)] - heights[_idx(xr, z)]
			var dz: float = heights[_idx(x, zd)] - heights[_idx(x, zu)]
			normals[_idx(x, z)] = Vector3(dx, 2.0 * CELL_SIZE, dz).normalized()

	for z in range(GRID_SIZE - 1):
		for x in range(GRID_SIZE - 1):
			var a: int = _idx(x, z)
			var b: int = _idx(x + 1, z)
			var c: int = _idx(x, z + 1)
			var d: int = _idx(x + 1, z + 1)
			indices.append(a)
			indices.append(c)
			indices.append(b)
			indices.append(b)
			indices.append(c)
			indices.append(d)

	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = vertex_colors
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	terrain_mesh.mesh = mesh

func _place_tree(point: Vector3, variant: int) -> void:
	var root: Node3D = Node3D.new()
	root.name = "Tree"
	root.set_meta("kind", "tree")
	root.set_meta("variant", variant)
	root.position = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, TAU)
	var random_scale: float = rng.randf_range(0.85, 1.18)
	root.scale = Vector3.ONE * random_scale
	objects_root.add_child(root)

	var trunk_mat: StandardMaterial3D = _material(Color("#70482f"), 1.0)
	var leaf_color: Color = Color("#39733b")
	if variant == 1:
		leaf_color = Color("#285d37")
	var leaf_mat: StandardMaterial3D = _material(leaf_color, 0.95)
	var trunk_height: float = 2.25
	var trunk_top: float = 0.16
	var trunk_bottom: float = 0.22
	if variant == 2:
		trunk_height = 1.05
		trunk_top = 0.11
		trunk_bottom = 0.14
	_add_trunk(root, trunk_height, trunk_top, trunk_bottom, trunk_mat)

	if variant == 0:
		_add_sphere_crown(root, Vector3(0.0, 2.4, 0.0), Vector3(1.45, 1.2, 1.45), leaf_mat)
		_add_sphere_crown(root, Vector3(0.45, 2.7, 0.1), Vector3(1.0, 0.9, 1.0), leaf_mat)
		_add_sphere_crown(root, Vector3(-0.5, 2.6, -0.15), Vector3(0.95, 0.85, 0.95), leaf_mat)
	elif variant == 1:
		_add_pine_crown(root, 1.65, 1.25, leaf_mat)
		_add_pine_crown(root, 2.37, 1.07, leaf_mat)
		_add_pine_crown(root, 3.09, 0.89, leaf_mat)
	else:
		_add_sphere_crown(root, Vector3(0.0, 1.0, 0.0), Vector3(1.25, 0.75, 1.25), leaf_mat)

func _add_trunk(root: Node3D, height_value: float, top_radius: float, bottom_radius: float, material: StandardMaterial3D) -> void:
	var trunk: MeshInstance3D = MeshInstance3D.new()
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = top_radius
	mesh.bottom_radius = bottom_radius
	mesh.height = height_value
	trunk.mesh = mesh
	trunk.material_override = material
	trunk.position.y = height_value * 0.5
	root.add_child(trunk)

func _add_sphere_crown(root: Node3D, position_value: Vector3, scale_value: Vector3, material: StandardMaterial3D) -> void:
	var crown: MeshInstance3D = MeshInstance3D.new()
	crown.mesh = SphereMesh.new()
	crown.material_override = material
	crown.position = position_value
	crown.scale = scale_value
	root.add_child(crown)

func _add_pine_crown(root: Node3D, y_value: float, bottom_radius: float, material: StandardMaterial3D) -> void:
	var crown: MeshInstance3D = MeshInstance3D.new()
	var cone: CylinderMesh = CylinderMesh.new()
	cone.top_radius = 0.05
	cone.bottom_radius = bottom_radius
	cone.height = 1.7
	crown.mesh = cone
	crown.material_override = material
	crown.position.y = y_value
	root.add_child(crown)

func _place_rock(point: Vector3, variant: int) -> void:
	var root: Node3D = Node3D.new()
	root.name = "Rock"
	root.set_meta("kind", "rock")
	root.set_meta("variant", variant)
	root.position = Vector3(point.x, _terrain_height_at(point.x, point.z), point.z)
	root.rotation.y = rng.randf_range(0.0, TAU)
	objects_root.add_child(root)

	var rock: MeshInstance3D = MeshInstance3D.new()
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
	var best_distance: float = brush_radius
	for i in range(objects_root.get_child_count()):
		var child: Node3D = objects_root.get_child(i) as Node3D
		if child == null:
			continue
		var distance: float = Vector2(child.position.x - point.x, child.position.z - point.z).length()
		if distance < best_distance:
			best_distance = distance
			nearest = child
	if nearest != null:
		objects_root.remove_child(nearest)
		nearest.queue_free()
		_show_status("تم حذف العنصر")
	else:
		_show_status("لا يوجد عنصر قريب داخل الفرشاة")

func _material(color: Color, roughness_value: float) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness_value
	return material

func _snap_objects_to_terrain() -> void:
	for i in range(objects_root.get_child_count()):
		var child: Node3D = objects_root.get_child(i) as Node3D
		if child != null:
			child.position.y = _terrain_height_at(child.position.x, child.position.z)

func _terrain_height_at(wx: float, wz: float) -> float:
	var gx: float = clampf((wx + HALF_SIZE) / CELL_SIZE, 0.0, float(GRID_SIZE) - 1.001)
	var gz: float = clampf((wz + HALF_SIZE) / CELL_SIZE, 0.0, float(GRID_SIZE) - 1.001)
	var x0: int = int(floor(gx))
	var z0: int = int(floor(gz))
	var x1: int = mini(GRID_SIZE - 1, x0 + 1)
	var z1: int = mini(GRID_SIZE - 1, z0 + 1)
	var tx: float = gx - float(x0)
	var tz: float = gz - float(z0)
	var h0: float = lerpf(heights[_idx(x0, z0)], heights[_idx(x1, z0)], tx)
	var h1: float = lerpf(heights[_idx(x0, z1)], heights[_idx(x1, z1)], tx)
	return lerpf(h0, h1, tz)

func _idx(x: int, z: int) -> int:
	return z * GRID_SIZE + x

func _update_camera() -> void:
	var horizontal: float = cos(camera_pitch) * camera_distance
	var offset: Vector3 = Vector3(
		sin(camera_yaw) * horizontal,
		sin(camera_pitch) * camera_distance,
		cos(camera_yaw) * horizontal
	)
	camera.position = camera_target + offset
	camera.look_at(camera_target, Vector3.UP)

func _push_undo_state() -> void:
	undo_heights.append(heights.duplicate())
	undo_colors.append(vertex_colors.duplicate())
	undo_objects.append(_serialize_objects())
	while undo_heights.size() > MAX_UNDO:
		undo_heights.pop_front()
		undo_colors.pop_front()
		undo_objects.pop_front()

func _undo() -> void:
	if undo_heights.is_empty():
		_show_status("لا يوجد تعديل للتراجع عنه")
		return
	heights = undo_heights.pop_back()
	vertex_colors = undo_colors.pop_back()
	var items: Array = undo_objects.pop_back()
	_restore_objects(items)
	_update_terrain_mesh()
	_show_status("تم التراجع")

func _serialize_objects() -> Array:
	var result: Array = []
	for i in range(objects_root.get_child_count()):
		var child: Node3D = objects_root.get_child(i) as Node3D
		if child == null or not child.has_meta("kind"):
			continue
		var item: Dictionary = {
			"kind": str(child.get_meta("kind")),
			"variant": int(child.get_meta("variant", 0)),
			"x": child.position.x,
			"z": child.position.z,
			"rotation_y": child.rotation.y,
			"scale": child.scale.x
		}
		result.append(item)
	return result

func _clear_objects() -> void:
	while objects_root.get_child_count() > 0:
		var child: Node = objects_root.get_child(0)
		objects_root.remove_child(child)
		child.queue_free()

func _restore_objects(items: Array) -> void:
	_clear_objects()
	for i in range(items.size()):
		var item: Dictionary = items[i]
		var px: float = float(item.get("x", 0.0))
		var pz: float = float(item.get("z", 0.0))
		var kind: String = str(item.get("kind", "tree"))
		var variant: int = int(item.get("variant", 0))
		var point: Vector3 = Vector3(px, 0.0, pz)
		if kind == "rock":
			_place_rock(point, variant)
		else:
			_place_tree(point, variant)
		var child: Node3D = objects_root.get_child(objects_root.get_child_count() - 1) as Node3D
		if child != null:
			child.rotation.y = float(item.get("rotation_y", child.rotation.y))
			var scale_value: float = float(item.get("scale", child.scale.x))
			child.scale = Vector3.ONE * scale_value

func _save_map() -> void:
	var saved_heights: Array = []
	var saved_colors: Array = []
	for i in range(heights.size()):
		saved_heights.append(heights[i])
		saved_colors.append(vertex_colors[i].to_html(true))
	var data: Dictionary = {
		"version": 1,
		"grid_size": GRID_SIZE,
		"heights": saved_heights,
		"colors": saved_colors,
		"objects": _serialize_objects()
	}
	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
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
	var file: FileAccess = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		_show_status("تعذر فتح ملف الخريطة")
		return
	var text: String = file.get_as_text()
	file.close()
	var json: JSON = JSON.new()
	var parse_error: Error = json.parse(text)
	if parse_error != OK or typeof(json.data) != TYPE_DICTIONARY:
		_show_status("ملف الحفظ غير صالح")
		return
	var data: Dictionary = json.data
	var saved_heights: Array = data.get("heights", [])
	var saved_colors: Array = data.get("colors", [])
	if saved_heights.size() != heights.size():
		_show_status("حجم الخريطة المحفوظة غير متوافق")
		return
	_push_undo_state()
	for i in range(heights.size()):
		heights[i] = float(saved_heights[i])
		if i < saved_colors.size():
			vertex_colors[i] = Color.from_string(str(saved_colors[i]), Color("#4f7f3a"))
	var saved_objects: Array = data.get("objects", [])
	_restore_objects(saved_objects)
	_update_terrain_mesh()
	_show_status("تم فتح الخريطة ✓")

func _new_map() -> void:
	_push_undo_state()
	_init_terrain_data()
	_clear_objects()
	_update_terrain_mesh()
	_show_status("تم إنشاء خريطة جديدة")

func _show_status(text: String) -> void:
	if status_label != null:
		status_label.text = text
