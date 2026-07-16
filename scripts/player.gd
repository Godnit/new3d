extends CharacterBody3D

signal health_changed(value: int)
signal died

var health := 100
var can_control := true
var visual_root: Node3D
var animation_player: AnimationPlayer
var move_amount := 0.0

func setup_visual(resource: Resource) -> void:
	visual_root = _resource_to_node(resource)
	if visual_root:
		add_child(visual_root)
		visual_root.rotation.y = PI
		_fit_visual(visual_root, 1.75)
		animation_player = _find_animation_player(visual_root)

	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.38
	capsule.height = 1.65
	collider.shape = capsule
	collider.position.y = 0.84
	add_child(collider)

func tick(move_input: Vector2, camera_yaw: float, jump_pressed: bool, sprinting: bool, delta: float) -> void:
	if not can_control:
		velocity = Vector3.ZERO
		return
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	elif jump_pressed:
		velocity.y = 7.2

	var forward := Vector3(-sin(camera_yaw), 0.0, -cos(camera_yaw))
	var right := Vector3(cos(camera_yaw), 0.0, -sin(camera_yaw))
	var direction := right * move_input.x + forward * (-move_input.y)
	if direction.length() > 1.0:
		direction = direction.normalized()
	var target_speed := 8.5 if sprinting else 5.2
	var target_velocity := direction * target_speed
	velocity.x = move_toward(velocity.x, target_velocity.x, 22.0 * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, 22.0 * delta)
	move_amount = Vector2(velocity.x, velocity.z).length()
	if direction.length() > 0.08:
		var target_angle := atan2(-direction.x, -direction.z)
		rotation.y = lerp_angle(rotation.y, target_angle, minf(1.0, 11.0 * delta))
	move_and_slide()
	_update_animation(sprinting)

func take_damage(amount: int) -> void:
	if health <= 0:
		return
	health = maxi(0, health - amount)
	health_changed.emit(health)
	if health <= 0:
		died.emit()

func heal(amount: int) -> void:
	health = mini(100, health + amount)
	health_changed.emit(health)

func set_active(value: bool) -> void:
	can_control = value
	visible = value
	for child in get_children():
		if child is CollisionShape3D:
			child.set_deferred("disabled", not value)

func _update_animation(sprinting: bool) -> void:
	if animation_player == null:
		if visual_root:
			visual_root.position.y = sin(Time.get_ticks_msec() * 0.012) * 0.025 if move_amount > 0.4 else 0.0
		return
	var desired := "Idle"
	if move_amount > 0.5:
		desired = "Run" if sprinting else "Walk"
	var found := _find_animation_name(desired)
	if found != "" and animation_player.current_animation != found:
		animation_player.play(found, 0.18)

func _find_animation_name(keyword: String) -> String:
	if animation_player == null:
		return ""
	for name in animation_player.get_animation_list():
		if keyword.to_lower() in String(name).to_lower():
			return String(name)
	return ""

func _resource_to_node(resource: Resource) -> Node3D:
	if resource is PackedScene:
		var instance := resource.instantiate()
		if instance is Node3D:
			return instance
		var wrap := Node3D.new()
		wrap.add_child(instance)
		return wrap
	if resource is Mesh:
		var mesh_instance := MeshInstance3D.new()
		mesh_instance.mesh = resource
		return mesh_instance
	return null

func _fit_visual(node: Node3D, target_height: float) -> void:
	var mesh_node := _find_mesh(node)
	if mesh_node and mesh_node.mesh:
		var box := mesh_node.mesh.get_aabb()
		var height := maxf(box.size.y, 0.001)
		var factor := target_height / height
		node.scale = Vector3.ONE * factor
		node.position.y = -box.position.y * factor

func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D and node.mesh:
		return node
	for child in node.get_children():
		var found := _find_mesh(child)
		if found:
			return found
	return null

func _find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found := _find_animation_player(child)
		if found:
			return found
	return null
