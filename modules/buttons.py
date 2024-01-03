from . import globalvars as gv

class Buttons():

    def __init__(self):

        self.bouncetime = 50 # time before another button press can take place (in milliseconds)
        self.buttondebug = ""
        
        if gv.IS_DEBIAN:

            import RPi.GPIO as GPIO

            if gv.USE_BUTTONS:

                if gv.SYSTEM_MODE == 1:

                    def button_callback(channel):
                        if GPIO.input(channel) == 0:
                            # print '-------\rChannel:%d Input value:%d' % (channel, GPIO.input(channel))
    
                            if channel == gv.BUTTON_LEFT_GPIO:
                                print('\rLEFT GPIO button pressed')  # debug
                                gv.nav.state.left()
                            elif channel == gv.BUTTON_RIGHT_GPIO:
                                print('\rRIGHT GPIO button pressed') # debug
                                gv.nav.state.right()
                            elif channel == gv.BUTTON_ENTER_GPIO:
                                print('\rENTER GPIO button pressed') # debug
                                gv.nav.state.enter()
                            elif channel == gv.BUTTON_CANCEL_GPIO:
                                print('\rCANCEL GPIO button pressed') # debug
                                gv.nav.state.cancel()

                    GPIO.setmode(GPIO.BCM)
                    GPIO_channel_list = [gv.BUTTON_LEFT_GPIO, gv.BUTTON_RIGHT_GPIO, gv.BUTTON_ENTER_GPIO, gv.BUTTON_CANCEL_GPIO]
                    GPIO.setup(GPIO_channel_list, GPIO.IN, pull_up_down=GPIO.PUD_UP)

                    # BUTTON_MOM = 'momentary'
                    # BUTTON_TOG = 'toggle'
                    # button_mode = BUTTON_TOG
    
                    GPIO.add_event_detect(gv.BUTTON_LEFT_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)
                    GPIO.add_event_detect(gv.BUTTON_RIGHT_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)
                    GPIO.add_event_detect(gv.BUTTON_ENTER_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)
                    GPIO.add_event_detect(gv.BUTTON_CANCEL_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)

                ##################
                # Hans' buttons
                ##################

                if gv.SYSTEM_MODE == 2:
    
                    def button_callback(channel):
    
                        if GPIO.input(channel) == 0:
                            # print '-------\rChannel:%d Input value:%d' % (channel, GPIO.input(channel))
   
                            if channel == gv.BUTTON_UP_GPIO:
                                # print("Button up")
                                gv.nav.up()

                            elif channel == gv.BUTTON_DOWN_GPIO:
                                # print("Button down")
                                gv.nav.down()

                            elif channel == gv.BUTTON_FUNC_GPIO:
                                # print("Function Button")
                                gv.nav.func()


                    GPIO.setmode(GPIO.BCM)
                    GPIO_channel_list = [gv.BUTTON_UP_GPIO, gv.BUTTON_DOWN_GPIO, gv.BUTTON_FUNC_GPIO]
                    GPIO.setup(GPIO_channel_list, GPIO.IN, pull_up_down=GPIO.PUD_UP)

                    GPIO.add_event_detect(gv.BUTTON_UP_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)
                    GPIO.add_event_detect(gv.BUTTON_DOWN_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)
                    GPIO.add_event_detect(gv.BUTTON_FUNC_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=self.bouncetime)


            if gv.USE_I2C_BUTTONS:

                import smbus
                #INT_GPIO = 4

                pcf8574 = smbus.SMBus(1)                                #bus anlegen
                pcf8574.write_byte(gv.I2C_BUTTONS_ADDR,0xff)            #alle ausgaenge(pullups) an
                print("--------> i2Cbuttons in Use")
                self.buttondebug=""

                def button_callback(channel):
                    #global self.buttondebug
                    self.buttondebug += " INT: "
                    self.buttondebug += str(channel)
                    if GPIO.input(channel) == 0:
                        # print '-------\rChannel:%d Input value:%d' % (channel, GPIO.input(channel))
                        channel = pcf8574.read_byte(gv.I2C_BUTTONS_ADDR)
                        pcf8574.write_byte(gv.I2C_BUTTONS_ADDR,0xff)            #alle ausgaenge(pullups) an
                        self.buttondebug += "Taste: "
                        self.buttondebug += str(channel)

                        if gv.SYSTEM_MODE == 1:
                            self.buttondebug += "mode: 1"

                            if (channel & (1 << gv.BUTTON_LEFT_GPIO )) == 0:          #.5
                                self.buttondebug += '\rLEFT i2c pressed'                   # debug
                                gv.nav.state.left()
                            elif (channel & (1 << gv.BUTTON_RIGHT_GPIO )) == 0:       #.6
                                self.buttondebug += '\rRIGHT i2c pressed'                  # debug
                                gv.nav.state.right()
                            elif (channel & (1 << gv.BUTTON_ENTER_GPIO )) == 0 :      #.7
                                self.buttondebug += '\rENTER i2c pressed'                  # debug
                                gv.nav.state.enter()
                            elif (channel & (1 << gv.BUTTON_CANCEL_GPIO )) == 0 :     #.4
                                self.buttondebug += '\rESC i2c pressed'                    # debug
                                gv.nav.state.cancel()
   

                        ##################
                        # Hans' buttons
                        ##################
                        if gv.SYSTEM_MODE == 2:
                            self.buttondebug += "mode: 2"
 
                            if (channel & (1 << gv.BUTTON_UP_GPIO )) == 0 :
                                self.buttondebug += '\rUP i2c pressed'                     # debug
                                gv.nav.up()

                            elif (channel & (1 << gv.BUTTON_DOWN_GPIO )) == 0 :
                                self.buttondebug += '\rDOWN i2c pressed'                   # debug
                                gv.nav.down()

                            elif (channel & (1 << gv.BUTTON_FUNC_GPIO )) == 0 :
                                self.buttondebug += '\rFUNCTION i2c pressed'               # debug
                                gv.nav.func()
                        #print self.buttondebug
                        



                GPIO.setmode(GPIO.BCM)
                GPIO.setup(gv.I2C_BUTTONS_INT, GPIO.IN, pull_up_down = GPIO.PUD_UP)

                # BUTTON_MOM = 'momentary'
                # BUTTON_TOG = 'toggle'
                # button_mode = BUTTON_TOG
    
                GPIO.add_event_detect(gv.I2C_BUTTONS_INT, GPIO.BOTH, callback = button_callback, bouncetime=self.bouncetime)


