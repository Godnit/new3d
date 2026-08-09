extends Node3D

const SAVE_PATH := "user://task_city.json"
const NORMAL := 0
const URGENT := 1

var state := {
	"normal": [],
	"urgent": [],
	"normal_houses": 0,
	"urgent_houses": 0
}

var current_city := NORMAL
var current_screen := "city"
var task_filter := NORMAL
var city_root: Node3D
var houses_root: Node3D
var camera: Camera3D
var env: Environment
var ui_root: Control
var content_root: Control
var title_label: Label
var normal_city_button: Button
var urgent_city_button: Button
var task_list: VBoxContainer
var model_paths: Array[String] = []
var touches := {}
var last_pinch := 0.0
var camera_distance := 18.0
var last_timer_tick := 0

var green := Color("#20d69a")
var green_dark := Color("#10352f")
var purple := Color("#8d5cff")
var purple_dark := Color("#241b43")
var navy := Color("#08131f")
var panel := Color("#101e2d")
var muted := Color("#8ea0b5")

func _ready() -> void:
	load_state()
	check_expired_tasks(false)
	load_model_paths()
	build_world()
	build_ui()
	show_city_screen()
	print("TASKCITY_READY normal_houses=", state.normal_houses, " urgent_houses=", state.urgent_houses, " models=", model_paths.size())
	if OS.get_environment("TASKCITY_CAPTURE") == "1":
		await get_tree().create_timer(3.0).timeout
		var p := OS.get_environment("TASKCITY_CAPTURE_PATH")
		var image := get_viewport().get_texture().get_image()
		var e := image.save_png(p)
		print("TASKCITY_CAPTURED path=", p, " error=", e)

func _process(_delta: float) -> void:
	var now := int(Time.get_unix_time_from_system())
	if now != last_timer_tick:
		last_timer_tick = now
		var changed := check_expired_tasks(true)
		if current_screen == "tasks" and task_filter == URGENT:
			rebuild_task_list()
		if changed:
			render_houses(false)

func load_state() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if f == null:
		return
	var parsed = JSON.parse_string(f.get_as_text())
	if parsed is Dictionary:
		for k in state.keys():
			if parsed.has(k): state[k] = parsed[k]

func save_state() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(state))

func check_expired_tasks(save_changes: bool) -> bool:
	var now := int(Time.get_unix_time_from_system())
	var keep: Array = []
	var failures := 0
	for item in state.urgent:
		if int(item.get("deadline", now + 1)) <= now:
			failures += 1
		else:
			keep.append(item)
	if failures == 0:
		return false
	state.urgent = keep
	state.urgent_houses = max(0, int(state.urgent_houses) - failures)
	if save_changes: save_state()
	return true

func load_model_paths() -> void:
	model_paths.clear()
	scan_models("res://assets/city")

func scan_models(path: String) -> void:
	var d := DirAccess.open(path)
	if d == null: return
	d.list_dir_begin()
	while true:
		var n := d.get_next()
		if n == "": break
		if n.begins_with("."): continue
		var full := path.path_join(n)
		if d.current_is_dir():
			scan_models(full)
		elif n.get_extension().to_lower() == "obj":
			var low := n.to_lower()
			if "building" in low or "house" in low or "shop" in low or "skyscraper" in low:
				model_paths.append(full)
	d.list_dir_end()

func build_world() -> void:
	city_root = Node3D.new()
	city_root.name = "CityRoot"
	add_child(city_root)
	houses_root = Node3D.new()
	houses_root.name = "Houses"
	city_root.add_child(houses_root)

	var environment_node := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#071927")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#b6d5e8")
	env.ambient_light_energy = 0.75
	environment_node.environment = env
	add_child(environment_node)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52, -35, 0)
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	add_child(sun)

	camera = Camera3D.new()
	camera.fov = 38.0
	add_child(camera)
	update_camera()

	add_box(city_root, Vector3(0, -0.7, 0), Vector3(17, 1.2, 17), Color("#194d3b"), 0.5)
	add_box(city_root, Vector3(0, -0.03, 0), Vector3(16.2, 0.16, 16.2), Color("#286846"), 0.45)
	for x in [-4.8, 0.0, 4.8]:
		add_box(city_root, Vector3(x, 0.08, 0), Vector3(1.05, 0.1, 16), Color("#28323d"), 0.2)
	for z in [-4.8, 0.0, 4.8]:
		add_box(city_root, Vector3(0, 0.09, z), Vector3(16, 0.1, 1.05), Color("#28323d"), 0.2)
	for p in [Vector3(-7,0,7),Vector3(7,0,7),Vector3(-7,0,-7),Vector3(7,0,-7),Vector3(2.8,0,2.8),Vector3(-2.8,0,-2.8)]:
		add_tree(p)
	render_houses(false)

