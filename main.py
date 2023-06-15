import time
import logging
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

LOGFILE_PATH = "./data/log.txt"


logging.basicConfig(filename=LOGFILE_PATH, level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')

def init_camera(camera_id, resolution=(640,480), fps=15, autofocus=False):
    # Define a video capture object (side camera)
    cam = cv2.VideoCapture(camera_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    cam.set(cv2.CAP_PROP_FPS, fps)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, int(autofocus))
    logging.debug(f'Initialised camera with ID {camera_id}, resolution {resolution}, fps {fps}, autofocus {autofocus}.')
    return cam


if __name__ == "__main__":

    leds.test()
    load_cells.tare()
    logging.info(f'Set-up complete. Entering main loop.')

    try:
        while(True):
            logging.debug(f'Resetting LEDs.')
            leds.off()

            # Presence detection: Motion detection
            camera = init_camera(SIDE_CAMERA_ID)
            print("Waiting for motion...")
            logging.info(f'Waiting for motion...')
            motion_detected = motion_detection.loop(camera=camera, crop_ratio=1)
            if not motion_detected:
                print("Motion detection failed. Trying again.")
                logging.error(f'Motion detection failed. Trying again.')
                continue
            logging.info(f"Motion detected.")

            leds.fade(to_c=(100,150,100), to_b=0.5, duration=0.5)

            # Presence detection: Colour detection
            logging.info(f"Checking object colour.")
            color_detected = colour_detection.start(camera=camera, timer=5.0, crop_ratio=1/2)
            camera.release() # Release the main camera to free-up USB bandwidth
            if not color_detected:
                print("No object of expected colour was detected. Skipping.")
                logging.warning(f"No object of expected colour was detected. Skipping.")
                leds.blink((255,100,0), brightness=0.25, times=2, pause=0.1)
                continue
            logging.info(f"Object is of expected colour.")

            print("Presence detected.")
            logging.info(f"-> Presence detected successfully.")
            leds.color((100,100,100), 0.25)

            # Validity checking: QR code detection
            logging.info(f"Starting QR code detection...")
            camera_top = init_camera(TOP_CAMERA_ID, autofocus=True) # Start the top-down camera
            code = qr_code.detect(camera_top, timer=8.0, crop_ratio=2/3)
            camera_top.release() # Stop the top_down camera
            print("qr_code:", code)
            if code is None:
                print("No QR code was detected. Skipping.")
                logging.warning(f"No QR code was detected.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue
            logging.info(f"QR code detected with data: {code}.")
            
            # Validity checking: QR code verification
            logging.info(f"Checking QR code data...")
            cup = qr_code.process(code)
            if not backend.check_container(cup):
                print("QR code is not valid. Skipping.")
                logging.warning(f"QR code data is not valid. Processed data: {cup}")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue
            logging.info(f"QR code data is valid.")
            logging.info(f"Current object is {cup.get('type', 'error')} {cup.get('id', 'error')}")

            # Validity checking: Weight checking
            logging.info(f"Checking weight...")
            valid_weight = load_cells.check_weight()
            if not valid_weight:
                print("Weight is not valid. Skipping.")
                logging.warning(f"Weight is not valid.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue
            logging.info(f"Weight is valid.")

            # Validity checking: Object detection
            logging.info(f"Starting object detection...")
            camera = init_camera(SIDE_CAMERA_ID, resolution=(640,480), fps=30) # Re-initialise the main camera
            conf, cauli_bbox = object_detection.run(camera=camera, tries=10)
            if cauli_bbox is None:
                print("No CauliCup was detected. Skipping.")
                logging.warning(f"No CauliCup was detected.")
                leds.blink((255,0,0), brightness=1, times=2, keep=True)
                time.sleep(3)
                continue
            logging.info(f"CauliCup detected with confidence {conf}.")

            logging.info(f"-> Validity checked successfully.")
            leds.fade((100,100,100), 0.25, to_c=(0,0,200), to_b=0.25, duration=0.5)

            # Object collection: Object tracking + Open and close iris
            logging.info(f"Starting object tracking and opening iris...")
            bbox, dims, uncertainty = object_tracking.track_and_open_iris(camera, cauli_bbox, timer=6.0, iris_open_delay=1)
            camera.release()
            logging.info(f"Closing iris...")
            iris.close()
            if (uncertainty is None) or (bbox is None):
                print("Tracking did not work. Collection is invalid.")
                logging.error(f"Tracking did not work.")
                backend.record_collection(cup, status="Broken tracking")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue
            logging.info(f"Tracking completed.")

            # Object collection: Analyse tracking results
            valid_tracking = object_tracking.validate(bbox, dims, uncertainty)
            if (valid_tracking is None) or (valid_tracking == False):
                print("Object did not fall through the trapdoor. Collection is invalid.")
                logging.warning(f"Tracking indicates that the object has not been collected.")
                backend.record_collection(cup, status="Failed tracking")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue
            logging.info(f"Tracking is valid.")

            # Object collection: Empty weight checking
            logging.info(f"Checking that the platform is now empty...")
            valid_weight = load_cells.check_empty_weight()
            if not valid_weight:
                print("Weight is not valid. Collection is invalid.")
                logging.warning(f"The platform has non zero weight, the object was not collected.")
                backend.record_collection(cup, status="Failed empty platform")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue
            logging.info(f"Platform is empty.")

            # Object collection: Send confirmation
            logging.info(f"Sending collection confirmation...")
            confirmation = backend.send_collection_confirmation(cup)
            if not confirmation:
                print("Failed to send collection confirmation.")
                logging.error(f"The collection confirmation was not sent successfully.")
                backend.record_collection(cup, status="Failed confirmation")
                leds.blink((255,100,0), brightness=1, times=3, keep=True)
                time.sleep(3)
                continue
            
            print("SUCCESS!\n")
            logging.info(f"-> Successful collection of {cup.get('type', 'error')} {cup.get('id', 'error')}!")
            backend.record_collection(cup, status="Collected")
            leds.blink((0,255,0), brightness=1, times=3, keep=False)


    except KeyboardInterrupt:
        print(" Excited with KeyboardInterrupt. Cleaning up...")
        logging.info(f"Excited with KeyboardInterrupt. Cleaning up...")
        # After the loop release the camera object
        camera.release()
        iris.cleanup()
        logging.info(f"-> Cleaned up successfully.")