import time
import board
import neopixel
import numpy as np

MAX_BRIGHTNESS = 0.05    # DO NOT CHANGE, UNLESS USING DEDICATED POWER SUPPLY
FADE_UPDATE_RATE = 20

pixels = neopixel.NeoPixel(board.D18, 60, bpp=3, brightness=MAX_BRIGHTNESS)

def test():
    pixels.fill((255,0,0))
    time.sleep(0.25)
    pixels.fill((0,255,0))
    time.sleep(0.25)
    pixels.fill((0,0,255))
    time.sleep(0.25)
    pixels.fill((125,125,125))
    time.sleep(0.25)

def color(color=(0,0,0), brightness=1):
    filler = np.array(color) * brightness
    pixels.fill(filler.astype(np.int16))

def off():
    pixels.fill((0,0,0))

def fade(from_c=(0,0,0), from_b=0, to_c=(0,0,0), to_b=0, duration=1.0):
    steps = int(FADE_UPDATE_RATE * duration)

    for i in range(1, steps+1):
        i_color = np.array(from_c) + i * ((np.array(to_c) - np.array(from_c)) / steps)
        i_brightness = from_b + i * ((to_b - from_b) / steps)
        color(color=i_color, brightness=i_brightness)
        time.sleep(1/FADE_UPDATE_RATE)

def blink(color=(0,0,0), brightness=1, times=2, pause=0.2, keep=False):
    filler = np.array(color) * brightness

    for i in range(times):
        pixels.fill((0,0,0))
        time.sleep(pause)
        pixels.fill(filler.astype(np.int16))
        time.sleep(pause)
        
    if keep==False:
        pixels.fill((0,0,0))


if __name__ == "__main__":
    color((255, 255, 255), brightness=0.5)
    time.sleep(1)
    color()
    time.sleep(1)
    fade(from_c=(255,0,0), from_b=0.5, to_c=(100,100,100), to_b=1)
    time.sleep(1)
    blink((255,0,0), 1, times=5, pause=0.2, keep=True)