import seeOutside
from gstage import GRBLStage
import time

#stage = GRBLStage('/dev/ttyUSB0')  
print("Connecting..")
stage = GRBLStage('COM7')  
stage.connect()

time.sleep(.1)
print(f"Position: {stage.get_position()}")
time.sleep(.1)
stage.move_by(dx=2)
time.sleep(.5)
print(f"Position: {stage.get_position()}")
stage.move_by(dx=-2)
time.sleep(.5)
print(f"Position: {stage.get_position()}")

print("Disconnecting..")
stage.disconnect()