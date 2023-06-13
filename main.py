import cv2
import src.colour_detection as colour_detection
import src.motion_detection as motion_detection
import src.qr_code_detector as qr_code_detector
import src.load_cells as load_cells
import src.object_detection as object_detection

def init_camera():
    # Define a video capture object (side camera)
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    assert cam.isOpened()
    return cam


if __name__ == "__main__":

    camera = init_camera()
    load_cells.tare()

    while(True):

        # Presence detection: Motion detection
        motion_detected = motion_detection.loop(camera=camera, crop_ratio=2/3)
        if not motion_detected:
            print("Motion detection failed. Trying again.")
            continue

        # Presence detection: Colour detection
        color_detected = colour_detection.start(camera=camera, timer=5.0, crop_ratio=1/2)
        print("result:", color_detected)
        if not color_detected:
            print("No object of a valid colour was detected. Skipping.")
            continue

        print("Success! Presence detected.")

        # Validity checking: Weight checking
        valid_weight = load_cells.check_weight()
        if not valid_weight:
            print("Weight is not valid. Skipping.")
            continue

        # Validity checking: QR code detection
        camera.release() # Release the main camera to free-up USB bandwidth
        qr_code = qr_code_detector.start(timer=5.0, crop_ratio=2/3)
        camera = init_camera() # Re-initialise the main camera
        print("result:", qr_code)
        if qr_code is None:
            print("No QR code was detected. Skipping.")
            continue
        #TODO: Check if QR code is valid with Cauli API

        # Validity checking: Object detection
        cauli_bbox = object_detection.run(camera=camera, tries=10)
        if cauli_bbox is None:
            print("No CauliCup was detected. Skipping.")
            continue

        print("result:", cauli_bbox)

        #TODO: run object tracking from bbox (add uncertainty counter)
        #TODO: open the iris (in parallel)
        #TODO: check object went in with tracking
        #TODO: confirm with weight check
        #TODO: close the iris
        #TODO: send collection message to Cauli API (keep in backlog if fails, sync at later collection)
        #TODO: tare the load cells (if necessary)

        #TODO: LED interface throughout the execution

        #TODO: add logging for maintainers
        #FIXME: remove debug prints

        #FIXME: remove this
        break


    # After the loop release the cap object
    camera.release()