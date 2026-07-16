extends Spatial

const PlayerScript = preload("res://scripts/player.gd")
const CarScript = preload("res://scripts/car.gd")
const EnemyScript = preload("res://scripts/enemy.gd")
const HUDScript = preload("res://scripts/hud.gd")

var hud = null
var camera = null
var player = null
var drive_car = null
var enemies = []
var coins = []
var checkpoint = null
var world_root = null

var city_paths = []
var car_paths = []
var character_paths = []

var camera_yaw = 0.55
var camera_pitch = -0.22
var game_started = false
var game_paused = false
var in_vehicle = false
var coin_count = 0
var kill_count = 0
var mission_stage = 0

func _ready():
	Engine.target_fps = 30
	_create_hud()
	_create_camera()
	_build_game_direct()

func _create_hud():
	var layer = CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	hud = HUDScript.new()
	layer.add_child(hud)
	hud.anchor_left = 0.0
	hud.anchor_top = 0.0
	hud.anchor_right = 1.0
	hud.anchor_bottom = 1.0
	hud.margin_left = 0.0
	hud.margin_top = 0.0
	hud.margin_right = 0.0
	hud.margin_bottom = 0.0
	hud.connect("restart_requested", self, "_restart_game")
	hud.connect("pause_requested", self, "_toggle_pause")

func _create_camera():
	camera = Camera.new()
	camera.current = true
	camera.fov = 72.0
	camera.near = 0.15
	camera.far = 100.0
	add_child(camera)

func _build_game_direct():
	_read_manifest()
	world_root = Spatial.new()
	world_root.name = "GLES2DirectCity"
	add_child(world_root)
	_build_ground_and_roads()

	var building_resource = _load_first(city_paths)
	var car_resource = _load_first(car_paths)
	var character_resource = _load_character()
	_build_city(building_resource)
	_build_actors(character_resource, car_resource)
	_build_collectibles_and_checkpoint()
	_update_mission()
	_update_camera(1.0)
	game_started = true
	hud.set_mode(hud.MODE_PLAY)
	print("CITYQUEST_READY gles2_direct city=", city_paths.size(), " cars=", car_paths.size(), " characters=", character_paths.size())

func _read_manifest():
	var file = File.new()
	if not file.file_exists("res://assets/model_manifest.json"):
		print("MODEL_MANIFEST_MISSING using fallbacks")
		return
	if file.open("res://assets/model_manifest.json", File.READ) != OK:
		print("MODEL_MANIFEST_OPEN_FAILED using fallbacks")
		return
	var parsed = JSON.parse(file.get_as_text())
	file.close()
	if parsed.error != OK or typeof(parsed.result) != TYPE_DICTIONARY:
		print("MODEL_MANIFEST_INVALID using fallbacks")
		return
	city_paths = _array_strings(parsed.result.get("city", []))
	car_paths = _array_strings(parsed.result.get("cars", []))
	character_paths = _array_strings(parsed.result.get("characters", []))

func _array_strings(value):
	var output = []
	if typeof(value) == TYPE_ARRAY:
		for item in value:
			if typeof(item) == TYPE_STRING:
				output.append(item)
	return output

func _load_first(paths):
	if paths.empty():
		return null
	return load(paths[0])

func _load_character():
	for path in character_paths:
		if "cesiumman" in String(path).to_lower():
			return load(path)
	for path in character_paths:
		if String(path).get_extension().to_lower() == "glb":
			return load(path)
	return null

func _build_ground_and_roads():
	_add_box(Vector3(0.0, -0.34, 0.0), Vector3(70.0, 0.55, 70.0), Color(0.18, 0.36, 0.16), true)
	var road_positions = [-18.0, 0.0, 18.0]
	for road_pos in road_positions:
		_add_box(Vector3(road_pos, -0.045, 0.0), Vector3(6.8, 0.08, 64.0), Color(0.08, 0.09, 0.12), false)
		_add_box(Vector3(0.0, -0.04, road_pos), Vector3(64.0, 0.08, 6.8), Color(0.08, 0.09, 0.12), false)
		for mark in range(-29, 30, 8):
			_add_box(Vector3(road_pos, 0.015, float(mark)), Vector3(0.12, 0.02, 2.4), Color(0.95, 0.76, 0.18), false)
			_add_box(Vector3(float(mark), 0.02, road_pos), Vector3(2.4, 0.02, 0.12), Color(0.95, 0.76, 0.18), false)

