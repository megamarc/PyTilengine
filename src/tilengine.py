"""
Python wrapper for Tilengine retro graphics engine
Updated to library version 2.11.0
http://www.tilengine.org
"""

"""
Copyright (c) 2017-2022 Marc Palacios Domenech

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# pylint: disable=C0103
# pylint: disable=W0614
# pylint: disable=W0312
# pylint: disable=R0201
from sys import platform as _platform
from ctypes import *
from os import path
from typing import List, Union, Optional


# constants --------------------------------------------------------------------

class WindowFlags:
	"""
	List of flag values for window creation
	"""
	FULLSCREEN = (1 << 0)
	VSYNC = (1 << 1)
	S1 = (1 << 2)
	S2 = (2 << 2)
	S3 = (3 << 2)
	S4 = (4 << 2)
	S5 = (5 << 2)
	NEAREST = (1 << 6)


class Flags:
	"""
	List of flags for tiles and sprites
	"""
	FLIPX = (1 << 15)  # horizontal flip
	FLIPY = (1 << 14)  # vertical flip
	ROTATE = (1 << 13)	# row/column flip (unsupported, Tiled compatibility)
	PRIORITY = (1 << 12)  # tile goes in front of sprite layer
	MASKED = (1 << 11) # sprite won't be drawn inside masked region
	TILESET = (7 << 8) # tileset index


class Error:
	"""
	List of possible error codes returned by :meth:`Engine.get_last_error()`
	"""
	OK = 0	# No error
	OUT_OF_MEMORY = 1  # Not enough memory
	IDX_LAYER = 2  # Layer index out of range
	IDX_SPRITE = 3	# Sprite index out of range
	IDX_ANIMATION = 4  # Animation index out of range
	IDX_PICTURE = 5	 # Picture or tile index out of range
	REF_TILESET = 6	 # Invalid Tileset reference
	REF_TILEMAP = 7	 # Invalid Tilemap reference
	REF_SPRITESET = 8  # Invalid Spriteset reference
	REF_PALETTE = 9	 # Invalid Palette reference
	REF_SEQUENCE = 10  # Invalid SequencePack reference
	REF_SEQPACK = 11  # Invalid Sequence reference
	REF_BITMAP = 12	 # Invalid Bitmap reference
	NULL_POINTER = 13  # Null pointer as argument
	FILE_NOT_FOUND = 14	 # Resource file not found
	WRONG_FORMAT = 15  # Resource file has invalid format
	WRONG_SIZE = 16	 # A width or height parameter is invalid
	UNSUPPORTED = 17  # Unsupported function
	REF_LIST = 18 # Invalid ObjectList reference


class LogLevel:
	"""
	Log levels for :meth:`Engine.set_log_level()`
	"""
	NONE, ERRORS, VERBOSE = range(3)


class Blend:
	"""
	Available blending modes
	"""
	NONE, MIX25, MIX50,	MIX75, ADD,	SUB, MOD, CUSTOM = range(8)
	MIX = MIX50


class Input:
	"""
	Available inputs to query in :meth:`Window.get_input`
	"""
	NONE, UP, DOWN, LEFT, RIGHT, A, B, C, D, E,	F, START, QUIT, CRT = range(14)
	BUTTON1, BUTTON2, BUTTON3, BUTTON4, BUTTON5, BUTTON6 = range(A, START)
	P1, P2, P3, P4 = range(0, 128, 32)


PLAYER1, PLAYER2, PLAYER3, PLAYER4 = range(4)


class Overlay:
	"""
	Unised, kept for backwards compatibility with pre-2.10 release
	"""
	NONE, SHADOWMASK, APERTURE, SCANLINES, CUSTOM = range(5)


class CRT:
	"""
	Types of crt effect for release 2.10
	"""
	SLOT, APERTURE, SHADOW = range(3)


class TilengineException(Exception):
	"""
	Tilengine exception class
	"""
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


# structures ------------------------------------------------------------------
class Tile(Structure):
	"""
	Tile data contained in each cell of a :class:`Tilemap` object

	:attr:`index`: tile index
	:attr:`flags`: sum of :class:`Flags` values
	"""
	_fields_ = [
		("index", c_ushort),
		("flags", c_ushort)
	]


class ColorStrip(Structure):
	"""
	Data used to define each frame of a color cycle for :class:`Sequence` objects
	"""
	_fields_ = [
		("delay", c_int),
		("first", c_ubyte),
		("count", c_ubyte),
		("dir", c_ubyte)
	]

	def __init__(self, delay: int, first: int, count: int, direction: int):
		self.delay = delay
		self.first = first
		self.count = count
		self.dir = direction


class SequenceInfo(Structure):
	"""Sequence info returned by :meth:`Sequence.get_info`"""
	_fields_ = [
		("name", c_char * 32),
		("num_frames", c_int)
	]


class SequenceFrame(Structure):
	"""
	Data used to define each frame of an animation for :class:`Sequence` objects
	"""
	_fields_ = [
		("index", c_int),
		("delay", c_int)
	]

	def __init__(self, index: int, delay: int):
		self.index = index
		self.delay = delay


class SpriteInfo(Structure):
	"""
	Data returned by :meth:`Spriteset.get_sprite_info` with dimensions of the required sprite
	"""
	_fields_ = [
		("w", c_int),
		("h", c_int)
	]


class TileInfo(Structure):
	"""
	Data returned by :meth:`Layer.get_tile` about a given tile inside a background layer
	"""
	_fields_ = [
		("index", c_ushort),
		("flags", c_ushort),
		("row", c_int),
		("col", c_int),
		("xoffset", c_int),
		("yoffset", c_int),
		("color", c_ubyte),
		("type", c_ubyte),
		("empty", c_bool)
	]


class SpriteData(Structure):
	"""
	Data used to create :class:`Spriteset` objects
	"""
	_fields_ = [
		("name", c_char * 64),
		("x", c_int),
		("y", c_int),
		("w", c_int),
		("h", c_int)
	]

	def __init__(self, name: str, x: int, y: int, width: int, height: int):
		self.name = _encode_string(name)
		self.x = x
		self.y = y
		self.w = width
		self.h = height


class TileAttributes(Structure):
	"""
	Data used to create :class:`Tileset` objects
	"""
	_fields_ = [
		("type", c_ubyte),
		("priority", c_bool)
	]

	def __init__(self, tile_type: int, priority: bool):
		self.type = tile_type
		self.priority = priority


class PixelMap(Structure):
	"""
	Data passed to :meth:`Layer.set_pixel_mapping` in a list
	"""
	_fields_ = [
		("dx", c_short),
		("dy", c_short)
	]


class ObjectInfo(Structure):
	"""
	Object item info returned by :meth:`ObjectInfo.get_info()`
	"""
	_fields_ = [
		("id", c_ushort),
		("gid", c_ushort),
		("flags", c_ushort),
		("x", c_int),
		("y", c_int),
		("width", c_int),
		("height", c_int),
		("type", c_ubyte),
		("visible", c_bool),
		("name", c_char * 64)		
	]


class TileImage(Structure):
	"""
	Image Tile items for TLN_CreateImageTileset()
	"""
	_fields_ = [
		("bitmap", c_void_p),
		("id", c_ushort),
		("type", c_ubyte)
	]


class SpriteState(Structure):
	"""
	Sprite state for :meth:`Sprite.get_state()`
	"""
	_fields_ = [
		("x", c_int),
		("y", c_int),
		("w", c_int),
		("h", c_int),
		("flags", c_ushort),
		("palette", c_void_p),
		("spriteset", c_void_p),
		("index", c_int),
		("enabled", c_bool),
		("collision", c_bool)
	]


class Color(object):
	"""
	Represents a color value in RGB format
	"""
	def __init__(self, r: int, g: int, b: int):
		self.r = r
		self.g = g
		self.b = b

	@classmethod
	def fromstring(cls, string: str):
		""" creates a color from a ccs-style #rrggbb string """
		r = int(string[1:3], 16)
		g = int(string[3:5], 16)
		b = int(string[5:7], 16)
		return Color(r, g, b)


# module internal variables
_tln: "Engine"			# handle to shared native library
_window: "Window"		# singleton window
_window_created = False	# singleton window is created

# select library depending on OS
_library = ""
if _platform == "linux" or _platform == "linux2":
	_library = "libTilengine.so"
elif _platform == "win32":
	_library = "Tilengine.dll"
elif _platform == "darwin":
	_library = "Tilengine.dylib"
else:
	raise OSError("Unsupported platform: must be Windows, Linux or Mac OS")

# load native library. Try local path, if not, system path
if path.isfile(_library):
	_tln = cdll.LoadLibrary(f"./{_library}")
else:
	_tln = cdll.LoadLibrary(_library)

# callback types for user functions
_video_callback_function = CFUNCTYPE(None, c_int)
_blend_function = CFUNCTYPE(c_ubyte, c_ubyte, c_ubyte)


# convert string to c_char_p
def _encode_string(string: Optional[str]):
	if string is not None:
		return string.encode()
	return None

# convert c_char_p to string
def _decode_string(byte_array: Optional[bytearray]):
	if byte_array is not None:
		return byte_array.decode()
	return None


# error handling --------------------------------------------------------------
_tln.TLN_GetLastError.restype = c_int
_tln.TLN_GetErrorString.argtypes = [c_int]
_tln.TLN_GetErrorString.restype = c_char_p


# raises exception depending on error code
def _raise_exception(result: bool=False):
	if result is not True:
		error = _tln.TLN_GetLastError()
		error_string = _tln.TLN_GetErrorString(error)
		raise TilengineException(error_string.decode())

# World management
_tln.TLN_LoadWorld.argtypes = [c_char_p, c_int]
_tln.TLN_LoadWorld.restype = c_bool
_tln.TLN_SetWorldPosition.argtypes = [c_int, c_int]
_tln.TLN_SetWorldPosition.restype = None
_tln.TLN_SetLayerParallaxFactor.argtypes = [c_int, c_float, c_float]
_tln.TLN_SetLayerParallaxFactor.restype = c_bool
_tln.TLN_SetSpriteWorldPosition.argtypes = [c_int, c_int, c_int]
_tln.TLN_SetSpriteWorldPosition.restype = c_bool
_tln.TLN_ReleaseWorld.argtypes = None
_tln.TLN_ReleaseWorld.restype = None

