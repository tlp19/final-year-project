# Import libraries
import time
import cv2
import numpy as np


COLOR_MATCH_THRESHOLD = 0.40
REPEATED_MATCHES = 3


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
        lower_range = np.array([int(230/360*180), int(25/100*255), int(25/100*255)])
        upper_range = np.array([int(290/360*180), int(90/100*255), int(80/100*255)])

        # Check which parts of the image are in the color boundaries
        mask = cv2.inRange(hsv_center_frame, lower_range, upper_range)

        # Check that the Detection Color is present above a certain threshold in the centerFrame
        if(np.mean(mask) >= COLOR_MATCH_THRESHOLD * 255):
            # print("COLOR MATCH")
            color_matches += 1
            if(color_matches >= REPEATED_MATCHES):
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


if __name__ == "__main__":
    cam = cv2.VideoCapture(2)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    assert cam.isOpened()
    result = start(cam, timer=100, crop_ratio=1/2)
    print(result)