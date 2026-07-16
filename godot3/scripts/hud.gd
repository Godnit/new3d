extends Control

signal restart_requested
signal pause_requested

const MODE_PLAY = 1
const MODE_PAUSE = 2
const MODE_WIN = 3
const MODE_LOSE = 4

var mode = MODE_PLAY
var move_vector = Vector2.ZERO
var look_delta = Vector2.ZERO
var jump_queued = false
var attack_queued = false
var interact_queued = false
var sprint_held = false

var health = 100
var coins = 0
var kills = 0
var speed_kmh = 0
var mission_text = "MISSION: COLLECT 3 CRYSTALS"
var hint_text = ""
var vehicle_mode = false

var _left_touch = -1
var _look_touch = -1
var _stick_origin = Vector2.ZERO
var _stick_pos = Vector2.ZERO

func _ready():
	set_process_input(true)
	set_process(true)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	update()

func set_mode(value):
	mode = value
	move_vector = Vector2.ZERO
	_left_touch = -1
	_look_touch = -1
	update()

func consume_look():
	var value = look_delta
	look_delta = Vector2.ZERO
	return value

func consume_jump():
	var value = jump_queued
	jump_queued = false
	return value

func consume_attack():
	var value = attack_queued
	attack_queued = false
	return value

func consume_interact():
	var value = interact_queued
	interact_queued = false
	return value

func _process(_delta):
	update()

func _input(event):
	if event is InputEventKey and event.pressed and not event.echo:
		if event.scancode == KEY_ESCAPE and mode in [MODE_PLAY, MODE_PAUSE]:
			emit_signal("pause_requested")
		elif event.scancode == KEY_R and mode in [MODE_WIN, MODE_LOSE, MODE_PAUSE]:
			emit_signal("restart_requested")
		return

	if event is InputEventScreenTouch:
		_handle_touch(event.index, event.position, event.pressed)
	elif event is InputEventScreenDrag:
		_handle_drag(event.index, event.position, event.relative)

func _handle_touch(index, pos, pressed):
	if not pressed:
		if index == _left_touch:
			_left_touch = -1
			move_vector = Vector2.ZERO
		if index == _look_touch:
			_look_touch = -1
		sprint_held = false
		return

	if mode == MODE_PAUSE:
		if _resume_rect().has_point(pos):
			emit_signal("pause_requested")
		elif _restart_rect().has_point(pos):
			emit_signal("restart_requested")
		return
	if mode in [MODE_WIN, MODE_LOSE]:
		if _restart_rect().has_point(pos):
			emit_signal("restart_requested")
		return
	if mode != MODE_PLAY:
		return

	if _pause_rect().has_point(pos):
		emit_signal("pause_requested")
	elif _jump_rect().has_point(pos):
		jump_queued = true
	elif _attack_rect().has_point(pos):
		attack_queued = true
	elif _interact_rect().has_point(pos):
		interact_queued = true
	elif _sprint_rect().has_point(pos):
		sprint_held = true
	elif pos.x < rect_size.x * 0.46:
		_left_touch = index
		_stick_origin = pos
		_stick_pos = pos
		move_vector = Vector2.ZERO
	else:
		_look_touch = index

func _handle_drag(index, pos, relative):
	if mode != MODE_PLAY:
		return
	if index == _left_touch:
		_stick_pos = pos
		var delta = pos - _stick_origin
		if delta.length() > 76.0:
			delta = delta.normalized() * 76.0
			_stick_pos = _stick_origin + delta
		move_vector = delta / 76.0
	elif index == _look_touch:
		look_delta += relative

func _draw():
	var font = get_font("font")
	_draw_game(font)
	if mode == MODE_PAUSE:
		_draw_overlay(font, "PAUSED", "RESUME", Color(0.03, 0.07, 0.13, 0.96))
	elif mode == MODE_WIN:
		_draw_overlay(font, "MISSION COMPLETE", "PLAY AGAIN", Color(0.02, 0.12, 0.07, 0.96))
	elif mode == MODE_LOSE:
		_draw_overlay(font, "YOU LOST", "RETRY", Color(0.16, 0.03, 0.04, 0.96))

