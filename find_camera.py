import cv2

def find_cameras(max_test_index=10):
    for i in range(max_test_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"摄像头索引 {i} 可用")
            cap.release()
        else:
            print(f"摄像头索引 {i} 不可用")

if __name__ == "__main__":
    find_cameras()