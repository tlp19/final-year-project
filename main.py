import time
import cv2
import src.colour_detection as colour_detection
import src.motion_detection as motion_detection
import src.qr_code_detector as qr_code_detector
import src.load_cells as load_cells
import src.object_detection as object_detection
import src.leds as leds


SIDE_CAMERA_ID = 2
TOP_CAMERA_ID = 0


def init_camera(camera_id, autofocus=False):
    # Define a video capture object (side camera)
    cam = cv2.VideoCapture(camera_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, int(autofocus))
    assert cam.isOpened()
    return cam


if __name__ == "__main__":

    camera = init_camera(SIDE_CAMERA_ID)
    leds.test()
    load_cells.tare()

    while(True):
        leds.off()

        # Presence detection: Motion detection
        motion_detected = motion_detection.loop(camera=camera, crop_ratio=1)
        if not motion_detected:
            print("Motion detection failed. Trying again.")
            continue

        leds.fade(to_c=(100,150,100), to_b=0.5, duration=0.5)

        # Presence detection: Colour detection
        color_detected = colour_detection.start(camera=camera, timer=5.0, crop_ratio=1/2)
        if not color_detected:
            print("No object of a valid colour was detected. Skipping.")
            leds.blink((255,100,0), brightness=0.25, times=2, pause=0.1)
            continue

        print("Success! Presence detected.")

        leds.fade((100,150,100), 0.5, to_c=(100,150,100), to_b=0.25, duration=0.5)

        # Validity checking: QR code detection
        camera.release() # Release the main camera to free-up USB bandwidth
        camera_top = init_camera(TOP_CAMERA_ID, autofocus=True) # Start the top-down camera
        qr_code = qr_code_detector.start(camera_top, timer=8.0, crop_ratio=2/3)
        camera_top.release() # Stop the top_down camera
        camera = init_camera(SIDE_CAMERA_ID) # Re-initialise the main camera
        print("qr_code:", qr_code)
        if qr_code is None:
            print("No QR code was detected. Skipping.")
            leds.blink((255,0,0), brightness=1, times=2, keep=True)
            time.sleep(3)
            continue
        #TODO: Check if QR code is valid with Cauli API

        # Validity checking: Weight checking
        valid_weight = load_cells.check_weight()
        if not valid_weight:
            print("Weight is not valid. Skipping.")
            leds.blink((255,0,0), brightness=1, times=2, keep=True)
            time.sleep(3)
            continue

        # Validity checking: Object detection
        cauli_bbox = object_detection.run(camera=camera, tries=10)
        if cauli_bbox is None:
            print("No CauliCup was detected. Skipping.")
            leds.blink((255,0,0), brightness=1, times=2, keep=True)
            time.sleep(3)
            continue

        print("result:", cauli_bbox)

        #TODO: run object tracking from bbox (add uncertainty counter)
        #TODO: open the iris (in parallel)
        #TODO: check object went in with tracking

        # Collection: Empty weight checking
        valid_weight = load_cells.check_empty_weight()
        if not valid_weight:
            print("Weight is not valid. Skipping.")
            leds.blink((255,0,0), brightness=1, times=3, keep=True)
            time.sleep(3)
            continue

        #TODO: close the iris
        #TODO: send collection message to Cauli API (keep in backlog if fails, sync at later collection)
        #TODO: tare the load cells (if necessary)

        #DONE: LED interface throughout the execution
        #TODO: add logging for maintainers
        #FIXME: remove debug prints

        leds.color(brightness=0)

        #FIXME: remove this
        break


    # After the loop release the camera object
    camera.release()