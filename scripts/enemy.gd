extends CharacterBody3D

signal defeated(enemy)

var target: CharacterBody3D
var health := 100
var attack_cooldown := 0.0
var visual_root: Node3D
var animation_player: AnimationPlayer
var active := true

func setup(resource: Resource, target_body: CharacterBody3D) -> void:
	target = target_body
	visual_root = _resource_to_node(resource)
	if visual_root:
		add_child(visual_root)
		visual_root.rotation.y = PI
		_fit_visual(visual_root, 1.7)
		_mark_enemy(visual_root)
		animation_player = _find_animation_player(visual_root)
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.36
	capsule.height = 1.6
	collider.shape = capsule
	collider.position.y = 0.82
	add_child(collider)

func tick(delta: float) -> void:
	if not active or target == null or not is_instance_valid(target):
		return
	attack_cooldown = maxf(0.0, attack_cooldown - delta)
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	var to_target := target.global_position - global_position
	var horizontal := Vector3(to_target.x, 0.0, to_target.z)
	var distance := horizontal.length()
	if distance < 28.0 and distance > 1.55:
		var dir := horizontal.normalized()
		velocity.x = move_toward(velocity.x, dir.x * 3.25, 10.0 * delta)
		velocity.z = move_toward(velocity.z, dir.z * 3.25, 10.0 * delta)
		rotation.y = lerp_angle(rotation.y, atan2(-dir.x, -dir.z), minf(1.0, 8.0 * delta))
		_play_named("walk")
	elif distance <= 1.8:
		velocity.x = move_toward(velocity.x, 0.0, 12.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 12.0 * delta)
		if attack_cooldown <= 0.0 and target.has_method("take_damage"):
			target.take_damage(12)
			attack_cooldown = 1.15
			_play_named("attack")
	else:
		velocity.x = move_toward(velocity.x, 0.0, 6.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 6.0 * delta)
		_play_named("idle")
	move_and_slide()

func take_damage(amount: int) -> void:
	if not active:
		return
	health -= amount
	if health <= 0:
		active = false
		defeated.emit(self)
		queue_free()

func _play_named(keyword: String) -> void:
	if animation_player == null:
		return
	for name in animation_player.get_animation_list():
		if keyword in String(name).to_lower():
			if animation_player.current_animation != String(name):
				animation_player.play(String(name), 0.15)
			return

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
		var factor := target_height / maxf(box.size.y, 0.001)
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

func _mark_enemy(node: Node) -> void:
	if node is MeshInstance3D:
		var overlay := StandardMaterial3D.new()
		overlay.albedo_color = Color(0.9, 0.04, 0.04, 0.22)
		overlay.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		node.material_overlay = overlay
	for child in node.get_children():
		_mark_enemy(child)
