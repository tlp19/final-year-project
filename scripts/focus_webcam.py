# import the opencv library
import cv2

CAMERA_ID = 2

# define a video capture object
cam = cv2.VideoCapture(CAMERA_ID)
cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)

print("\nPlace a CauliCup with the CauliCup logo facing the camera.")
print("Once the logo is in focus, press [q]: this will exit this script and save the autofocus.\n")

while(True):
    # Capture the video frame by frame
    success, frame = cam.read()

    if not success:
        print("Camera could not be read")
        break
    
    # Display the resulting frame
    cv2.imshow('initialFrame', frame)

    # the 'q' button is set as the
    # quitting button you may use any
    # desired button of your choice
    if cv2.waitKey(5) & 0xFF == ord('q'):
        cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        break

# After the loop release the cap object
cam.release()
# Destroy all the windows
cv2.destroyAllWindows()