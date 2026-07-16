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

var city_paths: Array[String] = []
var car_paths: Array[String] = []
var character_paths: Array[String] = []
var detail_paths: Array[String] = []

var camera_yaw := 0.55
var camera_pitch := -0.26
var game_started := false
var game_paused := false
var in_vehicle := false
var coin_count := 0
var kill_count := 0
var mission_stage := 0
var random := RandomNumberGenerator.new()
var world_root: Node3D
var quality_level := 1

func _ready() -> void:
	random.seed = 736281
	_create_hud()
	_create_camera_and_lighting()
	call_deferred("_build_game")

func _create_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	hud = HUDScript.new()
	layer.add_child(hud)
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.start_requested.connect(_start_game)
	hud.restart_requested.connect(_restart_game)
	hud.pause_requested.connect(_toggle_pause)
	hud.quality_requested.connect(_set_quality)

func _create_camera_and_lighting() -> void:
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 68.0
	add_child(camera)

	var environment_node := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.14, 0.31, 0.53)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.56, 0.65, 0.78)
	environment.ambient_light_energy = 0.72
	environment_node.environment = environment
	add_child(environment_node)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -28, 0)
	sun.light_energy = 1.35
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 90.0
	add_child(sun)

func _build_game() -> void:
	hud.loading_text = "تحميل نماذج المباني والسيارات والشخصيات..."
	_scan_assets()
	world_root = Node3D.new()
	world_root.name = "OpenCity"
	add_child(world_root)
	_build_ground_and_roads()
	hud.loading_text = "بناء أحياء المدينة..."
	_build_city()
	hud.loading_text = "إضافة اللاعب والسيارات والأعداء..."
	_build_actors()
	_build_collectibles_and_checkpoint()
	hud.assets_ready = true
	hud.loading_text = "جاهزة"
	_update_mission()
	_update_camera(1.0)
	print("CITYQUEST_READY buildings=", city_paths.size(), " cars=", car_paths.size(), " characters=", character_paths.size())

func _scan_assets() -> void:
	var all_city: Array[String] = []
	var all_cars: Array[String] = []
	var all_characters: Array[String] = []
	_scan_dir("res://assets/kenney/city", all_city)
	_scan_dir("res://assets/kenney/cars", all_cars)
	_scan_dir("res://assets/kenney/characters", all_characters)
	for path in all_city:
		var lower := path.to_lower()
		if "building" in lower or "skyscraper" in lower:
			city_paths.append(path)
		elif "tree" in lower or "bench" in lower or "light" in lower or "hydrant" in lower or "trash" in lower:
			detail_paths.append(path)
	for path in all_cars:
		var lower := path.to_lower()
		if "car" in lower or "sedan" in lower or "truck" in lower or "vehicle" in lower or "taxi" in lower or "racer" in lower:
			car_paths.append(path)
	for path in all_characters:
		var lower := path.to_lower()
		if lower.get_extension() in ["glb", "gltf", "fbx", "obj"]:
			character_paths.append(path)
	if city_paths.is_empty():
		city_paths = all_city
	if car_paths.is_empty():
		car_paths = all_cars
	if character_paths.is_empty():
		character_paths = all_characters

func _scan_dir(path: String, output: Array[String]) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		push_warning("Asset directory missing: " + path)
		return
	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not file_name.begins_with("."):
			var full := path.path_join(file_name)
			if dir.current_is_dir():
				_scan_dir(full, output)
			else:
				var ext := file_name.get_extension().to_lower()
				if ext in ["obj", "glb", "gltf", "fbx"]:
					output.append(full)
		file_name = dir.get_next()
	dir.list_dir_end()

