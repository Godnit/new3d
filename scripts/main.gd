extends Node3D

const PlayerScript = preload("res://scripts/player.gd")
const CarScript = preload("res://scripts/car.gd")
const EnemyScript = preload("res://scripts/enemy.gd")
const HUDScript = preload("res://scripts/hud.gd")

var hud: Control
var camera: Camera3D
var player: CharacterBody3D
var drive_car: CharacterBody3D
var enemies: Array[CharacterBody3D] = []
var coins: Array[Area3D] = []
var checkpoint: Area3D
var world_root: Node3D

var city_paths: Array[String] = []
var car_paths: Array[String] = []
var character_paths: Array[String] = []
var detail_paths: Array[String] = []

var camera_yaw: float = 0.55
var camera_pitch: float = -0.22
var game_started: bool = false
var game_paused: bool = false
var in_vehicle: bool = false
var coin_count: int = 0
var kill_count: int = 0
var mission_stage: int = 0
var quality_level: int = 0
var random: RandomNumberGenerator = RandomNumberGenerator.new()

func _ready() -> void:
	Engine.max_fps = 30
	if OS.has_feature("mobile"):
		DisplayServer.screen_set_orientation(DisplayServer.SCREEN_LANDSCAPE)
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	random.seed = 736281
	_create_hud()
	_create_camera_and_lighting()
	call_deferred("_build_game")

func _create_hud() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	hud = HUDScript.new()
	layer.add_child(hud)
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.start_requested.connect(_start_game)
	hud.restart_requested.connect(_restart_game)
	hud.pause_requested.connect(_toggle_pause)
	hud.quality_requested.connect(_set_quality)
	hud.quality_level = 0

func _create_camera_and_lighting() -> void:
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 72.0
	camera.near = 0.15
	camera.far = 125.0
	add_child(camera)

	var environment_node: WorldEnvironment = WorldEnvironment.new()
	var environment: Environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.16, 0.35, 0.58)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.72, 0.78, 0.86)
	environment.ambient_light_energy = 0.78
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	environment_node.environment = environment
	add_child(environment_node)

	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -30.0, 0.0)
	sun.light_energy = 1.1
	sun.shadow_enabled = false
	add_child(sun)

func _build_game() -> void:
	hud.loading_text = "تجهيز نسخة OpenGL المتوافقة مع هاتفك..."
	await get_tree().process_frame
	_scan_assets()
	world_root = Node3D.new()
	world_root.name = "LegacyOpenCity"
	add_child(world_root)
	_build_ground_and_roads()
	await get_tree().process_frame
	hud.loading_text = "إضافة المباني والسيارات الجاهزة..."
	_build_city()
	await get_tree().process_frame
	hud.loading_text = "إضافة الشخصيات المتحركة والمهام..."
	_build_actors()
	await get_tree().process_frame
	_build_collectibles_and_checkpoint()
	hud.assets_ready = true
	hud.loading_text = "جاهزة — OpenGL / Landscape"
	_update_mission()
	_update_camera(1.0)
	print("CITYQUEST_READY legacy_opengl buildings=", city_paths.size(), " cars=", car_paths.size(), " characters=", character_paths.size())

