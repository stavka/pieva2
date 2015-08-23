import time
import numpy as np
cimport numpy as np
cimport cython
import sys

from libc.math cimport sin, log, exp, pow



DTYPE = np.int
ctypedef np.int_t DTYPE_t


class Benchmark(object):
    def __init__(self, name):
        self.name= name
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, *args):
        if 'debug' in sys.argv:
            print self.name + ": " + str(time.time() - self.start)


@cython.cdivision(True) # turn off /0 check.
@cython.boundscheck(False) # turn of bounds-checking for entire function
cdef func_(np.ndarray[np.double_t, ndim=2] res, int t, int sizex, int sizey, double centerx, double centery, double scalex, double scaley, double power, double speed):

    cdef int x, y


    cdef double i, j
    cdef double a = t*speed

    for x in range(sizex):
        for y in range(sizey):

            i = ((x-centerx)/scalex)
            j = ((y-centery)/scaley)
            res[x, y] = \
                    sin(( 
                            i*i
                            +
                            j*j
                        ) ** power
                    - a) + 1


@cython.cdivision(True) # turn off /0 check.
@cython.boundscheck(False) # turn of bounds-checking for entire function
cdef inline make_mask_(np.ndarray[np.double_t, ndim=2] res, int sizex, int sizey, int t, double centerx, double centery, double scalex, double scaley, double start_time, double speed):

    cdef double age = t - start_time
    cdef double sigm = (age + 5) * speed
    cdef double a = -4*log(2) / sigm**2

    cdef int x, y
    cdef double xx, yy
    for x in range(sizex):
        for y in range(sizey):
            xx = (x-centerx) / scalex;
            yy = (y-centery) / scaley;

            res[x, y] = exp(( xx**2 + yy**2 ) * a)


cdef np.ndarray[np.double_t, ndim=3] _render_config(int sizex, int sizey, int t, double centerx, double centery, double scalex, double scaley, double power,
         double speed, double start_time, np.ndarray[np.uint32_t, ndim=1] palette):
    """Renders a single frame for a single ripple given by config.

    Args:
        t: int frame number
        config: a ripple config dict
    Returns:
        RGBA ripple image.
    """
    cdef np.ndarray[np.double_t, ndim=1] bins
    cdef np.ndarray[np.double_t, ndim=2] res, mask
    cdef np.ndarray[np.uint8_t, ndim=2] r, g, b
    cdef np.ndarray[np.double_t, ndim=3] rgba

    with Benchmark("_render"):
        res = np.zeros([sizex, sizey], dtype=np.double)
        with Benchmark("func_"):
            func_(res, t, sizex, sizey, centerx, centery, scalex, scaley, power, speed)

        #with Benchmark("0"):
            bins = np.linspace(np.min(res), np.max(res), len(palette))

        with Benchmark("digitize"):
            palette_idxs = np.digitize(res.flatten(), bins[:-1])

        with Benchmark("hui"):
            r = np.zeros([sizex, sizey], dtype=np.uint8)
            g = np.zeros([sizex, sizey], dtype=np.uint8)
            b = np.zeros([sizex, sizey], dtype=np.uint8)

            to_rgb(r, g, b, palette[palette_idxs].reshape((<object>res).shape))
        with Benchmark("hui2"):
            mask = np.zeros([sizex, sizey], dtype=np.double)
            make_mask_(mask, sizex, sizey, t, centerx, centery, scalex, scaley, start_time, speed)
            rgba = np.dstack((r, g, b, mask))

    return rgba

def render_config(sizex, sizey, t, config):
    assert config['scalex'] != 0
    assert config['scaley'] != 0
    assert config['speed'] != 0

    return _render_config(
            sizex, sizey, t, config['center'][0], config['center'][1],
            config['scalex'], config['scaley'], config['power'],
            config['speed'], config['start_time'], config['palette'])

@cython.cdivision(True) # turn off /0 check.
@cython.boundscheck(False) # turn of bounds-checking for entire function
cdef to_rgb(np.ndarray[np.uint8_t, ndim=2] r, np.ndarray[np.uint8_t, ndim=2] g,
            np.ndarray[np.uint8_t, ndim=2] b, np.ndarray[np.uint32_t, ndim=2] color):
    """ 0xffffff -> (255, 255, 255)."""
    cdef int sizex = (<object>color).shape[0]
    cdef int sizey = (<object>color).shape[1]

    cdef int x, y
    for x in range(sizex):
        for y in range(sizey):
            b[x, y] = (color[x,y] & 255)
            g[x, y] = ((color[x,y] >> 8) & 255)
            r[x, y] = ((color[x,y] >> 16) & 255)
