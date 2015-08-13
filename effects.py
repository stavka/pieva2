#!/usr/bin/python
#from argparse import ArgumentParser
#from pieva import *
#import fastopc as opc
import time
import Tkinter
import numpy as np
from math import sin
from math import radians
#from screen import *

class Bitmap():
    
    def __init__(self, sizex, sizey):
        self.bitmap = np.zeros([sizex,sizey])
        
    def set(self, x, y, colour):
        try:
            self.bitmap[x,y] = colour
        except:
            pass


def circle(bitmap, x0, y0, radius, colour=0xffffff):
    f = 1 - radius
    ddf_x = 1
    ddf_y = -2 * radius
    x = 0
    y = radius
    bitmap.set(x0, y0 + radius, colour)
    bitmap.set(x0, y0 - radius, colour)
    bitmap.set(x0 + radius, y0, colour)
    bitmap.set(x0 - radius, y0, colour)
 
 
    while x < y:
        if f >= 0: 
            y -= 1
            ddf_y += 2
            f += ddf_y
        x += 1
        ddf_x += 2
        f += ddf_x    
        bitmap.set(x0 + x, y0 + y, colour)
        bitmap.set(x0 - x, y0 + y, colour)
        bitmap.set(x0 + x, y0 - y, colour)
        bitmap.set(x0 - x, y0 - y, colour)
        bitmap.set(x0 + y, y0 + x, colour)
        bitmap.set(x0 - y, y0 + x, colour)
        bitmap.set(x0 + y, y0 - x, colour)
        bitmap.set(x0 - y, y0 - x, colour)


def arc(bitmap, x0, y0, radius, alpha, beta, colour=0xffffff):
    f = 1 - radius
    ddf_x = 1
    ddf_y = -2 * radius
    x = 0
    y = radius
    
    alpha = radius * sin(radians(alpha))
    beta = radius * sin(radians(beta))
    
    if(alpha <= 0 and beta >= 0):
        bitmap.set(x0, y0 + radius, colour)
        bitmap.set(x0, y0 - radius, colour)
        bitmap.set(x0 + radius, y0, colour)
        bitmap.set(x0 - radius, y0, colour)
 
 
    while x < y:        
            if f >= 0: 
                y -= 1
                ddf_y += 2
                f += ddf_y
            x += 1
            ddf_x += 2
            f += ddf_x  
            #if( x <> 0):
                #print float(y)/x
            #if( x <> 0 and (float(y)/x > alpha and float(y)/x < beta)  ):  
            if( float(x) > alpha and float(x) < beta ):  
                #bitmap.set(x0 + x, y0 + y, colour)
                bitmap.set(x0 - x, y0 + y, colour)
                bitmap.set(x0 + y, y0 + x, colour)
                bitmap.set(x0 - y, y0 - x, colour)
                
                
                bitmap.set(x0 + x, y0 - y, colour)
                #bitmap.set(x0 - x, y0 - y, colour)
                #bitmap.set(x0 - y, y0 + x, colour)
                #bitmap.set(x0 + y, y0 - x, colour)
                
def fill(image, color):
    """Fill image with a color=(r,b,g)."""
    r,g,b = color
    width = image.width()
    height = image.height()
    hexcode = "#%02x%02x%02x" % (r,g,b)
    horizontal_line = "{" + " ".join([hexcode]*width) + "}"
    image.put(" ".join([horizontal_line]*height))


class Effect(object):
    palette = ""
    delay = 0.1

    def __init__(self, palette, sizex = 140, sizey = 140):
        self.palette = palette
        self.framenumber = 0
        self.sizex = sizex
        self.sizey = sizey

    def drawFrame(self):
        bitmap = np.zeros([self.sizex,self.sizey])
        for x in range(20,40):  ###  example
            for y in range(20,40):
                bitmap[x][y]=0xffffff
        return bitmap
    
    
