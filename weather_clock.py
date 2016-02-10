#The MIT License (MIT)

#Copyright (c) 2016 Bill Jones

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# weather_clock.py
# by Bill Jones
# billsridepics@gmail.com
# 
# A Python program to be run on a Raspberry Pi
# Fetches several current weather conditions from wunderground.com
# and displays them on an analog dial using a unipolar stepper motor

import RPi.GPIO as GPIO
import time
import json, requests
import shutil
import ConfigParser

# Establishes that the GPIO mode is Broadcom - required for rPi
GPIO.setmode(GPIO.BCM)

# Loads configuration variables from humidity.config
parser = ConfigParser.SafeConfigParser()
parser.read('/home/pi/.config/weather_clock.config')

def prefGet(section, option, default):
	global parser	
	try:
		answer = parser.get(section, option)
	except:
		answer = default
	return answer

def prefGetInt(section, option, default):
	global parser	
	try:
		answer = parser.getint(section, option)
	except:
		answer = default
	return answer

def prefGetFloat(section, option, default):
	global parser	
	try:
		answer = parser.getfloat(section, option)
	except:
		answer = default
	return answer

# Establish constants for the retrieval of data from wunderground.com
api_key = parser.get('wunderground','key') # NO DEFAULT for this - you MUST place your personal wunderground API key in the weather_clock.config file
location = prefGet('wunderground','location', "IL/O'Fallon.json")
observation_metric = prefGet('wunderground','default_metric', "relative_humidity")
# Establish constants about the working range of the motor and scale
motor_steps = prefGetFloat('motor','steps', 512.0) # How many motor steps in a full revolution
scale = prefGetFloat('motor','scale', 133.3333)    # How many 'clockpoints' in a full revolution
normal_motor_delay = prefGetFloat('motor','normal_delay','7.0')
slow_mode_motor_delay = prefGetFloat('motor','slow_mode_delay',45.0)
# Establish constants and variables for keeping track of how long to wait before changing behaviors
indicator_mode_wait = prefGetFloat('wait','indicator_mode',4.0) # How many seconds to wait since last button push before going back to indicating humidity
slow_mode_wait = prefGetFloat('wait','slow_mode',1.0)           # How many seconds of continuous button pushing before moving the meter at normal speed (instead of slow)
observation_wait = prefGetInt('wait','observation',240)         # How many seconds to wait between web calls - the personal key used caps api calls at 500/day
# Identifies the GPIO pin numbers for the two push button inputs
left_pin = prefGetInt('pins','left',24)
right_pin = prefGetInt('pins','right',25)
# Identifies the GPIO pin numbers for the four coil control oputputs
coil_A_1_pin = prefGetInt('pins','coil_A_1',15)
coil_A_2_pin = prefGetInt('pins','coil_A_2',23)
coil_B_1_pin = prefGetInt('pins','coil_B_1',14)
coil_B_2_pin = prefGetInt('pins','coil_B_2',18)
# Establish constants related to log file management
log_dir = prefGet('log','dir','.')
log_file = prefGet('log','file','weather_clock.log')
log_rotate_wait = prefGetInt('log','rotate_wait',10800)

# Turn off warnings about already activated GPIO pins
GPIO.setwarnings(False)

# Set up each GPIO pin to be used
GPIO.setup(left_pin, GPIO.IN)
GPIO.setup(right_pin, GPIO.IN)
GPIO.setup(coil_A_1_pin, GPIO.OUT)
GPIO.setup(coil_A_2_pin, GPIO.OUT)
GPIO.setup(coil_B_1_pin, GPIO.OUT)
GPIO.setup(coil_B_2_pin, GPIO.OUT)

last_button_input_time = time.time() - (3*indicator_mode_wait)   # Make it appear that buttons have been pressed a long time ago
first_button_input_time = time.time() - (4*indicator_mode_wait)  # Make it appear that buttons have been pressed a long time ago
last_observation_time = time.time() - (2*observation_wait)       # Make it appear that the last observation is old

