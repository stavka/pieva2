import time
import numpy as np
cimport numpy as np
cimport cython

from libc.math cimport sin, log, exp, pow



DTYPE = np.int
ctypedef np.int_t DTYPE_t


class Benchmark(object):
    def __init__(self, name):
        self.name= name
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, *args):
        print self.name + ": " + str(time.time() - self.start)


@cython.cdivision(True) # turn off /0 check.
@cython.boundscheck(False) # turn of bounds-checking for entire function
cdef inline np.ndarray[np.double_t, ndim=2] func_(int t, int sizex, int sizey, double centerx, double centery, double scalex, double scaley, double power, double speed):
    cdef np.ndarray[np.double_t, ndim=2] res = np.zeros([sizex, sizey], dtype=np.double)

    cdef int x, y

    for x in range(sizex):
        for y in range(sizey):
            res[x, y] = \
                    sin(( 
                            ((x-centerx)/scalex) ** 2
                            +
                            ((y-centery)/scaley) ** 2
                        ) ** power
                    - t * speed) + 1
    return res


@cython.cdivision(True) # turn off /0 check.
@cython.boundscheck(False) # turn of bounds-checking for entire function
cdef inline np.ndarray[np.double_t, ndim=2] make_mask_(int sizex, int sizey, int t, double centerx, double centery, double scalex, double scaley, double start_time, double speed):
    cdef np.ndarray[np.double_t, ndim=2] res = np.zeros([sizex, sizey], dtype=np.double)

    cdef double age = t - start_time

    cdef double sigm = (age + 5) * speed

    cdef double xx, yy
    cdef int x, y
    for x in range(sizex):
        for y in range(sizey):
            xx = (x-centerx) / scalex;
            yy = (y-centery) / scaley;

            res[x, y] = exp(-4*log(2) * ((xx)**2 + (yy)**2) / sigm**2)
    return res


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
    cdef np.ndarray[np.double_t, ndim=3] rgba

    with Benchmark("_render"):
        with Benchmark("func_"):
            res = func_(t, sizex, sizey, centerx, centery, scalex, scaley, power, speed) + 1

        #with Benchmark("0"):
            bins = np.linspace(np.min(res), np.max(res), len(palette))

        with Benchmark("digitize"):
            palette_idxs = np.digitize(res.flatten(), bins[:-1])

        with Benchmark("hui"):
            r, g, b = to_rgb(palette[palette_idxs].reshape((<object>res).shape))
        with Benchmark("hui2"):
            mask = make_mask_(sizex, sizey, t, centerx, centery, scalex, scaley, start_time, speed)
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

def to_rgb(color):
    """ 0xffffff -> (255, 255, 255)."""
    b = (color & 255).astype(np.uint8)
    g = ((color >> 8) & 255).astype(np.uint8)
    r = ((color >> 16) & 255).astype(np.uint8)
    return (r, g, b)