class CenterSquareFillEffect(Effect):
    
    def __init__(self, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(CenterSquareFillEffect, self).__init__(palette, sizex, sizey)
        self.center = int(self.sizex / 2)
        self.bitmap = np.zeros([self.sizex,self.sizey])
        #self.bitmap = bitmap = Bitmap(self.sizex,self.sizey)
    
    def drawFrame(self):
        
        #bitmap = np.zeros([self.sizex,self.sizey])
        
        i = self.framenumber
        
        for y in range(-i,i):
            self.bitmap[center+y][center+i] =  self.palette[0]
            self.bitmap[center+i][center+y] =  self.palette[0]
            self.bitmap[center-i][center+y] =  self.palette[0]
            self.bitmap[center+y][center-i] =  self.palette[0]
        self.bitmap[center-i][center-i] =  self.palette[0]
                
        self.framenumber += 1
        if( self.framenumber > self.center):
            self.framenumber = 0
        return self.bitmap
    
class CenterCircleFillEffect(Effect):
    
    def __init__(self, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(CenterCircleFillEffect, self).__init__(palette, sizex, sizey)
        self.centerx = int(self.sizex / 2)
        self.centery = int(self.sizey / 2)
        self.radius = min(self.centerx, self.centery)
        self.bitmap = Bitmap(self.sizex,self.sizey)
    
    def drawFrame(self):
        
        #bitmap = np.zeros([self.sizex,self.sizey])
        
        i = self.framenumber
        
        circle(self.bitmap, self.centerx, self.centery, i, self.palette[0])
        
                
        self.framenumber += 1
        if( self.framenumber > self.radius):
            self.framenumber = 0
        return self.bitmap.bitmap

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
            for y in range(self.sizey-1):
                bitmap[x][y]=  self.palette[0] #0x0000ff
                if x>8:
                    bitmap[x-8][y]= self.palette[4] #0x000000
                    bitmap[x-7][y]= self.palette[3] #0x002222
                    bitmap[x-6][y]= self.palette[2] #0x004444
                    bitmap[x-5][y]= self.palette[1] #0x006666
                    bitmap[x-4][y]= self.palette[0]
                    bitmap[x-3][y]= self.palette[0]
                    bitmap[x-2][y]= self.palette[0]
                    bitmap[x-1][y]= self.palette[0]
        else:
            y = self.framenumber
            for x in range(self.sizex-1):
                bitmap[x][y]= self.palette[0] #0x0000ff
                if y>8:
                    bitmap[x][y-8]= self.palette[4] #0x000000
                    bitmap[x][y-7]= self.palette[3] #0x002222
                    bitmap[x][y-6]= self.palette[2] #0x004444
                    bitmap[x][y-5]= self.palette[1] #0x006666
                    bitmap[x][y-4]= self.palette[0]
                    bitmap[x][y-3]= self.palette[0]
                    bitmap[x][y-2]= self.palette[0]
                    bitmap[x][y-1]= self.palette[0]
                
        self.framenumber += 1
        if( self.framenumber >= self.size):
            self.framenumber = 0
        return bitmap

class FanEffect(Effect):
    
    def __init__(self, thickness = 15, palette = [0xffffff,], sizex = 140, sizey = 140):
        super(FanEffect, self).__init__(palette, sizex, sizey)
        self.centerx = int(self.sizex / 2)
        self.centery = int(self.sizey / 2)
        self.radius = min(self.centerx, self.centery)
        self.thickness = thickness
    
    def drawFrame(self):
        
        bitmap = Bitmap(self.sizex,self.sizey)
        
        alpha = self.framenumber
        
        for r in range(1, self.radius):
            arc(bitmap, self.centerx, self.centery, self.radius, alpha, alpha+self.thickness )
                
        self.framenumber += 1
        if( self.framenumber > 90-self.thickness):
            self.framenumber = 0
        return bitmap.bitmap

### testing code

root = Tkinter.Tk()

size = 140

w = Tkinter.Canvas(root, width=size, height=size)
w.pack()
#point = w.create_rectangle(70,70,71,71, fill="blue")

center = size/2
delay = 0

try:
    
    currentEffect = FanEffect()
    #currentEffect = WaveEffect()
    #currentEffect = WaveEffect(direction = 1)
    #currentEffect = CenterCircleFillEffect()
    
    i = Tkinter.PhotoImage(width=size,height=size)
    
    for f in range(1000):
        bitmap = currentEffect.drawFrame()
             
        fill(i, (0,0,0))           
        
        for x in range(size):
             for y in range(size):
                 if not bitmap[x,y] == 0:
                     i.put("#%06x" % bitmap[x,y],(x,y))
        w.create_image(0, 0, image = i, anchor=Tkinter.NW)
                
        root.update()
        time.sleep(delay)


except Tkinter.TclError:
    pass # to avoid errors when the window is closed

print "done"
root.mainloop()
exit(0)


