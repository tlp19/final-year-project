# import the opencv library
import cv2
import numpy as np

# define a video capture object
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)

while(True):
    # Capture the video frame by frame
    success, frame = cam.read()

    if not success:
        print("Camera could not be read")
        break

    else:
        # Display the resulting frame
        cv2.imshow('initialFrame', frame)

        # Choose a crop ratio
        crop_ratio = 1/2

        # Find the position of each border
        height, width, _ = frame.shape
        side_length = height * crop_ratio
        top_border = int((height/2) - (side_length/2))
        bottom_border = int((height/2) + (side_length/2))
        left_border = int((width/2) - (side_length/2))
        right_border = int((width/2) + (side_length/2))

        # Slice the initial image
        center_frame = frame[top_border:bottom_border, left_border:right_border]
        cv2.imshow('centerFrame', center_frame)

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
        else:
            print("no match")

        cv2.imshow('colorMaskedCenterFrame', mask)

    # the 'q' button is set as the
    # quitting button you may use any
    # desired button of your choice
    if cv2.waitKey(100) & 0xFF == ord('q'):
        break

# After the loop release the cap object
cam.release()
# Destroy all the windows
cv2.destroyAllWindows()