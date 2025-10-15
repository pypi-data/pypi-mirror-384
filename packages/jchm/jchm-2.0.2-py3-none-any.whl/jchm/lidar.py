# jajucha2/lidar


import requests
import base64
import subprocess
import numpy as np
import socket
import struct
import pickle
import re
import numpy as np
import cv2

SERVER_IP = "127.0.0.1"  # 서버 IP 주소
PORT = 12345            # 서버 포트 번호


def get_lidar():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 서버에 연결
        client_socket.connect((SERVER_IP, PORT))

            # 사용자 입력으로 요청 생성
        request = 'request';
        if request == "exit":
            print("Exiting...")
        
        if request == "request":
            # 서버에 요청 전송
            client_socket.sendall(request.encode('utf-8'))

            # 서버로부터 데이터 수신
            data = client_socket.recv(30000)  # 한 번에 최대 4096 바이트 수신
            if not data:
                print("Server disconnected.")

            # Update the regular expression pattern to capture 'Q' as well
            pattern = r'theta:\s*([0-9.]+)\s*Dist:\s*([0-9.]+)\s*Q:\s*(\d+)'

            # Use re.findall to extract all matches at once
            matches = re.findall(pattern, data.decode('utf-8'))

            # Filter out matches where Q is '0'
            filtered_matches = [match for match in matches if match[2] != '0']

            # Convert the filtered matches to NumPy arrays
            theta_array = np.array([float(match[0]) for match in filtered_matches])
            dist_array = np.array([float(match[1]) for match in filtered_matches])

            return theta_array, dist_array
        else:
            print("Invalid input. Type 'request' to fetch data or 'exit' to quit.")

    except KeyboardInterrupt:
        print("\nClient stopped.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # 소켓 닫기
        client_socket.close()

def show_lidar(theta_array,dist_array,max_dist = 5000):
    #convert lidar data to image and send it to server

    #theta_array, dist_array = get_lidar()

        # Convert theta from degrees to radians
    #theta_rad = np.deg2rad(theta_array)
    theta_rad = np.deg2rad(-theta_array)

    # Compute Cartesian coordinates
    x = dist_array * np.cos(theta_rad)
    y = dist_array * np.sin(theta_rad)

    # Since OpenCV's origin is at the top-left corner, and y increases downwards,
    # we need to adjust the coordinates. Also, we need to scale the coordinates
    # to fit within the image size.

    # Define image size
    img_size = 800  # Adjust the image size as needed
    #max_dist = dist_array.max()
    #max_dist= 12000

    # Avoid division by zero if max_dist is zero
    if max_dist == 0:
        max_dist = 1

    # Scale factor to fit the points within the image
    scale = (img_size / 2) / max_dist

    # Shift and scale the coordinates to the center of the image
    x_img = (x * scale + img_size / 2).astype(np.int32)
    # y_img = (y * scale + img_size / 2).astype(np.int32)
    y_img = ((-y) * scale + img_size / 2).astype(np.int32)


    # Create a blank image
    image = np.zeros((img_size, img_size, 3), dtype=np.uint8)

    # Draw center position (LiDAR location) as a red dot
    # cv2.circle(image, (img_size // 2, img_size // 2), radius=4, color=(0, 0, 255), thickness=-1)

    # Draw center position (LiDAR location) as a red triangle
    triangle_radius = 10  # 삼각형 크기 조절
    center_x, center_y = img_size // 2, img_size // 2

    # 삼각형의 꼭짓점 세 개 (오른쪽을 향하는 정삼각형)
    triangle_pts = np.array([[
        (center_x + triangle_radius, center_y),  # 오른쪽
        (center_x - triangle_radius, center_y - triangle_radius),  # 왼쪽 위
        (center_x - triangle_radius, center_y + triangle_radius)   # 왼쪽 아래
    ]], dtype=np.int32)

    cv2.fillPoly(image, triangle_pts, color=(0, 0, 255))  # 빨간색 삼각형

    # Ensure the coordinates are within image boundaries
    valid_indices = (x_img >= 0) & (x_img < img_size) & (y_img >= 0) & (y_img < img_size)
    x_img = x_img[valid_indices]
    y_img = y_img[valid_indices]

    # Draw the points
    for xi, yi in zip(x_img, y_img):
        cv2.circle(image, (xi, yi), radius=2, color=(0, 255, 0), thickness=-1)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]

    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    _, buffer = cv2.imencode('.jpg', image, encode_param)
    
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    data = {'image': jpg_as_text}
    #data = {window_name: jpg_as_text}

    url = 'http://121.184.63.113:4000/'+ 'lidar'
    
    response = requests.post(url, json=data)
    if response.status_code != 200:
        print('Failed to send data')

