extends Node

const MODEL_PATH := "res://assets/user_city/scene.gltf"
const BUILDING_NAMES := ["House", "House_2", "House_3", "Shop"]
const MODEL_SCALE := 0.0068
const MODEL_OFFSET := Vector3(435.3885, 357.9440, 453.7738)

var host: Node
var city_root: Node3D
var model_root: Node3D
var buildings: Array[Node3D] = []
var base_scales: Array[Vector3] = []
var last_city := -1
var last_count := -1
var ready_ok := false

func _ready() -> void:
	call_deferred("_setup")

func _setup() -> void:
	await get_tree().process_frame
	host = get_parent()
	city_root = host.get("city_root") as Node3D
	if city_root == null:
		push_error("Sketchfab city: CityRoot was not created")
		return
	if not ResourceLoader.exists(MODEL_PATH):
		push_error("Sketchfab city model missing: " + MODEL_PATH)
		return
	var packed = load(MODEL_PATH)
	if not (packed is PackedScene):
		push_error("Sketchfab city model did not import as PackedScene")
		return
	model_root = packed.instantiate() as Node3D
	model_root.name = "SketchfabCity"
	city_root.add_child(model_root)
	model_root.scale = Vector3.ONE * MODEL_SCALE
	model_root.position = MODEL_OFFSET * MODEL_SCALE
	_disable_imported_cameras_and_lights(model_root)
	_hide_old_placeholder_city()
	_collect_buildings()
	ready_ok = buildings.size() > 0
	_sync(true)
	print("SKETCHFAB_CITY_READY buildings=", buildings.size())

func _hide_old_placeholder_city() -> void:
	for child in city_root.get_children():
		if child == model_root:
			continue
		if child is Node3D:
			(child as Node3D).visible = false

func _disable_imported_cameras_and_lights(node: Node) -> void:
	for child in node.get_children():
		if child is Camera3D or child is Light3D:
			child.queue_free()
		else:
			_disable_imported_cameras_and_lights(child)

func _collect_buildings() -> void:
	buildings.clear()
	base_scales.clear()
	for wanted in BUILDING_NAMES:
		var found := model_root.find_child(wanted, true, false)
		if found is Node3D:
			var n := found as Node3D
			buildings.append(n)
			base_scales.append(n.scale)
			n.visible = false

func _process(_delta: float) -> void:
	if not ready_ok or host == null:
		return
	_sync(false)

func _current_count() -> int:
	var state = host.get("state")
	var current_city := int(host.get("current_city"))
	if not (state is Dictionary):
		return 0
	if current_city == 0:
		return int(state.get("normal_houses", 0))
	return int(state.get("urgent_houses", 0))

func _sync(force: bool) -> void:
	var city := int(host.get("current_city"))
	var count := mini(_current_count(), buildings.size())
	if not force and city == last_city and count == last_count:
		return
	var city_changed := city != last_city
	if force or city_changed:
		for i in range(buildings.size()):
			buildings[i].scale = base_scales[i]
			buildings[i].visible = i < count
	else:
		if count > last_count:
			for i in range(last_count, count):
				_build_in(i)
		elif count < last_count:
			for i in range(count, last_count):
				_demolish(i)
	last_city = city
	last_count = count

func _build_in(index: int) -> void:
	if index < 0 or index >= buildings.size():
		return
	var b := buildings[index]
	b.visible = true
	b.scale = base_scales[index] * 0.04
	var tween := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(b, "scale", base_scales[index], 0.75)

func _demolish(index: int) -> void:
	if index < 0 or index >= buildings.size():
		return
	var b := buildings[index]
	if not b.visible:
		return
	var tween := create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_property(b, "scale", base_scales[index] * Vector3(1.15, 0.05, 1.15), 0.45)
	tween.tween_callback(func():
		b.visible = false
		b.scale = base_scales[index]
	)
