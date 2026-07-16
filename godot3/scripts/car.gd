extends KinematicBody

var controlled = false
var velocity = Vector3.ZERO
var current_speed = 0.0
var max_speed = 17.0
var visual_root = null

func setup_visual(resource, body_color = Color(0.88, 0.04, 0.03, 1.0)):
	visual_root = _resource_to_node(resource)
	if visual_root:
		add_child(visual_root)
		_fit_visual(visual_root, 1.5)
		_apply_flat_material(visual_root, body_color)

	var collider = CollisionShape.new()
	var shape = BoxShape.new()
	shape.extents = Vector3(0.93, 0.62, 2.05)
	collider.shape = shape
	collider.translation.y = 0.72
	add_child(collider)

func tick(move_input, delta):
	if not controlled:
		current_speed = move_toward(current_speed, 0.0, 4.0 * delta)
		velocity = Vector3.ZERO
		return

	var throttle = clamp(-move_input.y, -1.0, 1.0)
	var steering = clamp(move_input.x, -1.0, 1.0)
	var target_speed = throttle * max_speed
	current_speed = move_toward(current_speed, target_speed, 10.5 * delta)
	var steer_strength = 1.75 * clamp(abs(current_speed) / 5.0, 0.25, 1.0)
	var speed_sign = sign(current_speed) if abs(current_speed) > 0.1 else 1.0
	rotate_y(-steering * steer_strength * delta * speed_sign)
	var forward = -global_transform.basis.z
	velocity.x = forward.x * current_speed
	velocity.z = forward.z * current_speed
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	else:
		velocity.y = -0.3
	velocity = move_and_slide(velocity, Vector3.UP, true, 4, 0.785398, false)
	current_speed *= 0.995

func set_controlled(value):
	controlled = value

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

func _apply_flat_material(node, color):
	if node is MeshInstance:
		var material = SpatialMaterial.new()
		material.albedo_color = color
		material.flags_unshaded = true
		node.material_override = material
		node.cast_shadow = GeometryInstance.SHADOW_CASTING_SETTING_OFF
	for child in node.get_children():
		_apply_flat_material(child, color)
