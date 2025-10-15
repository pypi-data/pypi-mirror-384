# jajucha2/camera
import requests
import base64
import subprocess
import numpy as np
import socket
import struct
import pickle
import cv2
import time

# window_name 별로 마지막 호출 시간 저장
last_camera_show_call_time = {}

def show_image(frame, window_name='center', quality=80):
    global last_camera_show_call_time

    # 현재 시간 확인
    current_time = time.time()

    # 30Hz 제한 적용 (window_name 별로 따로 관리)
    last_time = last_camera_show_call_time.get(window_name, 0)
    if current_time - last_time < 1 / 30:
        return  # 30Hz 제한으로 실행 스킵

    # 호출 시간 갱신
    last_camera_show_call_time[window_name] = current_time

    # 이미지 인코딩
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buffer = cv2.imencode('.jpg', frame, encode_param)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    data = {'image': jpg_as_text}
    url = 'http://121.184.63.113:4000/' + window_name

    # 이미지 전송
    response = requests.post(url, json=data)
    if response.status_code != 200:
        print('Failed to send data')

def get_depth():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9999))  # Replace 'SERVER_IP' with the actual server IP
        client_socket.sendall(b'depth')

                # Receive the size of the frame
        packed_msg_size = client_socket.recv(struct.calcsize("Q"))
        if not packed_msg_size:
            return  # Server closed connection
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        # Receive the frame data
        data = b""
        while len(data) < msg_size:
            packet = client_socket.recv(4*1024)
            if not packet:
                return
            data += packet

        frame_data = data

        # Deserialize and decode the frame from the byte array
        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)

    except Exception as e:
        print(f"Error during image retrieval: {e}")
        return None
    finally:
        if client_socket:
            client_socket.close()


    #print(frame.shape)
    return frame

    client_socket.close()

def get_image(location='center'):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9999))  # Replace 'SERVER_IP' with the actual server IP

        if(location == 'center'):
            client_socket.sendall(b'center')
        elif(location == 'left'):
            client_socket.sendall(b'left')
        elif(location == 'right'):
            client_socket.sendall(b'right')
        elif(location == 'depth'):
            client_socket.sendall(b'depth')
        elif(location == 'yolo'):
            client_socket.sendall(b'yolo')
        else:
            client_socket.sendall(b'center')

        # Receive the size of the frame
        packed_msg_size = client_socket.recv(struct.calcsize("Q"))
        if not packed_msg_size:
            return  # Server closed connection
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        # Receive the frame data
        data = b""
        while len(data) < msg_size:
            packet = client_socket.recv(4*1024)
            if not packet:
                return
            data += packet

        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)

    except Exception as e:
        print(f"Error during image retrieval: {e}")
        return None
    finally:
        if client_socket:
            client_socket.close()

    return frame

def canny(img,par1=200,par2=400):
    l = cv2.cvtColor(img,cv2.COLOR_BGR2HLS)[:, :, 1]
    blur = cv2.bilateralFilter(l, 7, 10, 20)
    edge = cv2.Canny(blur, par1, par2)
    return edge

def drawGrid(img2, v_bounds, u_bounds, u_max, v_max, c_v, c_u, v_line_color,h_line_color):
    #cv2.line(img2, (c_u, max(c_v - 50, 0)), (c_u, v_max), (0, 0, 255), 2)
    for v_bound in v_bounds:
        cv2.line(img2, (0, v_bound), (u_max, v_bound), h_line_color, 2)
    for u_bound in u_bounds:
        cv2.line(img2, (u_bound, c_v), (u_bound, v_max), v_line_color, 2)
    return img2

def findGrid(img, img2, cols, rows,v_max,u_max, ths1,ths2, v_line_color, h_line_color , v_point_color, u_point_color,y_max):
    V, L, R = [], [], []
    edge = canny(img, ths1, ths2)
    c_v, c_u = v_max // 2, u_max // 2 # Center points of the image
    c_v = 400 - y_max
    # Calculate row and column bounds based on image dimensions
    v_bounds = [int(c_v + (v_max - c_v) * i / (rows + 1)) for i in range(1, rows + 1)]
    u_bounds = [int(u_max * i / (cols + 1)) for i in range(1, cols + 1)]
    
    # Draw grid lines on the image
    img2 = drawGrid(img2, v_bounds, u_bounds, u_max, v_max, c_v, c_u, v_line_color,h_line_color)
    
    for u_bound in u_bounds:
        vertical_slice = edge[:, u_bound]
        y, = np.nonzero(vertical_slice)
        y = y[y >= c_v]
        if len(y):
            y_max = np.max(y)
            V.append(v_max - y_max)
            cv2.circle(img2, (u_bound, y_max), 5, v_point_color, -1)
        else:
            V.append(v_max - c_v + 1)

    for v_bound in v_bounds:
        horizontal_slice = edge[v_bound, :]
        x, = np.nonzero(horizontal_slice)
        
        left = x[x <= c_u]
        if len(left):
            left_max = np.max(left)
            L.append(c_u - left_max)
            cv2.circle(img2, (left_max, v_bound), 5, u_point_color, -1)
        else:
            L.append(c_u + 1)
        
        right = x[x >= c_u]
        if len(right):
            right_min = np.min(right)
            R.append(right_min - c_u)
            cv2.circle(img2, (right_min, v_bound), 5, u_point_color, -1)
        else:
            R.append(u_max - c_u + 1)

    return (V, L, R), img2

def gridFront(img, cols=7, rows=3 , y_max=200, ths1 = 100, ths2 = 300 , v_line_color=(39, 200, 47), h_line_color=(0, 0, 255),v_point_color=(18, 246, 255), u_point_color=(221, 0, 255)):
    # Calculate the aspect ratio and resize the image based on width = 640
    aspect_ratio = img.shape[1] / img.shape[0]
    new_width = 640
    new_height = int(new_width / aspect_ratio)
    img = cv2.resize(img, (new_width, new_height))

    v_max = img.shape[0]  # Default to image height
    u_max = img.shape[1]  # Default to image width

    if(y_max <= 0):
        y_max = 1
    if(y_max >= 400):
        y_max = 399
        
    # Process the resized image
    points, img2 = findGrid(img, img, cols, rows,v_max,u_max,ths1,ths2,v_line_color, h_line_color,v_point_color, u_point_color,y_max)
    return points, img2
