extends Node

func _ready():
	if OS.get_environment("CI") == "true":
		yield(get_tree().create_timer(3.0), "timeout")
		get_tree().quit()