# Establish boolean variables to keep track of what's going on with buttons
button_pressed_at_last_check = False
in_indicator_mode = True

# Identify the sets of coil inputs for each step and the order in which they are sequenced
# 
# each item in step_list has three elements: pin_map[next_step,previous_step]
# pin_map is a number between 0 and 15 identifying which coil input pins are on and which are off
#                1248  - value of each pin
# pin_map = 5  = 1010
# pin_map = 6  = 0110
# pin_map = 10 = 0101
# pin_map = 9  = 1001
# 
# when the pins are set in this repeating sequence, it moves the motor through 4 steps
# the sequence repeats to continue rotation of the motor, and runs in reverse order to 
# move the motor in the opposite direction

step_list = [[5,[1,3]],[6,[2,0]],[10,[3,1]],[9,[0,2]]]
current_step = step_list[0]

# Initialize the memory of the position of the motor at start-up
current_clock_num = 0
next_clock_num = 0
steps_to_go = 0

first_log_write = time.time() - (2*log_rotate_wait)

# proc to set the output pins according to a pin_map value
def setStep(pin_map):
  GPIO.output(coil_A_1_pin, bool(pin_map & 1))
  GPIO.output(coil_A_2_pin, bool(pin_map & 2))
  GPIO.output(coil_B_1_pin, bool(pin_map & 4))
  GPIO.output(coil_B_2_pin, bool(pin_map & 8))

# proc to move the motor forwards
def forward(delay, steps):  
  for i in range(0, steps):
    global current_step
    global step_list
    current_step = step_list[current_step[1][0]]
    setStep(current_step[0])
    time.sleep(delay)

# proc to move the motor backwards
def backwards(delay, steps):
  for i in range(0, steps):
    global current_step
    global step_list
    current_step = step_list[current_step[1][1]]
    setStep(current_step[0])
    time.sleep(delay)

# proc to calculate which direction, and how many steps are required to move the motor
# from one step position to a desired second step position
def stepsfrom(start, end):
  global motor_steps
  if end >= start:
    if end - start < motor_steps/2:
      return end - start
    else:
      return (motor_steps - end + start)*-1
  else:
    if start - end < motor_steps/2:
      return end - start
    else:
      return (end - start + motor_steps)

# function to translate a clockpoint into the closest representative step location
def clockpoint(clock_num):
  global motor_steps
  global scale
  return int(round(float(motor_steps)/scale*float(clock_num)))-1

# Proc to write a message to the log file
def logmessage(message):
  global log_dir
  global log_file
  global first_log_write
  global log_rotate_wait
  full_log_file = "%s/%s" % (log_dir, log_file)
  # If we've used this log file long enough to rotate it, back it up and start a new one  
  if time.time() - first_log_write > log_rotate_wait:
    backup_log_file = "%s%s" % (full_log_file, ".backup")
    shutil.copyfile(full_log_file, backup_log_file)
    f = open(full_log_file, "w")
    first_log_write = time.time()
  # ...otherwise just append the next message to it
  else:
    f = open(full_log_file, "a")
  f.write(message)
  f.write("\n")
  f.close()

# Establish constants related to web control of light
setting_dir = "/var/www"
setting_file = "setting.txt"
setting_poll_wait = 8
first_setting = time.time() - (2*setting_poll_wait)
setting_value = "auto"

# Proc to fetch the setting from the web interface
def getsetting():
  global setting_dir
  global setting_file
  global setting_poll_wait
  global first_setting
  global setting_value
  full_setting_file = "%s/%s" % (setting_dir, setting_file)
  try:
    f = open(full_setting_file, "r")
    return_value = f.readline().rstrip('\n\r ')
    f.close()
    return return_value
  except:
    return setting_value

