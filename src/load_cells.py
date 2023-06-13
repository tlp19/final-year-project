from .lib.DFRobot_HX711_I2C import *


SMALL_CUP_WEIGHT = 41.12
LARGE_CUP_WEIGHT = 59.56
WEIGHTING_IMPRECISION = 2.5
ALLOWED_WATER_WEIGHT = 10


IIC_MODE         = 0x01           # default use IIC1
IIC_ADDRESS_1    = 0x64           # device 1 address
IIC_ADDRESS_2    = 0x65           # device 2 address

loadcell1 = DFRobot_HX711_I2C(IIC_MODE, IIC_ADDRESS_1)
loadcell2 = DFRobot_HX711_I2C(IIC_MODE, IIC_ADDRESS_2)

loadcell1.begin()
loadcell2.begin()

loadcell1.set_calibration(2142)
loadcell2.set_calibration(2377)
# from on-chip cal script: (2265, 2315), (2249.37, 2338.22), (2203, 2344)
# from custom script: (2142, 2377) (2285, 2333)


def tare():
  loadcell1.peel()
  loadcell2.peel()

def read():
  # Get the weight of the object
  data1 = loadcell1.read_weight(10)
  data2 = loadcell2.read_weight(10)
  weight = - (data1 + data2)
  # print(f'weight is {weight:.2f} g   ({-data1:.2f} + {-data2:.2f})')
  return weight

def get_weight():
  # Take 5 readings
  readings = [read() for i in range(5)]
  # Remove the highest and lowest reading (outliers)
  readings.remove(max(readings))
  readings.remove(min(readings))
  # Return the average of the remaining readings
  return sum(readings) / len(readings)

def check_weight():
  weight = get_weight()
  print(f'weight is {weight:.2f} g')
  # Check if the weight is within the allowed range for a small cup
  if (weight > (SMALL_CUP_WEIGHT - WEIGHTING_IMPRECISION)) and (weight < (SMALL_CUP_WEIGHT + ALLOWED_WATER_WEIGHT + WEIGHTING_IMPRECISION)):
    return True
  # Check if the weight is within the allowed range for a large cup
  if (weight > (LARGE_CUP_WEIGHT - WEIGHTING_IMPRECISION)) and (weight < (LARGE_CUP_WEIGHT + ALLOWED_WATER_WEIGHT + WEIGHTING_IMPRECISION)):
    return True
  # Else return False
  return False
