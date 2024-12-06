from ultralytics import YOLO
import cv2
import os

def visualize_predictions(image_path, model, class_names):
    # Load the image
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Run inference
    results = model(image_rgb)

    # Get predicted boxes, confidences, and class IDs
    predictions = results[0].boxes
    pred_boxes = predictions.xyxy.cpu().numpy()  # Bounding boxes in [x_min, y_min, x_max, y_max]
    pred_scores = predictions.conf.cpu().numpy()  # Confidence scores
    pred_class_ids = predictions.cls.cpu().numpy().astype(int)  # Class IDs    

    # Create copies of the image to draw on
    image_pred = image_rgb.copy()

    # Set font and box thickness
    font_scale = 2.0          # Increased font scale
    font_thickness = 4        # Increased font thickness
    box_thickness = 4         # Increased box thickness
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Draw predicted bounding boxes in red on image_pred
    for box, class_id, score in zip(pred_boxes, pred_class_ids, pred_scores):
        x_min, y_min, x_max, y_max = map(int, box)
        label = f"{class_names[class_id]}: {score:.2f}"
        cv2.rectangle(image_pred, (x_min, y_min), (x_max, y_max), (255, 0, 0), thickness=box_thickness)

        # Adjust text position to stay within image boundaries
        text_y = y_min - 10 if y_min - 10 > 20 else y_min + 30
        cv2.putText(image_pred, label, (x_min, text_y), font, font_scale, (255, 0, 0), thickness=font_thickness)
    cv2.imwrite(os.path.join(os.path.split(os.path.dirname(image_path))[0], 'inference_results', os.path.basename(image_path)), image_pred)
    return os.path.basename(image_path)

def create_folders():
    script_dir = os.path.dirname(__file__)
    models_dir = os.path.split(script_dir)[0]
    backend_dir = os.path.join(os.path.split(models_dir)[0])
    inference_folder = os.path.join(backend_dir, 'data','inference_trash_images', 'inference_results')
    images_folder = os.path.join(backend_dir, 'data','inference_trash_images', 'images')
    os.makedirs(inference_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

def detect_trash_from_image(img_location: str):
    class_names = ['Plastic film', 'Cigarette', 'Clear plastic bottle', 'Plastic bottle cap', 'Drink can']
    script_dir = os.path.dirname(__file__)
    best_name = 'best.pt'
    best_abs_file_path = os.path.join(script_dir, best_name)
    model = YOLO(best_abs_file_path)
    return visualize_predictions(img_location, model, class_names)

if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    models_dir = os.path.split(script_dir)[0]
    backend_dir = os.path.join(os.path.split(models_dir)[0])
    image_name = os.path.join('data','inference_trash_images', 'test_images','310.jpg')
    image_abs_file_path = os.path.join(backend_dir, image_name)
    detect_trash_from_image(image_abs_file_path)