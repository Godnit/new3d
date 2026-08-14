extends "res://terrain_editor_legacy.gd"

# Startup-safe override for old Android/GLES2 devices.
# Avoids querying a Control theme from the Spatial root during boot.
func _build_loading_ui():
	var layer = CanvasLayer.new()
	layer.name = "LoadingLayer"
	add_child(layer)

	loading_label = Label.new()
	loading_label.text = "Terrain Studio\nجارٍ تشغيل وضع التوافق..."
	loading_label.align = Label.ALIGN_CENTER
	loading_label.valign = Label.VALIGN_CENTER
	loading_label.anchor_right = 1.0
	loading_label.anchor_bottom = 1.0
	layer.add_child(loading_label)

# Restore synchronously so loading/undo never leaves an unfinished coroutine.
func _restore_objects(arr):
	for child in objects_root.get_children():
		objects_root.remove_child(child)
		child.free()

	for item in arr:
		var px = float(item["x"])
		var pz = float(item["z"])
		var p = Vector3(px, _terrain_height_at(px, pz), pz)
		if item["kind"] == "tree":
			_place_tree(p, int(item["variant"]))
		else:
			_place_rock(p, int(item["variant"]))
		var last = objects_root.get_child(objects_root.get_child_count() - 1)
		last.rotation.y = float(item["rot"])
