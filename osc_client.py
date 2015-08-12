#!/usr/bin/python


import OSC



listen_address = ('localhost', 54321)
send_address = ('localhost', 12345)

c2 = OSC.OSCClient()
c2.connect(listen_address)


try:

    print "Sending..."
    subreq = OSC.OSCMessage("/MM_Remote/Control/activeObjectsID")
    subreq.append(1)
    subreq.append(1)
    subreq.append(1)
    subreq.append(2)
    subreq.append(2)
    subreq.append(0)
    c2.send(subreq)

    
except(OSC.OSCClientError):
    print "Sending failed.." 
    
      
