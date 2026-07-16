extends CharacterBody3D

var controlled: bool = false
var current_speed: float = 0.0
var max_speed: float = 18.0
var visual_root: Node3D

func setup_visual(resource: Resource, body_color: Color = Color(0.78, 0.05, 0.04)) -> void:
	visual_root = _resource_to_node(resource)
	if visual_root:
		add_child(visual_root)
		_fit_visual(visual_root, 1.55)
		_tint_first_body(visual_root, body_color)
	var collider: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = Vector3(1.85, 1.25, 4.1)
	collider.shape = shape
	collider.position.y = 0.72
	add_child(collider)

func tick(move_input: Vector2, delta: float) -> void:
	if not controlled:
		current_speed = move_toward(current_speed, 0.0, 4.0 * delta)
		velocity = Vector3.ZERO
		return
	var throttle: float = clampf(-move_input.y, -1.0, 1.0)
	var steering: float = clampf(move_input.x, -1.0, 1.0)
	var target: float = throttle * max_speed
	current_speed = move_toward(current_speed, target, 11.0 * delta)
	var steer_strength: float = 1.8 * clampf(absf(current_speed) / 5.0, 0.25, 1.0)
	rotate_y(-steering * steer_strength * delta * signf(current_speed if absf(current_speed) > 0.1 else 1.0))
	var forward: Vector3 = -global_transform.basis.z
	velocity.x = forward.x * current_speed
	velocity.z = forward.z * current_speed
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	else:
		velocity.y = -0.3
	move_and_slide()
	current_speed *= 0.995

func set_controlled(value: bool) -> void:
	controlled = value

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

func _tint_first_body(node: Node, color: Color) -> void:
	if node is MeshInstance3D:
		var material: StandardMaterial3D = StandardMaterial3D.new()
		material.albedo_color = Color(color.r, color.g, color.b, 1.0)
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.vertex_color_use_as_albedo = false
		node.material_override = material
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child: Node in node.get_children():
		_tint_first_body(child, color)
