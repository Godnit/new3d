extends Control

signal start_requested
signal restart_requested
signal pause_requested
signal quality_requested(level: int)

const MODE_MENU := 0
const MODE_PLAY := 1
const MODE_PAUSE := 2
const MODE_WIN := 3
const MODE_LOSE := 4

var mode: int = MODE_MENU
var move_vector := Vector2.ZERO
var look_delta := Vector2.ZERO
var jump_queued := false
var attack_queued := false
var interact_queued := false
var sprint_held := false

var health := 100
var coins := 0
var kills := 0
var speed_kmh := 0
var mission_text := "اجمع البلورات المنتشرة في المدينة"
var hint_text := ""
var vehicle_mode := false
var quality_level := 1
var loading_text := "جاري تجهيز المدينة والنماذج ثلاثية الأبعاد..."
var assets_ready := false

var _left_touch := -1
var _look_touch := -1
var _stick_origin := Vector2.ZERO
var _stick_pos := Vector2.ZERO

func _ready() -> void:
	set_process_input(true)
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	queue_redraw()

func set_mode(value: int) -> void:
	mode = value
	move_vector = Vector2.ZERO
	_left_touch = -1
	_look_touch = -1
	queue_redraw()

func consume_look() -> Vector2:
	var value := look_delta
	look_delta = Vector2.ZERO
	return value

func consume_jump() -> bool:
	var value := jump_queued
	jump_queued = false
	return value

func consume_attack() -> bool:
	var value := attack_queued
	attack_queued = false
	return value

func consume_interact() -> bool:
	var value := interact_queued
	interact_queued = false
	return value

func _process(_delta: float) -> void:
	queue_redraw()

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ENTER and mode == MODE_MENU and assets_ready:
			start_requested.emit()
		elif event.keycode == KEY_ESCAPE and mode in [MODE_PLAY, MODE_PAUSE]:
			pause_requested.emit()
		elif event.keycode == KEY_R and mode in [MODE_WIN, MODE_LOSE, MODE_PAUSE]:
			restart_requested.emit()
		return

	if event is InputEventScreenTouch:
		_handle_touch(event.index, event.position, event.pressed)
	elif event is InputEventScreenDrag:
		_handle_drag(event.index, event.position, event.relative)

func _handle_touch(index: int, pos: Vector2, pressed: bool) -> void:
	if not pressed:
		if index == _left_touch:
			_left_touch = -1
			move_vector = Vector2.ZERO
		if index == _look_touch:
			_look_touch = -1
		sprint_held = false
		return

	if mode == MODE_MENU:
		if assets_ready and _start_rect().has_point(pos):
			start_requested.emit()
		elif _quality_rect().has_point(pos):
			quality_level = (quality_level + 1) % 3
			quality_requested.emit(quality_level)
		return
	if mode == MODE_PAUSE:
		if _resume_rect().has_point(pos):
			pause_requested.emit()
		elif _restart_rect().has_point(pos):
			restart_requested.emit()
		return
	if mode in [MODE_WIN, MODE_LOSE]:
		if _restart_rect().has_point(pos):
			restart_requested.emit()
		return
	if mode != MODE_PLAY:
		return

	if _pause_rect().has_point(pos):
		pause_requested.emit()
	elif _jump_rect().has_point(pos):
		jump_queued = true
	elif _attack_rect().has_point(pos):
		attack_queued = true
	elif _interact_rect().has_point(pos):
		interact_queued = true
	elif _sprint_rect().has_point(pos):
		sprint_held = true
	elif pos.x < size.x * 0.46:
		_left_touch = index
		_stick_origin = pos
		_stick_pos = pos
		move_vector = Vector2.ZERO
	else:
		_look_touch = index

func _handle_drag(index: int, pos: Vector2, relative: Vector2) -> void:
	if mode != MODE_PLAY:
		return
	if index == _left_touch:
		_stick_pos = pos
		var delta := pos - _stick_origin
		if delta.length() > 85.0:
			delta = delta.normalized() * 85.0
			_stick_pos = _stick_origin + delta
		move_vector = delta / 85.0
	elif index == _look_touch:
		look_delta += relative

