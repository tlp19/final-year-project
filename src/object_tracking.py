# Import libraries
import time
import cv2
import numpy as np

if __name__ != "__main__":
    from . import iris
if __name__ == "__main__":
    import iris


DIFF_DILATION = 3
DIFF_THRESH = 10
MIN_CONTOUR_AREA = 2500

SEARCH_EXPANSION_FACTOR = 1.1
FRAGMENTED_BOX_OVERLAP_W_SEARCH = 0.75
SEARCH_OVERLAP_W_BIG_MOTION = 0.85

ALLOWED_DIM_REDUCTION_FACTOR = 0.6
ALLOWED_DIM_AUGMENTATION_FACTOR = 3.0
ALLOWED_MAX_SCREEN_PORTION = 0.80

# Find the bounding box that encompasses all the bounding boxes
def find_global_bounding_box(bounding_boxes):
    # Find the top left corner
    x1 = min([box[0] for box in bounding_boxes])
    y1 = min([box[1] for box in bounding_boxes])
    # Find the bottom right corner
    x2 = max([box[0] + box[2] for box in bounding_boxes])
    y2 = max([box[1] + box[3] for box in bounding_boxes])
    # Return the bounding box
    return (x1, y1, x2-x1, y2-y1)

# Compute the intersection of two bounding boxes
def find_intersection(box1, box2):
    # Find the top left corner
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    # Find the bottom right corner
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])
    # Return the bounding box if the intersection is valid; otherwise return None
    if (x1 < x2) and (y1 < y2):
        return (x1, y1, x2-x1, y2-y1)
    else:
        return None

# Compute the area of the intersection of two bounding boxes
def compute_intersection_area(box1, box2):
    # Find the intersection
    intersection_box = find_intersection(box1, box2)
    # Return the area if there is an intersection
    if (intersection_box is not None):
        return intersection_box[2] * intersection_box[3]
    else:
        return 0

# Compute the percentage of the overlapping box that is inside the box
def percentage_inside(overlapping_box, box):
    # Find the intersection area
    intersect_area = compute_intersection_area(overlapping_box, box)
    # Find the area of the overlapping box
    overlapping_box_area = overlapping_box[2] * overlapping_box[3]
    # Return the percentage
    return intersect_area / overlapping_box_area

# Expand a box by a certain factor
def expand_box(box, expansion_factor):
    # Find the center of the box
    center_x = box[0] + (box[2] / 2)
    center_y = box[1] + (box[3] / 2)
    # Find the new width and height
    new_width = box[2] * expansion_factor
    new_height = box[3] * expansion_factor
    # Find the new top left corner
    new_x = center_x - (new_width / 2)
    new_y = center_y - (new_height / 2)
    # Return the new box
    return (new_x, new_y, new_width, new_height)


