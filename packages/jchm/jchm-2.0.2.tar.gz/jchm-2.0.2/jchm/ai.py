import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image as Img
from torch.utils.data import Dataset
import os
import cv2
import numpy as np
from torchsummary import summary

from IPython.display import display, Image
import ipywidgets as widgets
from IPython.display import clear_output
import mysql.connector
from ultralytics import YOLO
import logging

logging.getLogger("ultralytics").setLevel(logging.CRITICAL)

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="1111",
    database="veluna_db"
)

transform = transforms.Compose([
    transforms.Resize(224),         
    transforms.CenterCrop((224, 224)), 
    transforms.ToTensor(),
])

cursor = conn.cursor()
home_dir = os.path.expanduser("~")
device = torch.device('cuda')

#yolo should be added
def get_model(name):
    # Step 1: UserModels에서 uuid, model_id 가져오기
    query = "SELECT uuid, model_id FROM UserModels WHERE name = %s"
    cursor.execute(query, (name,))
    row = cursor.fetchone()
    if not row:
        print("No user model found")
        return None

    uuid, model_id = row

    # Step 2: model_id로 모델 이름 가져오기
    query = "SELECT name FROM Models WHERE id = %s"
    cursor.execute(query, (model_id,))
    model_row = cursor.fetchone()
    if not model_row:
        print("No model found for model_id:", model_id)
        return None

    model_name = model_row[0]

    # Step 3: 모델 로드
    modeldir = home_dir + "/server/usermodels/" + uuid + ".pt"

    loaded_model = None
    if model_name in ['RESNET18', 'RESNET34' , 'RESNET50', 'RESNET101', 'RESNET152']:
        loaded_model = torch.jit.load(modeldir)
        loaded_model.eval()
    elif model_name in ['YOLO8N', 'YOLO9N', 'YOLO10N', 'YOLO11N', 'YOLO8N-SEG', 'YOLO11N-SEG']:
        loaded_model = YOLO(modeldir)

    return loaded_model

# Cache for model UUIDs, shapes, and loaded models
model_cache = {}

def get_model_output(input, name):
    if name not in model_cache:
        # Step 1: UserModels 테이블에서 uuid, model_id 가져오기
        query = "SELECT uuid, model_id FROM UserModels WHERE name = %s"
        cursor.execute(query, (name,))
        row = cursor.fetchone()
        if not row:
            print(f"No user model found for name: {name}")
            return None
        uuid, model_id = row

        # Step 2: model_id로 Models 테이블에서 name, shape 가져오기
        query = "SELECT name, shape FROM Models WHERE id = %s"
        cursor.execute(query, (model_id,))
        model_row = cursor.fetchone()
        if not model_row:
            print(f"No model found for model_id: {model_id}")
            return None
        model_name, shape = model_row

        # Step 3: 모델 파일 경로 및 로드
        modeldir = home_dir + "/server/usermodels/" + uuid + ".pt"

        loaded_model = None
        if model_name in ['RESNET18', 'RESNET34', 'RESNET50', 'RESNET101', 'RESNET152', 'EMPTY']:
            loaded_model = torch.jit.load(modeldir)
            loaded_model.eval()
        elif model_name in ['YOLO8N', 'YOLO9N', 'YOLO10N', 'YOLO11N', 'YOLO8N-SEG', 'YOLO11N-SEG']:
            loaded_model = YOLO(modeldir)

        # Step 4: 캐시에 저장
        model_cache[name] = {
            'modeldir': modeldir,
            'model_name': model_name,
            'shape': shape,
            'model': loaded_model
        }
    else:
        modeldir = model_cache[name]['modeldir']
        model_name = model_cache[name]['model_name']
        shape = model_cache[name]['shape']
        loaded_model = model_cache[name]['model']

    # Step 5: 모델로부터 결과 추론
    if model_name in ['RESNET18', 'RESNET34', 'RESNET50', 'RESNET101', 'RESNET152', 'EMPTY']:
        image = Img.fromarray(cv2.cvtColor(input, cv2.COLOR_BGR2RGB))
        image = transform(image)
        image = image.unsqueeze(0).to(device)
        output = loaded_model(image)
        return output

    elif model_name in ['YOLO8N', 'YOLO9N', 'YOLO10N', 'YOLO11N', 'YOLO8N-SEG', 'YOLO11N-SEG']:
        results = loaded_model(input)
        return results


def get_model_input(name):
    # Step 1: UserModels에서 model_id 가져오기
    query = "SELECT model_id FROM UserModels WHERE name = %s"
    cursor.execute(query, (name,))
    row = cursor.fetchone()
    if not row:
        print(f"No user model found for name: {name}")
        return None

    model_id = row[0]

    # Step 2: model_id로 Models에서 shape 조회
    query = "SELECT shape FROM Models WHERE id = %s"
    cursor.execute(query, (model_id,))
    row = cursor.fetchone()
    if not row:
        print(f"No model found for id: {model_id}")
        return None

    shape = row[0]
    print(shape)
    return shape
