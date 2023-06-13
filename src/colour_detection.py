# Import libraries
import time
import cv2
import numpy as np


def start(camera, timer = 1.0, crop_ratio = 1):

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

    color_matches = 0
    while(time.time() < end_time):

        # Slice the initial image
        center_frame = frame[top_border:bottom_border, left_border:right_border]
        # cv2.imshow('centerFrame', center_frame)

        # Convert the frame to HSV
        hsv_center_frame = cv2.cvtColor(center_frame, cv2.COLOR_BGR2HSV)
        
        # Define color detection boundaries
        lower_range = np.array([int(230/360*180), int(15/100*255), int(5/100*255)])
        upper_range = np.array([int(320/360*180), int(60/100*255), int(50/100*255)])

        # Check which parts of the image are in the color boundaries
        mask = cv2.inRange(hsv_center_frame, lower_range, upper_range)

        # Check that the Detection Color is present above a certain threshold in the centerFrame
        color_match_threshold = 0.20
        if(np.mean(mask) >= color_match_threshold * 255):
            print("COLOR MATCH")
            color_matches += 1
            if(color_matches >= 3):
                break

        cv2.imshow('colorMaskedCenterFrame', mask)

        # Capture the next video frame
        success, frame = camera.read()
        if not success:
            print("Camera could not be read")
            break

        # the 'q' button is set as the
        # quitting button you may use any
        # desired button of your choice
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break

    # Destroy all the windows
    cv2.destroyAllWindows()

    return (color_matches >= 3)