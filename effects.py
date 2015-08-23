#!/usr/bin/python
#from argparse import ArgumentParser
#from pieva import *
#import fastopc as opc
from math import pi
import os
import random
import time

import cairo
from PIL import Image, ImageTk
import Tkinter

import numpy as np
#from screen import *
import sys

try:
  import c_ripples as ripples
except ImportError:
  import warnings
  warnings.warn("Using slow ripples module. Consider using cython version "
                "instead. For this:\n  python setup.py build_ext && cp build/lib*/c_ripples* .")
  import slow_ripples as ripples

class Bitmap():

    def __init__(self, sizex, sizey):
        self.bitmap = np.zeros([sizex,sizey])

    def set(self, x, y, colour):
        try:
            self.bitmap[x,y] = colour
        except:
            pass

class Benchmark(object):
    def __init__(self, name):
        self.name= name
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, *args):
        if 'debug' in sys.argv:
            print self.name + ": " + str(time.time() - self.start)

def to_rgb(color):
    """ 0xffffff -> (255, 255, 255)."""
    b = (color & 255).astype(np.uint8)
    g = ((color >> 8) & 255).astype(np.uint8)
    r = ((color >> 16) & 255).astype(np.uint8)
    return (r, g, b)

def from_rgb(r,g,b):
    """ (255, 255, 255) -> 0xffffff """
    return (r.astype(np.uint32) << 16) + (g.astype(np.uint32) << 8) + b.astype(np.uint32)


class Effect(object):
    palette = ""
    delay = 0.1

    def __init__(self, palette=[0xffffff], sizex = 140, sizey = 140):
        self.palette = palette
        self.framenumber = 0
        self.sizex = sizex
        self.sizey = sizey
        self.configs = {}

    def drawFrame(self, positions):
        bitmap = np.zeros([self.sizex,self.sizey])
        bitmap[20:40, 20:40] = self.palette[0]  ###  example
        return bitmap

    def make_default_palette(self):
        rgb0 = (00, 0xa5, 0xa5)
        rgb1 = (00, 0xff, 0xff)
        ranges = [np.arange(i, j+1, 10) for (i, j) in zip(rgb0, rgb1)]
        palette = [(r, g, b) for r in ranges[0] for g in ranges[1] for b in ranges[2]]
        return np.array([from_rgb(*rgb) for rgb in palette],
                        dtype=np.uint32)

    def load_palette(self, fname='palettes/green_grass'):
        palette_matr= np.loadtxt(fname, delimiter=',').astype(np.uint8)
        return from_rgb(palette_matr[:,0], palette_matr[:,1], palette_matr[:,2])

    def get_palette(self):
        palettes_dir = 'palettes'
        palettes = [self.make_default_palette()]
        for p in os.listdir(palettes_dir):
            try:
                palette = self.load_palette(os.path.join(palettes_dir, p))
                palettes.append(palette)
            except ValueError:
                pass
        return random.choice(palettes)[::20]

    def reset(self):
        num_sources = np.random.randint(1, 5)
        self.configs = {}
        [self.add_config() for i in range(num_sources)]

    def make_one_config(self):
        config_id = max([0] + self.configs.keys()) + 1

        return config_id, {
                'center': np.random.uniform([0, 0], [self.sizex, self.sizey]),
                'radiusx': np.random.normal(0),
                'radiusy': np.random.normal(0),

                'scalex': np.random.normal(2, 1),
                'scaley': np.random.normal(2, 1),

                'power': np.random.normal(0.5, 0.1),
                'speed': np.random.normal(0.1, 0.01),
                'start_time': self.framenumber,
                'palette': self.get_palette(),
        }

    def add_config(self, config_id=None, config=None):
        if config is None:
            config_id, config = self.make_one_config()
        self.configs[config_id] = config
        return config_id

    def remove_config(self, config_id):
        del self.configs[config_id]


