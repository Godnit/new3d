extends CharacterBody3D

signal health_changed(value: int)
signal died

var health: int = 100
var can_control: bool = true
var visual_pivot: Node3D
var visual_root: Node3D
var animation_player: AnimationPlayer
var move_amount: float = 0.0
var wobble_time: float = 0.0
var attack_lock: float = 0.0
var base_visual_scale: Vector3 = Vector3.ONE

func setup_visual(resource: Resource) -> void:
	visual_pivot = Node3D.new()
	visual_pivot.name = "WobblyVisualPivot"
	add_child(visual_pivot)
	visual_root = _resource_to_node(resource)
	if visual_root:
		visual_pivot.add_child(visual_root)
		visual_root.rotation.y = PI
		_fit_visual(visual_root, 1.78)
		base_visual_scale = visual_root.scale
		animation_player = _find_animation_player(visual_root)
		_apply_team_tint(visual_root, Color(0.14, 0.48, 1.0, 1.0))

	var collider: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = 0.38
	capsule.height = 1.65
	collider.shape = capsule
	collider.position.y = 0.84
	add_child(collider)

func tick(move_input: Vector2, camera_yaw: float, jump_pressed: bool, sprinting: bool, delta: float) -> void:
	attack_lock = maxf(0.0, attack_lock - delta)
	if not can_control:
		velocity = Vector3.ZERO
		_update_wobble(delta, false)
		return
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	elif jump_pressed:
		velocity.y = 7.0
		_play_any(["jump", "fall"])

	var forward: Vector3 = Vector3(-sin(camera_yaw), 0.0, -cos(camera_yaw))
	var right: Vector3 = Vector3(cos(camera_yaw), 0.0, -sin(camera_yaw))
	var direction: Vector3 = right * move_input.x + forward * (-move_input.y)
	if direction.length() > 1.0:
		direction = direction.normalized()
	var target_speed: float = 7.2 if sprinting else 4.7
	var target_velocity: Vector3 = direction * target_speed
	velocity.x = move_toward(velocity.x, target_velocity.x, 18.0 * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, 18.0 * delta)
	move_amount = Vector2(velocity.x, velocity.z).length()
	if direction.length() > 0.08:
		var target_angle: float = atan2(-direction.x, -direction.z)
		rotation.y = lerp_angle(rotation.y, target_angle, minf(1.0, 9.0 * delta))
	move_and_slide()
	_update_animation(sprinting)
	_update_wobble(delta, sprinting)

func play_attack() -> void:
	attack_lock = 0.42
	_play_any(["attack", "melee", "chop", "punch", "slash"])
	if visual_pivot:
		visual_pivot.rotation.x = -0.18

func take_damage(amount: int) -> void:
	if health <= 0:
		return
	health = maxi(0, health - amount)
	health_changed.emit(health)
	if visual_pivot:
		visual_pivot.rotation.z = 0.22
	if health <= 0:
		died.emit()

func heal(amount: int) -> void:
	health = mini(100, health + amount)
	health_changed.emit(health)

func set_active(value: bool) -> void:
	can_control = value
	visible = value
	for child: Node in get_children():
		if child is CollisionShape3D:
			child.set_deferred("disabled", not value)

func _update_animation(sprinting: bool) -> void:
	if animation_player == null or attack_lock > 0.0:
		return
	if not is_on_floor():
		_play_any(["jump", "fall"])
	elif move_amount > 0.5:
		if sprinting:
			_play_any(["run", "running", "sprint"])
		else:
			_play_any(["walk", "walking"])
	else:
		_play_any(["idle", "breathing"])

func _update_wobble(delta: float, sprinting: bool) -> void:
	if visual_pivot == null or visual_root == null:
		return
	wobble_time += delta * (4.0 + move_amount * 0.8)
	var moving: float = clampf(move_amount / 5.0, 0.0, 1.0)
	var wobble: float = sin(wobble_time) * (0.025 + moving * 0.075)
	var forward_bob: float = cos(wobble_time * 0.5) * moving * 0.035
	visual_pivot.rotation.z = lerpf(visual_pivot.rotation.z, wobble, minf(1.0, delta * 9.0))
	visual_pivot.rotation.x = lerpf(visual_pivot.rotation.x, forward_bob, minf(1.0, delta * 8.0))
	visual_pivot.position.y = sin(wobble_time * 2.0) * moving * (0.035 if sprinting else 0.022)
	var squash: float = absf(sin(wobble_time * 2.0)) * moving * 0.035
	visual_root.scale = base_visual_scale * Vector3(1.0 + squash, 1.0 - squash, 1.0 + squash)

func _play_any(keywords: Array[String]) -> void:
	if animation_player == null:
		return
	for keyword: String in keywords:
		for anim_name: StringName in animation_player.get_animation_list():
			if keyword.to_lower() in String(anim_name).to_lower():
				if animation_player.current_animation != String(anim_name):
					animation_player.play(String(anim_name), 0.13)
				return

func _resource_to_node(resource: Resource) -> Node3D:
	if resource is PackedScene:
		var instance: Node = (resource as PackedScene).instantiate()
		if instance is Node3D:
			return instance
		var wrap: Node3D = Node3D.new()
		wrap.add_child(instance)
		return wrap
	if resource is Mesh:
		var mesh_instance: MeshInstance3D = MeshInstance3D.new()
		mesh_instance.mesh = resource
		return mesh_instance
	return null

func _fit_visual(node: Node3D, target_height: float) -> void:
	var mesh_node: MeshInstance3D = _find_mesh(node)
	if mesh_node and mesh_node.mesh:
		var box: AABB = mesh_node.mesh.get_aabb()
		var height: float = maxf(box.size.y, 0.001)
		var factor: float = target_height / height
		node.scale = Vector3.ONE * factor
		node.position.y = -box.position.y * factor

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D and node.mesh:
		return node
	for child: Node in node.get_children():
		var found: MeshInstance3D = _find_mesh(child)
		if found:
			return found
	return null

func _find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child: Node in node.get_children():
		var found: AnimationPlayer = _find_animation_player(child)
		if found:
			return found
	return null

func _apply_team_tint(node: Node, tint: Color) -> void:
	if node is MeshInstance3D:
		var material: StandardMaterial3D = StandardMaterial3D.new()
		material.albedo_color = tint
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.vertex_color_use_as_albedo = false
		node.material_override = material
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child: Node in node.get_children():
		_apply_team_tint(child, tint)
