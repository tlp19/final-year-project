import sys
import time
from sympy import symbols, Eq, solve
from lib.DFRobot_HX711_I2C import *

IIC_MODE         = 0x01           # default use IIC1
IIC_ADDRESS_1    = 0x64           # device 1 address
IIC_ADDRESS_2    = 0x65           # device 2 address

CALIBRATION_ACTIVATION_THRESHOLD = 20
CALIBRATION_WEIGHT = 168

loadcell1 = DFRobot_HX711_I2C(IIC_MODE, IIC_ADDRESS_1)
loadcell2 = DFRobot_HX711_I2C(IIC_MODE, IIC_ADDRESS_2)

def start_onchip_calibration():
  loadcell1.set_threshold(CALIBRATION_ACTIVATION_THRESHOLD)
  loadcell2.set_threshold(CALIBRATION_ACTIVATION_THRESHOLD)
  loadcell1.set_cal_weight(int(CALIBRATION_WEIGHT/2))
  loadcell2.set_cal_weight(int(CALIBRATION_WEIGHT/2))
  loadcell1.enable_cal()
  loadcell2.enable_cal()

print("\nSTARTING CALIBRATION\n")
time.sleep(1)

for timer in range(6, -1, -1):
  print(f"REMOVE all objects from the scale within {timer}s.", end="\r")
  time.sleep(1)

print("\nWaiting for everything to settle...")
time.sleep(1.5)

print("Measuring empty scale..", end="")
offset_x1 = loadcell1.read_value(100)
offset_y1 = loadcell2.read_value(100)
print("Done.\n")
# print("debug: offset_x1", offset_x1, "offset_y1", offset_y1)

time.sleep(0.5)

for timer in range(6, -1, -1):
  print(f"PUT the calibration object on ONE SIDE of the scale within {timer}s.", end="\r")
  time.sleep(1)

print("\nWaiting for everything to settle...")
time.sleep(1.5)

print("Measuring heavy scale..", end="")
value_x1 = loadcell1.read_value(100)
value_y1 = loadcell2.read_value(100)
print("Done.\n")
# print("debug: value_x1", value_x1, "value_y1", value_y1)

time.sleep(0.5)
start_onchip_calibration()

cal_done = 0
timer = 7
while (cal_done < 2): 
  if timer <= 0:
    print("Calibration failed: No object removal was detected. Decrease the activation threshold and try again.")
    sys.exit()
  timer -= 1
  print(f"REMOVE the object within {timer}s.", end="\r")
  time.sleep(1)
  cal_done += int(loadcell1.get_cal_flag()) + int(loadcell2.get_cal_flag())

print("\nWaiting for everything to settle...")
time.sleep(1.5)

print("Measuring empty scale..", end="")
offset_x2 = loadcell1.read_value(100)
offset_y2 = loadcell2.read_value(100)
print("Done.\n")
# print("debug: offset_x2", offset_x2, "offset_y2", offset_y2)
  
time.sleep(0.5)

for timer in range(6, -1, -1):
  print(f"PUT the calibration object on the OTHER SIDE of the scale within {timer}s.", end="\r")
  time.sleep(1)

print("\nWaiting for everything to settle...")
time.sleep(1.5)

print("Measuring heavy scale..", end="")
value_x2 = loadcell1.read_value(100)
value_y2 = loadcell2.read_value(100)
print("Done.\n")
# print("debug: value_x2", value_x2, "value_y2", value_y2)

time.sleep(0.5)
start_onchip_calibration()

cal_done = 0
timer = 7
while (cal_done < 2): 
  if timer <= 0:
    print("Calibration failed: No object removal was detected. Decrease the activation threshold and try again.")
    sys.exit()
  timer -= 1
  print(f"REMOVE the object within {timer}s.", end="\r")
  time.sleep(1)
  cal_done += int(loadcell1.get_cal_flag()) + int(loadcell2.get_cal_flag())