func _draw() -> void:
	var font := get_theme_default_font()
	if mode == MODE_MENU:
		_draw_menu(font)
	elif mode == MODE_PLAY:
		_draw_game(font)
	elif mode == MODE_PAUSE:
		_draw_game(font)
		_draw_overlay(font, "متوقف مؤقتًا", "متابعة", Color(0.05, 0.09, 0.16, 0.95))
	elif mode == MODE_WIN:
		_draw_overlay(font, "أحسنت! أنهيت مهمة المدينة", "العب مجددًا", Color(0.02, 0.12, 0.08, 0.95))
	elif mode == MODE_LOSE:
		_draw_overlay(font, "انتهت طاقتك", "إعادة المحاولة", Color(0.16, 0.035, 0.04, 0.95))

func _draw_menu(font: Font) -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.015, 0.028, 0.055, 1.0))
	for i in range(18):
		var x := fmod(float(i * 173 + 91), maxf(size.x, 1.0))
		var y := fmod(float(i * 97 + 41), maxf(size.y * 0.62, 1.0))
		draw_circle(Vector2(x, y), 2.0 + float(i % 3), Color(0.2, 0.75, 1.0, 0.5))
	_draw_centered(font, "CITY QUEST 3D", 90.0, 52, Color(0.55, 0.95, 1.0))
	_draw_centered(font, "مدينة مفتوحة • شخصيات • سيارات • مهام", 142.0, 25, Color.WHITE)
	_draw_panel(Rect2(size.x * 0.13, size.y * 0.29, size.x * 0.74, size.y * 0.27), Color(0.025, 0.07, 0.12, 0.94), Color(0.1, 0.75, 1.0))
	_draw_centered(font, "تحرك في المدينة، اجمع البلورات، اهزم الأعداء ثم قد السيارة إلى نقطة النهاية", size.y * 0.37, 23, Color(0.92, 0.97, 1.0))
	_draw_centered(font, "اللعبة تعمل دون إنترنت بعد التثبيت", size.y * 0.44, 21, Color(0.55, 1.0, 0.55))
	if assets_ready:
		_draw_button(font, _start_rect(), "ابدأ اللعب", Color(0.08, 0.65, 0.28, 1.0), 28)
	else:
		_draw_button(font, _start_rect(), "جاري التحميل...", Color(0.25, 0.3, 0.36, 1.0), 25)
		_draw_centered(font, loading_text, size.y * 0.77, 18, Color(0.7, 0.85, 1.0))
	var q_names := ["اقتصادية", "متوازنة", "عالية"]
	_draw_button(font, _quality_rect(), "الجودة: " + q_names[quality_level], Color(0.07, 0.18, 0.3, 1.0), 20)

func _draw_game(font: Font) -> void:
	_draw_panel(Rect2(18, 16, 310, 62), Color(0.02, 0.04, 0.08, 0.82), Color(0.1, 0.75, 1.0))
	var hp_width := 190.0 * clampf(float(health) / 100.0, 0.0, 1.0)
	draw_rect(Rect2(105, 34, 190, 20), Color(0.12, 0.12, 0.15, 0.9))
	draw_rect(Rect2(105, 34, hp_width, 20), Color(0.9, 0.12, 0.18, 0.95))
	draw_string(font, Vector2(32, 56), "HP %d" % health, HORIZONTAL_ALIGNMENT_LEFT, 80, 20, Color.WHITE)

	_draw_panel(Rect2(size.x * 0.32, 16, size.x * 0.43, 74), Color(0.02, 0.04, 0.08, 0.82), Color(0.15, 0.85, 0.55))
	_draw_centered(font, mission_text, 47, 19, Color.WHITE)
	_draw_centered(font, "بلورات %d   •   أعداء %d" % [coins, kills], 75, 17, Color(0.6, 1.0, 0.7))

	_draw_button(font, _pause_rect(), "II", Color(0.04, 0.09, 0.16, 0.9), 24)
	if vehicle_mode:
		_draw_panel(Rect2(size.x * 0.77, 18, 125, 58), Color(0.02, 0.04, 0.08, 0.82), Color(1.0, 0.6, 0.1))
		draw_string(font, Vector2(size.x * 0.785, 54), "%d km/h" % speed_kmh, HORIZONTAL_ALIGNMENT_LEFT, 110, 20, Color.WHITE)

	var joy_center := _stick_origin if _left_touch >= 0 else Vector2(120, size.y - 125)
	var knob_center := _stick_pos if _left_touch >= 0 else joy_center
	draw_circle(joy_center, 73, Color(0.03, 0.07, 0.12, 0.48))
	draw_arc(joy_center, 73, 0, TAU, 48, Color(0.2, 0.85, 1.0, 0.75), 3.0)
	draw_circle(knob_center, 33, Color(0.65, 0.9, 1.0, 0.65))
	_draw_round_action(font, _jump_rect(), "قفز", Color(0.12, 0.45, 0.95, 0.72))
	_draw_round_action(font, _attack_rect(), "هجوم", Color(0.9, 0.15, 0.16, 0.76))
	_draw_round_action(font, _interact_rect(), "ركوب", Color(0.95, 0.55, 0.08, 0.76))
	_draw_round_action(font, _sprint_rect(), "سرعة", Color(0.18, 0.75, 0.32, 0.72))
	if hint_text != "":
		_draw_panel(Rect2(size.x * 0.29, size.y - 75, size.x * 0.42, 48), Color(0.02, 0.04, 0.08, 0.82), Color(1.0, 0.7, 0.15))
		_draw_centered(font, hint_text, size.y - 43, 18, Color.WHITE)

