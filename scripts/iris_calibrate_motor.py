import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.OUT)

pwm = GPIO.PWM(32, 50)
pwm.start(0)

DUTY_BRACKET = (1000, 1750)

# 1000 : 1375 : 1750

def duty_from_dir(dir):
    # dir = min(1.0, max(-1.0, dir))      # Cutoff the direction between 1 and -1
    dir = - dir                         # Reverse the direction so that 1 is CW and -1 is CCW
    
    # Find the characteristics of the duty cycle
    middle_duty = (DUTY_BRACKET[0] + DUTY_BRACKET[1]) / 2
    range_duty = DUTY_BRACKET[1] - DUTY_BRACKET[0]

    # Compute the equivalent duty cycle value (microseconds)
    duty_value = middle_duty + dir * (range_duty / 2)

    # Find the associated duty cycle (percentage of a 50Hz freq (period is 20,000 microsec))
    duty = (duty_value / 20_000) * 100
    output = round(duty, 3)

    print("dir", -dir)
    print("duty_value", duty_value)
    print("duty", output)
    print("")
    return output

try:
    # Make the continuous servo turn
    pwm.ChangeDutyCycle(duty_from_dir(1))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(0.9))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(0.75))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(0.25))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(0))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(-0.25))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(-0.75))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(-0.9))
    time.sleep(1)
    pwm.ChangeDutyCycle(duty_from_dir(-1.0))
    time.sleep(1)
    pwm.stop()
    GPIO.cleanup()

except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()