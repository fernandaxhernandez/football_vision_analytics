from roboflow import Roboflow
rf = Roboflow(api_key="zoCOF1u7he2HpkNWpFWl")
project = rf.workspace("roboflow-jvuqo").project("football-players-detection-3zvbc")
version = project.version(1)
dataset = version.download("yolov5")

print("Dataset downloaded in:", dataset.location)
#!yolo task = detect mode = train model = yolov5x.pt data = {dataset.location}/data.yaml epochs = 100 imgsz=640