func _scan_assets() -> void:
	var all_city: Array[String] = []
	var all_cars: Array[String] = []
	var all_characters: Array[String] = []
	_scan_dir("res://assets/kenney/city", all_city)
	_scan_dir("res://assets/kenney/cars", all_cars)
	_scan_dir("res://assets/kaykit", all_characters)
	_scan_dir("res://assets/kenney/characters", all_characters)

	for path: String in all_city:
		var lower: String = path.to_lower()
		if "building" in lower or "skyscraper" in lower or "shop" in lower or "house" in lower:
			city_paths.append(path)
		elif "tree" in lower or "bench" in lower or "light" in lower or "hydrant" in lower or "trash" in lower or "fountain" in lower:
			detail_paths.append(path)

	for path: String in all_cars:
		var lower: String = path.to_lower()
		if "car" in lower or "sedan" in lower or "truck" in lower or "vehicle" in lower or "taxi" in lower or "racer" in lower:
			car_paths.append(path)

	for path: String in all_characters:
		var lower: String = path.to_lower()
		var rejected: bool = "animation" in lower or "weapon" in lower or "accessor" in lower or "sword" in lower or "shield" in lower or "axe" in lower or "bow" in lower or "staff" in lower or "helmet" in lower
		var likely_character: bool = "character" in lower or "barbar" in lower or "knight" in lower or "rogue" in lower or "mage" in lower or "ranger" in lower or "cesiumman" in lower or "rig_" in lower
		if not rejected and likely_character and lower.get_extension() in ["glb", "gltf", "fbx", "obj"]:
			character_paths.append(path)

	if city_paths.is_empty():
		city_paths = all_city
	if car_paths.is_empty():
		car_paths = all_cars
	if character_paths.is_empty():
		character_paths = all_characters
	city_paths.sort()
	car_paths.sort()
	character_paths.sort()
	detail_paths.sort()

func _scan_dir(path: String, output: Array[String]) -> void:
	var dir: DirAccess = DirAccess.open(path)
	if dir == null:
		return
	dir.list_dir_begin()
	var file_name: String = dir.get_next()
	while file_name != "":
		if not file_name.begins_with("."):
			var full: String = path.path_join(file_name)
			if dir.current_is_dir():
				_scan_dir(full, output)
			else:
				var ext: String = file_name.get_extension().to_lower()
				if ext in ["obj", "glb", "gltf", "fbx"]:
					output.append(full)
		file_name = dir.get_next()
	dir.list_dir_end()

func _build_ground_and_roads() -> void:
	_add_box(Vector3(0.0, -0.34, 0.0), Vector3(92.0, 0.55, 92.0), Color(0.18, 0.34, 0.14), true)
	var road_positions: Array[float] = [-24.0, 0.0, 24.0]
	for road_pos: float in road_positions:
		_add_box(Vector3(road_pos, -0.045, 0.0), Vector3(7.2, 0.08, 82.0), Color(0.075, 0.085, 0.1), false)
		_add_box(Vector3(0.0, -0.04, road_pos), Vector3(82.0, 0.08, 7.2), Color(0.075, 0.085, 0.1), false)
		for mark: int in range(-38, 39, 8):
			_add_box(Vector3(road_pos, 0.015, float(mark)), Vector3(0.12, 0.02, 2.6), Color(0.95, 0.76, 0.18), false)
			_add_box(Vector3(float(mark), 0.02, road_pos), Vector3(2.6, 0.02, 0.12), Color(0.95, 0.76, 0.18), false)
	var cells: Array[float] = [-12.0, 12.0]
	for block_x: float in cells:
		for block_z: float in cells:
			_add_box(Vector3(block_x, -0.005, block_z), Vector3(15.5, 0.12, 15.5), Color(0.34, 0.36, 0.37), false)

func _build_city() -> void:
	var cells: Array[float] = [-12.0, 12.0]
	var model_index: int = 0
	for block_x: float in cells:
		for block_z: float in cells:
			var placements: Array[Vector2] = [Vector2(-4.0, -4.0), Vector2(4.0, 3.8)]
			for local: Vector2 in placements:
				if city_paths.is_empty():
					_add_fallback_building(Vector3(block_x + local.x, 0.0, block_z + local.y), random.randf_range(6.0, 10.0))
				else:
					var path: String = city_paths[model_index % city_paths.size()]
					model_index += 1
					_add_imported_prop(path, Vector3(block_x + local.x, 0.0, block_z + local.y), random.randf_range(6.5, 10.5), true, random.randf_range(-PI, PI))
			if not detail_paths.is_empty():
				var detail_path: String = detail_paths[model_index % detail_paths.size()]
				_add_imported_prop(detail_path, Vector3(block_x + random.randf_range(-6.0, 6.0), 0.0, block_z + random.randf_range(-6.0, 6.0)), 2.1, false, random.randf_range(-PI, PI))