func add_box(parent: Node, pos: Vector3, size: Vector3, color: Color, roughness: float) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = roughness
	mesh.material = mat
	m.mesh = mesh
	m.position = pos
	parent.add_child(m)
	return m

func add_tree(pos: Vector3) -> void:
	var t := Node3D.new()
	t.position = pos
	city_root.add_child(t)
	add_box(t, Vector3(0,0.6,0), Vector3(0.35,1.2,0.35), Color("#71472d"), 1.0)
	var crown := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.8
	sph.height = 1.6
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("#2e985a")
	sph.material = mat
	crown.mesh = sph
	crown.position.y = 1.65
	t.add_child(crown)

func house_slots() -> Array[Vector3]:
	return [
		Vector3(-6.2,0.2,-6.2),Vector3(-2.6,0.2,-6.2),Vector3(2.6,0.2,-6.2),Vector3(6.2,0.2,-6.2),
		Vector3(-6.2,0.2,-2.6),Vector3(6.2,0.2,-2.6),Vector3(-6.2,0.2,2.6),Vector3(6.2,0.2,2.6),
		Vector3(-6.2,0.2,6.2),Vector3(-2.6,0.2,6.2),Vector3(2.6,0.2,6.2),Vector3(6.2,0.2,6.2),
		Vector3(-2.6,0.2,-2.6),Vector3(2.6,0.2,-2.6),Vector3(-2.6,0.2,2.6),Vector3(2.6,0.2,2.6)
	]

func render_houses(animate_last: bool) -> void:
	for c in houses_root.get_children(): c.queue_free()
	var count := int(state.normal_houses if current_city == NORMAL else state.urgent_houses)
	var slots := house_slots()
	for i in range(min(count, slots.size())):
		var h := make_house(i)
		h.position = slots[i]
		houses_root.add_child(h)
		if animate_last and i == count - 1:
			var target := h.scale
			h.scale = Vector3.ONE * 0.05
			var tw := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			tw.tween_property(h, "scale", target, 0.7)

func make_house(index: int) -> Node3D:
	if model_paths.size() > 0:
		var res = load(model_paths[index % model_paths.size()])
		if res is Mesh:
			var mi := MeshInstance3D.new()
			mi.mesh = res
			mi.scale = Vector3.ONE * 0.9
			mi.rotation_degrees.y = float((index * 90) % 360)
			return mi
	var h := Node3D.new()
	var colors := [Color("#eab66e"),Color("#74b9c6"),Color("#e58d75"),Color("#c3d06d")]
	add_box(h, Vector3(0,0.8,0), Vector3(1.8,1.6,1.6), colors[index % colors.size()], 0.7)
	var roof := MeshInstance3D.new()
	var prism := PrismMesh.new()
	prism.size = Vector3(2.15,0.8,1.9)
	var rm := StandardMaterial3D.new()
	rm.albedo_color = Color("#743d38")
	prism.material = rm
	roof.mesh = prism
	roof.position.y = 1.95
	roof.rotation_degrees.y = 90
	h.add_child(roof)
	add_box(h, Vector3(0,0.58,0.82), Vector3(0.48,0.86,0.08), Color("#6e4a31"), 0.8)
	return h

func update_camera() -> void:
	if camera == null: return
	var angle := city_root.rotation.y if city_root else -0.55
	camera.position = Vector3(sin(angle) * camera_distance, camera_distance * 0.72, cos(angle) * camera_distance)
	camera.look_at(Vector3(0,0.6,0), Vector3.UP)

