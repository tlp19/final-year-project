# Import libraries
import cv2
import numpy as np


SENSIBILITY = 50_000


def loop(camera, crop_ratio = 1):

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

    previous_frame = None
    motion_detected = False
    print("Waiting for motion...")

    while(not motion_detected):
        print("in while loop")

        # Capture the next video frame
        success, frame = camera.read()
        if not success:
            print("Camera could not be read")
            break

        # Slice the initial image
        center_frame = frame[top_border:bottom_border, left_border:right_border]

        # Prepare the image (greyscale + blur to negate noise)
        prepared_frame = cv2.cvtColor(center_frame, cv2.COLOR_BGR2GRAY)
        prepared_frame = cv2.GaussianBlur(src=prepared_frame, ksize=(5,5), sigmaX=0)

        if (previous_frame is None):
            # First frame; there is no previous one yet
            previous_frame = prepared_frame
            continue

        print("checkpoint")
            
        # Calculate difference and update previous frame
        diff_frame = cv2.absdiff(src1=previous_frame, src2=prepared_frame)
        previous_frame = prepared_frame

        # Dilate the detected changes to fill in small gaps
        kernel = np.ones((5, 5))
        diff_frame = cv2.dilate(diff_frame, kernel, 1)

        # Find if difference is above a certain threshold
        thresh_frame = cv2.threshold(src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]

        print("checkpoint2")

        # Draw contours of areas that have changed
        contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(image=center_frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
        print("checkpoint3")
        cv2.imshow('centerFrameWithContours', center_frame)

        print("checkpoint4")

        # Check if there is any significant motion
        for contour in contours:
            # print(cv2.contourArea(contour))
            if cv2.contourArea(contour) > SENSIBILITY:
                # Ignore small motion
                # e.g. something in the background or motion caused by camera autofocus
                motion_detected = True
                break

        print("in while loop end")

        # the 'q' button is set as the
        # quitting button you may use any
        # desired button of your choice
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break

    # Destroy all the windows
    cv2.destroyAllWindows()

    return motion_detected


if __name__ == "__main__":
    cam = cv2.VideoCapture(2)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    assert cam.isOpened()
    loop(cam, crop_ratio=3/4)