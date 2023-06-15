import time
import cv2
import RPi.GPIO as GPIO
import src.colour_detection as colour_detection
import src.motion_detection as motion_detection
import src.qr_code as qr_code
import src.load_cells as load_cells
import src.object_detection as object_detection
import src.leds as leds
import src.object_tracking as object_tracking
import src.iris as iris
import src.backend as backend


SIDE_CAMERA_ID = 2
TOP_CAMERA_ID = 0


def init_camera(camera_id, resolution=(640,480), fps=20, autofocus=False):
    # Define a video capture object (side camera)
    cam = cv2.VideoCapture(camera_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    cam.set(cv2.CAP_PROP_FPS, fps)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, int(autofocus))
    return cam


if __name__ == "__main__":

    leds.test()
    load_cells.tare()

    try:
        while(True):
            leds.off()

            # Presence detection: Motion detection
            camera = init_camera(SIDE_CAMERA_ID)
            print("Waiting for motion...")
            motion_detected = motion_detection.loop(camera=camera, crop_ratio=1)
            if not motion_detected:
                print("Motion detection failed. Trying again.")
                continue

            leds.fade(to_c=(100,150,100), to_b=0.5, duration=0.5)

            # Presence detection: Colour detection
            color_detected = colour_detection.start(camera=camera, timer=5.0, crop_ratio=1/2)
            camera.release() # Release the main camera to free-up USB bandwidth
            if not color_detected:
                print("No object of a valid colour was detected. Skipping.")
                leds.blink((255,100,0), brightness=0.25, times=2, pause=0.1)
                continue

            print("Presence detected.")

            leds.color((100,100,100), 0.25)

            # Validity checking: QR code detection
            camera_top = init_camera(TOP_CAMERA_ID, autofocus=True) # Start the top-down camera
            code = qr_code.detect(camera_top, timer=8.0, crop_ratio=2/3)
            camera_top.release() # Stop the top_down camera
            
            print("qr_code:", code)
            if code is None:
                print("No QR code was detected. Skipping.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue
            
            # Validity checking: QR code verification
            cup = qr_code.process(code)
            if not backend.check_container(cup):
                print("QR code is not valid. Skipping.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue

            # Validity checking: Weight checking
            valid_weight = load_cells.check_weight()
            if not valid_weight:
                print("Weight is not valid. Skipping.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue

            # Validity checking: Object detection
            camera = init_camera(SIDE_CAMERA_ID, resolution=(640,480), fps=30) # Re-initialise the main camera
            cauli_bbox = object_detection.run(camera=camera, tries=10)
            if cauli_bbox is None:
                print("No CauliCup was detected. Skipping.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue

            leds.fade((100,100,100), 0.25, to_c=(0,0,200), to_b=0.25, duration=0.5)

            # Object collection: Object tracking + Open and close iris
            bbox, dims, uncertainty = object_tracking.track_and_open_iris(camera, cauli_bbox, timer=6.0, iris_open_delay=1)
            camera.release()
            iris.close()
            if (uncertainty is None) or (bbox is None):
                print("Tracking did not work. Collection is invalid.")
                backend.record_collection(cup, status="Broken tracking")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue

            # Object collection: Analyse tracking results
            valid_tracking = object_tracking.validate(bbox, dims, uncertainty)
            if (valid_tracking is None) or (valid_tracking == False):
                print("Object did not fall through the trapdoor. Collection is invalid.")
                backend.record_collection(cup, status="Failed tracking")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue

            # Object collection: Empty weight checking
            valid_weight = load_cells.check_empty_weight()
            if not valid_weight:
                print("Weight is not valid. Collection is invalid.")
                backend.record_collection(cup, status="Failed empty platform")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue

            confirmation = backend.send_collection_confirmation(cup)
            if not confirmation:
                print("Failed to send collection confirmation.")
                backend.record_collection(cup, status="Failed confirmation")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue
            
            print("SUCCESS!\n")
            backend.record_collection(cup, status="Collected")
            leds.blink((0,255,0), brightness=1, times=3, keep=False)

            #TODO: add logging for maintainers


    except KeyboardInterrupt:
        print(" Excited with KeyboardInterrupt. Cleaning up...")
        # After the loop release the camera object
        camera.release()
        iris.cleanup()