func build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	ui_root = Control.new()
	ui_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui_root.layout_direction = Control.LAYOUT_DIRECTION_RTL
	layer.add_child(ui_root)
	var theme := Theme.new()
	if ResourceLoader.exists("res://assets/fonts/NotoSansArabic-Regular.ttf"):
		theme.default_font = load("res://assets/fonts/NotoSansArabic-Regular.ttf")
	theme.default_font_size = 24
	ui_root.theme = theme

	content_root = Control.new()
	content_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui_root.add_child(content_root)

	var top := PanelContainer.new()
	top.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top.offset_bottom = 178
	top.add_theme_stylebox_override("panel", style(navy, 0, 0))
	ui_root.add_child(top)
	var top_v := VBoxContainer.new()
	top_v.add_theme_constant_override("separation", 12)
	top.add_child(top_v)
	var spacer := Control.new(); spacer.custom_minimum_size.y = 18; top_v.add_child(spacer)
	title_label = Label.new()
	title_label.text = "مدينتي"
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.add_theme_font_size_override("font_size", 33)
	top_v.add_child(title_label)
	var toggles := HBoxContainer.new()
	toggles.alignment = BoxContainer.ALIGNMENT_CENTER
	toggles.add_theme_constant_override("separation", 12)
	top_v.add_child(toggles)
	normal_city_button = nav_card("مدينة الإنجاز", green)
	normal_city_button.custom_minimum_size = Vector2(250,72)
	normal_city_button.pressed.connect(func(): switch_city(NORMAL))
	toggles.add_child(normal_city_button)
	urgent_city_button = nav_card("مدينة التحدي", purple)
	urgent_city_button.custom_minimum_size = Vector2(250,72)
	urgent_city_button.pressed.connect(func(): switch_city(URGENT))
	toggles.add_child(urgent_city_button)

	var bottom := PanelContainer.new()
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_top = -104
	bottom.add_theme_stylebox_override("panel", style(Color("#0a1420"), 0, 0))
	ui_root.add_child(bottom)
	var bar := HBoxContainer.new()
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.add_theme_constant_override("separation", 18)
	bottom.add_child(bar)
	var tasks_btn := bottom_button("☑\nالمهام")
	tasks_btn.pressed.connect(show_tasks_screen)
	bar.add_child(tasks_btn)
	var city_btn := bottom_button("⌂\nالمدينة")
	city_btn.pressed.connect(show_city_screen)
	bar.add_child(city_btn)
	var settings_btn := bottom_button("⋯\nالمزيد")
	settings_btn.pressed.connect(show_info)
	bar.add_child(settings_btn)

func style(color: Color, radius: int = 20, border: int = 0, border_color: Color = Color.TRANSPARENT) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.corner_radius_top_left = radius; s.corner_radius_top_right = radius; s.corner_radius_bottom_left = radius; s.corner_radius_bottom_right = radius
	if border > 0:
		s.border_width_left = border; s.border_width_top = border; s.border_width_right = border; s.border_width_bottom = border
		s.border_color = border_color
	return s

func nav_card(text: String, color: Color) -> Button:
	var b := Button.new(); b.text = text
	b.add_theme_font_size_override("font_size", 24)
	b.add_theme_stylebox_override("normal", style(Color(color,0.22),18,2,Color(color,0.55)))
	b.add_theme_stylebox_override("hover", style(Color(color,0.32),18,2,color))
	b.add_theme_stylebox_override("pressed", style(Color(color,0.45),18,2,color))
	return b

func bottom_button(text: String) -> Button:
	var b := Button.new(); b.text = text; b.custom_minimum_size = Vector2(190,92)
	b.flat = true; b.add_theme_font_size_override("font_size",21)
	return b

func clear_content() -> void:
	for c in content_root.get_children(): c.queue_free()

func show_city_screen() -> void:
	current_screen = "city"
	clear_content()
	city_root.visible = true
	title_label.text = "مدينتي"
	var hint := Label.new()
	hint.text = "اسحب لتدوير المدينة  •  قرّب إصبعين للتكبير والتصغير"
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.add_theme_color_override("font_color", Color("#c6d1dd"))
	hint.add_theme_stylebox_override("normal", style(Color(0.02,0.06,0.09,0.72),18))
	hint.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	hint.offset_left = 70; hint.offset_right = -70; hint.offset_top = -165; hint.offset_bottom = -118
	content_root.add_child(hint)
	update_city_theme()

func show_tasks_screen() -> void:
	current_screen = "tasks"
	clear_content()
	city_root.visible = false
	title_label.text = "المهام"
	var page := VBoxContainer.new()
	page.position = Vector2(28,195); page.size = Vector2(664,970)
	page.add_theme_constant_override("separation",14)
	content_root.add_child(page)
	var tabs := HBoxContainer.new(); tabs.alignment = BoxContainer.ALIGNMENT_CENTER; tabs.add_theme_constant_override("separation",12); page.add_child(tabs)
	var n := nav_card("المهام العادية", green); n.custom_minimum_size=Vector2(300,66); n.pressed.connect(func(): task_filter=NORMAL; rebuild_task_list()); tabs.add_child(n)
	var u := nav_card("المهام الضرورية", purple); u.custom_minimum_size=Vector2(300,66); u.pressed.connect(func(): task_filter=URGENT; rebuild_task_list()); tabs.add_child(u)
	var scroll := ScrollContainer.new(); scroll.custom_minimum_size=Vector2(650,760); page.add_child(scroll)
	task_list = VBoxContainer.new(); task_list.custom_minimum_size.x=640; task_list.add_theme_constant_override("separation",12); scroll.add_child(task_list)
	var add := Button.new(); add.text="＋ إضافة مهمة"; add.custom_minimum_size=Vector2(650,72); add.add_theme_font_size_override("font_size",25)
	var accent := green if task_filter==NORMAL else purple
	add.add_theme_stylebox_override("normal",style(Color(accent,0.22),22,2,accent)); add.pressed.connect(open_add_task); page.add_child(add)
	rebuild_task_list()

