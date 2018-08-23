from yolo_model import YOLO_V3
import utils
def test_yolov3_predict():

    y = YOLO_V3(utils.load_json('./config.json'))
    ci = {'0': 0, '1': 1, '10': 2, '11': 3, '12': 4, '13': 5, '14': 6, '15': 7, '16': 8, '2': 9, '3': 10, '4': 11, '5': 12, '6': 13, '7': 14, '8': 15, '9': 16}

    while True:
        y.predict(image_path="./flowers17/test",class_indices=ci)

if __name__ == "__main__":
    test_yolov3_predict()