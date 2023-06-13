# import the opencv library
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time

# define a video capture object
# cam = cv2.VideoCapture(0)
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cam.set(cv2.CAP_PROP_FPS, 5)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)

MODEL_PATH = "./models/model_fp16.tflite"     # EfficientDet0 (float)

CONFIDENCE_THRESHOLD = 0.50

CLASS_LABELS = ["cauli", "other"]


# Load TFLite model and allocate tensors.
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
# Get input tensor details.
input_details = interpreter.get_input_details()
input_shape = input_details[0]['shape']
input_dtype = input_details[0]['dtype']
print("input shape:", input_shape)
print("input type:", input_dtype)

colors = np.random.uniform(0, 255, size=(len(CLASS_LABELS), 3))
if input_dtype != np.uint8:
    colors = colors / 255.0

running_fps = 0
running_inf_time = 0
iterations = 0


def detect(interpreter, data):
    signature_fn = interpreter.get_signature_runner()

    # Feed the input image to the model
    output = signature_fn(images=data)

    # Get all outputs from the model
    count = int(np.squeeze(output['output_0']))
    scores = np.squeeze(output['output_1'])
    classes = np.squeeze(output['output_2'])
    boxes = np.squeeze(output['output_3'])

    results = []
    for i in range(count):
        if scores[i] >= CONFIDENCE_THRESHOLD:
            result = {
                'box': boxes[i],
                'class_id': int(classes[i]),
                'class_name':  CLASS_LABELS[int(classes[i])],
                'confidence': scores[i]
            }
            results.append(result)
    return results


def draw_detection(image, detection):
    text = f"{detection['class_name']} {detection['confidence']:.2f}"
    color = colors[detection['class_id']]
    ymin, xmin, ymax, xmax = detection['box']
    xmin = int(xmin * image.shape[1])
    xmax = int(xmax * image.shape[1])
    ymin = int(ymin * image.shape[0])
    ymax = int(ymax * image.shape[0])
    start = (xmin, ymin)
    end = (xmax, ymax)
    cv2.rectangle(image, start, end, color, 2)
    cv2.putText(image, text, (start[0], start[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


while(True):
    # Capture the video frame by frame
    # First, skip the buffered image
    success, frame = cam.read()
    # Then, capture a fresh one
    success, frame = cam.read()

    if not success:
        print("Camera could not be read")
        break

    else:
        iterations += 1
        print(f"\niteration {iterations}")
        start = time.time()

        rows, cols, channels = frame.shape

        # Prepare input data
        if input_dtype != np.uint8:
            input_data = cv2.dnn.blobFromImage(image=frame, scalefactor=1/255.0, size=input_shape[1:3], swapRB=True, crop=True)
            input_data = np.transpose(input_data, (0, 2, 3, 1)).astype(input_dtype)
        else:
            input_data = cv2.dnn.blobFromImage(image=frame, scalefactor=1, size=input_shape[1:3], swapRB=True, crop=True)
            input_data = np.transpose(input_data, (0, 2, 3, 1)).astype(np.uint8)

        # Retrieve what input image looks like
        input_reconstructed = cv2.cvtColor(input_data[0], cv2.COLOR_RGB2BGR)

        # Run model on the input data.
        start2 = time.time()
        detections = detect(interpreter, input_data)
        end2 = time.time()

        # Draw detections
        for det in detections:
            print(f" - detected class {det['class_id']} ({det['class_name']}) with confidence {det['confidence']:.2f}")
            draw_detection(input_reconstructed, det)

        # Show the image with a rectangle surrounding the detected objects 
        # cv2.imshow('input', frame)
        cv2.imshow('detections', input_reconstructed)

        # Compute Inference time and FPS
        end = time.time()
        print(f"{end2-start2:.3f}s inference time")
        running_inf_time += end2-start2
        print(f"{running_inf_time/iterations:.3f}s avg inference time")
        fps = 1 / (end - start)
        print(f"{fps:.2f} fps")
        running_fps += fps
        print(f"{running_fps/iterations:.2f} avg fps")

        
    # the 'q' button is set as the
    # quitting button you may use any
    # desired button of your choice
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# After the loop release the cap object
cam.release()
# Destroy all the windows
cv2.destroyAllWindows()