#!/usr/bin/python

import time
import sys

import numpy as np


class Benchmark(object):
    def __init__(self, name):
        self.name= name
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, *args):
        if 'debug' in sys.argv:
            print self.name + ": " + str(time.time() - self.start)


def func(t, x, y, config):
    t = float(t)
    return np.sin((
                ((x-config['center'][0])/config['scalex'])**2
                +
                ((y-config['center'][1])/config['scaley'])**2
            )**(config['power'])
            - t*config['speed']) + 1

def make_mask(t, x, y, config):
    centerx, centery = config['center']

    xx = (x-centerx) / config['scalex']
    yy = (y-centery) / config['scaley']

    age = t - config['start_time']

    sigm = (age + 5) * (config['speed'])
    res = np.exp(-4*np.log(2) * ((xx)**2 + (yy)**2) / sigm**2)

    res.shape += (1,)
    return res

def to_rgb(color):
    """ 0xffffff -> (255, 255, 255)."""
    b = np.array(color & 255).astype(np.uint8)
    g = np.array((color >> 8) & 255).astype(np.uint8)
    r = np.array((color >> 16) & 255).astype(np.uint8)
    return (r, g, b)


def render_config(sizex, sizey, t, config):
    """Renders a single frame for a single ripple given by config.

    Args:
        t: int frame number
        config: a ripple config dict
    Returns:
        RGBA ripple image.
    """
    with Benchmark("_render"):
        x = np.arange(0, sizex)
        y = np.arange(0, sizey)
        xx, yy = np.meshgrid(x, y)

        with Benchmark("func"):
            res = func(t, xx, yy, config) + 1
            bins = np.linspace(np.min(res), np.max(res), len(config['palette']))

        with Benchmark("digitize"):
            palette_idxs = np.digitize(res.flatten(), bins[:-1]).reshape(res.shape)

        with Benchmark("hui"):
            r, g, b = to_rgb(np.array(config['palette'])[palette_idxs])
        with Benchmark("hui2"):
            mask = make_mask(t, xx, yy, config)
            rgba = np.dstack((r, g, b, mask))

        return rgba