func _build_ground_and_roads() -> void:
	_add_box(Vector3(0, -0.32, 0), Vector3(150, 0.5, 150), Color(0.16, 0.28, 0.12), true)
	for road_pos in [-48.0, -24.0, 0.0, 24.0, 48.0]:
		_add_box(Vector3(road_pos, -0.045, 0), Vector3(7.5, 0.08, 130), Color(0.075, 0.085, 0.1), false)
		_add_box(Vector3(0, -0.04, road_pos), Vector3(130, 0.08, 7.5), Color(0.075, 0.085, 0.1), false)
		for mark in range(-60, 61, 8):
			_add_box(Vector3(road_pos, 0.015, float(mark)), Vector3(0.13, 0.02, 3.0), Color(0.95, 0.77, 0.18), false)
			_add_box(Vector3(float(mark), 0.02, road_pos), Vector3(3.0, 0.02, 0.13), Color(0.95, 0.77, 0.18), false)
	for block_x in [-36.0, -12.0, 12.0, 36.0]:
		for block_z in [-36.0, -12.0, 12.0, 36.0]:
			_add_box(Vector3(block_x, -0.005, block_z), Vector3(16.2, 0.12, 16.2), Color(0.34, 0.36, 0.37), false)

func _build_city() -> void:
	var cells := [-36.0, -12.0, 12.0, 36.0]
	var model_index := 0
	for bx in cells:
		for bz in cells:
			var placements := [Vector2(-4.2, -4.2), Vector2(4.2, -4.0), Vector2(-4.0, 4.1), Vector2(4.1, 4.2)]
			for local in placements:
				if city_paths.is_empty():
					_add_fallback_building(Vector3(bx + local.x, 0, bz + local.y), random.randf_range(6.5, 15.0))
				else:
					var path := city_paths[model_index % city_paths.size()]
					model_index += 1
					_add_imported_prop(path, Vector3(bx + local.x, 0.0, bz + local.y), random.randf_range(7.0, 16.0), true, random.randf_range(-PI, PI))
			if not detail_paths.is_empty():
				for d in range(2):
					var detail_path := detail_paths[(model_index + d) % detail_paths.size()]
					_add_imported_prop(detail_path, Vector3(bx + random.randf_range(-7, 7), 0, bz + random.randf_range(-7, 7)), random.randf_range(1.4, 3.4), false, random.randf_range(-PI, PI))

func _build_actors() -> void:
	var player_resource := _load_safe(_pick_path(character_paths, 0))
	player = PlayerScript.new()
	player.name = "Player"
	player.global_position = Vector3(-4, 0.3, 7)
	world_root.add_child(player)
	player.setup_visual(player_resource)
	player.health_changed.connect(_on_health_changed)
	player.died.connect(_on_player_died)

	var car_resource := _load_safe(_pick_path(car_paths, 0))
	drive_car = CarScript.new()
	drive_car.name = "DriveCar"
	drive_car.global_position = Vector3(8, 0.3, 8)
	drive_car.rotation.y = -0.6
	world_root.add_child(drive_car)
	drive_car.setup_visual(car_resource, Color(0.85, 0.03, 0.02))

	for i in range(5):
		var enemy := EnemyScript.new()
		enemy.name = "Enemy_%d" % i
		var angle := float(i) / 5.0 * TAU
		enemy.global_position = Vector3(cos(angle) * 30.0, 0.3, sin(angle) * 30.0)
		world_root.add_child(enemy)
		var enemy_resource := _load_safe(_pick_path(character_paths, i + 1))
		enemy.setup(enemy_resource, player)
		enemy.defeated.connect(_on_enemy_defeated)
		enemies.append(enemy)

	for i in range(5):
		if car_paths.is_empty():
			break
		var decorative := _create_visual(_load_safe(_pick_path(car_paths, i + 1)))
		if decorative:
			world_root.add_child(decorative)
			decorative.position = Vector3(-48 + i * 24, 0.1, -6 if i % 2 == 0 else 6)
			decorative.rotation.y = 0 if i % 2 == 0 else PI
			_fit_visual(decorative, 1.45)

