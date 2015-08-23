#!/usr/bin/python
#from argparse import ArgumentParser
#from pieva import *
#import fastopc as opc
import time
import Tkinter
import random

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
    

# Generate random list of list RGBs
def RGBs(num):
    #random.seed(time.localtime)
    return [[random.randint(0,255) for i in range(0,3)] for j in range(0,num)]

# Convert RGB to Hex
def rgb2Hex(rgb_tuple):
    return '#%02x%02x%02x' % tuple(rgb_tuple)
    
    
# Circles moving from center
class circleWobbleEffect:
    def __init__(self, sizex = 140, sizey = 140):   
        self.sizex = sizex
        self.sizey = sizey
        self.centerx = self.sizex / 2
        self.centery = self.sizey / 2
        
        self.radius = 70
        self.thickness = 10        
        self.increment = self.radius / self.thickness
        
        # Random number for the color
        self.colors=RGBs(self.increment)        
        self.position = 0;
    
    # Draw on canvas and then create image from canvas
    def drawFrame(self, w):             
        # Fill the canvas with black        
        w.create_rectangle(0, 0, self.sizex, self.sizey, fill='black')
          
        x = 0
        for x in xrange(0, self.increment):
            size = x * self.thickness * 2
            w.create_oval(self.centerx - size - self.position, self.centery - size - self.position, self.centerx + size + self.position, self.centery + size + self.position, width=self.thickness, outline=rgb2Hex(self.colors[x]))
        
        self.position +=1
        if( self.position == self.thickness * 10):
            self.position = 0
            
        
### testing code
def main():
    size = 140
    
    root = Tkinter.Tk()
    w = Tkinter.Canvas(root, width=size, height=size); 
    w.pack()

    # delay is in second
    delay = 0.01
    
    
    try:
        # Initialise effect
        currentEffect = circleWobbleEffect()       
        
        # Loop forever and ever
        while True:
            # Delete all canvas items
            # Compulsory otherwise the program slows down a lot
            w.delete(Tkinter.ALL)
            
            # Draw current effect on screen
            currentEffect.drawFrame(w) 
            
            root.update()
            time.sleep(delay)  
    
    
    except Tkinter.TclError:
        pass # to avoid errors when the window is closed
        
    print "done"
    root.mainloop()
    exit(0)


if __name__ == "__main__":
    main()
