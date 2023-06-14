import time
import cv2
from multiprocessing import Process, Queue
import src.colour_detection as colour_detection
import src.motion_detection as motion_detection
import src.qr_code_detector as qr_code_detector
import src.load_cells as load_cells
import src.object_detection as object_detection
import src.leds as leds
import src.object_tracking as object_tracking
import src.iris as iris


SIDE_CAMERA_ID = 2
TOP_CAMERA_ID = 0


def init_camera(camera_id, resolution=(1280,720), autofocus=False):
    # Define a video capture object (side camera)
    cam = cv2.VideoCapture(camera_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, int(autofocus))
    assert cam.isOpened()
    return cam


if __name__ == "__main__":

    leds.test()
    load_cells.tare()

    while(True):
        leds.off()

        # Presence detection: Motion detection
        camera = init_camera(SIDE_CAMERA_ID)
        motion_detected = motion_detection.loop(camera=camera, crop_ratio=1)
        if not motion_detected:
            print("Motion detection failed. Trying again.")
            continue


        print("out")
        leds.fade(to_c=(100,150,100), to_b=0.5, duration=0.5)

        # Presence detection: Colour detection
        color_detected = colour_detection.start(camera=camera, timer=5.0, crop_ratio=1/2)
        camera.release() # Release the main camera to free-up USB bandwidth
        if not color_detected:
            print("No object of a valid colour was detected. Skipping.")
            leds.blink((255,100,0), brightness=0.25, times=2, pause=0.1)
            continue

        print("Success! Presence detected.")

        leds.fade((100,150,100), 0.5, to_c=(100,150,100), to_b=0.25, duration=0.5)

        # Validity checking: QR code detection
        camera_top = init_camera(TOP_CAMERA_ID, autofocus=True) # Start the top-down camera
        qr_code = qr_code_detector.start(camera_top, timer=8.0, crop_ratio=2/3)
        camera_top.release() # Stop the top_down camera
        
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
        camera = init_camera(SIDE_CAMERA_ID, resolution=(640,480)) # Re-initialise the main camera
        cauli_bbox = object_detection.run(camera=camera, tries=10)
        camera.release()
        if cauli_bbox is None:
            print("No CauliCup was detected. Skipping.")
            leds.blink((255,0,0), brightness=1, times=2, keep=True)
            time.sleep(3)
            continue

        # Object collection: Object tracking + Open and close iris
        bbox, uncertainty = None, None
        q = Queue()
        p = Process(target=object_tracking.track, args=(q, cauli_bbox, 8.0, SIDE_CAMERA_ID, (640,480)))
        p.start()
        time.sleep(1.0)
        iris.open()
        p.join()
        print(q.get())
        
        
        iris.close()
        if (uncertainty is None) or (bbox is None):
            print("Tracking failed. Collection is invalid.")
            leds.blink((255,100,0), brightness=1, times=3, keep=True)
            time.sleep(3)
            continue

        # Object collection: Analyse tracking results
        valid_tracking = object_tracking.validate(bbox, uncertainty)
        if (valid_tracking is None) or (valid_tracking == False):
            print("Object did not fall through the trapdoor. Collection is invalid.")
            leds.blink((255,100,0), brightness=1, times=3, keep=True)
            time.sleep(3)
            continue

        # Object collection: Empty weight checking
        valid_weight = load_cells.check_empty_weight()
        if not valid_weight:
            print("Weight is not valid. Collection is invalid.")
            leds.blink((255,100,0), brightness=1, times=3, keep=True)
            time.sleep(3)
            continue

        leds.blink((0,255,0), brightness=1, times=3, keep=False)

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