func rebuild_task_list() -> void:
	if task_list == null or not is_instance_valid(task_list): return
	for c in task_list.get_children(): c.queue_free()
	var arr: Array = state.normal if task_filter == NORMAL else state.urgent
	if arr.is_empty():
		var empty := Label.new(); empty.text = "لا توجد مهام الآن\nأضف مهمتك الأولى من الزر بالأسفل"; empty.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; empty.add_theme_color_override("font_color",muted); empty.custom_minimum_size.y=180; task_list.add_child(empty); return
	for item in arr:
		task_list.add_child(task_card(item, task_filter))

func task_card(item: Dictionary, kind: int) -> Control:
	var p := PanelContainer.new(); p.custom_minimum_size=Vector2(630,112)
	var accent := green if kind==NORMAL else purple
	p.add_theme_stylebox_override("panel",style(Color("#0e1c2a"),20,2,Color(accent,0.55)))
	var row := HBoxContainer.new(); row.add_theme_constant_override("separation",16); p.add_child(row)
	var done := Button.new(); done.text="✓"; done.custom_minimum_size=Vector2(86,86); done.add_theme_font_size_override("font_size",35); done.add_theme_stylebox_override("normal",style(Color(accent,0.22),20,2,accent)); done.pressed.connect(func(): complete_task(int(item.id),kind)); row.add_child(done)
	var v := VBoxContainer.new(); v.size_flags_horizontal=Control.SIZE_EXPAND_FILL; row.add_child(v)
	var name := Label.new(); name.text=str(item.title); name.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT; name.add_theme_font_size_override("font_size",25); v.add_child(name)
	if kind==URGENT:
		var remain := max(0,int(item.deadline)-int(Time.get_unix_time_from_system())); var timer:=Label.new(); timer.text="الوقت المتبقي  " + format_time(remain); timer.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT; timer.add_theme_color_override("font_color",Color("#c6aaff")); v.add_child(timer)
	else:
		var sub:=Label.new(); sub.text="عند الإنجاز سيُبنى بيت جديد"; sub.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT; sub.add_theme_color_override("font_color",muted); v.add_child(sub)
	return p

func format_time(seconds: int) -> String:
	var h := seconds / 3600; var m := (seconds % 3600) / 60; var s := seconds % 60
	return "%02d:%02d:%02d" % [h,m,s]

func open_add_task() -> void:
	var overlay := ColorRect.new(); overlay.color=Color(0,0,0,0.72); overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); ui_root.add_child(overlay)
	var box := PanelContainer.new(); box.position=Vector2(45,330); box.size=Vector2(630,500 if task_filter==URGENT else 360); box.add_theme_stylebox_override("panel",style(Color("#101e2d"),28,2,green if task_filter==NORMAL else purple)); overlay.add_child(box)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation",20); box.add_child(v)
	var head:=Label.new(); head.text="إضافة مهمة " + ("عادية" if task_filter==NORMAL else "ضرورية"); head.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; head.add_theme_font_size_override("font_size",30); v.add_child(head)
	var edit:=LineEdit.new(); edit.placeholder_text="اكتب المهمة هنا..."; edit.custom_minimum_size.y=70; edit.alignment=HORIZONTAL_ALIGNMENT_RIGHT; v.add_child(edit)
	var slider: HSlider = null; var time_label: Label = null
	if task_filter==URGENT:
		time_label=Label.new(); time_label.text="المدة: ساعة واحدة"; time_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; v.add_child(time_label)
		slider=HSlider.new(); slider.min_value=1; slider.max_value=360; slider.step=1; slider.value=60; slider.custom_minimum_size.y=60; v.add_child(slider)
		slider.value_changed.connect(func(value): time_label.text="المدة: " + duration_label(int(value)))
	var buttons:=HBoxContainer.new(); buttons.alignment=BoxContainer.ALIGNMENT_CENTER; buttons.add_theme_constant_override("separation",16); v.add_child(buttons)
	var cancel:=Button.new(); cancel.text="إلغاء"; cancel.custom_minimum_size=Vector2(220,66); cancel.pressed.connect(func(): overlay.queue_free()); buttons.add_child(cancel)
	var save:=Button.new(); save.text="حفظ المهمة"; save.custom_minimum_size=Vector2(260,66); save.add_theme_stylebox_override("normal",style(Color(green if task_filter==NORMAL else purple,0.35),18)); save.pressed.connect(func():
		var text:=edit.text.strip_edges();
		if text.is_empty(): return
		add_task(text, int(slider.value) if slider else 0)
		overlay.queue_free()
	); buttons.add_child(save)
	edit.grab_focus()

