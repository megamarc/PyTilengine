![Tilengine logo](Tilengine.png)
# PyTilengine
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## About PyTilengine
PyTilengine is the Python binding for Tilengine. It is not a direct 1:1 API translation of the original C library, but it uses familiar Python constructions as classes, lists, etc, and has its own documentation.

## Contents
* */src* directory contains the single `tilengine.py` module with the binding itself
* */samples* directory contains various examples ready to run and test
* */doc* directory contains the source files for the sphinx documentation tool

## Prerequisites
Tilengine native shared library must be installed separately. Please refer to https://github.com/megamarc/Tilengine about how to do it.

## Installation
No install step is required. Just make sure that the Tilengine library and the `tilengine.py` modules are accessible from within your own project

## Documentation
Online version of the generated docs can be found in the following address:
http://www.tilengine.org/doc_python/

## Basic program
The following program does these actions:
1. Import required classes from tilengine binding
2. Initialize the engine with a resolution of 400x240, one layer, no sprites and 20 animation slots
3. Set the loading path to the assets folder
4. Load a *tilemap*, the asset that contains background layer data
5. Attach the loaded tilemap to the allocated background layer
6. Create a display window with default parameters: windowed, auto scale and CRT effect enabled
7. Run the window loop, updating the display at each iteration until the window is closed

Source code:
```python
from tilengine import Engine, Window, Tilemap

engine = Engine.create(400, 240, 1, 0, 20)
engine.set_load_path("assets/sonic")
foreground = Tilemap.fromfile("sonic_md_fg1.tmx")
engine.layers[0].setup(foreground)

window = Window.create()
while window.process():
    window.draw_frame()
```

Resulting output:

![Test](test.png)

## Running the samples
To run the samples, just open a terminal window inside the "samples" directory and run any of these commands:
```python
python column_offset.py
python dkc.py
python mode7.py
python mosaic.py
python pixel_map.py
python platformer.py
python test.py
python vertical.py
```

## License
PyTilengine is released under the permissive MIT license
