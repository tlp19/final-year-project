# import the opencv library
import cv2
import numpy as np
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

# define a video capture object
# cam = cv2.VideoCapture(0)
cam = cv2.VideoCapture(2)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while(True):
    # Capture the video frame by frame
    success, frame = cam.read()

    if not success:
        print("Camera could not be read")
        break
    
    else:
        # # Display the resulting frame
        # cv2.imshow('initialFrame', frame)

        # Choose a crop ratio
        crop_ratio = 3/4

        # Find the position of each border
        height, width, _ = frame.shape
        side_length = height * crop_ratio
        top_border = int((height/2) - (side_length/2))
        bottom_border = int((height/2) + (side_length/2))
        left_border = int((width/2) - (side_length/2))
        right_border = int((width/2) + (side_length/2))

        # Slice the initial image
        frame = frame[top_border:bottom_border, left_border:right_border]
        # cv2.imshow('centerFrame', frame)

        barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
        
        for barcode in barcodes:
            x, y , w, h = barcode.rect
            barcode_info = barcode.data.decode('utf-8')
            cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
            
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 0.5, (255, 255, 255), 1)

        cv2.imshow('detectionFrame', frame)
        
    # the 'q' button is set as the
    # quitting button you may use any
    # desired button of your choice
    if cv2.waitKey(40) & 0xFF == ord('q'): #40 for 25Hz
        break

# After the loop release the cap object
cam.release()
# Destroy all the windows
cv2.destroyAllWindows()