class CenterSquareFillEffect(Effect):

    def __init__(self, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(CenterSquareFillEffect, self).__init__(palette, sizex, sizey)
        self.centerx = int(self.sizex / 2)
        self.centery = int(self.sizey / 2)
        self.bitmap = np.zeros([self.sizex,self.sizey])

    def drawFrame(self, positions):

        i = self.framenumber

        self.bitmap[self.centerx-i:self.centerx+i,self.centery+i] =  self.palette[0]
        self.bitmap[self.centerx+i,self.centery-i:self.centery+i] =  self.palette[0]
        self.bitmap[self.centerx-i,self.centery-i:self.centery+i] =  self.palette[0]
        self.bitmap[self.centerx-i:self.centerx+i,self.centery-i] =  self.palette[0]


        self.framenumber += 1
        if( self.framenumber > self.centerx-1):
            self.bitmap = np.zeros([self.sizex,self.sizey])
            self.framenumber = 1


        return self.bitmap

class NumpyEffect(Effect):
    def drawFrame(self, positions):
        i = self.framenumber
        rgba = self.drawNumpyFrame(i)

        bitmap = from_rgb(rgba[:,:,0], rgba[:,:,1], rgba[:,:,2])

        self.framenumber += 1
        return bitmap

class CairoEffect(NumpyEffect):
    def drawNumpyFrame(self, i):
        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.sizex, self.sizey)
        ctx = cairo.Context(img)

        color = [x/255. for x in to_rgb(self.palette[0])]
        ctx.set_source_rgb(*color)

        self.drawOnCairoCtx(ctx, i)

        ctx.stroke()

        rgba = np.frombuffer(img.get_data(), np.uint8)
        rgba.shape = (self.sizex, self.sizey, 4)
        return rgba

    def drawOnCairoCtx(self, ctx, i):
        raise NotImplementedError