# basic management ------------------------------------------------------------
_tln.TLN_Init.argtypes = [c_int, c_int, c_int, c_int, c_int]
_tln.TLN_Init.restype = c_void_p
_tln.TLN_DeleteContext.argtypes = [c_void_p]
_tln.TLN_DeleteContext.restype = c_bool
_tln.TLN_SetContext.argtypes = [c_void_p]
_tln.TLN_SetContext.restype = c_bool
_tln.TLN_GetContext.restype = c_void_p
_tln.TLN_GetNumObjects.restype = c_int
_tln.TLN_GetVersion.restype = c_int
_tln.TLN_GetUsedMemory.restype = c_int
_tln.TLN_SetBGColor.argtypes = [c_ubyte, c_ubyte, c_ubyte]
_tln.TLN_SetBGColorFromTilemap.argtypes = [c_void_p]
_tln.TLN_SetBGColorFromTilemap.restype = c_bool
_tln.TLN_SetBGBitmap.argtypes = [c_void_p]
_tln.TLN_SetBGBitmap.restype = c_bool
_tln.TLN_SetBGPalette.argtypes = [c_void_p]
_tln.TLN_SetBGPalette.restype = c_bool
_tln.TLN_SetRenderTarget.argtypes = [c_void_p, c_int]
_tln.TLN_UpdateFrame.argtypes = [c_int]
_tln.TLN_SetLoadPath.argtypes = [c_char_p]
_tln.TLN_SetLogLevel.argtypes = [c_int]
_tln.TLN_OpenResourcePack.argtypes = [c_char_p, c_char_p]
_tln.TLN_OpenResourcePack.restype = c_bool
_tln.TLN_SetSpritesMaskRegion.argtypes = [c_int, c_int]

class Engine(object):
	"""
	Main object for engine creation and rendering

	:ivar layers: tuple of Layer objects, one entry per layer
	:ivar sprites: tuple of Sprite objects, one entry per sprite
	:ivar animations: tuple of Animation objects, one entry per animation
	:ivar version: library version number
	"""
	def __init__(self, handle: c_void_p, num_layers: int, num_sprites: int, num_animations: int):
		self._as_parameter_ = handle
		self.layers = tuple([Layer(n) for n in range(num_layers)])
		self.sprites = tuple([Sprite(n) for n in range(num_sprites)])
		self.animations = tuple([Animation(n) for n in range(num_animations)])
		self.version = _tln.TLN_GetVersion()
		self.cb_raster_func = None
		self.cb_frame_func = None
		self.cb_blend_func = None
		self.library = _tln

		version = [2,11,0]	# expected library version
		req_version = (version[0] << 16) + (version[1] << 8) + version[2]
		if self.version < req_version:
			maj_version = self.version >> 16
			min_version = (self.version >> 8) & 255
			bug_version = self.version & 255
			print("WARNING: Library version is %d.%d.%d, expected at least %d.%d.%d!" % \
				(maj_version, min_version, bug_version, version[0], version[1], version[2]))

	@classmethod
	def create(cls, width: int, height: int, num_layers: int, num_sprites: int, num_animations: int) -> "Engine":
		"""
		Static method that creates a new instance of the engine

		:param width: horizontal resolution in pixels
		:param height: vertical resolution in pixels
		:param num_layers: max number of background layers
		:param num_sprites: max number of sprites
		:param num_animations: number of color-cycle animations
		:return: new instance
		"""
		handle = _tln.TLN_Init(width, height, num_layers, num_sprites, num_animations)
		if handle is not None:
			_engine = Engine(handle, num_layers, num_sprites, num_animations)
			return _engine
		else:
			_raise_exception()

	def __del__(self):
		_tln.TLN_DeleteContext(self)

	def get_num_objects(self) -> int:
		"""
		:return: the number of objets used by the engine so far
		"""
		return _tln.TLN_GetNumObjects()

	def get_used_memory(self) -> int:
		"""
		:return: the total amount of memory used by the objects
		"""
		return _tln.TLN_GetUsedMemory()

	def set_background_color(self, param):
		"""
		Sets the background color

		:param param: can be a Color object or a Tilemap object. In this case, \
			it assigns de background color as defined inside the tilemap
		"""
		param_type = type(param)
		if param_type is Color:
			_tln.TLN_SetBGColor(param.r, param.g, param.b)
		elif param_type is Tilemap:
			_tln.TLN_SetBGColorFromTilemap(param)

	def disable_background_color(self):
		"""
		Disales background color rendering. If you know that the last background layer will always
		cover the entire screen, you can disable it to gain some performance
		"""
		_tln.TLN_DisableBGColor()

	def set_background_bitmap(self, bitmap: "Bitmap"):
		"""
		Sets a static bitmap as background

		:param bitmap: Bitmap object to set as background. Set None to disable it.
		"""
		ok = _tln.TLN_SetBGBitmap(bitmap)
		_raise_exception(ok)

	def set_background_palette(self, palette: "Palette"):
		"""
		Sets the palette for the background bitmap. By default it is assigned the palette
		of the bitmap passed in :meth:`Engine.set_background_bitmap`

		:param palette: Palette object to set
		"""
		ok = _tln.TLN_SetBGPalette(palette)
		_raise_exception(ok)

	def set_raster_callback(self, raster_callback):
		"""
		Enables raster effects processing, like a virtual HBLANK interrupt where any render parameter can be modified between scanlines.

		:param raster_callback: name of the user-defined function to call for each scanline. Set None to disable. \
			This function takes one integer parameter that indicates the current scanline, between 0 and vertical resolution.

		Example::

			def my_raster_callback(num_scanline):
			    if num_scanline is 32:
			        engine.set_background_color(Color(0,0,0))

			engine.set_raster_callback(my_raster_callback)
		"""
		if raster_callback is None:
			self.cb_raster_func = None
		else:
			self.cb_raster_func = _video_callback_function(raster_callback)
		_tln.TLN_SetRasterCallback(self.cb_raster_func)

	def set_frame_callback(self, frame_callback):
		"""
		Enables user callback for each drawn frame, like a virtual VBLANK interrupt

		:param frame_callback: name of the user-defined function to call for each frame. Set None to disable. \
			This function takes one integer parameter that indicates the current frame.

		Example::

			def my_frame_callback(num_frame):
		        engine.set_background_color(Color(0,0,0))

			engine.set_frame_callback(my_frame_callback)
		"""
		if frame_callback is None:
			self.cb_frame_func = None
		else:
			self.cb_frame_func = _video_callback_function(frame_callback)
		_tln.TLN_SetFrameCallback(self.cb_frame_func)

	def set_render_target(self, pixels, pitch):
		"""
		Sets the output surface for rendering

		:param pixels: Pointer to the start of the target framebuffer
		:param pitch: Number of bytes per each scanline of the framebuffer
		"""
		_tln.TLN_SetRenderTarget(pixels, pitch)

	def update_frame(self, num_frame=0):
		"""
		Draws the frame to the previously specified render target

		:param num_frame: optional frame number for animation control
		"""
		_tln.TLN_UpdateFrame(num_frame)

	def set_load_path(self, path: str):
		"""
		Sets base path for all data loading static methods `fromfile`

		:param path: Base path. Files will load at path/filename. Set None to use current directory
		"""
		_tln.TLN_SetLoadPath(_encode_string(path))

	def set_custom_blend_function(self, blend_function):
		"""
		Sets custom blend function to use in sprites or background layers when `BLEND_CUSTOM` mode
		is selected with the :meth:`Layer.set_blend_mode` and :meth:`Sprite.set_blend_mode` methods.

		:param blend_function: name of the user-defined function to call when blending that takes \
			two integer arguments: source component intensity, destination component intensity, and returns \
			the desired intensity.

		Example::

			# do 50%/50% blending
			def blend_50(src, dst):
			    return (src + dst) / 2

			engine.set_custom_blend_function(blend_50)
		"""
		self.cb_blend_func = _blend_function(blend_function)
		_tln.TLN_SetCustomBlendFunction(self.cb_blend_func)

	def set_log_level(self, log_level: int):
		"""
		Sets output messages
		"""
		_tln.TLN_SetLogLevel(log_level)

	def get_available_sprite(self) -> int:
		"""
		:return: Index of the first unused sprite (starting from 0) or -1 if none found
		"""
		index = _tln.TLN_GetAvailableSprite()
		return index

	def get_available_animation(self) -> int:
		"""
		:return: Index of the first unused animation (starting from 0) or -1 if none found
		"""
		index = _tln.TLN_GetAvailableAnimation()
		return index

	def open_resource_pack(self, filename: str, key: str=''):
		"""
		Opens the resource package with optional aes-128 key and binds it
		:param filename: file with the resource package (.dat extension)
		:param key: optional null-terminated ASCII string with aes decryption key
		"""
		ok = _tln.TLN_OpenResourcePack(_encode_string(str(filename)), _encode_string(str(key)))
		_raise_exception(ok)

	def close_resource_pack(self):
		"""
		Closes currently opened resource package and unbinds it 
		"""
		return _tln.TLN_CloseResourcePack()

	def set_sprites_mask_region(self, top: int, bottom: int):
		"""
		Defines a sprite masking region between the two scanlines. Sprites masked with Sprite.enable_mask_region() won't be drawn inside this region
		
		:param top: upper scaline of the exclusion region
		:param bottom: lower scanline of the exclusion region
		"""
		ok = _tln.TLN_SetSpritesMaskRegion(top, bottom)
		_raise_exception(ok)

	def load_world(self, filename: str, first_layer: int=0):
		"""
		Loads and assigns complete TMX file

		:param filename: main .tmx file to load
		:first_layer: optional layer index to start to assign, by default 0
		"""
		ok =_tln.TLN_LoadWorld(filename, first_layer)
		_raise_exception(ok)

	def set_world_position(self, x: int, y: int):
		"""
		Sets global world position, moving all layers in sync according to their parallax factor
		
		:param x: horizontal position in world space
		:param y: vertical position in world space
		"""
		ok = _tln.TLN_SetWorldPosition(x, y)
		_raise_exception(ok)

	def release_world(self):
		"""
		Releases world resources loaded with Engine.load_world
		"""
		_tln.TLN_ReleaseWorld()


