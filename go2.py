#!/usr/bin/python
from pieva import *
from palette import ColorPalette
from screen import Screen
from palette import ColorPalette
import numpy as np
import time
import fastopc as opc
import random
from core import NoiseGenerator

import OSC
import threading
import sys

#from pythonosc import dispatcher
#from pythonosc import osc_server


greenPalette = ColorPalette(CSVfilename="palettes/green_grass")
rainbowPalette = ColorPalette(CSVfilename="palettes/rainbow")
pinkPalette = ColorPalette(CSVfilename="palettes/pink")
mainPalette = greenPalette
flash=0

def display_img(filename):
    import matplotlib.image as mpimg
    img = mpimg.imread(filename)
    
    if img.dtype == np.uint8:
        img = img.astype(np.uint32)
    elif img.dtype == np.float32:
        img = (img * 255).astype(np.uint32)
    
    bitmap = img[:,:,0] << 16 | img[:,:,1] << 8 | img[:,:,2]
    print "Sending", len(bitmap[0]), "X", len(bitmap), "bitmap", filename
    global screen
    global flash
    flash = 1
    screen.send(bitmap)
    time.sleep(3)
    flash = 0


########### pyosc stuff
# define a message-handler function for the server to call.
def printing_handler(addr, tags, stuff, source):
    msg_string = "%s [%s] %s" % (addr, tags, str(stuff))
    print "OSCServer Got: '%s' from %s\n" % (msg_string, OSC.getUrlStr(source))
            
            # send a reply to the client.
    msg = OSC.OSCMessage("/printed")
    msg.append(msg_string)
    return msg

# define a message-handler function for the server to call.
def pallete_handler(addr, tags, stuff, source):
    msg_string = "%s [%s] %s" % (addr, tags, str(stuff))
    print "PHOSCServer Got: '%s' from %s\n" % (msg_string, OSC.getUrlStr(source))
    

    global mainPalette
    global greenPalette
    global rainbowPalette
    global pinkPalette
    if (stuff[0] == 0):
        print "Switching palette to green"
        mainPalette = greenPalette
        display_img('palettes/test.png')

    if (stuff[0] == 1):
        print "Switching palette to rainbow"
        mainPalette = rainbowPalette
    if (stuff[0] == 2):
        print "Switching palette to pink"
        mainPalette = pinkPalette

#    return msg

################


class NoiseParams:
    octaves = 1
    persistence = 0.5
    lacunarity = 2.0
    wavelength = 32
    xScrollSpeed = 0
    yScrollSpeed = 0
    amplitude = 127
    offset = 128 
    
    def __init__(self, octaves, persistence, lacunarity, wavelength, xScrollSpeed, yScrollSpeed, amplitude, offset):
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.wavelength = wavelength
        self.xScrollSpeed = xScrollSpeed
        self.yScrollSpeed = yScrollSpeed
        self.amplitude = amplitude
        self.offset = offset
        
#paletteFileCSV="palettes/green_grass"#
#paletteFileCSV="palettes/rainbow"
#paletteFileCSV="palettes/pink"
#mainPalette = ColorPalette(CSVfilename=paletteFileCSV)



width = 140
height = 140

sun = NoiseParams(
    octaves = 1, 
    persistence = 0.5, 
    lacunarity = 2.0, 
    wavelength = width * 8.0, 
    xScrollSpeed = 1, 
    yScrollSpeed = 0, 
    amplitude = 95, 
    offset = 140)

grass = NoiseParams(
    octaves = 4, 
    persistence = 0.702, 
    lacunarity = 2.0, 
    wavelength = width / 8, 
    xScrollSpeed = 0, 
    yScrollSpeed = 5, 
    amplitude = 120, 
    offset = 120)



screen = Screen(sections, ['127.0.0.1:7891'])
screen.dimm(0)

targetFPS = 24
targetFrameTime = 1./targetFPS
timeCounter = int(random.random() * 65535)

#dispatcher = dispatcher.Dispatcher()
#dispatcher.map("/MM_Remote/Control/objectPosition", set_pallete, "Set Pallete: " )
#dispatcher.map("/volume", set_pallete, "Pallete")

                
#server = osc_server.ThreadingOSCUDPServer(  ('127.0.0.1', 54321), dispatcher)
#print("Serving on {}".format(server.server_address))
#server.serve_forever()


###########################
# EXPERIMENT

listen_address = ('localhost', 54321)
send_address = ('localhost', 12345)



try:
    #c = OSC.OSCClient()
    #c.connect(listen_address)
    s = OSC.ThreadingOSCServer(listen_address)#, c)#, return_port=54321)

    print s
            
    # Set Server to return errors as OSCMessages to "/error"
    s.setSrvErrorPrefix("/error")
    # Set Server to reply to server-info requests with OSCMessages to "/serverinfo"
    s.setSrvInfoPrefix("/serverinfo")

    # this registers a 'default' handler (for unmatched messages),
    # an /'error' handler, an '/info' handler.
    # And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
    s.addDefaultHandlers()

    #s.addMsgHandler("/print", printing_handler)
    s.addMsgHandler("default", printing_handler)
    #s.addMsgHandler("/MM_Remote/Control/activeObjectsID", pallete_handler)
    s.addMsgHandler("/MM_Remote/Control/activeObjectsPosition", pallete_handler)


    # if client & server are bound to 'localhost', server replies return to itself!
    s.addMsgHandler("/printed", s.msgPrinter_handler)
    s.addMsgHandler("/serverinfo", s.msgPrinter_handler)

    print "Registered Callback-functions:"
    for addr in s.getOSCAddressSpace():
        print addr

    print "\nStarting OSCServer. Use ctrl-C to quit."
    st = threading.Thread(target=s.serve_forever)
    st.start()

    c2 = OSC.OSCClient()
    c2.connect(send_address)
    #subreq = OSC.OSCMessage("/MashMachine/Control/getActiveObjectsPosition")

    paired = 0
    while paired == 0:
        try:
            print "Pairing..."
            subreq = OSC.OSCMessage("/MashMachine/Global/makePairing")
            subreq.append("localhost")
            subreq.append(54321)
            c2.send(subreq)
            #time.sleep(0.5)

            print "Subscribing..."
            subreq = OSC.OSCMessage("/MashMachine/Global/subscribeObjectsID")
            subreq.append("localhost")
            c2.send(subreq)
            paired = 1
        except(OSC.OSCClientError):
            print "Pairing or Subscribing failed.."
            time.sleep(1)
        except(KeyboardInterrupt):
            print "Continue without pairing.."
            paired = 1


#time.sleep(0.5)

##  /MashMachine/Global/subscribeObjectsID
##  /MashMachine/Global/subscribeObjectsPosition

    print("eina.. Control+C to stop")


    while True:
        startTime = time.time()
        global flash
        if not flash:
            screen.render(width, height, timeCounter/640., [grass, sun], mainPalette)
            endTime = time.time()
            timeToWait = targetFrameTime - (endTime - startTime)
            print"Frame time: ", (endTime - startTime)
            if timeToWait < 0:
                print("late!", timeToWait)
                timeToWait = 0
            time.sleep(timeToWait)
            timeCounter +=1


except (KeyboardInterrupt): #, OSC.OSCClientError, SystemExit):
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    #print "Closing OSCClient"
    #c.close()
    print "Done"
    sys.exit(0)