func _build_actors() -> void:
	var player_resource: Resource = _load_safe(_pick_path(character_paths, 0))
	player = PlayerScript.new()
	player.name = "Player"
	world_root.add_child(player)
	player.position = Vector3(-4.0, 0.3, 7.0)
	player.setup_visual(player_resource)
	player.health_changed.connect(_on_health_changed)
	player.died.connect(_on_player_died)

	var car_resource: Resource = _load_safe(_pick_path(car_paths, 0))
	drive_car = CarScript.new()
	drive_car.name = "DriveCar"
	world_root.add_child(drive_car)
	drive_car.position = Vector3(8.0, 0.3, 8.0)
	drive_car.rotation.y = -0.6
	drive_car.setup_visual(car_resource, Color(0.85, 0.03, 0.02))

	for i: int in range(3):
		var enemy: CharacterBody3D = EnemyScript.new()
		enemy.name = "Enemy_%d" % i
		world_root.add_child(enemy)
		var angle: float = float(i) / 3.0 * TAU
		enemy.position = Vector3(cos(angle) * 23.0, 0.3, sin(angle) * 23.0)
		var enemy_resource: Resource = _load_safe(_pick_path(character_paths, i + 1))
		enemy.setup(enemy_resource, player)
		enemy.defeated.connect(_on_enemy_defeated)
		enemies.append(enemy)

	for i: int in range(2):
		if car_paths.is_empty():
			break
		var decorative: Node3D = _create_visual(_load_safe(_pick_path(car_paths, i + 1)))
		if decorative:
			world_root.add_child(decorative)
			decorative.position = Vector3(-18.0 + float(i) * 36.0, 0.1, -5.0 if i % 2 == 0 else 5.0)
			decorative.rotation.y = 0.0 if i % 2 == 0 else PI
			_fit_visual(decorative, 1.35)

func _build_collectibles_and_checkpoint() -> void:
	var positions: Array[Vector3] = [
		Vector3(-18.0, 1.0, -5.0), Vector3(-8.0, 1.0, 18.0), Vector3(8.0, 1.0, -18.0),
		Vector3(18.0, 1.0, 8.0), Vector3(-18.0, 1.0, 18.0), Vector3(18.0, 1.0, -18.0)
	]
	for pos: Vector3 in positions:
		var area: Area3D = Area3D.new()
		area.position = pos
		area.collision_layer = 2
		area.collision_mask = 1
		var shape_node: CollisionShape3D = CollisionShape3D.new()
		var sphere: SphereShape3D = SphereShape3D.new()
		sphere.radius = 0.68
		shape_node.shape = sphere
		area.add_child(shape_node)
		var mesh_node: MeshInstance3D = MeshInstance3D.new()
		var crystal: PrismMesh = PrismMesh.new()
		crystal.size = Vector3(0.68, 1.15, 0.68)
		mesh_node.mesh = crystal
		var material: StandardMaterial3D = StandardMaterial3D.new()
		material.albedo_color = Color(0.08, 0.95, 1.0)
		material.emission_enabled = true
		material.emission = Color(0.05, 0.65, 0.95)
		material.emission_energy_multiplier = 1.25
		mesh_node.material_override = material
		area.add_child(mesh_node)
		world_root.add_child(area)
		area.body_entered.connect(_on_coin_body_entered.bind(area))
		coins.append(area)

	checkpoint = Area3D.new()
	checkpoint.position = Vector3(31.0, 0.2, 31.0)
	var cp_shape_node: CollisionShape3D = CollisionShape3D.new()
	var cp_shape: CylinderShape3D = CylinderShape3D.new()
	cp_shape.radius = 3.5
	cp_shape.height = 1.0
	cp_shape_node.shape = cp_shape
	checkpoint.add_child(cp_shape_node)
	var ring: MeshInstance3D = MeshInstance3D.new()
	var ring_mesh: CylinderMesh = CylinderMesh.new()
	ring_mesh.top_radius = 3.5
	ring_mesh.bottom_radius = 3.5
	ring_mesh.height = 0.10
	ring.mesh = ring_mesh
	var ring_material: StandardMaterial3D = StandardMaterial3D.new()
	ring_material.albedo_color = Color(0.1, 1.0, 0.25, 0.55)
	ring_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring_material.emission_enabled = true
	ring_material.emission = Color(0.08, 0.8, 0.2)
	ring_material.emission_energy_multiplier = 1.4
	ring.material_override = ring_material
	checkpoint.add_child(ring)
	world_root.add_child(checkpoint)

