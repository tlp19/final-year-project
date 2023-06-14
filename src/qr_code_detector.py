# Import libraries
import time
import cv2
import numpy as np
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol


REPEATED_DETECTIONS = 3


def start(camera, timer=1.0, crop_ratio=1):

    end_time = time.time() + timer

    # Capture the first video frame
    success, frame = camera.read()
    if not success:
        print("Camera could not be read")
        return False

    # Find the position of each border
    height, width, _ = frame.shape
    side_length = height * crop_ratio
    top_border = int((height/2) - (side_length/2))
    bottom_border = int((height/2) + (side_length/2))
    left_border = int((width/2) - (side_length/2))
    right_border = int((width/2) + (side_length/2))

    data = {}
    final_data = None

    while(time.time() < end_time):

        # Slice the initial image
        frame = frame[top_border:bottom_border, left_border:right_border]

        # Find and decode QR codes
        qrcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
       
        for qrcode in qrcodes:
            code_info = qrcode.data.decode('utf-8')
            
            # Check that QR code has been decoded reliably multiple (3) times
            previous_occurrences = data.get(code_info, 0)
            if previous_occurrences >= (REPEATED_DETECTIONS-1):
                final_data = code_info
                break
            
            data[code_info] = previous_occurrences + 1

            # Overlay detected QR codes on the frame
            x, y , w, h = qrcode.rect
            cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, code_info, (x + 6, y - 6), font, 0.5, (255, 255, 255), 1)

        if final_data is not None:
            break

        cv2.imshow('detectionFrame', frame)

        # Capture the next video frame
        success, frame = camera.read()
        if not success:
            print("Camera could not be read")
            break
            
        # the 'q' button is set as the
        # quitting button you may use any
        # desired button of your choice
        if cv2.waitKey(100) & 0xFF == ord('q'): #40 for 25Hz
            break

    # Destroy all the windows
    cv2.destroyAllWindows()

    return final_data


if __name__ == "__main__":
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    assert cam.isOpened()
    result = start(cam, timer=100, crop_ratio=2/3)
    print(result)
    cam.release()