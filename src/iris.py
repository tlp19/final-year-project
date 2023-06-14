import RPi.GPIO as GPIO
import time


DUTY_BRACKET = (1000, 1700)
OPEN_DURATION = 1.5
CLOSE_DURATION = 1.2


def duty_from_dir(dir):
    dir = min(1.0, max(-1.0, dir))      # Cutoff the direction between 1 and -1
    dir = - dir                         # Reverse the direction so that 1 is CW and -1 is CCW
    # Find the characteristics of the duty cycle
    middle_duty = (DUTY_BRACKET[0] + DUTY_BRACKET[1]) / 2
    range_duty = DUTY_BRACKET[1] - DUTY_BRACKET[0]
    # Compute the equivalent duty cycle value (microseconds)
    duty_value = middle_duty + dir * (range_duty / 2)
    # Find the associated duty cycle (percentage of a 50Hz freq (period is 20,000 microsec))
    duty = (duty_value / 20_000) * 100
    return round(duty, 3)

def open():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(12, GPIO.OUT)
    pwm = GPIO.PWM(12, 50)
    pwm.start(0)
    pwm.ChangeDutyCycle(duty_from_dir(0.5))
    time.sleep(OPEN_DURATION)
    pwm.ChangeDutyCycle(duty_from_dir(0))
    pwm.stop()
    

def close():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(12, GPIO.OUT)
    pwm = GPIO.PWM(12, 50)
    pwm.start(0)
    pwm.ChangeDutyCycle(duty_from_dir(-0.5))
    time.sleep(CLOSE_DURATION)
    pwm.ChangeDutyCycle(duty_from_dir(0))
    pwm.stop()

def open_continuously():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(12, GPIO.OUT)
    pwm = GPIO.PWM(12, 50)
    pwm.start(0)
    pwm.ChangeDutyCycle(duty_from_dir(0.5))
    return pwm

def stop(pwm):
    pwm.ChangeDutyCycle(duty_from_dir(0))
    pwm.stop()



if __name__ == "__main__":
    open()
    time.sleep(2)
    close()
    GPIO.cleanup()
    
    