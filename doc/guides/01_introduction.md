\mainpage

# Introduction
Tilengine is a free, cross-platform 2D graphics engine for creating classic/retro games with tile maps, sprites and palettes. Its unique scanline-based rendering algorithm makes raster effects a core feature, a technique used by many games running on real 2D graphics chips. This engine brings back the 16-bit era in its full glory and pushes it even further!

PyTilengine is the Python binding for Tilengine. It is not a direct 1:1 API translation of the original C library, but it uses familiar Python constructions as classes, lists, etc, and has its own documentation. Tilengine native shared library must be installed separately. Please refer to https://github.com/megamarc/Tilengine about how to do it.

## Tilengine Features
* Written in portable C (C99)
* LGPL Licensed: free for any project, including commercial ones
* Cross platform: available builds for Windows (32/64), Linux PC(32/64), Mac OS X and Raspberry Pi
* High performance: all samples run at 60 fps with CRT emulation enabled on a Raspberry Pi 3
* Streamlined, easy to learn API that requires very little lines of code
* Built-in SDL-based windowing for quick tests
* Integrate inside any existing framework as a slave renderer
* Loads assets from open standard standard file formats
* Create or modify graphic assets procedurally at run time
* True raster effects: modify render parameters between scanlines
* Background layer scaling and rotation
* Sprite scaling
* Several blending modes for layers and sprites
* Pixel accurate sprite vs sprite and sprite vs layer collision detection
* Special effects: per-column offset, mosaic, per-pixel displacement, CRT emulation...