func _draw_overlay(font: Font, title: String, action: String, bg: Color) -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.48))
	var box := Rect2(size.x * 0.25, size.y * 0.24, size.x * 0.5, size.y * 0.5)
	_draw_panel(box, bg, Color(0.2, 0.85, 1.0))
	_draw_centered(font, title, box.position.y + 95, 34, Color.WHITE)
	_draw_button(font, _resume_rect() if mode == MODE_PAUSE else _restart_rect(), action, Color(0.08, 0.62, 0.28, 1.0), 25)
	if mode == MODE_PAUSE:
		_draw_button(font, _restart_rect(), "إعادة المهمة", Color(0.55, 0.12, 0.13, 1.0), 21)

func _draw_panel(rect: Rect2, fill: Color, border: Color) -> void:
	draw_rect(rect, fill)
	draw_rect(rect, border, false, 2.0)

func _draw_button(font: Font, rect: Rect2, text: String, fill: Color, font_size: int) -> void:
	draw_rect(rect, fill)
	draw_rect(rect, Color(0.35, 0.9, 1.0, 0.9), false, 2.0)
	draw_string(font, Vector2(rect.position.x, rect.position.y + rect.size.y * 0.65), text, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, font_size, Color.WHITE)

func _draw_round_action(font: Font, rect: Rect2, text: String, fill: Color) -> void:
	var center := rect.get_center()
	var radius := minf(rect.size.x, rect.size.y) * 0.5
	draw_circle(center, radius, fill)
	draw_arc(center, radius, 0, TAU, 40, Color.WHITE, 2.0)
	draw_string(font, Vector2(rect.position.x, center.y + 7), text, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, 18, Color.WHITE)

func _draw_centered(font: Font, text: String, y: float, font_size: int, color: Color) -> void:
	draw_string(font, Vector2(0, y), text, HORIZONTAL_ALIGNMENT_CENTER, size.x, font_size, color)

func _start_rect() -> Rect2:
	return Rect2(size.x * 0.34, size.y * 0.6, size.x * 0.32, 72)
func _quality_rect() -> Rect2:
	return Rect2(size.x * 0.38, size.y * 0.84, size.x * 0.24, 50)
func _pause_rect() -> Rect2:
	return Rect2(size.x - 76, 18, 56, 56)
func _jump_rect() -> Rect2:
	return Rect2(size.x - 235, size.y - 205, 78, 78)
func _attack_rect() -> Rect2:
	return Rect2(size.x - 135, size.y - 145, 94, 94)
func _interact_rect() -> Rect2:
	return Rect2(size.x - 330, size.y - 115, 72, 72)
func _sprint_rect() -> Rect2:
	return Rect2(size.x - 235, size.y - 105, 70, 70)
func _resume_rect() -> Rect2:
	return Rect2(size.x * 0.36, size.y * 0.49, size.x * 0.28, 62)
func _restart_rect() -> Rect2:
	var y := size.y * 0.61 if mode == MODE_PAUSE else size.y * 0.55
	return Rect2(size.x * 0.36, y, size.x * 0.28, 58)