# window management -----------------------------------------------------------
_tln.TLN_CreateWindow.argtypes = [c_char_p, c_int]
_tln.TLN_CreateWindow.restype = c_bool
_tln.TLN_CreateWindowThread.argtypes = [c_char_p, c_int]
_tln.TLN_CreateWindowThread.restype = c_bool
_tln.TLN_ProcessWindow.restype = c_bool
_tln.TLN_IsWindowActive.restype = c_bool
_tln.TLN_GetInput.argtypes = [c_int]
_tln.TLN_GetInput.restype = c_bool
_tln.TLN_EnableInput.argtypes = [c_int, c_bool]
_tln.TLN_AssignInputJoystick.argtypes = [c_int, c_int]
_tln.TLN_DefineInputKey.argtypes = [c_int, c_int, c_uint]
_tln.TLN_DefineInputButton.argtypes = [c_int, c_int, c_ubyte]
_tln.TLN_DrawFrame.argtypes = [c_int]
_tln.TLN_EnableCRTEffect.argtypes = [c_int, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_bool, c_ubyte]
_tln.TLN_ConfigCRTEffect.argtypes = [c_int, c_bool]
_tln.TLN_GetTicks.restype = c_int
_tln.TLN_Delay.argtypes = [c_int]
_tln.TLN_GetWindowWidth.restype = c_int
_tln.TLN_GetWindowHeight.restype = c_int

class Window(object):
	"""
	Built-in window manager for easy setup and testing

	:ivar num_frame: current frame being drawn, starting from 0
	:ivar width: actual window width (after scaling)
	:ivar height: actual window height (after scaling)
	"""
	def __init__(self):
		self.cb_sdl_func = None

	@classmethod
	def create(cls, title:str='Tilengine window', overlay=None, flags:int=WindowFlags.VSYNC) -> "Window":
		"""
		Static method that creates a single-threaded window that must be used in conjunction with
		:meth:`Window.process` in a loop

		:param overlay: obsolete, kept for compatibility with pre 2.10 release with old CRT effect
		:param flags: optional flags combination of :class:`WindowFlags` values
		:return: instance of the created window
		"""
		global _window, _window_created

		"""Added the ability to choose the window title ~AleK3y"""
		_tln.TLN_SetWindowTitle(_encode_string(str(title)))

		if _window_created:
			return _window
		ok = _tln.TLN_CreateWindow(_encode_string(overlay), flags)
		if ok is True:
			_window = Window()
			_window.num_frame = 0
			_window.width = _tln.TLN_GetWindowWidth()
			_window.height = _tln.TLN_GetWindowHeight()
			_window_created = True
			return _window
		else:
			_raise_exception(ok)

	@classmethod
	def create_threaded(cls, overlay=None, flags:int=WindowFlags.VSYNC) -> "Window":
		"""
		Static method that creates a multi-threaded window that runs in its own thread without user loop.
		Used mainly in python interactive console

		:param overlay: obsolete, kept for compatibility with pre 2.10 release with old CRT effect
		:param flags: optional flags combination of :class:`WindowFlags` values
		"""
		global _window
		if _window is not None:
			return _window
		ok = _tln.TLN_CreateWindowThread(_encode_string(overlay), flags)
		if ok is True:
			_window = Window()
			_window.width = _tln.TLN_GetWindowWidth()
			_window.height = _tln.TLN_GetWindowHeight()
			return _window
		else:
			_raise_exception(ok)

	def process(self):
		"""
		Does basic window housekeeping in signgle-threaded window, created with :meth:`Window.create`.
		This method must be called in a loop by the main thread.
		:return: True if window is active or False if the user has requested to end the application
		(by pressing Esc key or clicking the close button)
		"""
		_tln.TLN_DrawFrame(self.num_frame)
		self.num_frame += 1
		return _tln.TLN_ProcessWindow()

	def is_active(self) -> bool:
		"""
		:return: True if window is active or False if the user has requested to end the application \
			(by pressing Esc key or clicking the close button)
		"""
		return _tln.TLN_IsWindowActive()

	def get_input(self, input_id: int) -> bool:
		"""
		Returns the state of a given input

		:param input_id: one of the :class:`Input` defined values. By default it requests input of player 1. \
			To request input of a given player, add one of the possible P1 - P4 values.

		:return: True if that input is pressed or False if not

		Example::

			# check if player 1 is pressing right:
			value = window.get_input(Input.RIGHT)

			# check if player 2 is pressing action button 1:
			value = window.get_input(Input.P2 + Input.BUTTON1)
		"""
		return _tln.TLN_GetInput(input_id)

	def enable_input(self, player: int, state: bool):
		"""
		Enables or disables input for specified player

		:param player: player identifier to configure (PLAYER1 - PLAYER4)
		:param state: True to enable, False to disable
		"""
		_tln.TLN_EnableInput(player, state)

	def assign_joystick(self, player: int, joystick_index: int):
		"""

		:param player: player identifier to configure (PLAYER1 - PLAYER4)
		:param joystick_index: zero-based joystick index to assign. 0 = first, 1 = second.... Disable with -1
		"""
		_tln.TLN_AssignInputJoystick(player, joystick_index)

	def define_input_key(self, player: int, input: int, key: int):
		"""
		Assigns a keyboard input to a player

		:param player: player identifier to configure (PLAYER1 - PLAYER4)
		:param input: input to assign, member of :class:`Input`
		:param key: ASCII key value or scancode as defined in SDL.h		
		"""
		_tln.TLN_DefineInputKey(player, input, key)

	def define_input_button(self, player: int, input: int, button: int):
		"""
		Assigns a joystick button input to a player

		:param player: player identifier to configure (PLAYER1 - PLAYER4)
		:param input: input to assign, member of :class:`Input`
		:param button: button index
		"""
		_tln.TLN_DefineInputButton(player, input, button)

	def draw_frame(self, num_frame=0):
		"""
		Deprecated, kept for old source code compatibility. Subsumed by :meth:`Window.process`.
		"""

	def wait_redraw(self):
		"""
		In multi-threaded windows, it waits until the current frame has finished rendering.
		"""
		_tln.TLN_WaitRedraw()

	def config_crt_effect(self, crt_type: int, rf_blur: bool):
		"""
		Enables CRT simulation post-processing effect to give true retro appeareance

		:param crt_type: One possible value of \ref CRT class
		:param rf_blur: Optional RF (horizontal) blur, increases CPU usage
		"""
		_tln.TLN_ConfigCRTEffect(crt_type, rf_blur)
	
	def enable_crt_effect(self, overlay_id, overlay_blend, threshold, v0, v1, v2, v3, blur, glow_factor):
		"""
		Obsolete, kept for backward compatibility with pre- 2.10 release. Use config_crt_effect() instead.
		"""
		_tln.TLN_EnableCRTEffect(overlay_id, overlay_blend, threshold, v0, v1, v2, v3, blur, glow_factor)

	def disable_crt_effect(self):
		"""
		Disables the CRT post-processing effect enabled with :meth:`Window.enable_crt_effect`
		"""
		_tln.TLN_DisableCRTEffect()

	def set_sdl_callback(self, sdl_callback):
		"""
		Sets callback to process other SDL2 events inside the window
		"""

		if sdl_callback is None:
			self.cb_sdl_func = None
		else:
			from sdl2 import SDL_Event
			_sdl_callback_function = CFUNCTYPE(None, SDL_Event)
			self.cb_sdl_func = _sdl_callback_function(sdl_callback)
		_tln.TLN_SetSDLCallback(self.cb_sdl_func)


	def get_ticks(self) -> int:
		"""
		:return: the number of milliseconds since application start
		"""
		return _tln.TLN_GetTicks()

	def delay(self, msecs: int):
		"""
		Suspends execition for a fixed time

		:param msecs: number of milliseconds to pause
		"""
		_tln.TLN_Delay(msecs)


# spritesets management -----------------------------------------------------------
_tln.TLN_CreateSpriteset.argtypes = [c_void_p, POINTER(SpriteData), c_int]
_tln.TLN_CreateSpriteset.restype = c_void_p
_tln.TLN_LoadSpriteset.argtypes = [c_char_p]
_tln.TLN_LoadSpriteset.restype = c_void_p
_tln.TLN_CloneSpriteset.argtypes = [c_void_p]
_tln.TLN_CloneSpriteset.restype = c_void_p
_tln.TLN_GetSpriteInfo.argtypes = [c_void_p, c_int, POINTER(SpriteInfo)]
_tln.TLN_GetSpriteInfo.restype = c_bool
_tln.TLN_GetSpritesetPalette.argtypes = [c_void_p]
_tln.TLN_GetSpritesetPalette.restype = c_void_p
_tln.TLN_SetSpritesetData.argtypes = [c_void_p, c_int, POINTER(SpriteData), POINTER(c_ubyte), c_int]
_tln.TLN_SetSpritesetData.restype = c_bool
_tln.TLN_DeleteSpriteset.argtypes = [c_void_p]
_tln.TLN_DeleteSpriteset.restype = c_bool