func _build_city(building_resource):
	var placements = [
		Vector3(-10.5, 0.0, -10.5), Vector3(10.5, 0.0, -10.5),
		Vector3(-10.5, 0.0, 10.5), Vector3(10.5, 0.0, 10.5),
		Vector3(-27.0, 0.0, 27.0), Vector3(27.0, 0.0, -27.0)
	]
	var colors = [
		Color(0.42, 0.55, 0.72), Color(0.58, 0.45, 0.34), Color(0.42, 0.64, 0.52),
		Color(0.63, 0.5, 0.68), Color(0.38, 0.5, 0.6), Color(0.64, 0.58, 0.42)
	]
	for index in range(placements.size()):
		var height = 7.0 + float(index % 3) * 1.4
		if building_resource != null:
			_add_resource_prop(building_resource, placements[index], height, true, float(index) * 0.72, colors[index])
		else:
			_add_fallback_building(placements[index], height, colors[index])

func _build_actors(character_resource, car_resource):
	var player_resource = character_resource if character_resource != null else _fallback_character_mesh()
	var vehicle_resource = car_resource if car_resource != null else _fallback_car_mesh()

	player = PlayerScript.new()
	player.name = "Player"
	world_root.add_child(player)
	player.translation = Vector3(-4.0, 0.3, 7.0)
	player.setup_visual(player_resource)
	player.connect("health_changed", self, "_on_health_changed")
	player.connect("died", self, "_on_player_died")

	drive_car = CarScript.new()
	drive_car.name = "DriveCar"
	world_root.add_child(drive_car)
	drive_car.translation = Vector3(7.5, 0.3, 7.5)
	drive_car.rotation.y = -0.6
	drive_car.setup_visual(vehicle_resource, Color(0.88, 0.05, 0.03))

	for i in range(2):
		var enemy = EnemyScript.new()
		enemy.name = "Enemy_%d" % i
		world_root.add_child(enemy)
		enemy.translation = Vector3(-19.0 if i == 0 else 19.0, 0.3, -15.0 if i == 0 else 16.0)
		enemy.setup(player_resource, player)
		enemy.connect("defeated", self, "_on_enemy_defeated")
		enemies.append(enemy)

func _build_collectibles_and_checkpoint():
	var positions = [
		Vector3(-15.0, 1.0, -5.0), Vector3(-7.0, 1.0, 15.0),
		Vector3(10.0, 1.0, -15.0), Vector3(15.0, 1.0, 9.0)
	]
	for pos in positions:
		var area = Area.new()
		area.translation = pos
		area.collision_layer = 2
		area.collision_mask = 1
		var shape_node = CollisionShape.new()
		var sphere = SphereShape.new()
		sphere.radius = 0.68
		shape_node.shape = sphere
		area.add_child(shape_node)
		var mesh_node = MeshInstance.new()
		var crystal = PrismMesh.new()
		crystal.size = Vector3(0.68, 1.15, 0.68)
		mesh_node.mesh = crystal
		mesh_node.material_override = _flat_material(Color(0.05, 0.9, 1.0))
		mesh_node.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
		area.add_child(mesh_node)
		world_root.add_child(area)
		area.connect("body_entered", self, "_on_coin_body_entered", [area])
		coins.append(area)

	checkpoint = Area.new()
	checkpoint.translation = Vector3(28.0, 0.2, 28.0)
	var cp_shape_node = CollisionShape.new()
	var cp_shape = CylinderShape.new()
	cp_shape.radius = 3.5
	cp_shape.height = 1.0
	cp_shape_node.shape = cp_shape
	checkpoint.add_child(cp_shape_node)
	var ring = MeshInstance.new()
	var ring_mesh = CylinderMesh.new()
	ring_mesh.top_radius = 3.5
	ring_mesh.bottom_radius = 3.5
	ring_mesh.height = 0.10
	ring.mesh = ring_mesh
	ring.material_override = _flat_material(Color(0.08, 0.95, 0.2))
	ring.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
	checkpoint.add_child(ring)
	world_root.add_child(checkpoint)