func _draw_game(font):
	_draw_panel(Rect2(16, 14, 255, 55), Color(0.02, 0.04, 0.08, 0.82), Color(0.1, 0.75, 1.0))
	var hp_width = 150.0 * clamp(float(health) / 100.0, 0.0, 1.0)
	draw_rect(Rect2(96, 31, 150, 17), Color(0.12, 0.12, 0.15, 0.9))
	draw_rect(Rect2(96, 31, hp_width, 17), Color(0.9, 0.12, 0.18, 0.95))
	draw_string(font, Vector2(28, 48), "HP %d" % health, Color.white)

	_draw_panel(Rect2(rect_size.x * 0.29, 14, rect_size.x * 0.45, 64), Color(0.02, 0.04, 0.08, 0.82), Color(0.15, 0.85, 0.55))
	_draw_centered(font, mission_text, 40, Color.white)
	_draw_centered(font, "CRYSTALS %d   ENEMIES %d" % [coins, kills], 62, Color(0.6, 1.0, 0.7))

	_draw_button(font, _pause_rect(), "II", Color(0.04, 0.09, 0.16, 0.9))
	if vehicle_mode:
		_draw_panel(Rect2(rect_size.x - 230, 14, 150, 55), Color(0.02, 0.04, 0.08, 0.82), Color(1.0, 0.6, 0.1))
		draw_string(font, Vector2(rect_size.x - 215, 48), "%d km/h" % speed_kmh, Color.white)

	var joy_center = _stick_origin if _left_touch >= 0 else Vector2(112, rect_size.y - 112)
	var knob_center = _stick_pos if _left_touch >= 0 else joy_center
	draw_circle(joy_center, 66, Color(0.03, 0.07, 0.12, 0.5))
	draw_arc(joy_center, 66, 0, PI * 2.0, 40, Color(0.2, 0.85, 1.0, 0.8), 3.0)
	draw_circle(knob_center, 30, Color(0.65, 0.9, 1.0, 0.7))

	_draw_round_action(font, _jump_rect(), "JUMP", Color(0.12, 0.45, 0.95, 0.76))
	_draw_round_action(font, _attack_rect(), "HIT", Color(0.9, 0.15, 0.16, 0.8))
	_draw_round_action(font, _interact_rect(), "CAR", Color(0.95, 0.55, 0.08, 0.8))
	_draw_round_action(font, _sprint_rect(), "RUN", Color(0.18, 0.75, 0.32, 0.76))

	if hint_text != "":
		_draw_panel(Rect2(rect_size.x * 0.31, rect_size.y - 58, rect_size.x * 0.38, 38), Color(0.02, 0.04, 0.08, 0.84), Color(1.0, 0.7, 0.15))
		_draw_centered(font, hint_text, rect_size.y - 34, Color.white)

func _draw_overlay(font, title, action, bg):
	draw_rect(Rect2(Vector2.ZERO, rect_size), Color(0, 0, 0, 0.52))
	var box = Rect2(rect_size.x * 0.25, rect_size.y * 0.22, rect_size.x * 0.5, rect_size.y * 0.52)
	_draw_panel(box, bg, Color(0.2, 0.85, 1.0))
	_draw_centered(font, title, box.position.y + 92, Color.white)
	_draw_button(font, _resume_rect() if mode == MODE_PAUSE else _restart_rect(), action, Color(0.08, 0.62, 0.28, 1.0))
	if mode == MODE_PAUSE:
		_draw_button(font, _restart_rect(), "RESTART", Color(0.55, 0.12, 0.13, 1.0))

func _draw_panel(rect, fill, border):
	draw_rect(rect, fill)
	draw_rect(rect, border, false, 2.0)

func _draw_button(font, rect, text, fill):
	draw_rect(rect, fill)
	draw_rect(rect, Color(0.35, 0.9, 1.0, 0.9), false, 2.0)
	var text_size = font.get_string_size(text)
	draw_string(font, Vector2(rect.position.x + (rect.size.x - text_size.x) * 0.5, rect.position.y + rect.size.y * 0.62), text, Color.white)

func _draw_round_action(font, rect, text, fill):
	var center = rect.position + rect.size * 0.5
	var radius = min(rect.size.x, rect.size.y) * 0.5
	draw_circle(center, radius, fill)
	draw_arc(center, radius, 0, PI * 2.0, 32, Color(0.8, 0.95, 1.0, 0.9), 2.0)
	var text_size = font.get_string_size(text)
	draw_string(font, center + Vector2(-text_size.x * 0.5, 5), text, Color.white)

func _draw_centered(font, text, y, color):
	var text_size = font.get_string_size(text)
	draw_string(font, Vector2((rect_size.x - text_size.x) * 0.5, y), text, color)

func _pause_rect():
	return Rect2(rect_size.x - 67, 14, 50, 50)

func _jump_rect():
	return Rect2(rect_size.x - 155, rect_size.y - 145, 78, 78)

func _attack_rect():
	return Rect2(rect_size.x - 105, rect_size.y - 245, 88, 88)

func _interact_rect():
	return Rect2(rect_size.x - 255, rect_size.y - 118, 72, 72)

func _sprint_rect():
	return Rect2(rect_size.x - 260, rect_size.y - 220, 70, 70)

func _resume_rect():
	return Rect2(rect_size.x * 0.37, rect_size.y * 0.48, rect_size.x * 0.26, 62)

func _restart_rect():
	return Rect2(rect_size.x * 0.37, rect_size.y * 0.63, rect_size.x * 0.26, 56)