class CenterCircleFillEffect(CairoEffect):

    def __init__(self, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(CenterCircleFillEffect, self).__init__(palette, sizex, sizey)
        self.centerx = int(self.sizex / 2)
        self.centery = int(self.sizey / 2)
        self.radius = min(self.centerx, self.centery)

    def drawOnCairoCtx(self, ctx, i):
        radius = i % self.radius
        ctx.arc(self.centerx, self.centery, radius, 0, 2*pi)
        ctx.fill()

class WaveEffect(Effect):

    def __init__(self, direction = 0, palette = [0x0000ff,0x006666,0x004444,0x002222,0x000000], sizex = 140, sizey = 140):
        super(WaveEffect, self).__init__(palette, sizex, sizey)
        self.direction = direction
        if(self.direction%2 == 0):
            self.size = self.sizex
        else:
            self.size = self.sizey
        self.framenumber = 9

    def drawFrame(self, positions):

        bitmap = np.zeros([self.sizex,self.sizey])

        if(self.direction%2 == 0):
            x = self.framenumber
            bitmap[x][:]=  self.palette[0] #0x0000ff
            if x>8:
                bitmap[x-8][:]= self.palette[4] #0x000000
                bitmap[x-7][:]= self.palette[3] #0x002222
                bitmap[x-6][:]= self.palette[2] #0x004444
                bitmap[x-5][:]= self.palette[1] #0x006666
                bitmap[x-4][:]= self.palette[0]
                bitmap[x-3][:]= self.palette[0]
                bitmap[x-2][:]= self.palette[0]
                bitmap[x-1][:]= self.palette[0]
        else:
            y = self.framenumber
            bitmap[:][y]= self.palette[0] #0x0000ff
            if y>8:
                bitmap[:][y-8]= self.palette[4] #0x000000
                bitmap[:][y-7]= self.palette[3] #0x002222
                bitmap[:][y-6]= self.palette[2] #0x004444
                bitmap[:][y-5]= self.palette[1] #0x006666
                bitmap[:][y-4]= self.palette[0]
                bitmap[:][y-3]= self.palette[0]
                bitmap[:][y-2]= self.palette[0]
                bitmap[:][y-1]= self.palette[0]

        self.framenumber += 1
        if( self.framenumber >= self.size):
            self.framenumber = 0
        return bitmap

class FanEffect(CairoEffect):

    def __init__(self, thickness = 35, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(FanEffect, self).__init__(palette, sizex, sizey)
        self.centerx = int(self.sizex / 2)
        self.centery = int(self.sizey / 2)
        self.radius = min(self.centerx, self.centery)
        self.thickness = thickness


    def drawOnCairoCtx(self, ctx, i):
        alpha = self.framenumber * pi / 180.
        betha = alpha + self.thickness * pi/180.

        for t0 in [0, pi/2, pi, 3*pi/2]:
            ctx.move_to(self.centerx, self.centery)
            ctx.arc(self.centerx, self.centery, self.radius-5, t0+alpha, t0+betha)
            ctx.line_to(self.centerx, self.centery)
            ctx.fill()

class RipplesEffect(NumpyEffect):
    def __init__(self, auto_reset_frames=200, *args, **kwargs):
        # Reconfigre after this many frames. None means don't autoreconfigure.
        self.period = auto_reset_frames

        return super(RipplesEffect, self).__init__(*args, **kwargs)

    def func(self, t, x, y, config):
        return ripples.func(t, x, y, config)

    def drawNumpyFrame(self, i):
        if self.period and i % self.period == 0:
            self.reset()

        if not self.configs:
            return np.zeros((self.sizex, self.sizey, 3))

        x = np.arange(0, self.sizex)
        y = np.arange(0, self.sizey)
        xx, yy = np.meshgrid(x, y)

        all_ripples = [ripples.render_config(self.sizex, self.sizey, i, config) for config in self.configs.values()]

        # Null ripple ensures black background.
        null_ripple = np.zeros_like(all_ripples[0])
        null_ripple[:,:,3]=0.01
        all_ripples.append(null_ripple)

        with Benchmark("blend"):
            res = self.blend_rgba_ripples(all_ripples)
        return res

    def blend_rgba_ripples(self, all_ripples):
        """Blends a list of ripples.

        Args:
            all_ripples: list of RGBA ripple matrices.
        Returns:
            Single RGB ripple image.
        """
        total_rgba = sum(all_ripples)
        total_a = np.atleast_3d(total_rgba[:,:,3])

        # Same shape as ripple, but alpha channel is ignored.
        res = np.zeros(all_ripples[0].shape[:2] + (4,))

        for ripple in all_ripples:
            alpha = np.atleast_3d(ripple[:,:,3])
            res += ripple * alpha

        return res[:,:,:3] / total_a


### testing code


def main():

    root = Tkinter.Tk()

    size = 140

    w = Tkinter.Canvas(root, width=size, height=size)
    w.pack()
    #point = w.create_rectangle(70,70,71,71, fill="blue")

    center = size/2
    delay = 0

    try:

        #currentEffect = FanEffect()
        #currentEffect = WaveEffect()
        #currentEffect = WaveEffect(direction = 1)
        #currentEffect = CenterCircleFillEffect()
        currentEffect = RipplesEffect()

        #currentEffect = CenterSquareFillEffect()

        for f in range(1000):
            bitmap = currentEffect.drawFrame().astype(np.uint32)

            r, g, b = to_rgb(bitmap)

            data = np.zeros(bitmap.shape + (3,), dtype=np.uint8)
            data = np.dstack((r, g, b))
            im = Image.fromstring("RGB", bitmap.shape, data.tostring())
            tk_im = ImageTk.PhotoImage(im)
            w.create_image((0, 0), image=tk_im, anchor=Tkinter.NW)

            root.update()
            time.sleep(delay)


    except Tkinter.TclError:
        pass # to avoid errors when the window is closed

    print "done"
    root.mainloop()
    exit(0)

if __name__ == "__main__":
    main()