func _physics_process(delta):
	_animate_collectibles(delta)
	if not game_started or game_paused or hud.mode != hud.MODE_PLAY:
		_update_camera(delta)
		return

	var move_input = hud.move_vector
	if Input.is_key_pressed(KEY_A):
		move_input.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		move_input.x += 1.0
	if Input.is_key_pressed(KEY_W):
		move_input.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		move_input.y += 1.0
	move_input = move_input.clamped(1.0)
	var jump = hud.consume_jump() or Input.is_key_pressed(KEY_SPACE)
	var sprint = hud.sprint_held or Input.is_key_pressed(KEY_SHIFT)
	var attack = hud.consume_attack() or Input.is_key_pressed(KEY_F)
	var interact = hud.consume_interact() or Input.is_key_pressed(KEY_E)
	var look = hud.consume_look()
	camera_yaw -= look.x * 0.0055
	camera_pitch = clamp(camera_pitch - look.y * 0.004, -0.65, 0.03)

	if in_vehicle:
		drive_car.tick(move_input, delta)
		hud.speed_kmh = int(abs(drive_car.current_speed) * 5.2)
	else:
		player.tick(move_input, camera_yaw, jump, sprint, delta)
		hud.speed_kmh = 0
	if attack and not in_vehicle:
		player.play_attack()
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

func _input(event):
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(BUTTON_RIGHT) and game_started and not game_paused:
		camera_yaw -= event.relative.x * 0.004
		camera_pitch = clamp(camera_pitch - event.relative.y * 0.003, -0.65, 0.03)

func _start_game():
	game_started = true
	game_paused = false
	hud.set_mode(hud.MODE_PLAY)

func _restart_game():
	get_tree().reload_current_scene()

func _toggle_pause():
	if not game_started:
		return
	game_paused = not game_paused
	hud.set_mode(hud.MODE_PAUSE if game_paused else hud.MODE_PLAY)

func _set_quality(_level):
	pass

func _toggle_vehicle():
	if in_vehicle:
		in_vehicle = false
		drive_car.set_controlled(false)
		player.global_transform.origin = drive_car.global_transform.origin + drive_car.global_transform.basis.x * 2.3 + Vector3.UP * 0.2
		player.set_active(true)
		hud.vehicle_mode = false
		return
	if player.global_transform.origin.distance_to(drive_car.global_transform.origin) < 3.4:
		in_vehicle = true
		player.set_active(false)
		drive_car.set_controlled(true)
		hud.vehicle_mode = true
		if mission_stage == 2:
			mission_stage = 3
			_update_mission()

func _attack_nearby():
	var best = null
	var best_distance = 3.1
	for enemy in enemies:
		if not is_instance_valid(enemy):
			continue
		var distance = player.global_transform.origin.distance_to(enemy.global_transform.origin)
		if distance < best_distance:
			best = enemy
			best_distance = distance
	if best:
		best.take_damage(50)

func _on_health_changed(value):
	hud.health = value

func _on_player_died():
	game_paused = true
	hud.set_mode(hud.MODE_LOSE)

func _on_enemy_defeated(enemy):
	enemies.erase(enemy)
	kill_count += 1
	hud.kills = kill_count
	player.heal(10)
	_check_mission_progress()

func _on_coin_body_entered(body, area):
	if body != player and body != drive_car:
		return
	if not is_instance_valid(area):
		return
	coins.erase(area)
	area.queue_free()
	coin_count += 1
	hud.coins = coin_count
	player.heal(5)
	_check_mission_progress()

func _check_mission_progress():
	if mission_stage == 0 and coin_count >= 3:
		mission_stage = 1
		_update_mission()
	elif mission_stage == 1 and kill_count >= 2:
		mission_stage = 2
		_update_mission()
	elif mission_stage == 3 and in_vehicle and drive_car.global_transform.origin.distance_to(checkpoint.global_transform.origin) < 4.8:
		mission_stage = 4
		_update_mission()
		game_paused = true
		hud.set_mode(hud.MODE_WIN)

func _update_mission():
	match mission_stage:
		0:
			hud.mission_text = "MISSION 1: CRYSTALS %d/3" % coin_count
		1:
			hud.mission_text = "MISSION 2: ENEMIES %d/2" % kill_count
		2:
			hud.mission_text = "MISSION 3: ENTER THE RED CAR"
		3:
			hud.mission_text = "MISSION 4: DRIVE TO GREEN ZONE"
		4:
			hud.mission_text = "ALL MISSIONS COMPLETE"

func _update_hint():
	if in_vehicle:
		hud.hint_text = "TAP CAR TO EXIT"
	elif player.global_transform.origin.distance_to(drive_car.global_transform.origin) < 4.2:
		hud.hint_text = "RED CAR NEARBY - TAP CAR"
	else:
		hud.hint_text = ""