func _physics_process(delta: float) -> void:
	_animate_collectibles(delta)
	if not game_started or game_paused or hud.mode != hud.MODE_PLAY:
		_update_camera(delta)
		return

	var move_input: Vector2 = hud.move_vector
	if Input.is_key_pressed(KEY_A):
		move_input.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		move_input.x += 1.0
	if Input.is_key_pressed(KEY_W):
		move_input.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		move_input.y += 1.0
	move_input = move_input.limit_length(1.0)
	var jump: bool = hud.consume_jump() or Input.is_key_pressed(KEY_SPACE)
	var sprint: bool = hud.sprint_held or Input.is_key_pressed(KEY_SHIFT)
	var attack: bool = hud.consume_attack() or Input.is_key_pressed(KEY_F)
	var interact: bool = hud.consume_interact() or Input.is_key_pressed(KEY_E)
	var look: Vector2 = hud.consume_look()
	camera_yaw -= look.x * 0.0055
	camera_pitch = clampf(camera_pitch - look.y * 0.004, -0.65, 0.03)

	if in_vehicle:
		drive_car.tick(move_input, delta)
		hud.speed_kmh = int(absf(drive_car.current_speed) * 5.2)
	else:
		player.tick(move_input, camera_yaw, jump, sprint, delta)
		hud.speed_kmh = 0
	if attack and not in_vehicle:
		player.play_attack()
		_attack_nearby()
	if interact:
		_toggle_vehicle()

	for enemy: CharacterBody3D in enemies.duplicate():
		if is_instance_valid(enemy):
			enemy.target = player
			enemy.tick(delta)
	_update_hint()
	_check_mission_progress()
	_update_camera(delta)

func _process(_delta: float) -> void:
	if OS.has_feature("web"):
		return
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	else:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and game_started and not game_paused:
		camera_yaw -= event.relative.x * 0.004
		camera_pitch = clampf(camera_pitch - event.relative.y * 0.003, -0.65, 0.03)

func _start_game() -> void:
	game_started = true
	game_paused = false
	hud.set_mode(hud.MODE_PLAY)
	_play_tone(440.0, 0.12, 0.18)

func _restart_game() -> void:
	get_tree().reload_current_scene()

func _toggle_pause() -> void:
	if not game_started:
		return
	game_paused = not game_paused
	hud.set_mode(hud.MODE_PAUSE if game_paused else hud.MODE_PLAY)

func _set_quality(level: int) -> void:
	quality_level = level
	if camera:
		camera.fov = [72.0, 69.0, 66.0][level]

func _toggle_vehicle() -> void:
	if in_vehicle:
		in_vehicle = false
		drive_car.set_controlled(false)
		player.global_position = drive_car.global_position + drive_car.global_transform.basis.x * 2.3 + Vector3.UP * 0.2
		player.set_active(true)
		hud.vehicle_mode = false
		_play_tone(360.0, 0.10, 0.15)
		return
	if player.global_position.distance_to(drive_car.global_position) < 3.4:
		in_vehicle = true
		player.set_active(false)
		drive_car.set_controlled(true)
		hud.vehicle_mode = true
		if mission_stage == 2:
			mission_stage = 3
			_update_mission()
		_play_tone(620.0, 0.10, 0.18)

func _attack_nearby() -> void:
	var best: CharacterBody3D
	var best_distance: float = 3.1
	for enemy: CharacterBody3D in enemies:
		if not is_instance_valid(enemy):
			continue
		var distance: float = player.global_position.distance_to(enemy.global_position)
		if distance < best_distance:
			best = enemy
			best_distance = distance
	if best:
		best.take_damage(50)
		_play_tone(170.0, 0.08, 0.22)

