# rpi_weather_clock
Analog weather conditions with Raspberry Pi, stepper motor, weather underground API

## Purpose: 

This program indicates current weather conditions on an analog guage driven by a unipolar stepper motor connected to the GPIO pins of a Raspberry Pi computer.

## User experience: 

When connected to a apropriate circuits including a unipolar stepper motor and two momentary push buttons, the program periodically connects to the Weather Underground API using the API key and loaction URL provided at setup, and turns the stepper motor to point to the value of the selected weather condition. 

Should the stepper motor become "uncalibrated" due to interruption of power to the Raspberry Pi, the user can "zero" the stepper motor with the pair of momentary buttons, fine tuning it's zero position. When the user stops pressing the buttons, the program assumes the motor position to be calibrated and returns the indicator to the latest measurement for the selected weather condition.

The user can select which of 5 current weather conditions measures are displayed by the device by selecting one from the Weather Clock Mode Control web page hosted by the Raspberry Pi. Selecting a measure differnt from the current measurement updates the stepper motor position immediately, ad the Mode Control web page reflects the currently selected measure.

The 5 selectable weather conditions are:  

1. Relative Humidity (%)
2. Feels Like (degrees F)
3. Precipitation Today (inches)
4. Pressure (inches)
5. Visibility (Miles)

## Interfaces

### Hardware

The weather clock relies on a unipolar stepper motor to move the indicator - this should be wired to the Raspberry Pi GPIO as described in [Adafruit's excellent stepper motor tutorial](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-10-stepper-motors). Note that all of the necessary components are sold by Adafruit and are linked directly to the tutorial. The Weather clock also needs two momentary (usually open) switches with pull-down resistors wired to the GPIO as inputs for calibrating the position of the stepper motor. Again I refer you to another excellent Adafruit tutorial on [wiring input buttons for the Raspberry Pi GPIO](https://learn.adafruit.com/playing-sounds-and-using-buttons-with-raspberry-pi/bread-board-setup-for-input-buttons).

The Weather Clock also requires an internet connection - ideally this should be a WiFi USB adapter, unless you don't mind connecting your Weather Clock with an ethernet cable.

## Software

The Weather Clock software is composed of two parts, the python program that fetches weather observation data and controls the stepper motor, and the web interface.

### Python program

The Weather Clock python program uses the following python libraries:

1. RPi.GPIO - library for controlling and reading the Raspberry Pi General Purpose Input Output pins
2. time - library providing system timer functions
3. json, requests - libraries allowing interaction with JSON RESTful APIs such as that of Weather Underground
4. shutil - library allowing for file handling, as in rotating the program's log file
5. ConfigParser - library simplifying reading the program's .config file, used to set run time options for the program

All of these libraries can be downloaded and installed using pip as explained in [this reference](https://www.raspberrypi.org/documentation/linux/software/python.md) from raspberrypi.org.

The python program reads from the weather_clock.config file (example included in the source) to gather information about:

* What API key to use to connect to wunderground.com, for what location to gather weather observations, and how often to refresh the observation data. **Note** the API key MUST be provided in this config file. You can get your very own personal API key for free from wunderground.com [here](http://www.wunderground.com/weather/api/d/login.html).
* Information about your stepper motor setup including what GPIO output pins it's connected to, and how many steps in a complete revolution for your motor
* Information about your guage face. For example, if you use the sample guage face provided, indicator positions 0-100 occupy 3/4 of a revolution, so a complete revolution would be 133.333 positions. If on the other hand you wanted to represent a range from 0-120 in a half revolution of the motor, an entire revolution would be 240 positions.
* Information about what GPIO pins your calibration buttons are connected to.
* Settings for how long to wait between steps (to give a slower or faster movement of the stepper motor) and how long fast or precise modes should persist while the user is calibrating the motor
* Where to program should write its log file and what that log file should be called

### Web interface

The code includes two php files that allow a user to change the weather observation measure indicated by the Weather Clock via a web browser. "weather.php" reads the settings file and pre-selects the apropriate setting in the options list, and allows the user to select any of the 5 measures and submit it with the "submit" button. Clicking the submit button loads the "write_setting.php" page which changes the content of the "setting.txt" file and re-loads the "weather.php" page.

You can use the Weather Clock without the web interface, but the setting.txt file must be in place in the /var/www folder with one of the five usable values in it.

To install a working php web server, follow the steps in [this guide](https://www.raspberrypi.org/documentation/remote-access/web-server/apache.md) from raspberrypi.org.
