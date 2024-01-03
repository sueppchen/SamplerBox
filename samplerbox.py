#  SamplerBox RX!!
#
#  author:          Joseph Ernest (twitter: @JosephErnest, mail: contact@samplerbox.org)
#  contributor:     Alex MacRae (alex.finlay.macrae@gmail.com)
#  url:             http://www.samplerbox.org/
#  license:         Creative Commons ShareAlike 3.0 (http://creativecommons.org/licenses/by-sa/3.0/)
#
#  samplerbox.py:  Main file
#

# TODO: if we're compiling a dist (Windows/Mac), bundled files such as config.ini can't be found, ie relative paths are affected
# --> Pilink einpflegen!

# import os, sys
# if 'Python' in  os.path.dirname(sys.executable):
#     env_basename = os.path.dirname(sys.executable)
# else:
#     env_basename = ''

#########################################
# IMPORT
# MODULES
#########################################


#samplerbox.original
from os.path import ismount
from os.path import isfile
from os import system
import subprocess
import time

time_start = time.time()
usleep = lambda x: time.sleep(x / 1000000.0)
msleep = lambda x: time.sleep(x / 1000.0)
import threading
import rtmidi2
# from filters import FilterType, Filter, FilterChain
# from utility import byteToPCM, floatToPCM, pcmToFloat, sosfreqz

#print('modules other')

from modules import globalvars as gv
#print('import ok: gv')
from modules import displayer
from modules import audiocontrols
from modules import buttons
from modules import systemfunctions
from modules import setlist
from modules import loadsamples
from modules import sound
from modules import midimaps
from modules import midicallback
from modules import midiserial

#print('import done')

#pilink
import sys
import os
sys.path.append('/root/SamplerBox/pilink_var')
import pilink


###########
# Fix USB #
###########

# if ismount('/media'):
    # try:
    #     subprocess.call(["fsck", "-yvp", "/media"])  # auto-repair USB drive in case of dirty bits (if connected/mounted)
    #     path = gv.SAMPLES_DIR
    #     if 'media' in path:
    #         if path.endswith('/'): path = path[:-1]
    #         subprocess.call(['rm', '-v', path + '/FSCK*.REC'])
    #     else:
    #         subprocess.call(['rm', '-v', '/media/FSCK*.REC'])
    # except:
    #     print 'USB repair failed'

try:
    if ismount('/media'):
        if 'media' in gv.SAMPLES_DIR:
            subprocess.call(['rm', '-v', gv.SAMPLES_DIR.rstrip('/') + '/FSCK*.REC'])
        else:
            subprocess.call(['rm', '-v', '/media/FSCK*.REC'])
except:
    pass

###################
# Fix MIDI Serial #
###################

try:
    subprocess.call(['systemctl', 'stop', 'serial-getty@ttyAMA0.service'])
    subprocess.call(['systemctl', 'disable', 'serial-getty@ttyAMA0.service'])
except:
    print('Failed to stop MIDI serial')
    pass

###########
# Logging #
###########

# import sys
# log_file = open("console.log", 'w')
log_file = None
# sys.stdout = log_file

#######################
# Start Displayer     #
# Load MIDI mappings  #
# Start the Navigator #
# Start the GUI       #
#######################

samples_fs_resize_format_script = '/boot/resize_samples_partition.sh'
gv.displayer = displayer.Displayer()

if isfile(samples_fs_resize_format_script):
    gv.SYSTEM_MODE = 1
    from modules import HD44780_sys_1

    gv.displayer.LCD_SYS = HD44780_sys_1.LCD_SYS_1()
    gv.displayer.LCD_SYS.temp_display = True
    time.sleep(0.1)
    gv.displayer.disp_change(str_override='ExpandingStorage', timeout=60, line=1, is_priority=True)
    gv.displayer.disp_change(str_override='DO NOT TURN OFF!', timeout=60, line=2, is_priority=True)
    time.sleep(0.1)
    systemfunctions.mount_boot_rw()
    systemfunctions.mount_root_rw()
    system('sh ' + samples_fs_resize_format_script)
    print('Finished expanding. Reboot now.')
    systemfunctions.SystemFunctions().reboot()
    exit()
else:
    print('\r\n***********\r\n/SAMPLES/ HAS BEEN GROWN AND FORMATTED - READY TO GO\r\n***********\r\n')

print('#### START SETLIST ####')
gv.setlist = setlist.Setlist()
print('####  END SETLIST  ####\n')

if gv.SYSTEM_MODE == 1:
    from modules import HD44780_sys_1
    from modules import navigator_sys_1

    gv.displayer.LCD_SYS = HD44780_sys_1.LCD_SYS_1()
    gv.nav = navigator_sys_1.Navigator(navigator_sys_1.PresetNav)
elif gv.SYSTEM_MODE == 2:
    from modules import HD44780_sys_2
    from modules import navigator_sys_2

    gv.displayer.LCD_SYS = HD44780_sys_2.LCD_SYS_2()
    gv.nav = navigator_sys_2

if gv.DEBUG :
    print("DEBUG SB - midimaps")