func _build_collectibles_and_checkpoint() -> void:
	var positions := [Vector3(-31, 1.0, -5), Vector3(-17, 1.0, 28), Vector3(7, 1.0, -31), Vector3(31, 1.0, 17), Vector3(-7, 1.0, 42), Vector3(42, 1.0, -18), Vector3(-42, 1.0, 34), Vector3(18, 1.0, 42), Vector3(29, 1.0, -42)]
	for pos in positions:
		var area := Area3D.new()
		area.position = pos
		area.collision_layer = 2
		area.collision_mask = 1
		var shape_node := CollisionShape3D.new()
		var sphere := SphereShape3D.new()
		sphere.radius = 0.75
		shape_node.shape = sphere
		area.add_child(shape_node)
		var mesh_node := MeshInstance3D.new()
		var crystal := PrismMesh.new()
		crystal.size = Vector3(0.75, 1.35, 0.75)
		mesh_node.mesh = crystal
		var material := StandardMaterial3D.new()
		material.albedo_color = Color(0.08, 0.95, 1.0)
		material.emission_enabled = true
		material.emission = Color(0.05, 0.75, 1.0)
		material.emission_energy_multiplier = 2.5
		mesh_node.material_override = material
		area.add_child(mesh_node)
		world_root.add_child(area)
		area.body_entered.connect(_on_coin_body_entered.bind(area))
		coins.append(area)

	checkpoint = Area3D.new()
	checkpoint.position = Vector3(43, 0.2, 43)
	var cp_shape_node := CollisionShape3D.new()
	var cp_shape := CylinderShape3D.new()
	cp_shape.radius = 4.0
	cp_shape.height = 1.0
	cp_shape_node.shape = cp_shape
	checkpoint.add_child(cp_shape_node)
	var ring := MeshInstance3D.new()
	var ring_mesh := CylinderMesh.new()
	ring_mesh.top_radius = 4.0
	ring_mesh.bottom_radius = 4.0
	ring_mesh.height = 0.12
	ring.mesh = ring_mesh
	var ring_mat := StandardMaterial3D.new()
	ring_mat.albedo_color = Color(0.1, 1.0, 0.25, 0.5)
	ring_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring_mat.emission_enabled = true
	ring_mat.emission = Color(0.08, 1.0, 0.2)
	ring_mat.emission_energy_multiplier = 3.0
	ring.material_override = ring_mat
	checkpoint.add_child(ring)
	world_root.add_child(checkpoint)

func _physics_process(delta: float) -> void:
	_animate_collectibles(delta)
	if not game_started or game_paused or hud.mode != hud.MODE_PLAY:
		_update_camera(delta)
		return

	var move_input := hud.move_vector
	if Input.is_key_pressed(KEY_A): move_input.x -= 1.0
	if Input.is_key_pressed(KEY_D): move_input.x += 1.0
	if Input.is_key_pressed(KEY_W): move_input.y -= 1.0
	if Input.is_key_pressed(KEY_S): move_input.y += 1.0
	move_input = move_input.limit_length(1.0)
	var jump := hud.consume_jump() or Input.is_key_pressed(KEY_SPACE)
	var sprint := hud.sprint_held or Input.is_key_pressed(KEY_SHIFT)
	var attack := hud.consume_attack() or Input.is_key_pressed(KEY_F)
	var interact := hud.consume_interact() or Input.is_key_pressed(KEY_E)
	var look := hud.consume_look()
	camera_yaw -= look.x * 0.0055
	camera_pitch = clampf(camera_pitch - look.y * 0.004, -0.72, 0.05)

	if in_vehicle:
		drive_car.tick(move_input, delta)
		hud.speed_kmh = int(absf(drive_car.current_speed) * 5.2)
	else:
		player.tick(move_input, camera_yaw, jump, sprint, delta)
		hud.speed_kmh = 0
	if attack and not in_vehicle:
		_attack_nearby()
	if interact:
		_toggle_vehicle()

	for enemy in enemies.duplicate():
		if is_instance_valid(enemy):
			enemy.target = player
			enemy.tick(delta)
	_update_hint()
	_check_mission_progress()
	_update_camera(delta)

func _process(_delta: float) -> void:
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	else:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and game_started and not game_paused:
		camera_yaw -= event.relative.x * 0.004
		camera_pitch = clampf(camera_pitch - event.relative.y * 0.003, -0.72, 0.05)

