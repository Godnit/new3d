extends KinematicBody

signal health_changed(value)
signal died

var health = 100
var can_control = true
var velocity = Vector3.ZERO
var visual_pivot = null
var visual_root = null
var animation_player = null
var move_amount = 0.0
var wobble_time = 0.0
var attack_lock = 0.0
var base_visual_scale = Vector3.ONE

func setup_visual(resource):
	visual_pivot = Spatial.new()
	visual_pivot.name = "WobblyVisualPivot"
	add_child(visual_pivot)
	visual_root = _resource_to_node(resource)
	if visual_root:
		visual_pivot.add_child(visual_root)
		visual_root.rotation.y = PI
		_fit_visual(visual_root, 1.78)
		base_visual_scale = visual_root.scale
		animation_player = _find_animation_player(visual_root)
		_apply_flat_material(visual_root, Color(0.12, 0.48, 1.0, 1.0))

	var collider = CollisionShape.new()
	var capsule = CapsuleShape.new()
	capsule.radius = 0.38
	capsule.height = 1.65
	collider.shape = capsule
	collider.translation.y = 0.84
	add_child(collider)

func tick(move_input, camera_yaw, jump_pressed, sprinting, delta):
	attack_lock = max(0.0, attack_lock - delta)
	if not can_control:
		velocity = Vector3.ZERO
		_update_wobble(delta, false)
		return

	if not is_on_floor():
		velocity.y -= 18.0 * delta
	elif jump_pressed:
		velocity.y = 7.0
		_play_any(["jump", "fall"])

	var forward = Vector3(-sin(camera_yaw), 0.0, -cos(camera_yaw))
	var right = Vector3(cos(camera_yaw), 0.0, -sin(camera_yaw))
	var direction = right * move_input.x + forward * (-move_input.y)
	if direction.length() > 1.0:
		direction = direction.normalized()
	var target_speed = 7.0 if sprinting else 4.6
	var target_velocity = direction * target_speed
	velocity.x = move_toward(velocity.x, target_velocity.x, 18.0 * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, 18.0 * delta)
	move_amount = Vector2(velocity.x, velocity.z).length()
	if direction.length() > 0.08:
		var target_angle = atan2(-direction.x, -direction.z)
		rotation.y = lerp_angle(rotation.y, target_angle, min(1.0, 9.0 * delta))
	velocity = move_and_slide(velocity, Vector3.UP, true, 4, 0.785398, false)
	_update_animation(sprinting)
	_update_wobble(delta, sprinting)

func play_attack():
	attack_lock = 0.42
	_play_any(["attack", "melee", "punch", "slash"])
	if visual_pivot:
		visual_pivot.rotation.x = -0.18

func take_damage(amount):
	if health <= 0:
		return
	health = max(0, health - amount)
	emit_signal("health_changed", health)
	if visual_pivot:
		visual_pivot.rotation.z = 0.22
	if health <= 0:
		emit_signal("died")

func heal(amount):
	health = min(100, health + amount)
	emit_signal("health_changed", health)

func set_active(value):
	can_control = value
	visible = value
	for child in get_children():
		if child is CollisionShape:
			child.set_deferred("disabled", not value)

func _update_animation(sprinting):
	if animation_player == null or attack_lock > 0.0:
		return
	if not is_on_floor():
		_play_any(["jump", "fall"])
	elif move_amount > 0.5:
		_play_any(["run", "sprint"] if sprinting else ["walk", "walking"])
	else:
		_play_any(["idle", "breathing"])

func _update_wobble(delta, sprinting):
	if visual_pivot == null or visual_root == null:
		return
	wobble_time += delta * (4.0 + move_amount * 0.8)
	var moving = clamp(move_amount / 5.0, 0.0, 1.0)
	var wobble = sin(wobble_time) * (0.025 + moving * 0.075)
	var forward_bob = cos(wobble_time * 0.5) * moving * 0.035
	visual_pivot.rotation.z = lerp(visual_pivot.rotation.z, wobble, min(1.0, delta * 9.0))
	visual_pivot.rotation.x = lerp(visual_pivot.rotation.x, forward_bob, min(1.0, delta * 8.0))
	visual_pivot.translation.y = sin(wobble_time * 2.0) * moving * (0.035 if sprinting else 0.022)
	var squash = abs(sin(wobble_time * 2.0)) * moving * 0.035
	visual_root.scale = base_visual_scale * Vector3(1.0 + squash, 1.0 - squash, 1.0 + squash)

func _play_any(keywords):
	if animation_player == null:
		return
	for keyword in keywords:
		for anim_name in animation_player.get_animation_list():
			if String(keyword).to_lower() in String(anim_name).to_lower():
				if animation_player.current_animation != String(anim_name):
					animation_player.play(String(anim_name), 0.13)
				return

func _resource_to_node(resource):
	if resource is PackedScene:
		var instance = resource.instance()
		if instance is Spatial:
			return instance
		var wrap = Spatial.new()
		wrap.add_child(instance)
		return wrap
	if resource is Mesh:
		var mesh_instance = MeshInstance.new()
		mesh_instance.mesh = resource
		return mesh_instance
	return null

func _fit_visual(node, target_height):
	var mesh_node = _find_mesh(node)
	if mesh_node and mesh_node.mesh:
		var box = mesh_node.mesh.get_aabb()
		var factor = target_height / max(box.size.y, 0.001)
		node.scale = Vector3.ONE * factor
		node.translation.y = -box.position.y * factor

func _find_mesh(node):
	if node is MeshInstance and node.mesh:
		return node
	for child in node.get_children():
		var found = _find_mesh(child)
		if found:
			return found
	return null

func _find_animation_player(node):
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found = _find_animation_player(child)
		if found:
			return found
	return null

func _apply_flat_material(node, color):
	if node is MeshInstance:
		var material = SpatialMaterial.new()
		material.albedo_color = color
		material.flags_unshaded = true
		node.material_override = material
		node.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
	for child in node.get_children():
		_apply_flat_material(child, color)
