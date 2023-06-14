# import the opencv library
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time


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

def convert_bbox(bbox, original_image_shape, network_input_shape):
    # Find the equivalent bounding box on the original image
    size_ratio = original_image_shape[0] / network_input_shape[1]
    crop_margins = (original_image_shape[1] - size_ratio * network_input_shape[2]) / 2
    ymin, xmin, ymax, xmax = bbox
    xmin = int(crop_margins + xmin * size_ratio * network_input_shape[2])
    xmax = int(crop_margins + xmax * size_ratio * network_input_shape[2])
    ymin = int(ymin * size_ratio * network_input_shape[1])
    ymax = int(ymax * size_ratio * network_input_shape[1])
    return (ymin, xmin, ymax, xmax)



def run(camera, tries=3, debug=False):
    while(tries > 0):
        # Capture the video frame by frame
        # First, skip the buffered image
        success, frame = camera.read()
        # Then, capture a fresh one
        success, frame = camera.read()
        if not success:
            print("Camera could not be read")
            return None

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
        start = time.time()
        detections = detect(interpreter, input_data)
        end = time.time()
        print(f"{end-start:.3f}s inference time")

        # Draw detections
        for det in detections:
            print(f" - detected class {det['class_id']} ({det['class_name']}) with confidence {det['confidence']:.2f}")
            draw_detection(input_reconstructed, det)

        # Show the image with a rectangle surrounding the detected objects 
        cv2.imshow('detections', input_reconstructed)

        # Find the detections of 'cauli' object
        cauli_detections = [det for det in detections if det['class_name'] == 'cauli']
        if len(cauli_detections) > 0 and debug==False:
            # Sort detections by confidence
            cauli_detections.sort(key=lambda x: x['confidence'], reverse=True)
            return convert_bbox(cauli_detections[0]['box'], frame.shape, input_shape)

        tries -= 1
            
        # the 'q' button is set as the
        # quitting button you may use any
        # desired button of your choice
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    # Destroy all the windows
    cv2.destroyAllWindows()

    return None


if __name__ == "__main__":
    cam = cv2.VideoCapture(2)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_FPS, 20)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    assert cam.isOpened()
    run(cam, tries=100, debug=True)