func _start_game() -> void:
	game_started = true
	game_paused = false
	hud.set_mode(hud.MODE_PLAY)
	_play_tone(440, 0.14, 0.22)

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
		camera.fov = [72.0, 68.0, 64.0][level]

func _toggle_vehicle() -> void:
	if in_vehicle:
		in_vehicle = false
		drive_car.set_controlled(false)
		player.global_position = drive_car.global_position + drive_car.global_transform.basis.x * 2.4 + Vector3.UP * 0.2
		player.set_active(true)
		hud.vehicle_mode = false
		_play_tone(360, 0.12, 0.18)
		return
	if player.global_position.distance_to(drive_car.global_position) < 3.4:
		in_vehicle = true
		player.set_active(false)
		drive_car.set_controlled(true)
		hud.vehicle_mode = true
		if mission_stage == 2:
			mission_stage = 3
			_update_mission()
		_play_tone(620, 0.12, 0.2)

func _attack_nearby() -> void:
	var best: CharacterBody3D
	var best_distance := 3.2
	for enemy in enemies:
		if not is_instance_valid(enemy):
			continue
		var distance := player.global_position.distance_to(enemy.global_position)
		if distance < best_distance:
			best = enemy
			best_distance = distance
	if best:
		best.take_damage(50)
		_play_tone(170, 0.09, 0.28)
	else:
		_play_tone(120, 0.06, 0.1)

func _on_health_changed(value: int) -> void:
	hud.health = value
	_play_tone(95, 0.08, 0.2)

func _on_player_died() -> void:
	game_paused = true
	hud.set_mode(hud.MODE_LOSE)
	_play_tone(75, 0.45, 0.24)

func _on_enemy_defeated(enemy: CharacterBody3D) -> void:
	enemies.erase(enemy)
	kill_count += 1
	hud.kills = kill_count
	player.heal(8)
	_play_tone(520, 0.16, 0.24)
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
	_play_tone(880 + coin_count * 35, 0.12, 0.22)
	_check_mission_progress()

func _check_mission_progress() -> void:
	if mission_stage == 0 and coin_count >= 6:
		mission_stage = 1
		_update_mission()
		_play_tone(740, 0.3, 0.25)
	elif mission_stage == 1 and kill_count >= 4:
		mission_stage = 2
		_update_mission()
		_play_tone(790, 0.3, 0.25)
	elif mission_stage == 3 and in_vehicle and drive_car.global_position.distance_to(checkpoint.global_position) < 5.2:
		mission_stage = 4
		_update_mission()
		game_paused = true
		hud.set_mode(hud.MODE_WIN)
		_play_tone(1040, 0.5, 0.28)

func _update_mission() -> void:
	match mission_stage:
		0: hud.mission_text = "المهمة 1: اجمع 6 بلورات (%d/6)" % coin_count
		1: hud.mission_text = "المهمة 2: اهزم 4 أعداء (%d/4)" % kill_count
		2: hud.mission_text = "المهمة 3: اقترب من السيارة واضغط ركوب"
		3: hud.mission_text = "المهمة 4: قد السيارة إلى الدائرة الخضراء"
		4: hud.mission_text = "اكتملت جميع المهام"

func _update_hint() -> void:
	if in_vehicle:
		hud.hint_text = "اضغط ركوب للنزول من السيارة"
	elif player.global_position.distance_to(drive_car.global_position) < 4.2:
		hud.hint_text = "السيارة قريبة — اضغط ركوب"
	else:
		hud.hint_text = ""

func _update_camera(delta: float) -> void:
	var target_pos := Vector3.ZERO
	if in_vehicle and is_instance_valid(drive_car):
		target_pos = drive_car.global_position + Vector3.UP * 1.3
	elif is_instance_valid(player):
		target_pos = player.global_position + Vector3.UP * 1.45
	else:
		target_pos = Vector3(0, 3, 0)
	var distance := 8.2 if in_vehicle else 6.3
	var offset := Vector3(0, 0, distance)
	offset = offset.rotated(Vector3.RIGHT, camera_pitch)
	offset = offset.rotated(Vector3.UP, camera_yaw)
	var desired := target_pos + offset + Vector3.UP * (1.5 if in_vehicle else 0.8)
	var weight := 1.0 - exp(-7.0 * maxf(delta, 0.001))
	camera.global_position = camera.global_position.lerp(desired, weight)
	camera.look_at(target_pos, Vector3.UP)

