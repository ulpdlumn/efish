import serial
import time
import seeOutside

from PS300 import *

# Connect to power supply
ps = PS300(port='COM6')

# Basic operation
ps.set_voltage(-10)      #
assert ps.get_last_error() == 0
ps.set_current_limit(-3e-4)  # Set current limit to 0.3mA (max 525ua)
ps.set_current_trip(-5e-4)  #TODO check that the current has to be negative here
assert ps.get_last_error() == 0
ps.high_voltage_on()      # Enable output
assert ps.get_last_error() == 0

# Monitor parameters
for ii in range(10):
    print(f"Voltage: {ps.get_output_voltage()} V")
    print(f"Current: {ps.get_output_current() * 1e6} μA")

ps.high_voltage_off()      # Enable output


# Save configuration
# ps.save_configuration(1)

# Cleanup
ps.close()
