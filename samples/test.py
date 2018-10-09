import sys
sys.path.append("../src")
from tilengine import Engine, Window, Tilemap

engine = Engine.create(400, 240, 1, 0, 20)
engine.set_load_path("assets/sonic")
foreground = Tilemap.fromfile("Sonic_md_fg1.tmx")
engine.layers[0].setup(foreground)

window = Window.create()
while window.process():
	window.draw_frame()