func _animate_collectibles(delta: float) -> void:
	for coin in coins:
		if is_instance_valid(coin):
			coin.rotate_y(delta * 1.9)
			coin.position.y = 1.0 + sin(Time.get_ticks_msec() * 0.003 + coin.position.x) * 0.15
	if is_instance_valid(checkpoint):
		checkpoint.rotate_y(delta * 0.35)

func _add_imported_prop(path: String, pos: Vector3, target_height: float, collision: bool, yaw: float) -> void:
	var resource := _load_safe(path)
	var visual := _create_visual(resource)
	if visual == null:
		return
	world_root.add_child(visual)
	visual.position = pos
	visual.rotation.y = yaw
	_fit_visual(visual, target_height)
	if collision:
		var body := StaticBody3D.new()
		body.position = pos + Vector3.UP * target_height * 0.46
		var shape_node := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(5.8, target_height * 0.92, 5.8)
		shape_node.shape = shape
		body.add_child(shape_node)
		world_root.add_child(body)

func _add_fallback_building(pos: Vector3, height: float) -> void:
	_add_box(pos + Vector3.UP * height * 0.5, Vector3(5.5, height, 5.5), Color(0.2 + random.randf() * 0.2, 0.25, 0.32), true)

func _add_box(pos: Vector3, box_size: Vector3, color: Color, collision: bool) -> Node3D:
	var mesh_node := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = box_size
	mesh_node.mesh = mesh
	mesh_node.position = pos
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.83
	mesh_node.material_override = material
	if world_root:
		world_root.add_child(mesh_node)
	else:
		add_child(mesh_node)
	if collision:
		var body := StaticBody3D.new()
		body.position = pos
		var shape_node := CollisionShape3D.new()
		var shape := BoxShape3D.new()
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
		var instance := resource.instantiate()
		if instance is Node3D:
			return instance
		var wrap := Node3D.new()
		wrap.add_child(instance)
		return wrap
	if resource is Mesh:
		var mesh_node := MeshInstance3D.new()
		mesh_node.mesh = resource
		return mesh_node
	return null

func _fit_visual(node: Node3D, target_height: float) -> void:
	var mesh_node := _find_mesh(node)
	if mesh_node and mesh_node.mesh:
		var box := mesh_node.mesh.get_aabb()
		var factor := target_height / maxf(box.size.y, 0.001)
		node.scale = Vector3.ONE * factor
		node.position.y -= box.position.y * factor

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D and node.mesh:
		return node
	for child in node.get_children():
		var found := _find_mesh(child)
		if found:
			return found
	return null

func _load_safe(path: String) -> Resource:
	if path == "":
		return _fallback_character_mesh()
	var resource := load(path)
	if resource == null:
		push_warning("Failed to load model: " + path)
		return _fallback_character_mesh()
	return resource

func _pick_path(paths: Array[String], index: int) -> String:
	if paths.is_empty():
		return ""
	return paths[index % paths.size()]

func _fallback_character_mesh() -> Mesh:
	var mesh := CapsuleMesh.new()
	mesh.radius = 0.4
	mesh.height = 1.7
	return mesh

func _play_tone(frequency: float, duration: float, volume: float) -> void:
	var rate := 22050
	var sample_count := int(duration * rate)
	var bytes := PackedByteArray()
	bytes.resize(sample_count * 2)
	for i in range(sample_count):
		var fade := 1.0 - float(i) / float(maxi(sample_count, 1))
		var sample := sin(TAU * frequency * float(i) / float(rate)) * fade * volume
		bytes.encode_s16(i * 2, int(clampf(sample, -1.0, 1.0) * 32767.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.stereo = false
	stream.data = bytes
	var audio := AudioStreamPlayer.new()
	audio.stream = stream
	add_child(audio)
	audio.finished.connect(audio.queue_free)
	audio.play()
