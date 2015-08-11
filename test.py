#!/usr/bin/python
from argparse import ArgumentParser
from pieva import *
import fastopc as opc
import time
from screen import *

leds = opc.FastOPC()

def testPattern(pattern):
    global testDotIndex
    pixels = []
    for i in range(len(pattern)):
        if i == testDotIndex:
            pixels += testDot
        else:
            pixels += testBlank
    testDotIndex = testDotIndex + 1
    if(testDotIndex >= len(pattern)):
        testDotIndex = 0
    return pixels
    
def blank(pattern):
    pixels = []
    for led in pattern:
        pixels += testBlank
    return pixels

def test(testSectionIdx):
    for t in range(len(sections[testSectionIdx]['pattern'])):
        s = 0
        pixels = []
        startTime = time.time()
        for section in sections:
            if s == testSectionIdx:
                pixels += testPattern(section['pattern'])
            else:
                pixels += blank(section['pattern'])
            s = s +1
         
        leds.putPixels(0, pixels)
        endTime = time.time()
        print "pushing pixels in", (endTime - startTime), "s"
        if None != screen:
            screen.putPixels(0, pixels)
        time.sleep(0.05)

parser = ArgumentParser(description = "Play test sequences")
parser.add_argument("testSection", type=int, action="store", default=None, nargs="?", help=" - which section to test. All sections will be tested if omitted")
parser.add_argument("--server", action="store", default=None, help="additional OPC server for debug purposes")
parser.add_argument("--X", action="store", default=None, help="Fill one corner of the screen")
parser.add_argument("--palette", action="store", default=None, type=open, help="Cycle a palette")
parser.add_argument("--image", action="store", default=None, help="bitmap")
parser.add_argument("--A", action="store", default=None, help="annimation")

cliargs = parser.parse_args()

testDotIndex = 0
testBlank = [0, 0, 0]
testDot = [255, 255, 255]

if None != cliargs.server:
    screen = opc.FastOPC(cliargs.server)
else:
    screen = None


if None != cliargs.testSection:
    currSection = cliargs.testSection
    print "Testing section", currSection 
else:
    currSection = 0
    print "Testing all sections"
print "Control-C to interrupt"

#~ print testPattern(sections[0]['pattern'])

if None != cliargs.A:
    
    
    
    bitmap = np.zeros([140,140])
    screen = Screen(sections)
    screen.send(bitmap)
    delay = 0.1

    if cliargs.A == '1':
        for x in range(140):
            for y in range(140):
                bitmap[x][y]=0x00ffffff
            screen.send(bitmap)
            time.sleep(delay)
    elif cliargs.A == '2':
        for x in range(140):
            for y in range(140):
                bitmap[x][y]=0x0000ff
                if x>8:
                    bitmap[x-8][y]=0x000000
                    bitmap[x-7][y]=0x002222
                    bitmap[x-6][y]=0x004444
                    bitmap[x-5][y]=0x006666
            screen.send(bitmap)
            time.sleep(delay)
    elif cliargs.A == '3':
        for r in range(70):
            for i in range(10):
                bitmap[70+r][70+i]=0xffffff
                bitmap[70-r][70+i]=0xffffff
                bitmap[70+i][70+r]=0xffffff
                bitmap[70+i][70-r]=0xffffff
            screen.send(bitmap)
            time.sleep(delay)

    elif cliargs.A == '4':
        center = 70
        for i in range(center):
            for y in range(-i,i):
                bitmap[center+y][center+i] =  0xffffff
                bitmap[center+i][center+y] =  0xffffff
                bitmap[center-i][center+y] =  0xffffff
                bitmap[center+y][center-i] =  0xffffff
            screen.send(bitmap)
            time.sleep(0.1)

    print "done"
    exit(0)


if None != cliargs.X:
    bitmap = np.zeros([140,140])
    for x in range(40):
        for y in range(40):
            bitmap[x][y]=0x00ffffff
        #bitmap[116-x][x]=0x00ffffff
    screen = Screen(sections)
    screen.send(bitmap)
    time.sleep(0.1)
    print "done"
    exit(0)

if None != cliargs.palette:
    from palette import ColorPalette
    screen = Screen(sections)
    palette = ColorPalette(CSVfilename=cliargs.palette)
    bitmap = np.zeros([140, 140])
    i = 0
    while True:
        bitmap[:] = palette.get32bitColor(i)
        startTime = time.time()
        screen.send(bitmap)
        endTime = time.time()
        i += 1;
        if i > 255:
            i = 0
        print (endTime - startTime)
        timeToWait = 1/48. - (endTime - startTime)
        if timeToWait < 0:
            timeToWait = 0
        time.sleep(timeToWait)
    
if None != cliargs.image:
    import matplotlib.image as mpimg
    img = mpimg.imread(cliargs.image)

    if img.dtype == np.uint8:
        img = img.astype(np.uint32)
    elif img.dtype == np.float32:
        img = (img * 255).astype(np.uint32)

    bitmap = img[:,:,0] << 16 | img[:,:,1] << 8 | img[:,:,2]

    print bitmap, bitmap.shape
    print "Sending", len(bitmap[0]), "X", len(bitmap), "bitmap", cliargs.image
    screen = Screen(sections)
    screen.send(bitmap)
    exit(0)

while True:
    test(currSection)
    if None == cliargs.testSection:
        currSection += 1
        if currSection >= len(sections):
            currSection = 0
