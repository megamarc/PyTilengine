\page page_first_steps First steps

[TOC]


# First steps

## Installation

No install step is required. Just make sure that the Tilengine library and the tilengine.py modules are accessible from within your own project


## Initialize
First of all, you have to import the module at the top of the file:
```python
from tilengine import *
```

To initialize the engine, use the \ref create() method in the \ref Engine class, which creates a new instance of the engine. The method sets the framebuffer resolution, and the number of layers, sprites, and animators. Once set, these values are immutable and cannot be changed. For example, to set a 400x240 framebuffer with 2 layers, 80 sprites and no animations -Sega Genesis setup- you should do:
```python
engine = Engine.create(400, 240, 2, 80, 0)
```

## Setting the background
The background is what is shown when there isn't any layer or sprite at a given location. Tilengine supports two types of backgrounds: solid color and static bitmap. By default the background is black color.

### Solid color background
To set a solid color, there is the method \ref set_background_color() that takes a \ref Color object. This object has three components of a RGB color, between 0 and 255. For example, to set a dark blue background you can do:
```python
engine.set_background_color(Color(0, 32, 96))
```
Alternatively, you can use a hex color code:
```python
engine.set_background_color(Color('#002060'))
```

It is also possible to set the background color defined inside a \ref Tilemap object. Tilemaps may specify a default background color that can be used here. To see how to load and manipulate tilemaps, please refer to [chapter 10](10_tilemaps.md). For now, to load a tilemap called "tilemap.tmx" and use its default background color, you have to do the following:
```python
tilemap = Tilemap.fromfile("tilemap.tmx")
engine.set_background_color(tilemap)
```

### Bitmap background
To set a bitmap, there is the \ref set_background_bitmap() method that takes a \ref Bitmap object with a reference of a loaded bitmap. To see how to load an manipulate bitmaps, please refer to [chapter 14](14_bitmaps.md). For now, to load a bitmap called "Background.png" and set it as the background, you have to do the following:
```python
background = Bitmap.fromfile("Background.png")
engine.set_background_bitmap(background)
```
It's possible to change the default palette provided by the bitmap. To do so, use the \ref set_background_palette() method that takes a \ref Palette object. To see how to load and manipulate palettes, please refer to [chapter 12](12_palettes.md). Assuming you have an alternative palette file called "Background.act", do the following to set it:
```python
palette = Palette.fromfile("Background.act")
engine.set_background_palette(palette)
```

### Disabling background
It is possible to disable background at all if you know that the last layer covers the entire screen without holes, to gain some performance:
```python
engine.disable_background_color()
```

## Setting the assets path
By default tilengine loads all graphic assets in the same directory where the executable is. If you want to set your assets in a structured tree of folders -which is recommended-, you can set it with the \ref set_load_path() method. It accepts relative or absolute paths, and interprets slash and backslash as path separator on any platform. For example:
```python
engine.set_load_path("./assets/level1")
```

## Getting runtime info
Tilengine keeps track about the memory being used and the number of assets:
* \ref engine.version : returns the engine version number
* \ref engine.get_used_memory() : returns the total amount of memory used by tilengine and loaded assets
* \ref engine.get_num_objects() : returns the combined number of loaded assets


## Summary
This is a quick reference of related functions in this chapter:

|Function                       | Quick description
|-------------------------------|-------------------------------------
|\ref create()                  |Creates a Tilengine rendering context
|\ref set_load_path()           |Sets defautl load path for asset loading
|\ref get_num_objects()         |Returns the number of runtime assets
|\ref get_used_memory()         |Returns the amount of memory used by runtime assets
|\ref set_background_color()    |Sets the default background color using Color or Tilemap objects
|\ref disable_background_color()|Disables use of background color
|\ref set_backgroun_bitmap()    |Sets a static background bitmap
|\ref set_background_palette()  |Sets the palette of the static background bitmap