func duration_label(minutes: int) -> String:
	if minutes < 60: return str(minutes) + " دقيقة"
	var h := minutes / 60; var m := minutes % 60
	return str(h) + " ساعة" + ((" و" + str(m) + " دقيقة") if m>0 else "")

func add_task(text: String, minutes: int) -> void:
	var id := int(Time.get_unix_time_from_system() * 1000.0) + randi_range(0,999)
	if task_filter==NORMAL:
		state.normal.append({"id":id,"title":text})
	else:
		state.urgent.append({"id":id,"title":text,"deadline":int(Time.get_unix_time_from_system()) + minutes*60})
	save_state(); rebuild_task_list()

func complete_task(id: int, kind: int) -> void:
	var arr: Array = state.normal if kind==NORMAL else state.urgent
	for i in range(arr.size()):
		if int(arr[i].id)==id:
			arr.remove_at(i); break
	if kind==NORMAL: state.normal_houses=int(state.normal_houses)+1
	else: state.urgent_houses=int(state.urgent_houses)+1
	save_state(); rebuild_task_list()
	current_city=kind; render_houses(true)

func switch_city(kind: int) -> void:
	current_city=kind; render_houses(false); update_city_theme()
	if current_screen!="city": show_city_screen()

func update_city_theme() -> void:
	if env==null: return
	if current_city==NORMAL:
		env.background_color=Color("#0a2833"); env.ambient_light_color=Color("#c7e8df"); env.ambient_light_energy=0.9
		normal_city_button.modulate=Color.WHITE; urgent_city_button.modulate=Color("#a7a9b8")
	else:
		env.background_color=Color("#100d2b"); env.ambient_light_color=Color("#9f8be8"); env.ambient_light_energy=0.72
		normal_city_button.modulate=Color("#a7a9b8"); urgent_city_button.modulate=Color.WHITE

func show_info() -> void:
	var overlay:=ColorRect.new(); overlay.color=Color(0,0,0,0.7); overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); ui_root.add_child(overlay)
	var p:=PanelContainer.new(); p.position=Vector2(70,430); p.size=Vector2(580,320); p.add_theme_stylebox_override("panel",style(panel,28)); overlay.add_child(p)
	var v:=VBoxContainer.new(); p.add_child(v)
	var l:=Label.new(); l.text="مدينة المهام\n\nأنجز مهمة = يُبنى بيت\nانتهاء مهمة ضرورية = يُهدم بيت من مدينة التحدي"; l.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; l.add_theme_font_size_override("font_size",24); v.add_child(l)
	var b:=Button.new(); b.text="إغلاق"; b.custom_minimum_size.y=64; b.pressed.connect(func(): overlay.queue_free()); v.add_child(b)

func _unhandled_input(event: InputEvent) -> void:
	if current_screen!="city": return
	if event is InputEventScreenTouch:
		if event.pressed: touches[event.index]=event.position
		else: touches.erase(event.index); last_pinch=0.0
	elif event is InputEventScreenDrag:
		touches[event.index]=event.position
		if touches.size()==1:
			city_root.rotation.y -= event.relative.x*0.006
		elif touches.size()>=2:
			var vals:=touches.values(); var dist:float=(vals[0] as Vector2).distance_to(vals[1] as Vector2)
			if last_pinch>0.0:
				camera_distance=clamp(camera_distance-(dist-last_pinch)*0.025,10.0,28.0)
			last_pinch=dist
		update_camera()
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		city_root.rotation.y -= event.relative.x*0.006; update_camera()
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_WHEEL_UP and event.pressed:
		camera_distance=max(10.0,camera_distance-1.0); update_camera()
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
		camera_distance=min(28.0,camera_distance+1.0); update_camera()
