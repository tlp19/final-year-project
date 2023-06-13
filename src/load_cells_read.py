import time
from lib.DFRobot_HX711_I2C import *

IIC_MODE         = 0x01           # default use IIC1
IIC_ADDRESS_1    = 0x64           # device 1 address
IIC_ADDRESS_2    = 0x65           # device 2 address

loadcell1 = DFRobot_HX711_I2C(IIC_MODE, IIC_ADDRESS_1)
loadcell2 = DFRobot_HX711_I2C(IIC_MODE, IIC_ADDRESS_2)

loadcell1.begin()
loadcell2.begin()

# Manually set the calibration values
loadcell1.set_calibration(2142)
loadcell2.set_calibration(2377)

# (2270, 2225), (2221, 2281), (2248.98, 2219.49), (2240, 2245), (2250, 2280), (2265, 2295)
# from on-chip cal script: (2265, 2315), (2249.37, 2338.22)
# from custom script: (2298, 2190), (2142, 2377)

time.sleep(0.5)

# Tare the sensors
loadcell1.peel()
loadcell2.peel()

print("start\r\n")

while(1):
  # Get the weight of the object
  data1 = loadcell1.read_weight(20)
  data2 = loadcell2.read_weight(20)
  weight = - (data1 + data2)
  print(f'weight is {weight:.2f} g   ({-data1:.2f} + {-data2:.2f})')
  time.sleep(0.05)