def track_and_open_iris(camera, tracking_box, timer, iris_open_delay, debug=False):

    end_time = time.time() + timer
    iris_open_time = time.time() + iris_open_delay
    iris_stop_time = iris_open_time + iris.OPEN_DURATION
    iris_opened = False
    iris_stopped = False
    pwm = None

    assert (end_time > iris_stop_time) and (iris_stop_time > iris_open_time)

    previous_frame = None
    uncertainty = 0
    cam_height, cam_width = 0, 0

    iter_time = time.time()

    while(iter_time < end_time):

        if (time.time() > iris_stop_time) and not iris_stopped:
            iris_stopped = True
            iris.stop(pwm)

        if (time.time() > iris_open_time) and not iris_opened:
            iris_opened = True
            pwm = iris.open_continuously()

        # Capture the video frame by frame
        success, frame = camera.read()
        if not success:
            print("Camera could not be read")
            uncertainty += 1
            continue
        
        cam_height, cam_width, _ = frame.shape
        
        # Prepare the image (greyscale + blur to negate noise)
        prepared_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prepared_frame = cv2.GaussianBlur(src=prepared_frame, ksize=(5,5), sigmaX=0)

        if (previous_frame is None):
            # First frame; there is no previous one yet
            previous_frame = prepared_frame
            continue
            
        # Calculate difference and update previous frame
        diff_frame = cv2.absdiff(src1=previous_frame, src2=prepared_frame)
        previous_frame = prepared_frame

        # Dilate the detected changes to fill in small gaps
        kernel = np.ones((DIFF_DILATION, DIFF_DILATION))
        diff_frame = cv2.dilate(diff_frame, kernel, 1)

        # Find if difference is above a certain threshold
        thresh_frame = cv2.threshold(src=diff_frame, thresh=DIFF_THRESH, maxval=255, type=cv2.THRESH_BINARY)[1]

        # Draw contours of areas that have changed
        contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

        # Check if there is any significant motion
        contours = [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]
        bounding_boxes = [cv2.boundingRect(c) for c in contours]
        
        if debug:
            # Draw contours
            c_frame = frame.copy()
            cv2.drawContours(image=c_frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
            cv2.imshow('MotionContours', c_frame)
            # Draw the bounding boxes on the frame
            b_frame = frame.copy()
            for box in bounding_boxes:
                x, y, w, h = box
                cv2.rectangle(b_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.imshow('MotionBoundingBoxes', b_frame)
        
        # Find all the bounding boxes that overlap more that 50% with the expanded tracking box
        search_box = expand_box(tracking_box, SEARCH_EXPANSION_FACTOR)
        intersecting_boxes = [current_bbox for current_bbox in bounding_boxes
                            if (percentage_inside(current_bbox, search_box) > FRAGMENTED_BOX_OVERLAP_W_SEARCH)
                            or (percentage_inside(search_box, current_bbox) > SEARCH_OVERLAP_W_BIG_MOTION)]

        # Find the bounding box that encompasses all the intersecting boxes
        allowed_max_area = ALLOWED_MAX_SCREEN_PORTION * cam_width * cam_height

        tracking_succeeded = False
        if (len(intersecting_boxes) > 0):
            candidate_tracking_box = find_global_bounding_box(intersecting_boxes)
            # Use the global box if it is not significantly smaller than the tracking box
            # and is not not big with regards to the camera frame
            if ((candidate_tracking_box[2] > ALLOWED_DIM_REDUCTION_FACTOR * tracking_box[2])
            and (candidate_tracking_box[3] > ALLOWED_DIM_REDUCTION_FACTOR * tracking_box[3])
            and (candidate_tracking_box[2] < ALLOWED_DIM_AUGMENTATION_FACTOR * tracking_box[2])
            and (candidate_tracking_box[3] < ALLOWED_DIM_AUGMENTATION_FACTOR * tracking_box[3])
            and (candidate_tracking_box[2] * candidate_tracking_box[3] < allowed_max_area)):
                tracking_box = candidate_tracking_box
                tracking_succeeded = True
            else:
                # Failed to find a valid update, increase uncertainty
                uncertainty += 1 
        else:
            # No intersecting boxes; use the previous tracking box
            pass

        # Draw the updated tracking box
        t_frame = frame.copy()
        
        if debug:
            for box in intersecting_boxes:
                colour = (0,255,0) if tracking_succeeded else (0,0,255)
                cv2.rectangle(t_frame, (int(box[0]), int(box[1])), (int(box[0] + box[2]), int(box[1] + box[3])), colour, 2)
            
        cv2.rectangle(t_frame, (int(tracking_box[0]), int(tracking_box[1])), (int(tracking_box[0] + tracking_box[2]), int(tracking_box[1] + tracking_box[3])), (255, 0, 0), 3)
        cv2.imshow('Tracking Box', t_frame)

        if debug:
            print("fps:", (1/(time.time()-iter_time)))

        iter_time = time.time()

        # the 'q' button is set as the
        # quitting button you may use any
        # desired button of your choice
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Destroy all the windows
    cv2.destroyAllWindows()

    return tracking_box, (cam_height, cam_width), uncertainty


def validate(bbox, dims, uncertainty):

    height = dims[0]
    width = dims[1]

    xmin = bbox[0]
    ymin = bbox[1]
    xmax = bbox[0] + bbox[2]
    ymax = bbox[1] + bbox[3]

    x_center = (xmin+xmax)/2
    y_center = (ymin+ymax)/2

    print("tracking result:", bbox, dims, uncertainty)
    print("center of tracking box:", x_center, y_center)

    if uncertainty > 15:
        if (ymin <= 5) or (y_center <= 0.25 * height):
            return False
        if (x_center <= 0.10 * width) or (x_center >= 0.90 * width):
            return False
        
    elif uncertainty > 8:
        if (ymin <= 0.05 * height) or (y_center <= 0.33 * height):
            return False
        if (x_center <= 0.15 * width) or (x_center >= 0.85 * width):
            return False
        
    elif uncertainty > 3:
        if (ymin <= 0.10 * height) or (y_center <= 0.45 * height):
            return False
        if (x_center <= 0.20 * width) or (x_center >= 0.80 * width):
            return False
        
    else:
        if (ymin <= 0.15 * height) or (y_center <= 0.50 * height):
            return False
        if (x_center <= 0.25 * width) or (x_center >= 0.75 * width):
            return False

    return True



if __name__ == "__main__":
    camera = cv2.VideoCapture(2)
    camera.set(cv2.CAP_PROP_FPS, 20)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    assert camera.isOpened()
    # Read first frame.
    success, first_frame = camera.read()
    if not success:
        print("Camera could not be read")
        import sys 
        sys.exit()
    # Select a bounding box
    bbox = cv2.selectROI(first_frame, False)
    print(track_and_open_iris(camera, tracking_box=bbox, timer=100, iris_open_delay=10, debug=True))
    iris.close()
    camera.release()
    iris.cleanup()