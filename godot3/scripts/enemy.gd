extends KinematicBody

signal defeated(enemy)

var target = null
var health = 100
var velocity = Vector3.ZERO
var attack_cooldown = 0.0
var visual_pivot = null
var visual_root = null
var active = true
var wobble_time = 0.0
var base_visual_scale = Vector3.ONE

func setup(resource, target_body):
	target = target_body
	visual_pivot = Spatial.new()
	visual_pivot.name = "EnemyWobble"
	add_child(visual_pivot)
	visual_root = _resource_to_node(resource)
	if visual_root:
		visual_pivot.add_child(visual_root)
		visual_root.rotation.y = PI
		_fit_visual(visual_root, 1.72)
		base_visual_scale = visual_root.scale
		_apply_flat_material(visual_root, Color(0.94, 0.08, 0.12, 1.0))

	var collider = CollisionShape.new()
	var capsule = CapsuleShape.new()
	capsule.radius = 0.36
	capsule.height = 1.6
	collider.shape = capsule
	collider.translation.y = 0.82
	add_child(collider)

func tick(delta):
	if not active or target == null or not is_instance_valid(target):
		return
	attack_cooldown = max(0.0, attack_cooldown - delta)
	if not is_on_floor():
		velocity.y -= 18.0 * delta

	var to_target = target.global_transform.origin - global_transform.origin
	var horizontal = Vector3(to_target.x, 0.0, to_target.z)
	var distance = horizontal.length()
	var moving = false
	if distance < 22.0 and distance > 1.55:
		var direction = horizontal.normalized()
		velocity.x = move_toward(velocity.x, direction.x * 2.6, 8.0 * delta)
		velocity.z = move_toward(velocity.z, direction.z * 2.6, 8.0 * delta)
		rotation.y = lerp_angle(rotation.y, atan2(-direction.x, -direction.z), min(1.0, 7.0 * delta))
		moving = true
	elif distance <= 1.8:
		velocity.x = move_toward(velocity.x, 0.0, 10.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 10.0 * delta)
		if attack_cooldown <= 0.0 and target.has_method("take_damage"):
			target.take_damage(10)
			attack_cooldown = 1.25
			if visual_pivot:
				visual_pivot.rotation.x = -0.2
	else:
		velocity.x = move_toward(velocity.x, 0.0, 5.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, 5.0 * delta)

	velocity = move_and_slide(velocity, Vector3.UP, true, 4, 0.785398, false)
	_update_wobble(delta, moving)

func take_damage(amount):
	if not active:
		return
	health -= amount
	if visual_pivot:
		visual_pivot.rotation.z = -0.28
	if health <= 0:
		active = false
		emit_signal("defeated", self)
		queue_free()

func _update_wobble(delta, moving):
	if visual_pivot == null or visual_root == null:
		return
	wobble_time += delta * (5.5 if moving else 2.2)
	var amount = 0.08 if moving else 0.025
	visual_pivot.rotation.z = lerp(visual_pivot.rotation.z, sin(wobble_time) * amount, min(1.0, delta * 7.0))
	visual_pivot.rotation.x = lerp(visual_pivot.rotation.x, cos(wobble_time * 0.55) * amount * 0.45, min(1.0, delta * 7.0))
	visual_pivot.translation.y = abs(sin(wobble_time * 1.7)) * (0.035 if moving else 0.008)
	var squash = abs(sin(wobble_time * 1.7)) * (0.035 if moving else 0.012)
	visual_root.scale = base_visual_scale * Vector3(1.0 + squash, 1.0 - squash, 1.0 + squash)

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