func _on_health_changed(value: int) -> void:
	hud.health = value

func _on_player_died() -> void:
	game_paused = true
	hud.set_mode(hud.MODE_LOSE)
	_play_tone(75.0, 0.38, 0.2)

func _on_enemy_defeated(enemy: CharacterBody3D) -> void:
	enemies.erase(enemy)
	kill_count += 1
	hud.kills = kill_count
	player.heal(8)
	_play_tone(520.0, 0.14, 0.2)
	_check_mission_progress()

func _on_coin_body_entered(body: Node3D, area: Area3D) -> void:
	if body != player and body != drive_car:
		return
	if not is_instance_valid(area):
		return
	coins.erase(area)
	area.queue_free()
	coin_count += 1
	hud.coins = coin_count
	player.heal(4)
	_play_tone(780.0 + float(coin_count) * 35.0, 0.10, 0.18)
	_check_mission_progress()

func _check_mission_progress() -> void:
	if mission_stage == 0 and coin_count >= 4:
		mission_stage = 1
		_update_mission()
	elif mission_stage == 1 and kill_count >= 3:
		mission_stage = 2
		_update_mission()
	elif mission_stage == 3 and in_vehicle and drive_car.global_position.distance_to(checkpoint.global_position) < 4.8:
		mission_stage = 4
		_update_mission()
		game_paused = true
		hud.set_mode(hud.MODE_WIN)
		_play_tone(960.0, 0.45, 0.24)

func _update_mission() -> void:
	match mission_stage:
		0:
			hud.mission_text = "المهمة 1: اجمع 4 بلورات (%d/4)" % coin_count
		1:
			hud.mission_text = "المهمة 2: اهزم 3 أعداء (%d/3)" % kill_count
		2:
			hud.mission_text = "المهمة 3: اقترب من السيارة واضغط ركوب"
		3:
			hud.mission_text = "المهمة 4: قد السيارة إلى الدائرة الخضراء"
		4:
			hud.mission_text = "اكتملت جميع المهام"

func _update_hint() -> void:
	if in_vehicle:
		hud.hint_text = "اضغط ركوب للنزول من السيارة"
	elif player.global_position.distance_to(drive_car.global_position) < 4.2:
		hud.hint_text = "السيارة قريبة — اضغط ركوب"
	else:
		hud.hint_text = ""

func _update_camera(delta: float) -> void:
	var target_pos: Vector3 = Vector3.ZERO
	if in_vehicle and is_instance_valid(drive_car):
		target_pos = drive_car.global_position + Vector3.UP * 1.25
	elif is_instance_valid(player):
		target_pos = player.global_position + Vector3.UP * 1.42
	else:
		target_pos = Vector3(0.0, 3.0, 0.0)
	var distance: float = 7.4 if in_vehicle else 5.8
	var offset: Vector3 = Vector3(0.0, 0.0, distance)
	offset = offset.rotated(Vector3.RIGHT, camera_pitch)
	offset = offset.rotated(Vector3.UP, camera_yaw)
	var desired: Vector3 = target_pos + offset + Vector3.UP * (1.25 if in_vehicle else 0.72)
	var weight: float = 1.0 - exp(-6.5 * maxf(delta, 0.001))
	camera.global_position = camera.global_position.lerp(desired, weight)
	camera.look_at(target_pos, Vector3.UP)

func _animate_collectibles(delta: float) -> void:
	for coin: Area3D in coins:
		if is_instance_valid(coin):
			coin.rotate_y(delta * 1.6)
			coin.position.y = 1.0 + sin(Time.get_ticks_msec() * 0.003 + coin.position.x) * 0.12
	if is_instance_valid(checkpoint):
		checkpoint.rotate_y(delta * 0.25)

