#!/usr/bin/python
from pieva import *
from screen import Screen
import numpy as np

from bibliopixel.drivers.driver_base import DriverBase

class DriverPieva(DriverBase):
    def __init__(self, num=0, width=0, height=0):
        super(DriverPieva, self).__init__(num, width, height)
        self.screen = Screen(sections)
        self.screen.dimm(0)
        self.pixels = width * height
        self.width = width
        self.height = height

    def update(self, data):
        if len(data) != self.pixels * 3:
            print "Data length mismatch"
            return

        bitmap = np.zeros([140, 140])
        for i in range(self.pixels):
            r = data[i * 3 + 0]
            g = data[i * 3 + 1]
            b = data[i * 3 + 2]
            rgb = (r << 16) + (g << 8) + b
            self.draw(bitmap, i, rgb)
        self.screen.send(bitmap)

    def draw(self, bitmap, i, rgb):
        bitmap[i % self.width][i / self.height] = rgb

class DriverPievaX4(DriverPieva):
    def draw(self, bitmap, i, rgb):
        bitmap[i % self.width][i / self.height] = rgb
        bitmap[i / self.height][139 - (i % self.width)] = rgb
        bitmap[139 - (i / self.height)][i % self.width] = rgb
        bitmap[139 - (i % self.width)][139 - (i / self.height)] = rgb

class DriverPievaX4Rev(DriverPieva):
    def draw(self, bitmap, i, rgb):
        bitmap[70 - (i % self.width)][70 - (i / self.height)] = rgb
        bitmap[70 - (i / self.height)][70 + (i % self.width)] = rgb
        bitmap[70 + (i / self.height)][70 - (i % self.width)] = rgb
        bitmap[70 + (i % self.width)][70 + (i / self.height)] = rgb
