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

class Bitmap():

    def __init__(self, sizex, sizey):
        self.bitmap = np.zeros([sizex,sizey])

    def set(self, x, y, colour):
        try:
            self.bitmap[x,y] = colour
        except:
            pass


def to_rgb(color):
    """ 0xffffff -> (255, 255, 255)."""
    b = np.array(color & 255).astype(np.uint8)
    g = np.array((color >> 8) & 255).astype(np.uint8)
    r = np.array((color >> 16) & 255).astype(np.uint8)
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

    def drawFrame(self):
        bitmap = np.zeros([self.sizex,self.sizey])
        bitmap[20:40, 20:40] = self.palette[0]  ###  example
        return bitmap


class CenterSquareFillEffect(Effect):

    def __init__(self, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(CenterSquareFillEffect, self).__init__(palette, sizex, sizey)
        self.centerx = int(self.sizex / 2)
        self.centery = int(self.sizey / 2)
        self.bitmap = np.zeros([self.sizex,self.sizey])

    def drawFrame(self):

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
    def drawFrame(self):
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

    def drawFrame(self):

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
    # Reconfigre after this many frames
    period = 100

    # Configuration
    center = None
    radiusx = None
    radiusy = None
    scalex = None
    scaley = None
    power = None
    speed = None

    def __init__(self, *args, **kwargs):
        #default_palette = self.make_default_palette()
        default_palette = self.load_palette()
        kwargs.setdefault('palette', default_palette)
        return super(RipplesEffect, self).__init__(*args, **kwargs)

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
        return random.choice(palettes)

    def reset(self):
        self.center = np.random.uniform([0, 0], [self.sizex, self.sizey])
        self.radiusx = np.random.normal(0)
        self.radiusy = np.random.normal(0)

        self.scalex = np.random.normal(2, 1)
        self.scaley = np.random.normal(2, 1)

        self.power = np.random.normal(0.5, 0.1)
        self.speed = np.random.normal(0.1, 0.01)
        self.palette = self.get_palette()

    def func(self, t, x, y):
        t = float(t)
        return np.sin((
                    ((x-self.center[0])/self.scalex)**2
                    +
                    ((y-self.center[0])/self.scaley)**2
                )**(self.power)
                - t*self.speed)

    def drawNumpyFrame(self, i):
        if i % self.period == 0:
            self.reset()

        x = np.arange(0, self.sizex)
        y = np.arange(0, self.sizey)
        xx, yy = np.meshgrid(x, y, sparse=True)

        res = self.func(i, xx,yy)
        bins = np.linspace(np.min(res), np.max(res), len(self.palette))

        palette_idxs = np.digitize(res.flatten(), bins, right=True).reshape(res.shape)

        r, g, b = to_rgb(np.array(self.palette)[palette_idxs])

        return np.dstack((r, g, b))


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