func _add_imported_prop(path: String, pos: Vector3, target_height: float, collision: bool, yaw: float) -> void:
	var resource: Resource = _load_safe(path)
	var visual: Node3D = _create_visual(resource)
	if visual == null:
		return
	world_root.add_child(visual)
	visual.position = pos
	visual.rotation.y = yaw
	_fit_visual(visual, target_height)
	if collision:
		var body: StaticBody3D = StaticBody3D.new()
		body.position = pos + Vector3.UP * target_height * 0.44
		var shape_node: CollisionShape3D = CollisionShape3D.new()
		var shape: BoxShape3D = BoxShape3D.new()
		shape.size = Vector3(5.2, target_height * 0.88, 5.2)
		shape_node.shape = shape
		body.add_child(shape_node)
		world_root.add_child(body)

func _add_fallback_building(pos: Vector3, height: float) -> void:
	_add_box(pos + Vector3.UP * height * 0.5, Vector3(5.0, height, 5.0), Color(0.25, 0.31, 0.39), true)

func _add_box(pos: Vector3, box_size: Vector3, color: Color, collision: bool) -> Node3D:
	var mesh_node: MeshInstance3D = MeshInstance3D.new()
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = box_size
	mesh_node.mesh = mesh
	mesh_node.position = pos
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.86
	mesh_node.material_override = material
	if world_root:
		world_root.add_child(mesh_node)
	else:
		add_child(mesh_node)
	if collision:
		var body: StaticBody3D = StaticBody3D.new()
		body.position = pos
		var shape_node: CollisionShape3D = CollisionShape3D.new()
		var shape: BoxShape3D = BoxShape3D.new()
		shape.size = box_size
		shape_node.shape = shape
		body.add_child(shape_node)
		if world_root:
			world_root.add_child(body)
		else:
			add_child(body)
	return mesh_node

func _create_visual(resource: Resource) -> Node3D:
	if resource is PackedScene:
		var instance: Node = (resource as PackedScene).instantiate()
		if instance is Node3D:
			return instance
		var wrap: Node3D = Node3D.new()
		wrap.add_child(instance)
		return wrap
	if resource is Mesh:
		var mesh_node: MeshInstance3D = MeshInstance3D.new()
		mesh_node.mesh = resource
		return mesh_node
	return null

func _fit_visual(node: Node3D, target_height: float) -> void:
	var mesh_node: MeshInstance3D = _find_mesh(node)
	if mesh_node and mesh_node.mesh:
		var box: AABB = mesh_node.mesh.get_aabb()
		var factor: float = target_height / maxf(box.size.y, 0.001)
		node.scale = Vector3.ONE * factor
		node.position.y -= box.position.y * factor

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D and node.mesh:
		return node
	for child: Node in node.get_children():
		var found: MeshInstance3D = _find_mesh(child)
		if found:
			return found
	return null

func _load_safe(path: String) -> Resource:
	if path == "":
		return _fallback_character_mesh()
	var resource: Resource = load(path)
	if resource == null:
		push_warning("Failed to load model: " + path)
		return _fallback_character_mesh()
	return resource

func _pick_path(paths: Array[String], index: int) -> String:
	if paths.is_empty():
		return ""
	return paths[index % paths.size()]

func _fallback_character_mesh() -> Mesh:
	var mesh: CapsuleMesh = CapsuleMesh.new()
	mesh.radius = 0.4
	mesh.height = 1.7
	return mesh

func _play_tone(frequency: float, duration: float, volume: float) -> void:
	var rate: int = 22050
	var sample_count: int = int(duration * float(rate))
	var bytes: PackedByteArray = PackedByteArray()
	bytes.resize(sample_count * 2)
	for i: int in range(sample_count):
		var fade: float = 1.0 - float(i) / float(maxi(sample_count, 1))
		var sample: float = sin(TAU * frequency * float(i) / float(rate)) * fade * volume
		bytes.encode_s16(i * 2, int(clampf(sample, -1.0, 1.0) * 32767.0))
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.stereo = false
	stream.data = bytes
	var audio: AudioStreamPlayer = AudioStreamPlayer.new()
	audio.stream = stream
	add_child(audio)
	audio.finished.connect(audio.queue_free)
	audio.play()
