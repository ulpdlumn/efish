import serial
import time
import seeOutside
<<<<<<< HEAD

=======
>>>>>>> a4ac57e5ef3af5cd7579611a55f8caf44f23c5ec
from PS300 import *

# Connect to power supply
# ps = PS300(port='COM6')
ps = PS300(port='/dev/ttyUSB0')

ps.clear_trips()
ps.clear_status()
assert ps.get_last_error() == 0

# Basic operation
<<<<<<< HEAD
ps.set_voltage(-10)      #
=======
ps.set_voltage(-15)      #
>>>>>>> a4ac57e5ef3af5cd7579611a55f8caf44f23c5ec
assert ps.get_last_error() == 0
# ps.set_current_limit(3e-4)  # Set current limit to 0.3mA (max 525ua)
# ps.set_current_trip(5e-4)  #TODO check that the current has to be negative here
assert ps.get_last_error() == 0
ps.high_voltage_on()      # Enable output
assert ps.get_last_error() == 0

# Monitor parameters
for ii in range(100):
    print(f"Voltage: {ps.get_output_voltage()} V\tCurrent: {ps.get_output_current() * 1e6} μA")

ps.high_voltage_off()      # Enable output


# Save configuration
# ps.save_configuration(1)

# Cleanup
ps.close()