class Spriteset(object):
	"""
	The Spriteset object holds the graphic data used to render moving objects (sprites)

	:ivar palette: original palette attached inside the resource file
	"""
	def __init__(self, handle: c_void_p, owner: bool=True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln
		self.palette = Palette(_tln.TLN_GetSpritesetPalette(handle), False)

	@classmethod
	def create(cls, bitmap: "Bitmap", sprite_data: POINTER(SpriteData)) -> "Spriteset":
		"""
		Static method that creates an empty spriteset

		:param bitmap: Bitmap object containing the packaged sprite pictures
		:param sprite_data: list of SpriteData tuples describing each sprite pictures
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateSpriteset(bitmap, sprite_data, len(sprite_data))
		if handle is not None:
			return Spriteset(handle)
		else:
			_raise_exception()

	@classmethod
	def fromfile(cls, filename: str) -> "Spriteset":
		"""
		Static method that loads a spriteset from a pair of png/txt files

		:param filename: png filename with bitmap data
		:return: instance of the created object
		"""
		handle = _tln.TLN_LoadSpriteset(_encode_string(filename))
		if handle is not None:
			return Spriteset(handle)
		else:
			_raise_exception()

	def clone(self) -> "Spriteset":
		"""
		Creates a copy of the object

		:return: instance of the copy
		"""
		handle = _tln.TLN_CloneSpriteset(self)
		if handle is not None:
			return Spriteset(handle)
		else:
			_raise_exception()

	def set_sprite_data(self, entry: int, data: POINTER(SpriteData), pixels: POINTER(c_byte), pitch: int):
		"""
		Sets attributes and pixels of a given sprite inside a spriteset

		:param entry: The entry index inside the spriteset to modify [0, num_sprites - 1]
		:param data: Pointer to a user-provided SpriteData structure with sprite description
		:param pixels: Pointer to user-provided pixel data block
		:param pitch: Number of bytes per scanline of the source pixel data
		"""
		ok = _tln.TLN_SetSpritesetData(self, entry, data, pixels, pitch)
		_raise_exception(ok)

	def get_sprite_info(self, entry: int, info: POINTER(SpriteInfo)):
		"""
		Gets info about a given sprite into an user-provided SpriteInfo tuple

		:param entry: sprite index to query
		:param info: SpriteInfo to get the data
		"""
		ok = _tln.TLN_GetSpriteInfo(self, entry, info)
		_raise_exception(ok)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeleteSpriteset(self)
			_raise_exception(ok)


# tilesets management ---------------------------------------------------------
_tln.TLN_CreateTileset.argtypes = [c_int, c_int, c_int, c_void_p, c_void_p, POINTER(TileAttributes)]
_tln.TLN_CreateTileset.restype = c_void_p
_tln.TLN_LoadTileset.argtypes = [c_char_p]
_tln.TLN_LoadTileset.restype = c_void_p
_tln.TLN_CloneTileset.argtypes = [c_void_p]
_tln.TLN_CloneTileset.restype = c_void_p
_tln.TLN_SetTilesetPixels.argtypes = [c_void_p, c_int, POINTER(c_byte), c_int]
_tln.TLN_SetTilesetPixels.restype = c_bool
_tln.TLN_GetTileWidth.argtypes = [c_void_p]
_tln.TLN_GetTileWidth.restype = c_int
_tln.TLN_GetTileHeight.argtypes = [c_void_p]
_tln.TLN_GetTileHeight.restype = c_int
_tln.TLN_GetTilesetNumTiles.argtypes = [c_void_p] 
_tln.TLN_GetTilesetNumTiles.restype = c_int
_tln.TLN_GetTilesetPalette.argtypes = [c_void_p]
_tln.TLN_GetTilesetPalette.restype = c_void_p
_tln.TLN_GetTilesetSequencePack.argtypes = [c_void_p]
_tln.TLN_GetTilesetSequencePack.restype = c_void_p
_tln.TLN_FindSpritesetSprite.argtypes = [c_void_p, c_char_p]
_tln.TLN_FindSpritesetSprite.restype = c_int
_tln.TLN_DeleteTileset.argtypes = [c_void_p]
_tln.TLN_DeleteTileset.restype = c_bool


class Tileset(object):
	"""
	The Tileset object holds the graphic tiles used to render background layers from a Tilemap

	:ivar tile_width: width of each tile
	:ivar tile_height: height of each tile
	:ivar num_tiles: number of unique tiles
	:ivar palette: original palette attached inside the resource file
	:ivar sequence_pack: optional SequencePack embedded inside the Tileset for tileset animation
	"""
	def __init__(self, handle: c_void_p, owner: bool=True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln
		self.tile_width = _tln.TLN_GetTileWidth(handle)
		self.tile_height = _tln.TLN_GetTileHeight(handle)
		self.num_tiles = _tln.TLN_GetTilesetNumTiles(handle)
		self.palette = Palette(_tln.TLN_GetTilesetPalette(handle), False)
		self.sequence_pack = SequencePack(_tln.TLN_GetTilesetSequencePack(handle), False)

	@classmethod
	def create(cls, num_tiles: int, width: int, height: int, palette: "Palette", sequence_pack: Optional["SequencePack"]=None, attributes: Optional[POINTER(TileAttributes)]=None) -> "Tileset":
		"""
		Static method that creates an empty Tileset at runtime

		:param num_tiles: number of unique tiles
		:param width: Width of each tile (must be multiple of 8)
		:param height: Height of each tile (must be multiple of 8)
		:param palette: Palette object
		:param sequence_pack: Optional SequencePack with associated Tileset animations
		:param attributes: Optional list of TileAttributes, one element per tile in the tileset
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateTileset(num_tiles, width, height, palette, sequence_pack, attributes)
		if handle is not None:
			return Tileset(handle)
		else:
			_raise_exception()

	@classmethod
	def fromfile(cls, filename: str) -> "Tileset":
		"""
		Static method that loads a Tiled TSX tileset from file

		:param filename: TSX file with the tileset
		:return:
		"""
		handle = _tln.TLN_LoadTileset(_encode_string(filename))
		if handle is not None:
			return Tileset(handle)
		else:
			_raise_exception()

	def clone(self) -> "Tileset":
		"""
		Creates a copy of the object

		:return: instance of the copy
		"""
		handle = _tln.TLN_CloneTileset(self)
		if handle is not None:
			return Tileset(handle)
		else:
			_raise_exception()

	def set_pixels(self, entry: int, data: POINTER(c_byte), pitch: int):
		"""
		Sets pixel data for a single tile

		:param entry: Number of tile to set [0, num_tiles - 1]
		:param data: List of bytes with pixel data, one byte per pixel
		:param pitch: Number of bytes per line in source data
		"""
		ok = _tln.TLN_SetTilesetPixels(self, entry, data, pitch)
		_raise_exception(ok)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeleteTileset(self)
			_raise_exception(ok)


# tilemaps management ---------------------------------------------------------
_tln.TLN_CreateTilemap.argtypes = [c_int, c_int, POINTER(Tile), c_int, c_void_p]
_tln.TLN_CreateTilemap.restype = c_void_p
_tln.TLN_LoadTilemap.argtypes = [c_char_p]
_tln.TLN_LoadTilemap.restype = c_void_p
_tln.TLN_CloneTilemap.argtypes = [c_void_p]
_tln.TLN_CloneTilemap.restype = c_void_p
_tln.TLN_GetTilemapRows.argtypes = [c_void_p]
_tln.TLN_GetTilemapRows.restype = c_int
_tln.TLN_GetTilemapCols.argtypes = [c_void_p]
_tln.TLN_GetTilemapCols.restype = c_int
_tln.TLN_SetTilemapTileset2.argtypes = [c_void_p, c_void_p, c_int]
_tln.TLN_SetTilemapTileset2.restype = c_bool
_tln.TLN_GetTilemapTileset2.argtypes = [c_void_p, c_int]
_tln.TLN_GetTilemapTileset2.restype = c_void_p
_tln.TLN_GetTilemapTile.argtypes = [c_void_p, c_int, c_int, POINTER(Tile)]
_tln.TLN_GetTilemapTile.restype = c_bool
_tln.TLN_SetTilemapTile.argtypes = [c_void_p, c_int, c_int, POINTER(Tile)]
_tln.TLN_SetTilemapTile.restype = c_bool
_tln.TLN_CopyTiles.argtypes = [c_void_p, c_int, c_int, c_int, c_int, c_void_p, c_int, c_int]
_tln.TLN_CopyTiles.restype = c_bool
_tln.TLN_DeleteTilemap.argtypes = [c_void_p]
_tln.TLN_DeleteTilemap.restype = c_bool


class Tilemap(object):
	"""
	The Tilemap object holds the grid of tiles that define the background layout

	:ivar rows: number of rows (vertical cells)
	:ivar cols: number of columns (horizontal cells)
	:ivar tileset: Tileset object attached inside the resource file
	"""
	def __init__(self, handle: c_void_p, owner: bool=True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln
		self.rows = _tln.TLN_GetTilemapRows(handle)
		self.cols = _tln.TLN_GetTilemapCols(handle)
		tileset_handle = _tln.TLN_GetTilemapTileset2(handle, 0)
		if tileset_handle is not None:
			self.tileset = Tileset(tileset_handle, False)
		else:
			self.tileset = None

	@classmethod
	def create(cls, rows: int, cols: int, tiles: POINTER(Tile), background_color: int=0, tileset: Optional[Tileset]=None) -> "Tilemap":
		"""
		Static method that creates an empty tilemap

		:param rows: Number of rows (vertical dimension)
		:param cols: Number of cols (horizontal dimension)
		:param tiles: List of Tile objects with tile data
		:param background_color: optional Color object with default background color
		:param tileset: Optional reference to associated tileset
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateTilemap(rows, cols, tiles, background_color, tileset)
		if handle is not None:
			return Tilemap(handle)
		else:
			_raise_exception()

	@classmethod
	def fromfile(cls, filename: str, layer_name: Optional[str]=None) -> "Tilemap":
		"""
		Static method that loads a Tiled TMX tilemap from file

		:param filename: TMX file with the tilemap
		:param layer_name: Optional name of the layer to load when the TMX file has more than one layer. \
			By default it loads the first layer inside the TMX
		:return: instance of the created object
		"""
		handle = _tln.TLN_LoadTilemap(_encode_string(filename), _encode_string(layer_name))
		if handle is not None:
			return Tilemap(handle)
		else:
			_raise_exception()

	def clone(self) -> "Tilemap":
		"""
		Creates a copy of the object

		:return: instance of the copy
		"""
		handle = _tln.TLN_CloneTilemap(self)
		if handle is not None:
			return Tilemap(handle)
		else:
			_raise_exception()

	def get_tileset(self, index: int=0) -> Tileset:
		"""
		Returns the nth tileset associated tileset to the specified tilemap
		:param index: Tileset index (0 - 7), 0 by default
		"""
		return Tileset(_tln.TLN_GetTilemapTileset2(self, index), False)

	def set_tileset(self, tileset: Tileset, index:int = 0):
		"""
		Sets the nth tileset associated tileset to the specified tilemap
		:param tileset: Reference to tileset object to associate
		:param index: Tileset index (0 - 7), 0 by default
		"""
		ok = _tln.TLN_SetTilemapTileset2(self, tileset, index)
		_raise_exception(ok)

	def get_tile(self, row: int, col: int, tile_info: POINTER(TileInfo)):
		"""
		Gets data about a given tile

		:param row: Vertical position of the tile (0 <= row < rows)
		:param col: Horizontal position of the tile (0 <= col < cols)
		:param tile_info: pointer to user-provided :class:`TileInfo` object where to get the data
		"""
		ok = _tln.TLN_GetTilemapTile(self, row, col, tile_info)
		_raise_exception(ok)

	def set_tile(self, row: int, col: int, tile_info: Optional[POINTER(TileInfo)]):
		"""
		Sets a tile inside the tilemap

		:param row: Vertical position of the tile (0 <= row < rows)
		:param col: Horizontal position of the tile (0 <= col < cols)
		:param tile_info: pointer to user-provided :class:`Tile` object, or None to erase
		"""
		if tile_info is not None:
			ok = _tln.TLN_SetTilemapTile(self, row, col, tile_info)
		else:
			tile_info = Tile()
			tile_info.index = 0
			ok = _tln.TLN_SetTilemapTile(self, row, col, tile_info)
			del tile_info
		_raise_exception(ok)

	def copy_tiles(self, src_row: int, src_col: int, num_rows: int, num_cols: int, dst_tilemap: "Tilemap", dst_row: int, dst_col: int):
		"""
		Copies blocks of tiles between two tilemaps

		:param src_row: Starting row (vertical position) inside the source tilemap
		:param src_col: Starting column (horizontal position) inside the source tilemap
		:param num_rows: Number of rows to copy
		:param num_cols: Number of columns to copy
		:param dst_tilemap: Target tilemap
		:param dst_row: Starting row (vertical position) inside the target tilemap
		:param dst_col: Starting column (horizontal position) inside the target tilemap
		"""
		ok = _tln.TLN_CopyTiles(self, src_row, src_col, num_rows, num_cols, dst_tilemap, dst_row, dst_col)
		_raise_exception(ok)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeleteTilemap(self)
			_raise_exception(ok)


# color tables management -----------------------------------------------------
_tln.TLN_CreatePalette.argtypes = [c_int]
_tln.TLN_CreatePalette.restype = c_void_p
_tln.TLN_LoadPalette.argtypes = [c_char_p]
_tln.TLN_LoadPalette.restype = c_void_p
_tln.TLN_ClonePalette.argtypes = [c_void_p]
_tln.TLN_ClonePalette.restype = c_void_p
_tln.TLN_SetPaletteColor.argtypes = [c_void_p, c_int, c_ubyte, c_ubyte, c_ubyte]
_tln.TLN_SetPaletteColor.restype = c_bool
_tln.TLN_MixPalettes.argtypes = [c_void_p, c_void_p, c_void_p, c_ubyte]
_tln.TLN_MixPalettes.restype = c_bool
_tln.TLN_AddPaletteColor.argtypes = [c_void_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte]
_tln.TLN_AddPaletteColor.restype = c_bool
_tln.TLN_SubPaletteColor.argtypes = [c_void_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte]
_tln.TLN_SubPaletteColor.restype = c_bool
_tln.TLN_ModPaletteColor.argtypes = [c_void_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte]
_tln.TLN_ModPaletteColor.restype = c_bool
_tln.TLN_GetPaletteData.argtypes = [c_void_p, c_int]
_tln.TLN_GetPaletteData.restype = POINTER(c_ubyte)
_tln.TLN_DeletePalette.argtypes = [c_void_p]
_tln.TLN_DeletePalette.restype = c_bool


class Palette(object):
	"""
	The Palette object holds the color tables used by tileesets and spritesets to render sprites and backgrounds
	"""
	def __init__(self, handle: c_void_p, owner:bool = True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln

	@classmethod
	def create(cls, num_entries: int=256) -> "Palette":
		"""
		Static method that creates an empty palette

		:param num_entries: optional number of colors to hold (up to 256, default value)
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreatePalette(num_entries)
		if handle is not None:
			return Palette(handle)
		else:
			_raise_exception()

	@classmethod
	def fromfile(cls, filename: str) -> "Palette":
		"""
		Static method that loads a palette from an Adobe Color Table (.act) file

		:param filename: name of the .act file to load
		:return: instance of the created object
		"""
		handle = _tln.TLN_LoadPalette(_encode_string(filename))
		if handle is not None:
			return Palette(handle)
		else:
			_raise_exception()

	def clone(self) -> "Palette":
		"""
		Creates a copy of the object

		:return: instance of the copy
		"""
		handle = _tln.TLN_ClonePalette(self)
		if handle is not None:
			return Palette(handle)
		else:
			_raise_exception()

	def set_color(self, entry: int, color: Color):
		"""
		Sets the RGB color value of a palette entry

		:param entry: Index of the palette entry to modify (0-255)
		:param color: Color object with the r,g,b components of the color
		"""
		ok = _tln.TLN_SetPaletteColor(self, entry, color.r, color.g, color.b)
		_raise_exception(ok)

	def mix(self, src_palette1: "Palette", src_palette2: "Palette", factor: int):
		"""
		Mixes two palettes

		:param src_palette1: First palette to mix
		:param src_palette2: Second palette to mix
		:param factor: Integer value with percentage of mix (0-100)
		"""
		ok = _tln.TLN_MixPalettes(src_palette1, src_palette2, self, factor)
		_raise_exception(ok)

	def add_color(self, first: int, count: int, color: Color):
		"""
		Modifies a range of colors by adding the provided color value to the selected range.
		The result is always a brighter color.

		:param first: index of the first color entry to modify
		:param count: number of colors from start to modify
		:param color: Color object to add
		"""
		ok = _tln.TLN_AddPaletteColor(self, first, count, color.r, color.g, color.b)
		_raise_exception(ok)

	def sub_color(self, first: int, count: int, color: Color):
		"""
		Modifies a range of colors by subtracting the provided color value to the selected range.
		The result is always a darker color.

		:param first: index of the first color entry to modify
		:param count: number of colors from start to modify
		:param color: Color object to subtract
		"""
		ok = _tln.TLN_SubPaletteColor(self, first, count, color.r, color.g, color.b)
		_raise_exception(ok)

	def mod_color(self, first: int, count: int, color: Color):
		"""
		Modifies a range of colors by modulating (normalized product) the provided color value to the selected range.
		The result is always a darker color.

		:param first: index of the first color entry to modify
		:param count: number of colors from start to modify
		:param color: Color object to modulate
		"""
		ok = _tln.TLN_ModPaletteColor(self, first, count, color.r, color.g, color.b)
		_raise_exception(ok)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeletePalette(self)
			_raise_exception(ok)


# bitmaps ---------------------------------------------------------------------
_tln.TLN_CreateBitmap.argtypes = [c_int, c_int, c_int]
_tln.TLN_CreateBitmap.restype = c_void_p
_tln.TLN_LoadBitmap.argtypes = [c_char_p]
_tln.TLN_LoadBitmap.restype = c_void_p
_tln.TLN_CloneBitmap.argtypes = [c_void_p]
_tln.TLN_CloneBitmap.restype = c_void_p
_tln.TLN_GetBitmapPtr.argtypes = [c_void_p, c_int, c_int]
_tln.TLN_GetBitmapPtr.restype = POINTER(c_ubyte)
_tln.TLN_GetBitmapWidth.argtypes = [c_void_p]
_tln.TLN_GetBitmapWidth.restype = c_int
_tln.TLN_GetBitmapHeight.argtypes = [c_void_p]
_tln.TLN_GetBitmapHeight.restype = c_int
_tln.TLN_GetBitmapDepth.argtypes = [c_void_p]
_tln.TLN_GetBitmapDepth.restype = c_int
_tln.TLN_GetBitmapPitch.argtypes = [c_void_p]
_tln.TLN_GetBitmapPitch.restype = c_int
_tln.TLN_GetBitmapPalette.argtypes = [c_void_p]
_tln.TLN_GetBitmapPalette.restype = c_void_p
_tln.TLN_DeleteBitmap.argtypes = [c_void_p]
_tln.TLN_DeleteBitmap.restype = c_bool


class Bitmap(object):
	"""
	The Bitmap object holds graphic data used to build in backgrounds, Tileset and Spriteset objects

	:ivar width: number of horizontal pixels
	:ivar height: number of vertical pixels
	:ivar depth: number of bits per pixel
	:ivar pitch: number of bytes per each scanline
	:ivar palette: Palette object attached inside the bitmap
	"""
	def __init__(self, handle: c_void_p, owner=True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln
		self.width = _tln.TLN_GetBitmapWidth(handle)
		self.height = _tln.TLN_GetBitmapHeight(handle)
		self.depth = _tln.TLN_GetBitmapDepth(handle)
		self.pitch = _tln.TLN_GetBitmapPitch(handle)
		self.palette = Palette(_tln.TLN_GetBitmapPalette(handle), False)

	@classmethod
	def create(cls, width: int, height: int, bpp: int=8) -> "Bitmap":
		"""
		Static method that creates an empty bitmap

		:param width: Width in pixels
		:param height: Height in pixels
		:param bpp: Optional bits per pixel (8 by default)
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateBitmap(width, height, bpp)
		if handle is not None:
			return Bitmap(handle)
		else:
			_raise_exception()

	@classmethod
	def fromfile(cls, filename: str) -> "Bitmap":
		"""
		Static method that loads a BMP or PNG file

		:param filename: name of the file to load (.bmp or .png)
		:return: instance of the created object
		"""
		handle = _tln.TLN_LoadBitmap(_encode_string(filename))
		if handle is not None:
			return Bitmap(handle)
		else:
			_raise_exception()

	def clone(self) -> "Bitmap":
		"""
		Creates a copy of the object

		:return: instance of the copy
		"""
		handle = _tln.TLN_CloneBitmap(self)
		if handle is not None:
			return Bitmap(handle)
		else:
			_raise_exception()

	def get_data(self, x: int, y: int) -> c_void_p:
		"""
		Returns a pointer to the starting memory address

		:param x: Starting x position [0, width - 1]
		:param y: Starting y position [0, height - 1]
		:return: pointer
		"""
		return _tln.TLN_GetBitmapPtr(self, x, y)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeleteBitmap(self)
			_raise_exception(ok)

class ObjectList(object):
	"""
	TODO: ObjectList reference
	"""


# sequences management --------------------------------------------------------
_tln.TLN_CreateSequence.argtypes = [c_char_p, c_int, c_int, POINTER(SequenceFrame)]
_tln.TLN_CreateSequence.restype = c_void_p
_tln.TLN_CreateCycle.argtypes = [c_char_p, c_int, POINTER(ColorStrip)]
_tln.TLN_CreateCycle.restype = c_void_p
_tln.TLN_CreateSpriteSequence.argtypes = [c_char_p, c_void_p, c_char_p, c_int]
_tln.TLN_CreateSpriteSequence.restype = c_void_p
_tln.TLN_CloneSequence.argtypes = [c_void_p]
_tln.TLN_CloneSequence.restype = c_void_p
_tln.TLN_GetSequenceInfo.argtypes = [c_void_p, POINTER(SequenceInfo)]
_tln.TLN_GetSequenceInfo.restype = c_bool
_tln.TLN_DeleteSequence.argtypes = [c_void_p]
_tln.TLN_DeleteSequence.restype = c_bool


class Sequence(object):
	"""
	The Sequence object holds the sequences to feed the animation engine
	"""
	def __init__(self, handle: c_void_p, owner: bool=True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln

	@classmethod
	def create_sequence(cls, name: str, target: int, frames: List[SequenceFrame]) -> "Sequence":
		"""
		Static method that creates an empty Sequence for Sprite and Tileset animations

		:param name: String with an unique name to identify the sequence inside a SequencePack object
		:param target: For Tileset animations, the tile index to animate
		:param frames: List with SequenceFrame objects, one for each frame of animation
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateSequence(_encode_string(name), target, len(frames), frames)
		if handle is not None:
			return Sequence(handle)
		else:
			_raise_exception()

	@classmethod
	def create_cycle(cls, name: str, strips: List[ColorStrip]) -> "Sequence":
		"""
		Static method that creates an empty Sequence for Palette animations

		:param name: String with an unique name to identify the sequence inside a SequencePack object
		:param strips: List with ColorStrip objects, one for each frame of animation
		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateCycle(_encode_string(name), len(strips), strips)
		if handle is not None:
			return Sequence(handle)
		else:
			_raise_exception()

	@classmethod
	def create_sprite_sequence(cls, spriteset: Spriteset, basename: str, delay: int) -> "Sequence":
		"""
		Static method that creates a sprite sequence based on names inside a spriteset

		:param spriteset: Reference to the spriteset with frames to animate
		:param basename: Base of the sprite name for the numbered sequence
		:param delay: Number of frames to hold each animation frame
		:return: created Sequence object or None if error
		"""
		handle = _tln.TLN_CreateSpriteSequence(None, spriteset, _encode_string(basename), delay)
		if handle is not None:
			return Sequence(handle)
		else:
			_raise_exception()

	def clone(self) -> "Sequence":
		"""
		Creates a copy of the object

		:return: instance of the copy
		"""
		handle = _tln.TLN_CloneSequence(self)
		if handle is not None:
			return Sequence(handle)
		else:
			_raise_exception()

	def get_info(self, info: POINTER(SequenceInfo)):
		"""
		Returns runtime info about a given sequence

		:param info: user-provided SequenceInfo structure to hold the returned data
		"""
		return _tln.TLN_GetSequenceInfo(self, info)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeleteSequence(self)
			_raise_exception(ok)


# sequence pack management --------------------------------------------------------
_tln.TLN_CreateSequencePack.restype = c_void_p
_tln.TLN_LoadSequencePack.argtypes = [c_char_p]
_tln.TLN_LoadSequencePack.restype = c_void_p
_tln.TLN_FindSequence.argtypes = [c_void_p, c_char_p]
_tln.TLN_FindSequence.restype = c_void_p
_tln.TLN_GetSequence.argtypes = [c_void_p]
_tln.TLN_GetSequence.restype = c_void_p
_tln.TLN_GetSequencePackCount.argtypes = [c_void_p]
_tln.TLN_GetSequencePackCount.restype = c_int
_tln.TLN_AddSequenceToPack.argtypes = [c_void_p, c_void_p]
_tln.TLN_AddSequenceToPack.restype = c_bool
_tln.TLN_DeleteSequencePack.argtypes = [c_void_p]
_tln.TLN_DeleteSequencePack.restype = c_bool


class SequencePack(object):
	"""
	The SequencePack object holds a collection of Sequence objects

	:ivar count: number of sequences inside the pack
	:ivar sequences: dictionary of contained sequences indexed by name
	"""
	def __init__(self, handle: c_void_p, owner: bool=True):
		self._as_parameter_ = handle
		self.owner = owner
		self.library = _tln
		self.count = _tln.TLN_GetSequencePackCount(self)
		self.sequences = dict()
		sequence_info = SequenceInfo()
		for s in range(self.count):
			sequence = self.get_sequence(s)
			sequence.get_info(sequence_info)
			self.sequences[_decode_string(sequence_info.name)] = sequence

	@classmethod
	def create(cls) -> "SequencePack":
		"""
		Static method that creates an empty SequencePack object

		:return: instance of the created object
		"""
		handle = _tln.TLN_CreateSequencePack()
		if handle is not None:
			return SequencePack(handle)
		else:
			_raise_exception()

	@classmethod
	def fromfile(cls, filename: str) -> "SequencePack":
		"""
		Static method that loads a SQX file with sequence data (XML-based)

		:param filename: Name of the SQX file to load
		:return: instance of the created object
		"""
		handle = _tln.TLN_LoadSequencePack(_encode_string(filename))
		if handle is not None:
			return SequencePack(handle)
		else:
			_raise_exception()

	def get_sequence(self, index: int) -> Sequence:
		"""
		Returns the nth sequence inside a sequence pack

		:param index: zero-based index number
		:return: Sequence object
		"""
		handle = _tln.TLN_GetSequence(self, index)
		if handle is not None:
			return Sequence(handle, False)
		else:
			_raise_exception()

	def find_sequence(self, name: str) -> Sequence:
		"""
		Finds a Sequence by its name

		:param name: name of the Sequence to find
		:return: Sequence object if found, or None if error
		"""
		handle = _tln.TLN_FindSequence(self, _encode_string(name))
		if handle is not None:
			return Sequence(handle)
		else:
			_raise_exception()

	def add_sequence(self, sequence: Sequence):
		"""
		Adds a Sequence to a SequencePack

		:param sequence: Sequence object to add
		"""
		sequence_info = SequenceInfo()
		sequence.get_info(sequence_info)
		ok = _tln.TLN_AddSequenceToPack(self, sequence)
		if ok:
			self.sequences[_decode_string(sequence_info.name)] = sequence
		_raise_exception(ok)

	def __del__(self):
		if self.owner:
			ok = self.library.TLN_DeleteSequencePack(self)
			_raise_exception(ok)


# layer management ------------------------------------------------------------
_tln.TLN_SetLayer.argtypes = [c_int, c_void_p, c_void_p]
_tln.TLN_SetLayer.restype = c_bool

_tln.TLN_SetLayerTilemap.argtypes = [c_int, c_void_p]
_tln.TLN_SetLayerTilemap.restype = c_bool
_tln.TLN_SetLayerBitmap.argtypes = [c_int, c_void_p]
_tln.TLN_SetLayerBitmap.restype = c_bool
_tln.TLN_SetLayerObjects.argtypes = [c_int, c_void_p, c_void_p]
_tln.TLN_SetLayerObjects.restype = c_bool
_tln.TLN_SetLayerPalette.argtypes = [c_int, c_void_p]
_tln.TLN_SetLayerPalette.restype = c_bool
_tln.TLN_SetLayerPosition.argtypes = [c_int, c_int, c_int]
_tln.TLN_SetLayerPosition.restype = c_bool
_tln.TLN_SetLayerScaling.argtypes = [c_int, c_float, c_float]
_tln.TLN_SetLayerScaling.restype = c_bool
_tln.TLN_SetLayerTransform.argtypes = [c_int, c_float, c_float, c_float, c_float, c_float]
_tln.TLN_SetLayerTransform.restype = c_bool
_tln.TLN_SetLayerPixelMapping.argtypes = [c_int, POINTER(PixelMap)]
_tln.TLN_SetLayerPixelMapping.restype = c_bool
_tln.TLN_ResetLayerMode.argtypes = [c_int]
_tln.TLN_ResetLayerMode.restype = c_bool
_tln.TLN_SetLayerBlendMode.argtypes = [c_int, c_int, c_ubyte]
_tln.TLN_SetLayerBlendMode.restype = c_bool
_tln.TLN_SetLayerColumnOffset.argtypes = [c_int, POINTER(c_int)]
_tln.TLN_SetLayerColumnOffset.restype = c_bool
_tln.TLN_SetLayerClip.argtypes = [c_int, c_int, c_int, c_int, c_int]
_tln.TLN_SetLayerClip.restype = c_bool
_tln.TLN_DisableLayerClip.argtypes = [c_int]
_tln.TLN_DisableLayerClip.restype = c_bool
_tln.TLN_SetLayerMosaic.argtypes = [c_int, c_int, c_int]
_tln.TLN_SetLayerMosaic.restype = c_bool
_tln.TLN_DisableLayerMosaic.argtypes = [c_int]
_tln.TLN_DisableLayerMosaic.restype = c_bool
_tln.TLN_DisableLayer.argtypes = [c_int]
_tln.TLN_DisableLayer.restype = c_bool
_tln.TLN_EnableLayer.argtypes = [c_int]
_tln.TLN_EnableLayer.restype = c_bool
_tln.TLN_GetLayerPalette.argtypes = [c_int]
_tln.TLN_GetLayerPalette.restype = c_void_p
_tln.TLN_GetLayerTile.argtypes = [c_int, c_int, c_int, POINTER(TileInfo)]
_tln.TLN_GetLayerTile.restype = c_bool
_tln.TLN_GetLayerWidth.argtypes = [c_int]
_tln.TLN_GetLayerWidth.restype = c_int
_tln.TLN_GetLayerHeight.argtypes = [c_int]
_tln.TLN_GetLayerHeight.restype = c_int
_tln.TLN_SetLayerPriority.argtypes = [c_int, c_bool]
_tln.TLN_SetLayerPriority.restype = c_bool

class Layer(object):
	"""
	The Layer object manages each tiled background plane

	:ivar index: layer index, from 0 to num_layers - 1
	:ivar width: width in pixels of the assigned tilemap
	:ivar height: height in pixels of the assigned tilemap
	:ivar tilemap: assigned Tilemap object, for tilemap layers
	:ivar bitmap: assigned Bitmap object, for bitmap layers
	:ivar objectlist: assigned ObjectList object, for object list layers
	"""
	def __init__(self, index):
		self.index = index
		self._as_parameter_ = index
		self.width = 0
		self.height = 0
		self.tilemap = None
		self.bitmap = None
		self.objectlist = None

	def setup(self, tilemap: Tilemap, tileset: Optional[Tileset]=None):
		"""
		Enables a background layer by setting the specified tilemap and optional tileset

		:param tilemap: Tilemap object with background layout
		:param tileset: Optional Tileset object. If not set, the Tilemap's own Tileset is selected
		"""
		ok = _tln.TLN_SetLayer(self, tileset, tilemap)
		if ok is True:
			self.width = _tln.TLN_GetLayerWidth(self)
			self.height = _tln.TLN_GetLayerHeight(self)
			self.tilemap = tilemap
			if tileset is not None:
				tilemap.set_tileset(tileset)
			return ok
		else:
			_raise_exception()

	def set_tilemap(self, tilemap: Tilemap):
		"""
		Configures a tiled background layer with the specified tilemap

		:param tilemap: Tilemap object with background layout
		"""
		ok = _tln.TLN_SetLayerTilemap(self, tilemap)
		if ok is True:
			self.width = _tln.TLN_GetLayerWidth(self)
			self.height = _tln.TLN_GetLayerHeight(self)
			self.tilemap = tilemap
			self.bitmap = None
			self.objectlist = None
			return ok
		else:
			_raise_exception()

	def set_bitmap(self, bitmap: Bitmap):
		"""
		Configures a background layer with the specified full bitmap

		:param bitmap: Bitmap object with full bitmap background
		"""
		ok = _tln.TLN_SetLayerBitmap(self, bitmap)
		if ok is True:
			self.width = _tln.TLN_GetLayerWidth(self)
			self.height = _tln.TLN_GetLayerHeight(self)
			self.bitmap = bitmap
			self.tilemap = None
			self.objectlist = None
			return ok
		else:
			_raise_exception()

	def set_palette(self, palette: Palette):
		"""
		Sets the color palette to the layer

		:param palette: Palette object to assign. By default the Tileset's own palette is used
		"""
		ok = _tln.TLN_SetLayerPalette(self, palette)
		_raise_exception(ok)

	def set_position(self, x: int, y: int):
		"""
		Sets the position of the tileset that corresponds to the upper left corner of the viewport

		:param x: horizontal position
		:param y: vertical position
		"""
		ok = _tln.TLN_SetLayerPosition(self, int(x), int(y))
		_raise_exception(ok)

	def set_scaling(self, sx: float, sy: float):
		"""
		Enables layer scaling

		:param sx: floating-point value with horizontal scaling factor
		:param sy: floating-point value with vertical scaling factor
		"""
		ok = _tln.TLN_SetLayerScaling(self, sx, sy)
		_raise_exception(ok)

	def set_transform(self, angle: float, x: float, y: float, sx: float, sy: float):
		"""
		Enables layer affine transformation (rotation and scaling). All parameters are floating point values

		:param angle: rotation angle in degrees
		:param x: horizontal displacement in screen space where the rotation center is located
		:param y: vertical displacement in screen space where the rotation center is located
		:param sx: horizontal scaling factor
		:param sy: vertical scaling factor
		"""
		ok = _tln.TLN_SetLayerTransform(self, angle, x, y, sx, sy)
		_raise_exception(ok)

	def set_pixel_mapping(self, pixel_map: POINTER(PixelMap)):
		"""
		Enables pixel mapping displacement table

		:param pixel_map: user-provided list of PixelMap objects of hres*vres size: one item per screen pixel
		"""
		ok = _tln.TLN_SetLayerPixelMapping(self, pixel_map)
		_raise_exception(ok)

	def reset_mode(self):
		"""
		Disables all special effects: scaling, affine transform and pixel mapping, and returns to default render mode.
		"""
		ok = _tln.TLN_ResetLayerMode(self)
		_raise_exception(ok)

	def set_blend_mode(self, mode: int):
		"""
		Enables blending mode with background objects

		:param mode: One of the :class:`Blend` defined values
		"""
		ok = _tln.TLN_SetLayerBlendMode(self, mode, 0)
		_raise_exception(ok)

	def set_column_offset(self, offsets: Optional[POINTER(c_int)]=None):
		"""
		Enables column offset mode for tiles

		:param offsets: User-provided tuple of integers with offsets, one per column of tiles. Pass None to disable
		"""
		ok = _tln.TLN_SetLayerColumnOffset(self, offsets)
		_raise_exception(ok)

	def set_clip(self, x1: int, y1: int, x2: int, y2: int):
		"""
		Enables clipping rectangle

		:param x1: left coordinate
		:param y1: top coordinate
		:param x2: right coordinate
		:param y2: bottom coordinate
		"""
		ok = _tln.TLN_SetLayerClip(self, x1, y1, x2, y2)
		_raise_exception(ok)

	def disable_clip(self):
		"""
		Disables clipping rectangle
		"""
		ok = _tln.TLN_DisableLayerClip(self)
		_raise_exception(ok)

	def set_mosaic(self, pixel_w: int, pixel_h: int):
		"""
		Enables mosaic effect (pixelation)

		:param pixel_w: horizontal pixel size
		:param pixel_h: vertical pixel size
		"""
		ok = _tln.TLN_SetLayerMosaic(self, pixel_w, pixel_h)
		_raise_exception(ok)

	def disable_mosaic(self):
		"""
		Disables mosaic effect
		"""
		ok = _tln.TLN_DisableLayerMosaic(self)
		_raise_exception(ok)

	def disable(self):
		"""
		Disables the layer so it is not drawn
		"""
		ok = _tln.TLN_DisableLayer(self)
		_raise_exception(ok)
		
	def enable(self):
		"""
		Re-enables previously disabled layer
		"""
		ok = _tln.TLN_EnableLayer(self)
		_raise_exception(ok)
		
	def get_palette(self) -> Palette:
		"""
		Gets the layer active palette

		:return: Palette object of the Layer
		"""
		handle = _tln.TLN_GetLayerPalette(self)
		if handle is not None:
			return Palette(handle)
		else:
			_raise_exception()

	def get_tile(self, x: int, y: int, tile_info: POINTER(TileInfo)):
		"""
		Gets detailed info about the tile located in Tilemap space

		:param x: x position inside the Tilemap
		:param y: y position inside the Tilemap
		:param tile_info: User-provided TileInfo object where to get the data
		"""
		ok = _tln.TLN_GetLayerTile(self, x, y, tile_info)
		_raise_exception(ok)

	def set_priority(self, enable: bool):
		"""
		Sets full layer priority, appearing in front of regular sprites

		:param enable: True for enable, False for disable
		"""
		ok = _tln.TLN_SetLayerPriority(self, enable)
		_raise_exception(ok)

	def set_parallax_factor(self, x: int, y: int):
		"""
		Sets layer parallax factor to use in conjunction with Engine.set_world_position()
		
		:param x: Horizontal parallax factor
		:param y: Vertical parallax factor
		"""
		ok = _tln.TLN_SetLayerParallaxFactor(self, x, y)
		_raise_exception(ok)


# sprite management -----------------------------------------------------------
_tln.TLN_ConfigSprite.argtypes = [c_int, c_void_p, c_ushort]
_tln.TLN_ConfigSprite.restype = c_bool
_tln.TLN_SetSpriteSet.argtypes = [c_int, c_void_p]
_tln.TLN_SetSpriteSet.restype = c_bool
_tln.TLN_SetSpriteFlags.argtypes = [c_int, c_ushort]
_tln.TLN_SetSpriteFlags.restype = c_bool
_tln.TLN_EnableSpriteFlag.argtypes = [c_int, c_uint, c_bool]
_tln.TLN_EnableSpriteFlag.restype = c_bool
_tln.TLN_SetSpritePivot.argtypes = [c_int, c_float, c_float]
_tln.TLN_SetSpritePivot.restype = c_bool
_tln.TLN_SetSpritePosition.argtypes = [c_int, c_int, c_int]
_tln.TLN_SetSpritePosition.restype = c_bool
_tln.TLN_SetSpritePicture.argtypes = [c_int, c_int]
_tln.TLN_SetSpritePicture.restype = c_bool
_tln.TLN_SetSpritePalette.argtypes = [c_int, c_void_p]
_tln.TLN_SetSpritePalette.restype = c_bool
_tln.TLN_SetSpriteBlendMode.argtypes = [c_int, c_int, c_ubyte]
_tln.TLN_SetSpriteBlendMode.restype = c_bool
_tln.TLN_SetSpriteScaling.argtypes = [c_int, c_float, c_float]
_tln.TLN_SetSpriteScaling.restype = c_bool
_tln.TLN_ResetSpriteScaling.argtypes = [c_int]
_tln.TLN_ResetSpriteScaling.restype = c_bool
_tln.TLN_GetSpritePicture.argtypes = [c_int]
_tln.TLN_GetSpritePicture.restype = c_int
_tln.TLN_GetAvailableSprite.restype = c_int
_tln.TLN_EnableSpriteCollision.argtypes = [c_int, c_bool]
_tln.TLN_EnableSpriteCollision.restype = c_bool
_tln.TLN_GetSpriteCollision.argtypes = [c_int]
_tln.TLN_GetSpriteCollision.restype = c_bool
_tln.TLN_DisableSprite.argtypes = [c_int]
_tln.TLN_DisableSprite.restype = c_bool
_tln.TLN_GetSpritePalette.argtypes = [c_int]
_tln.TLN_GetSpritePalette.restype = c_void_p
_tln.TLN_SetSpriteAnimation.argtypes = [c_int, c_void_p, c_int]
_tln.TLN_SetSpriteAnimation.restype = c_bool
_tln.TLN_PauseSpriteAnimation.argtypes = [c_int]
_tln.TLN_PauseSpriteAnimation.restype = c_bool
_tln.TLN_ResumeSpriteAnimation.argtypes = [c_int]
_tln.TLN_ResumeSpriteAnimation.restype = c_bool
_tln.TLN_GetAnimationState.argtypes = [c_int]
_tln.TLN_GetAnimationState.restype = c_bool
_tln.TLN_DisableSpriteAnimation.argtypes = [c_int]
_tln.TLN_DisableSpriteAnimation.restype = c_bool
_tln.TLN_GetSpriteState.argtypes = [c_int, POINTER(SpriteState)]
_tln.TLN_GetSpriteState.restype = c_bool
_tln.TLN_SetFirstSprite.argtypes = [c_int]
_tln.TLN_SetFirstSprite.restype = c_bool
_tln.TLN_SetNextSprite.argtypes = [c_int, c_int]
_tln.TLN_SetNextSprite.restype = c_bool
_tln.TLN_EnableSpriteMasking.argtypes = [c_int, c_bool]
_tln.TLN_EnableSpriteMasking.restype = c_bool

class Sprite(object):
	"""
	The Sprite object manages each moving character onscreen

	:ivar index: sprite index, from 0 to num_sprites - 1
	:ivar spriteset: assigned Spriteset object
	"""
	def __init__(self, index: int):
		self.index = index
		self._as_parameter_ = index
		self.spriteset = None

	def setup(self, spriteset: Spriteset, flags: int=0):
		"""
		Enables a sprite by setting its Spriteset and optional flags

		:param spriteset: Spriteset object with the graphic data of the sprites
		:param flags: Optional combination of defined :class:`Flag` values, 0 by default
		"""
		ok = _tln.TLN_ConfigSprite(self, spriteset, flags)
		self.spriteset = spriteset
		_raise_exception(ok)

	def set_spriteset(self, spriteset: Spriteset):
		"""
		Enables a sprite by setting its Spriteset

		:param spriteset: Spriteset object with the graphic data of the sprites
		"""
		ok = _tln.TLN_SetSpriteSet(self, spriteset)
		self.spriteset = spriteset
		_raise_exception(ok)

	def set_flags(self, flags: int=0):
		"""
		Sets modification flags

		:param flags: Combination of defined :class:`Flag` values
		"""
		ok = _tln.TLN_SetSpriteFlags(self, flags)
		_raise_exception(ok)
		
	def enable_flag(self, flag: int, value: bool=True):
		"""
		Enables (or disables) specified flag for a sprite

		:param flag: Combination of defined :class:`Flag` values
		:param value: True to enable (default) or False to disable
		"""
		ok = _tln.TLN_EnableSpriteFlag(self, flag, value)
		_raise_exception(ok)

	def set_pivot(self, u: float, v: float):
		"""
		Sets sprite pivot point for placement and scaling source. By default is at (0,0) = top left corner. Uses normalized coordinates in [ 0.0 - 1.0] range.

		:param u: Horizontal position (0.0 = full left, 1.0 = full right)
		:param v: Vertical position (0.0 = top, 1.0 = bottom)
		"""
		ok = _tln.TLN_SetSpritePivot(self, u, v)
		_raise_exception(ok)

	def set_position(self, x: int, y: int):
		"""
		Sets the sprite position in screen coordinates

		:param x: Horizontal position
		:param y: Vertical position
		"""
		ok = _tln.TLN_SetSpritePosition(self, x, y)
		_raise_exception(ok)

	def set_world_position(self, x: int, y: int):
		"""
		Sets the sprite position in world space coordinates
		
		:param x: Horizontal world position of pivot (0 = left margin)
		:param y: Vertical world position of pivot (0 = top margin)
		"""
		ok = _tln.TLN_SetSpriteWorldPosition(self, x, y)
		_raise_exception(ok)		

	def set_picture(self, picture: Union[int,str]):
		"""
		Sets the actual graphic contained in the Spriteset to the sprite

		:param picture: can be an integer with the index inside the Spriteset, or a string with its name
		"""
		ok = False
		param_type = type(picture)
		if param_type is int:
			ok = _tln.TLN_SetSpritePicture(self, picture)
		elif param_type is str:
			entry = _tln.TLN_FindSpritesetSprite(self.spriteset, picture)
			if entry != -1:
				ok = _tln.TLN_SetSpritePicture(self, entry)
			else:
				return
		else:
			return
		_raise_exception(ok)

	def set_palette(self, palette: Palette):
		"""
		Assigns a Palette object to the sprite. By default it is assigned wit the Spriteset's own palette

		:param palette: Palette object to set
		"""
		ok = _tln.TLN_SetSpritePalette(self, palette)
		_raise_exception(ok)

	def set_blend_mode(self, mode: int):
		"""
		Enables blending mode with background objects

		:param mode: One of the :class:`Blend` defined values
		"""
		ok = _tln.TLN_SetSpriteBlendMode(self, mode, 0)
		_raise_exception(ok)

	def set_scaling(self, sx: float, sy: float):
		"""
		Enables sprite scaling

		:param sx: floating-point value with horizontal scaling factor
		:param sy: floating-point value with vertical scaling factor
		"""
		ok = _tln.TLN_SetSpriteScaling(self, sx, sy)
		_raise_exception(ok)

	def reset_mode(self):
		"""
		Disables scaling and returns to default render mode.
		"""
		ok = _tln.TLN_ResetSpriteScaling(self)
		_raise_exception(ok)

	def get_picture(self) -> int:
		"""
		Returns the index of the assigned picture from the Spriteset

		:return: the graphic index
		"""
		return _tln.TLN_GetSpritePicture(self)

	def enable_collision(self, mode: bool=True):
		"""
		Enables pixel-accurate sprite collision detection with other sprites

		:param mode: True for enabling or False for disabling
		"""
		ok = _tln.TLN_EnableSpriteCollision(self, mode)
		_raise_exception(ok)

	def check_collision(self) -> bool:
		"""
		Gets the collision status of the sprite. Requires :meth:`Sprite.enable_collision` set to True

		:return: True if collision with another sprite detected, or False if not
		"""
		return _tln.TLN_GetSpriteCollision(self)

	def disable(self):
		"""
		Disables the sprite so it is not drawn
		"""
		ok = _tln.TLN_DisableSprite(self)
		_raise_exception(ok)

	def get_palette(self) -> Palette:
		"""
		Gets the sprite active palette

		:return: Palette object of the Sprite
		"""
		handle = _tln.TLN_GetSpritePalette(self)
		if handle is not None:
			return Palette(handle)
		else:
			_raise_exception()

	def set_animation(self, sequence: Sequence, loop: int=0):
		"""
		Starts a Sprite animation

		:param sequence: Sequence object to play on the sprite
		:param loop: number of times to repeat, 0=infinite
		"""
		ok = _tln.TLN_SetSpriteAnimation(self, sequence, loop)
		_raise_exception(ok)

	def get_animation_state(self) -> bool:
		"""
		Gets the state of the animation

		:return: True if still running, False if it has finished
		"""
		return _tln.TLN_GetAnimationState(self)

	def pause_animation(self):
		"""
		Paused sprite animation
		"""
		ok = _tln.TLN_PauseSpriteAnimation(self)
		_raise_exception(ok)
	
	def resume_animation(self):
		"""
		Resumes paused animation
		"""
		ok = _tln.TLN_ResumeSpriteAnimation(self)
		_raise_exception(ok)

	def disable_animation(self):
		"""
		Disables the animation so it doesn't run
		"""
		ok = _tln.TLN_DisableSpriteAnimation(self)
		_raise_exception(ok)

	def get_state(self, state: POINTER(SpriteState)):
		"""
		Returns runtime info about the sprite

		:param state: user-allocated SpriteState structure
		"""
		ok = _tln.TLN_GetSpriteState(self, state)
		_raise_exception(ok)

	def set_first(self):
		"""
		Sets this to be the first sprite drawn (beginning of list)
		"""
		ok = _tln.TLN_SetFirstSprite(self)
		_raise_exception(ok)

	def set_next(self, next: int):
		"""
		Sets the next sprite to after this one, builds list

		:param next: sprite to draw after this one
		"""
		ok = _tln.TLN_SetNextSprite(self, next)
		_raise_exception(ok)
	
	def enable_masking(self, enable: bool=True):
		"""
		Enables or disables masking for this sprite, if enabled it won't be drawn inside the region set up with Engine.set_sprite_mask_region()
		"""
		ok = _tln.TLN_EnableSpriteMasking(self, enable)
		_raise_exception(ok)


# color cycle animation engine ------------------------------------------------------------
_tln.TLN_SetPaletteAnimation.argtypes = [c_int, c_void_p, c_void_p, c_bool]
_tln.TLN_SetPaletteAnimation.restype = c_bool
_tln.TLN_SetPaletteAnimationSource.argtypes = [c_int, c_void_p]
_tln.TLN_SetPaletteAnimationSource = c_bool
_tln.TLN_GetAvailableAnimation.restype = c_int
_tln.TLN_DisablePaletteAnimation.argtypes = [c_int]
_tln.TLN_DisablePaletteAnimation.restype = c_bool


class Animation(object):
	"""
	The Animation object manages color-cycle (palette) animations

	:ivar index: animation index, from 0 to num_animations - 1
	"""
	def __init__(self, index: int):
		self.index = index
		self._as_parameter_ = index

	def set_palette_animation(self, palette: Palette, sequence: Sequence, blend: bool=True):
		"""
		Starts a color cycle animation for Palette object

		:param palette: Palette object to animate
		:param sequence: Sequence object to play on the palette
		:param blend: True for smooth frame interpolation, False for classic coarse mode
		"""
		ok = _tln.TLN_SetPaletteAnimation(self, palette, sequence, blend)
		_raise_exception(ok)

	def set_palette_animation_source(self, palette: Palette):
		"""
		Sets the source palette of a color cycle animation already in motion.
		Useful for combining color cycling and palette interpolation at the same time

		:param palette: Palette object to assign
		"""
		ok = _tln.TLN_SetPaletteAnimationSource(self, palette)
		_raise_exception(ok)

	def disable(self):
		"""
		Disables the animation so it doesn't run
		"""
		ok = _tln.TLN_DisablePaletteAnimation(self)
		_raise_exception(ok)
