"""
    pilink - OSC to midi for the Raspberry Pi
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
         http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""

import os
import sys
import time
import socket
import struct
import traceback
import unittest
import queue

import rtmidi

import config
import stats

outq = queue.Queue()

def parseHexValue(v) :
    if v.startswith("0x") or v.startswith("0X") :
        return int(v,16)
    else :
        return int(v,10)

def oscParser(msg, parsedMsg):
    """ parse the osc buffer; from http://www.cs.cmu.edu/~15104/week11/server.py

    """

    end_of_addr = msg.find('\000')
    if end_of_addr == -1:
        raise EOFError("Unable to find end of message")
    address = msg[ : end_of_addr]

    # Since the RaspberryPi doesn't have any time synchro, bundle 
    # time frames are not yet processed.    
    if address == "#bundle" :
        msgSize = struct.unpack('!i', msg[16 : 20])[0]
        oscParser(msg[20:20+msgSize], parsedMsg)
        return

    ret = [address]

    # skip past the address
    tsx = end_of_addr # find type string index tsx
    while tsx < len(msg) and msg[tsx] == '\000':
        tsx += 1
        
    if tsx >= len(msg):
        actual_types = ""
    else: # i will be index into msg for parameters
        i = msg.find('\000', tsx)
        if i > tsx:
            # skip the comma
            actual_types = msg[tsx + 1 : i]
        else:
            i = len(msg)
        
    # skip past the type string to the next multiple of 4 bytes:
    while i < len(msg) and i % 4 > 0:
        i += 1
    
    for typechar in actual_types:
        if typechar == 'i':
            if i + 4 <= len(msg):
                intval = struct.unpack('!i', msg[i : i + 4])
                i += 4
                ret.append(intval[0])
        elif typechar == 'f':
            if i + 4 <= len(msg):
                floval = struct.unpack('!f', msg[i : i + 4])
                i += 4
                ret.append(floval[0])
        elif typechar in "sSc":
            i2 = msg.find('\000', i)
            if i2 != -1:
                strval = msg[i : i2]
                i = i2 + 1
                ret.append(strval[0])
        elif typechar == 'd':
            if i + 4 <= len(msg):
                floval = struct.unpack('!d', msg[i : i + 8])
                i += 8
                ret.append(floval[0])

    parsedMsg.append(ret)

def parseMidiMsg(msg, replaceValues) :
    midiMsg = []
    msg = msg.replace(',', ' ')     # touchosc sends ' ' ; lemur sends ','
    for i in msg.split() :
        first = i[0].lower()
        if first in "xyz" :
            replacePos = ord(first) - ord('x')
            if len(i) > 1 and i[1] == "(" :
                rng = list(map(parseHexValue, i[2:-1].split("..")))
                ratio = rng[1] - rng[0]
                midiMsg.append(int(replaceValues[replacePos] * ratio) + rng[0])
            else :
                midiMsg.append(int(replaceValues[replacePos] * 127))
        else :
            midiMsg.append(parseHexValue(i))
    return midiMsg

def osc2Midi(msg) :
    oscToken = msg[0].split("/")[1:]
    #print (oscToken)
    token = oscToken.pop(0)
    #print (token)
    midiMsg = []

    if token == 'note' :
        chl = int(msg[1])
        midiMsg = [ (0x89 + int(msg[1])), int(msg[2]), int(msg[3]) ]
        
    return midiMsg

# #########################################################################

def oscInput() :
    networkConn = -1
    lastError = 0

    while 1 :
        try :
            networkConn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            networkConn.bind(("0.0.0.0", config.receiveport))
            print(("LISTENING UDP PORT %d" % config.receiveport))
            while 1 :
                midiMsg = [] # send empty midi message
                msg = networkConn.recvfrom(4096)[0]
                try :
                    parsedMsg = []
                    oscParser(msg, parsedMsg)

                    stats.oscin(str(parsedMsg))                                                    #das kommt noch an...
#                    print (parsedMsg)

                    for i in parsedMsg :
#                        print (i)
                        midiMsg.extend(osc2Midi(i))

                except Exception as e :
                    stats.error(e)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    print((str(traceback.format_exception(exc_type, exc_value, exc_traceback))))
                if len(midiMsg) != 0 :
                    outq.put_nowait(midiMsg)
        except Exception as e :
            stats.error(e)
            print(("**> Exception cought: %s" % e))
            if lastError + 5 > time.time() :
                print("Waiting before trying again....")
                time.sleep(5)
            lastError = time.time()
        except BaseException  :
            print("Keyboard / base interrupt received, stopping deamon...")
            return 1
        finally :
            try :                   
                if networkConn != - 1 :
                    networkConn.close()
            except :
                pass

def midiOutput() :

    mididev = config.mididev
    midiConn = -1
    lastError = 0

    while True :
        try :
#           midiConn = os.open(config.mididev, os.O_WRONLY)                                    #alt
            midiConn = rtmidi.MidiOut()                                                        #neu
            available_ports = midiConn.get_ports()                                             #neu
            if available_ports:                                                                #neu
                 midiConn.open_port(1)                                                         #neu
                 print("modioutport: ")                                                        #neu-test
                 for i in available_ports :                                                    #neu-test
                     print(i)                                                                  #neu-test
            else:                                                                              #neu
                 midiConn.open_virtual_port("My virtual output")                               #neu
            while 1 :
                midiMsg = outq.get(True)
                display = ""
#-
#                print("midiMsg: ")                                                        #neu-test
#                for i in midiMsg :                                                    #neu-test
#                    print(i)                                                                  #neu-test
#-
                for i in midiMsg :
                    display = display + "0x%x " % i
                stats.midiout(display)                                                         # chan Note Vel
                #os.write(midiConn, bytearray(midiMsg))                                        #alt
                # -- note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112             #neu-notizen
                # -- note_off = [0x80, 60, 0]                                                  #neu-notizen
                midiConn.send_message(midiMsg)                                                 #neu
        except Exception as e :
            stats.error(e)
            print(("**> Midi Output Exception cought: %s" % e))
            if lastError + 5 > time.time() :
                print("Waiting before trying again....")
                time.sleep(5)
            lastError = time.time()
        except BaseException  :
            print("Keyboard / base interrupt received, stopping deamon...")
            return 1
        finally :
            # close stuff we need to 
            try :
                if midiConn != -1 :
                    del midiConn                   #neu
                    #os.close(midiConn)
            except :
                pass

# #########################################################################
# ## UNIT TESTS
# #########################################################################

class PiLink(unittest.TestCase) :
    def testOne(self) :
        self.assertEqual(osc2Midi(["/midi/0x90 60 127", 0]), [0x90, 60, 127])
        self.assertEqual(osc2Midi(["/midi/z/0x90 60 127/0x91 0x21 00", 0]), [0x90, 60, 127, 0x91, 0x21, 0])
        self.assertEqual(osc2Midi(["/midi/0xf0 0xb0 0 0 0xb0 0x20 0x00 0xc0 52 0xf7", 0]), [0xf0, 0xb0, 0, 0, 0xb0, 0x20, 0x00, 0xc0, 52, 0xF7])

if __name__ == "__main__" :
    unittest.main()