print("\nWaiting for everything to settle...")
time.sleep(1.5)

print("Measuring empty scale..", end="")
offset_x3 = loadcell1.read_value(100)
offset_y3 = loadcell2.read_value(100)
print("Done.\n")
# print("debug: offset_x3", offset_x3, "offset_y3", offset_y3)

for timer in range(6, -1, -1):
  print(f"PUT the calibration object on the CENTER of the scale within {timer}s.", end="\r")
  time.sleep(1)

print("\nWaiting for everything to settle...")
time.sleep(1.5)

print("Measuring heavy scale..", end="")
value_x3 = loadcell1.read_value(100)
value_y3 = loadcell2.read_value(100)
print("Done.\n")
# print("debug: value_x3", value_x3, "value_y3", value_y3)

time.sleep(0.5)
start_onchip_calibration()

cal_done = 0
timer = 7
while (cal_done < 2): 
  if timer <= 0:
    print("Calibration failed: No object removal was detected. Decrease the activation threshold and try again.")
    sys.exit()
  timer -= 1
  print(f"REMOVE the object within {timer}s.", end="\r")
  time.sleep(1)
  cal_done += int(loadcell1.get_cal_flag()) + int(loadcell2.get_cal_flag())

print("\n\nCALIBRATION OVER.")


print("\nThe ON-CHIP calibration value of the sensors are (weak calibration):")
calibration1 = loadcell1.get_calibration()
calibration2 = loadcell2.get_calibration()
print("1: ", hex(IIC_ADDRESS_1), "", calibration1[0])
print("2: ", hex(IIC_ADDRESS_2), "", calibration2[0])

print("\nComputing a stronger calibration:")

x, y = symbols("x y")
offset_x = offset_x1 #(offset_x1 + offset_x2 + offset_x3) / 3
offset_y = offset_y1 #(offset_y1 + offset_y2 + offset_y3) / 3
equation_1 = Eq((((value_x1 - offset_x)/x) + (value_y1 - offset_y)/y), -CALIBRATION_WEIGHT)
equation_2 = Eq((((value_x2 - offset_x)/x) + (value_y2 - offset_y)/y), -CALIBRATION_WEIGHT)
equation_3 = Eq((((value_x3 - offset_x)/x) + (value_y3 - offset_y)/y), -CALIBRATION_WEIGHT)

print("Solving sets of equations 1/3..", end="\r")
solution12 = solve((equation_1, equation_2), (x, y))
print("Solving sets of equations 2/3..", end="\r")
solution13 = solve((equation_1, equation_3), (x, y))
print("Solving sets of equations 3/3..", end="")
solution23 = solve((equation_2, equation_3), (x, y))
print("Done.")
print("Combining solutions..", end="")
result1 = (float(solution12[0][0]) + float(solution13[0][0]) + float(solution23[0][0])) / 3
result2 = (float(solution12[0][1]) + float(solution13[0][1]) + float(solution23[0][1])) / 3
print("Done.")

print("\nIndividual solutions are:")
print(f"({float(solution12[0][0]):.2f}, {float(solution12[0][1]):.2f})  ({float(solution13[0][0]):.2f}, {float(solution13[0][1]):.2f})  ({float(solution23[0][0]):.2f}, {float(solution23[0][1]):.2f})")
# print("Solution 1-2:", float(solution12[0][0]), float(solution12[0][1]))
# print("Solution 1-3:", float(solution13[0][0]), float(solution13[0][1]))
# print("Solution 2-3:", float(solution23[0][0]), float(solution23[0][1]))

print("\nThe COMPUTED calibration value of the sensors are (strong calibration):")
print("1: ", hex(IIC_ADDRESS_1), "", result1)
print("2: ", hex(IIC_ADDRESS_2), "", result2)
print("")

# print("")
# print("offset_x1     ", offset_x1)
# print("avg offset_x  ", offset_x)
# print("offset_y1     ", offset_y1)
# print("avg offset_y  ", offset_y)