# MAIN loop
full_log_file = "%s/%s" % (log_dir, log_file)
f = open(full_log_file, "w")
f.write("humidity.py log started \n")
f.close()
while True:
  try:
        # If either button is being pressed...
        if GPIO.input(left_pin) == True or GPIO.input(right_pin) == True:
                # Set flag saying we're not to try to indicate the observation metric until further notice
                in_indicator_mode = False
                # Whatever position the motor moves to will be called "zero" from now on
                current_clock_num = 0        
                # If buttons were both off before this...
                if button_pressed_at_last_check == False:
                        # Record the time of button initiation and note that buttons are being pressed now
                        first_button_input_time = time.time()
                        button_pressed_at_last_check = True
                # Record the time we last noticed buttons were being pressed
                last_button_input_time = time.time()
                # If buttons have been held continuously for long enough, go fast, else go slow
                if last_button_input_time - first_button_input_time >= slow_mode_wait:
                        this_motor_delay = normal_motor_delay
                else:
                        this_motor_delay = slow_mode_motor_delay
                # Move the motor according to which button is being pressed
                if GPIO.input(left_pin) == True:
                        forward(int(this_motor_delay)/1000.0,1)
                else:
                        backwards(int(this_motor_delay)/1000.0,1)
        # If neither button is being pressed...
        else:
                # Record that both buttons are off
                button_pressed_at_last_check = False
                # If it wasnt decided before that it's time to start indicating the observation metric...
                if in_indicator_mode == False:
                        # Check to see if it's time to start indicating the observation metric
                        if time.time() - last_button_input_time >= indicator_mode_wait:
                                in_indicator_mode = True
                                next_steps = stepsfrom(clockpoint(0.0), clockpoint(float(next_clock_num)))
                # If it IS time to indicate the observation metric...
                else:
                        # ...and it's time to fetch data from the web...
                        if time.time() - last_observation_time >= observation_wait:
                                # fetch current conditions, parse observation metric to a float
                                r=requests.get("http://api.wunderground.com/api/" + api_key + "/conditions/q/" + location)
                                binary=r.content
                                output = json.loads(binary)
                                next_clock_num = float(output['current_observation'][observation_metric].rstrip('%'))
                                # Record the last time we fetched data from the web
                                last_observation_time = time.time()
                                # Calculate the next motor movement
                                next_steps = stepsfrom(clockpoint(float(current_clock_num)), clockpoint(float(next_clock_num)))
                                # Do a little logging
                                logmessage(output['current_observation']['observation_time_rfc822'])
                                logmessage(output['current_observation'][observation_metric])

			# Retrieve the observation metric selected through the web interface
			setting_now = getsetting()
			observation_metric = setting_now
			next_clock_num = float(output['current_observation'][observation_metric].rstrip('%'))
                        # Calculate the next motor movement
                        next_steps = stepsfrom(clockpoint(float(current_clock_num)), clockpoint(float(next_clock_num)))
				
                        # call the right step proc depending on the sign of the variable next_steps
			if next_steps >= 0:
                                backwards(int(normal_motor_delay)/1000.0, int(next_steps))
                        else:
                                forward(int(normal_motor_delay)/1000.0, -1*int(next_steps))
                        next_steps = 0
                        # remember the new position of the motor 
                        current_clock_num = float(next_clock_num)
                        time.sleep(0.25)
  except (KeyboardInterrupt, SystemExit):
    # on interrupt, move the motor back to the zero position
    next_clock_num = 0.0
    next_steps = stepsfrom(clockpoint(current_clock_num), clockpoint(float(next_clock_num)))
    if next_steps >= 0:
      backwards(int(normal_motor_delay)/1000.0, int(next_steps))
    else:
      forward(int(normal_motor_delay)/1000.0, -1*int(next_steps))

    # reset all the GPIO pins and exit
    GPIO.cleanup()		
    exit()
  except requests.exceptions.RequestException as e:
    # on a request failure, log the problem and retry after 30 seconds
    logmessage(str(e))
    time.sleep(30)    	
  except:
    # for all other exceptions, print a generic message and retry after 30 seconds
    logmessage('An error occured')
    time.sleep(30)
