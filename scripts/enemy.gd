extends CharacterBody3D

signal defeated(enemy)

var target: CharacterBody3D
var health: int = 100
var attack_cooldown: float = 0.0
var visual_pivot: Node3D
var visual_root: Node3D
var animation_player: AnimationPlayer
var active: bool = true
var wobble_time: float = 0.0
var base_visual_scale: Vector3 = Vector3.ONE

func setup(resource: Resource, target_body: CharacterBody3D) -> void:
	target = target_body
	visual_pivot = Node3D.new()
	visual_pivot.name = "EnemyWobble"
	add_child(visual_pivot)
	visual_root = _resource_to_node(resource)
	if visual_root:
		visual_pivot.add_child(visual_root)
		visual_root.rotation.y = PI
		_fit_visual(visual_root, 1.72)
		base_visual_scale = visual_root.scale
		_mark_enemy(visual_root)
		animation_player = _find_animation_player(visual_root)
	var collider: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
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
	var to_target: Vector3 = target.global_position - global_position
	var horizontal: Vector3 = Vector3(to_target.x, 0.0, to_target.z)
	var distance: float = horizontal.length()
	var moving: bool = false
	if distance < 24.0 and distance > 1.55:
		var direction: Vector3 = horizontal.normalized()
		velocity.x = move_toward(velocity.x, direction.x * 2.75, 8.5 * delta)
		velocity.z = move_toward(velocity.z, direction.z * 2.75, 8.5 * delta)
		rotation.y = lerp_angle(rotation.y, atan2(-direction.x, -direction.z), minf(1.0, 7.0 * delta))
		_play_any(["walk", "walking", "run"])
		moving = true
	elif distance <= 1.8:
		velocity.x = move_toward(velocity.x, 0.0, 10.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 10.0 * delta)
		if attack_cooldown <= 0.0 and target.has_method("take_damage"):
			target.take_damage(10)
			attack_cooldown = 1.25
			_play_any(["attack", "melee", "chop", "punch"])
			if visual_pivot:
				visual_pivot.rotation.x = -0.2
	else:
		velocity.x = move_toward(velocity.x, 0.0, 5.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 5.0 * delta)
		_play_any(["idle", "breathing"])
	move_and_slide()
	_update_wobble(delta, moving)

func take_damage(amount: int) -> void:
	if not active:
		return
	health -= amount
	if visual_pivot:
		visual_pivot.rotation.z = -0.28
	if health <= 0:
		active = false
		defeated.emit(self)
		queue_free()

func _update_wobble(delta: float, moving: bool) -> void:
	if visual_pivot == null or visual_root == null:
		return
	wobble_time += delta * (5.5 if moving else 2.2)
	var amount: float = 0.08 if moving else 0.025
	visual_pivot.rotation.z = lerpf(visual_pivot.rotation.z, sin(wobble_time) * amount, minf(1.0, delta * 7.0))
	visual_pivot.rotation.x = lerpf(visual_pivot.rotation.x, cos(wobble_time * 0.55) * amount * 0.45, minf(1.0, delta * 7.0))
	visual_pivot.position.y = absf(sin(wobble_time * 1.7)) * (0.035 if moving else 0.008)
	var squash: float = absf(sin(wobble_time * 1.7)) * (0.035 if moving else 0.012)
	visual_root.scale = base_visual_scale * Vector3(1.0 + squash, 1.0 - squash, 1.0 + squash)

func _play_any(keywords: Array[String]) -> void:
	if animation_player == null:
		return
	for keyword: String in keywords:
		for anim_name: StringName in animation_player.get_animation_list():
			if keyword.to_lower() in String(anim_name).to_lower():
				if animation_player.current_animation != String(anim_name):
					animation_player.play(String(anim_name), 0.14)
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
		var factor: float = target_height / maxf(box.size.y, 0.001)
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

func _mark_enemy(node: Node) -> void:
	if node is MeshInstance3D:
		var material: StandardMaterial3D = StandardMaterial3D.new()
		material.albedo_color = Color(0.92, 0.09, 0.12, 1.0)
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.vertex_color_use_as_albedo = false
		node.material_override = material
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child: Node in node.get_children():
		_mark_enemy(child)
