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
import effects


greenPalette = ColorPalette(CSVfilename="palettes/green_grass")
rainbowPalette = ColorPalette(CSVfilename="palettes/rainbow")
pinkPalette = ColorPalette(CSVfilename="palettes/pink")
mainPalette = greenPalette


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



screen = Screen(sections) #, ['127.0.0.1:7891'])
screen.dimm(0)

targetFPS = 24
targetFrameTime = 1./targetFPS
timeCounter = int(random.random() * 65535)



#currentEffect = effects.CenterSquareFillEffect()
#currentEffect = effects.FanEffect()
#currentEffect = effects.WaveEffect()
currentEffect = effects.RipplesEffect()


#dispatcher = dispatcher.Dispatcher()
#dispatcher.map("/MM_Remote/Control/objectPosition", set_pallete, "Set Pallete: " )
#dispatcher.map("/volume", set_pallete, "Pallete")

                
#server = osc_server.ThreadingOSCUDPServer(  ('127.0.0.1', 54321), dispatcher)
#print("Serving on {}".format(server.server_address))
#server.serve_forever()


listen_address = ('localhost', 54321)
send_address = ('localhost', 12345)
paired = 0

class OSCThread(threading.Thread):
    
    ########### pyosc stuff
    # define a message-handler function for the server to call.
    def printing_handler(self, addr, tags, stuff, source):
        msg_string = "%s [%s] %s" % (addr, tags, str(stuff))
        print "OSCServer Got: '%s' from %s\n" % (msg_string, OSC.getUrlStr(source))
                
        # send a reply to the client.
        msg = OSC.OSCMessage("/printed")
        msg.append(msg_string)
        return msg
    
    # define a message-handler function for the server to call.
    def pallete_handler(self, addr, tags, stuff, source):
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
            
            
    def pairing_handler(self, addr, tags, stuff, source):
        
        msg_string = "%s [%s] %s" % (addr, tags, str(stuff))
        print "Got pairing message: '%s' from %s\n" % (msg_string, OSC.getUrlStr(source))
        self.paired = 1 
               
        print "Subscribing..."
        #self.c2 = OSC.OSCClient()
        #self.c2.connect(send_address)
        subreq = OSC.OSCMessage("/MashMachine/Global/subscribeObjectsID")
        #  /MashMachine/Global/subscribeObjectsPosition
        subreq.append(listen_address[0])
        self.c2.send(subreq)

    def objectID_handler(self, addr, tags, stuff, source):
        
        msg_string = "%s [%s] %s" % (addr, tags, str(stuff))
        print "Got Object ID message: '%s' from %s\n" % (msg_string, OSC.getUrlStr(source))
        
        
        if self.objectID_lock.acquire(False):
            try:
                self.activeObjects = np.zeros([5,10])
                for i in xrange(0, len(stuff), 2):
                    group = stuff[i]
                    objectid = stuff[i+1]
                    print "Object: ", group, ":",  objectid, "is active"
                    self.activeObjects[group][objectid] = 1
            finally:
                self.objectID_lock.release()
        
            
    
    
    def __init__(self, send_address, listen_address):
        super(OSCThread, self).__init__()
        self.stoprequest = threading.Event()
        self.s = OSC.ThreadingOSCServer(listen_address)
        
        self.objectID_lock = threading.Lock()
        self.activeObjects = np.zeros([5,10])
        
        # Set Server to return errors as OSCMessages to "/error"
        self.s.setSrvErrorPrefix("/error")
        # Set Server to reply to server-info requests with OSCMessages to "/serverinfo"
        self.s.setSrvInfoPrefix("/serverinfo")

        # this registers a 'default' handler (for unmatched messages),
        # an /'error' handler, an '/info' handler.
        # And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
        self.s.addDefaultHandlers()

        self.s.addMsgHandler("default", self.printing_handler)
        #s.addMsgHandler("/MM_Remote/Control/activeObjectsID", pallete_handler)
        self.s.addMsgHandler("/MM_Remote/Control/activeObjectsID", self.objectID_handler)
        
        self.s.addMsgHandler("/MM_Remote/Control/activeObjectsPosition", self.pallete_handler)
        self.s.addMsgHandler("/MM_Remote/Global/pairingAccepted", self.pairing_handler)

        print "Registered Callback-functions:"
        for addr in self.s.getOSCAddressSpace():
            print addr
        
        print "\nStarting OSCServer. Use ctrl-C to quit."
        self.st = threading.Thread(target=self.s.serve_forever)
        self.st.start()
        
            
        self.c2 = OSC.OSCClient()
        self.c2.connect(send_address)
        #subreq = OSC.OSCMessage("/MashMachine/Control/getActiveObjectsPosition")


        tries = 10
        self.paired = 0
        
        try:
            while self.paired == 0 and tries > 0:
                try:


                    print "Pairing..."
                    subreq = OSC.OSCMessage("/MashMachine/Global/makePairing")
                    subreq.append(listen_address[0])
                    subreq.append(listen_address[1])
                    self.c2.send(subreq)

                    
                except(OSC.OSCClientError):
                    print "Pairing or Subscribing failed.."   
                time.sleep(1)
                tries -=1
        except(KeyboardInterrupt):
            print "Continue without pairing.."
            self.paired = 2

        if (tries==0):
            print "Continue without pairing.."
            self.paired = 2


        
    def join(self, timeout=None):
        self.stoprequest.set()
        self.close_threads()
        super(OSCThread, self).join(timeout)
        
    def close_threads(self):
        print "\nClosing OSCServer."
        self.s.close()
        print "Waiting for Server-thread to finish"
        self.st.join()
        print "OSC Server shutdown Done"

    def run(self):


        try:
            print "Starting OSC thread..."
    
            while not self.stoprequest.isSet():
                #check messages
#OSCServer Got: '/MM_Remote/Control/activeObjectsID [iiiiii] [1, 1, 1, 2, 1, 0]' from localhost:52094
                print "Sleeping..."
                time.sleep(0.5)
        
    
        except (KeyboardInterrupt, OSC.OSCClientError, SystemExit):
            self.close_threads()
            #raise


def main():
    
    print "!Main Starting..."
    
    try:
    
        #oscThread = threading.Thread(target = oscThreadFunction, args = (send_address, listen_address ))
        
        oscThread = OSCThread(send_address, listen_address)
        oscThread.start()
        print "Paired: ", oscThread.paired

        print("eina.. Control+C to stop")
        timeCounter = int(random.random() * 65535)
        global currentEffect
        print currentEffect

        while True:
            startTime = time.time()          
            if oscThread.paired == 1 or oscThread.paired == 0:
                screen.render(width, height, timeCounter/640., [grass, sun], mainPalette)
            else:
                bitmap = currentEffect.drawFrame()
                screen.send(bitmap)
            endTime = time.time()
            timeToWait = targetFrameTime - (endTime - startTime)
            #print"Frame time: ", (endTime - startTime)
            if timeToWait < 0:
            #    print("late!", timeToWait)
                timeToWait = 0
            time.sleep(timeToWait)
            timeCounter +=1



    except (KeyboardInterrupt): #, OSC.OSCClientError, SystemExit):
        #print "\nClosing OSCServer."
        #s.close()
        #print "Waiting for Server-thread to finish"
        #st.join()
        print "Trying to stop OSC Thread..."
        oscThread.join()
        #print "Closing OSCClient"
        #c.close()
        print "Main Done"
        sys.exit(0)


if __name__ == "__main__":
    main()