func _update_camera(delta):
	var target_pos = Vector3.ZERO
	if in_vehicle and is_instance_valid(drive_car):
		target_pos = drive_car.global_transform.origin + Vector3.UP * 1.25
	elif is_instance_valid(player):
		target_pos = player.global_transform.origin + Vector3.UP * 1.42
	else:
		target_pos = Vector3(0.0, 3.0, 0.0)
	var distance = 7.4 if in_vehicle else 5.8
	var offset = Vector3(0.0, 0.0, distance)
	offset = offset.rotated(Vector3.RIGHT, camera_pitch)
	offset = offset.rotated(Vector3.UP, camera_yaw)
	var desired = target_pos + offset + Vector3.UP * (1.25 if in_vehicle else 0.72)
	var weight = 1.0 - exp(-6.5 * max(delta, 0.001))
	camera.translation = camera.translation.linear_interpolate(desired, weight)
	camera.look_at(target_pos, Vector3.UP)

func _animate_collectibles(delta):
	for coin in coins:
		if is_instance_valid(coin):
			coin.rotate_y(delta * 1.6)
			coin.translation.y = 1.0 + sin(OS.get_ticks_msec() * 0.003 + coin.translation.x) * 0.12
	if is_instance_valid(checkpoint):
		checkpoint.rotate_y(delta * 0.25)

func _add_resource_prop(resource, pos, target_height, collision, yaw, color):
	var visual = _create_visual(resource)
	if visual == null:
		_add_fallback_building(pos, target_height, color)
		return
	world_root.add_child(visual)
	visual.translation = pos
	visual.rotation.y = yaw
	_fit_visual(visual, target_height)
	_apply_flat_material(visual, color)
	if collision:
		var body = StaticBody.new()
		body.translation = pos + Vector3.UP * target_height * 0.44
		var shape_node = CollisionShape.new()
		var shape = BoxShape.new()
		shape.extents = Vector3(2.6, target_height * 0.44, 2.6)
		shape_node.shape = shape
		body.add_child(shape_node)
		world_root.add_child(body)

func _add_fallback_building(pos, height, color):
	_add_box(pos + Vector3.UP * height * 0.5, Vector3(5.0, height, 5.0), color, true)

func _add_box(pos, box_size, color, collision):
	var mesh_node = MeshInstance.new()
	var mesh = BoxMesh.new()
	mesh.size = box_size
	mesh_node.mesh = mesh
	mesh_node.translation = pos
	mesh_node.material_override = _flat_material(color)
	mesh_node.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
	world_root.add_child(mesh_node)
	if collision:
		var body = StaticBody.new()
		body.translation = pos
		var shape_node = CollisionShape.new()
		var shape = BoxShape.new()
		shape.extents = box_size * 0.5
		shape_node.shape = shape
		body.add_child(shape_node)
		world_root.add_child(body)
	return mesh_node

func _flat_material(color):
	var material = SpatialMaterial.new()
	material.albedo_color = color
	material.flags_unshaded = true
	return material

func _apply_flat_material(node, color):
	if node is MeshInstance:
		node.material_override = _flat_material(color)
		node.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
	for child in node.get_children():
		_apply_flat_material(child, color)

func _create_visual(resource):
	if resource is PackedScene:
		var instance = resource.instance()
		if instance is Spatial:
			return instance
		var wrap = Spatial.new()
		wrap.add_child(instance)
		return wrap
	if resource is Mesh:
		var mesh_node = MeshInstance.new()
		mesh_node.mesh = resource
		return mesh_node
	return null

func _fit_visual(node, target_height):
	var mesh_node = _find_mesh(node)
	if mesh_node and mesh_node.mesh:
		var box = mesh_node.mesh.get_aabb()
		var factor = target_height / max(box.size.y, 0.001)
		node.scale = Vector3.ONE * factor
		node.translation.y -= box.position.y * factor

func _find_mesh(node):
	if node is MeshInstance and node.mesh:
		return node
	for child in node.get_children():
		var found = _find_mesh(child)
		if found:
			return found
	return null

func _fallback_character_mesh():
	var mesh = CapsuleMesh.new()
	mesh.radius = 0.4
	mesh.mid_height = 0.9
	return mesh

func _fallback_car_mesh():
	var mesh = CubeMesh.new()
	mesh.size = Vector3(1.8, 1.0, 3.8)
	return mesh
