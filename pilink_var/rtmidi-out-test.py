import time
import rtmidi

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()
print("modioutport= ")                                        #neu-test
for i in available_ports :
    print(i)                                        #neu-test

if available_ports:
    midiout.open_port(0)
else:
    midiout.open_virtual_port("My virtual output")

note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
note_off = [0x80, 60, 0]
midiout.send_message(note_on)
time.sleep(2.5)
midiout.send_message(note_off)

del midiout