gv.midimaps = midimaps.MidiMapping().maps

if gv.DEBUG :
    print("DEBUG SB - autocorder")
gv.autochorder = audiocontrols.AutoChorder()

if gv.DEBUG :
    print("DEBUG SB - audioControlls")
gv.ac = audiocontrols.AudioControls()

if gv.DEBUG :
    print("DEBUG SB - startsound")
gv.sound = sound.StartSound()

if gv.DEBUG :
    print("DEBUG SB - systemfuncs")
gv.sysfunc = systemfunctions.SystemFunctions()

if gv.DEBUG :
    print("DEBUG SB - loadsamples")
gv.ls = loadsamples.LoadingSamples()

if gv.DEBUG :
    print("DEBUG SB - buttons")
bnt = buttons.Buttons()

if gv.DEBUG :
    print("DEBUG SB - midicallback")
gv.midicallback = midicallback.Midi()

if gv.DEBUG :
    print("DEBUG SB - midiserial")
gv.midiserial = midiserial.MIDISerial(midicallback=gv.midicallback)

import modules.gui as gui

###########################################
# START GUI                               #
# If running on Windows/Mac. Experimental #
###########################################

if gv.DEBUG :
    print("DEBUG SB - gui")
if gv.USE_GUI and not gv.IS_DEBIAN: gv.gui = gui.SamplerBoxGUI()  # Start the GUI

################################
# LOAD FIRST SAMPLE-SET/PRESET #
################################

if gv.DEBUG :
    print("DEBUG SB - load preset")
gv.ls.load_preset()

################################################################
# MIDI IN via SERIAL PORT                                      #
# this should be extended with logic for "midi running status" #
# possible solution at http://www.samplerbox.org/forum/146     #
################################################################

if gv.DEBUG :
    print("DEBUG SB - midiserial-Start")
gv.midiserial.start()

#################################
# Test initial script load time #
#################################

time_end = time.time()
time_total = float(time_end - time_start)
print('\r\nINIT LOAD TIME: %d seconds (before sample loading)\r\n' % time_total)

##########################
# MIDI DEVICES DETECTION #
# MAIN LOOP              #
##########################

midi_in = rtmidi2.MidiInMulti()

curr_ports = []
prev_ports = []
first_loop = True

time.sleep(0.5)

try:

    def deamonize(callable) :
        t = threading.Thread(target=callable)
        t.daemon = True
        t.start()
    
    def midi_devices_loop():
        global prev_ports, first_loop
        
        #main loop
        while True:
    
            no_playing_sounds = False
            for channel in range(16):
                if not gv.playingnotes[channel + 1]:
                    no_playing_sounds = True
    
            if no_playing_sounds:  # only check when there are no sounds

                #liste mit allen Midi-In-Ports
                curr_ports = rtmidi2.get_in_ports()
                
                #mit letzter Liste vergleichen, bei Abweichung einlesen
                if (len(prev_ports) != len(curr_ports)):
                    if gv.DEBUG :
                        print('\n==== START GETTING MIDI DEVICES ====')
                    midi_in.close_ports()
                    prev_ports = []
                    for port in curr_ports:
                        if port not in prev_ports and 'Midi Through' not in port and (
                                        len(prev_ports) != len(curr_ports) and 'LoopBe Internal' not in port):
                            midi_in.open_ports(port)
                            midi_in.callback = gv.midicallback.callback
                            if gv.DEBUG:
                                if first_loop:
                                    print('Opened MIDI port: ' + port)
                                else:
                                    print('Reopening MIDI port: ' + port)
                    if gv.DEBUG:
                        print('====  END GETTING MIDI DEVICES  ====\n')
                prev_ports = curr_ports
                first_loop = False
            time.sleep(0.2)


    if gv.USE_GUI and not gv.IS_DEBIAN:

        # MIDI device detection is threaded because Tkinter's loop will become the main loop (below)
        LoadingInterrupt = False
        LoadingThread = threading.Thread(target=midi_devices_loop)
        LoadingThread.daemon = True
        LoadingThread.start()
#        startup()

        #########################
        # START GUI / MAIN LOOP #
        #########################

        if not gv.IS_DEBIAN:
            gv.gui.start_gui_loop()  # this is the main loop

    else:
        deamonize(pilink.startup)
        midi_devices_loop()  # this is the main loop


except KeyboardInterrupt:
    print("\nStopped by CTRL-C\n")
    gv.sysfunc.shutdown(log_file)
    exit()
except:
    print("\nStopped by other error\n")
    gv.sysfunc.shutdown(log_file)
    exit()

# TODO: returns fatal errors to the LCD screen. `try:` needs to encapsulate whole script. Buggy.
# except:
#     exc_info = sys.exc_info()
#     # print exc_info
#     traceback_str = '%s %s' % (str(exc_info[0]), str(exc_info[1]))
#     print traceback_str
#     gv.displayer.disp_change('FATAL ERROR'.center(gv.LCD_COLS, ' '), line=1, is_error=True)
#     gv.nav.text_scroller.set_string(string=traceback_str, line=2, is_error=True)
#     while True:
#         time.sleep(1)
