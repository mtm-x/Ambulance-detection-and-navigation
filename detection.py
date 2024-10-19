import cv2
import torch
import numpy as np
import time
import queue
import threading
import paramiko

device = torch.device('cpu')


model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt', device=device)
model.conf = 0.80 #confidential probability
model.iou = 0.45   

ip_cam_url = "http://192.168.x.x:port/video" #Use Droid cam


frame_queue = queue.Queue(maxsize=2)
display_frame_queue = queue.Queue(maxsize=2)


stop_event = threading.Event()
FRAME_SKIP = 2
TARGET_WIDTH = 640
TARGET_HEIGHT = 480
# Raspberry Pi SSH connection info
RASPBERRY_PI_IP = ""  # Replace with your Raspberry Pi's IP address
USERNAME = ""              # Replace with your Raspberry Pi's username
PASSWORD = ""                    # Replace with your Raspberry Pi's password
REMOTE_SCRIPT_PATH = "/home/rasukutty/run_script.py"  # Replace with your script path on the Raspberry Pi
SCRIPT_PATH = "/home/rasukutty/run_script.py"
RUNNING_SCRIPT = "run.py"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(RASPBERRY_PI_IP, username=USERNAME, password=PASSWORD)

def send_command_to_raspberry_pi():
    """Send a command to the Raspberry Pi to run a Python script."""
    try:
        # Command to run the script on Raspberry Pi
        command = f"python3 {REMOTE_SCRIPT_PATH}"
        
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(command)
        print("Script executed on Raspberry Pi.")
        
        # Optionally print the output
        output = stdout.read().decode()
        error = stderr.read().decode()
        print(f"Output: {output}")
        print(f"Error: {error}")
        
    except Exception as e:
        print(f"Failed to send command to Raspberry Pi: {e}")

# Timer for detection
last_detected_time = None
detection_duration_threshold = 2 # Time in seconds

def capture_frames(cap):
    frame_count = 0
    while not stop_event.is_set():
        ret, frame = cap.read()
        if ret:
            frame_count += 1
            if frame_count % FRAME_SKIP == 0:
                frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))
                if frame_queue.full():
                    frame_queue.get()
                frame_queue.put(frame)
        else:
            print("Failed to get frame from camera. Retrying...")
            time.sleep(0.1)

def detect_ambulance(frame):
    global last_detected_time
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Perform detection
    results = model(rgb_frame, size=TARGET_WIDTH)
    
    # Process results
    detected_now = False
    for det in results.xyxy[0]:  # det is (x1, y1, x2, y2, conf, cls)
        class_id = int(det[5])
        confidence = float(det[4])
        
        if model.names[class_id] in ['ambulance', 'emergency-vehicle'] and confidence >= 0.80:
            label = f'{model.names[class_id]} {confidence:.2f}'
            color = (0, 255, 0)  # Green for bounding box
            c1, c2 = (int(det[0]), int(det[1])), (int(det[2]), int(det[3]))
            cv2.rectangle(frame, c1, c2, color, 2)
            cv2.putText(frame, label, (c1[0], c1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            # If detected, record the time
            detected_now = True

    # Check detection status
    if detected_now:
        if last_detected_time is None:
            last_detected_time = time.time()  # Start the timer
        else:
            # Check if ambulance is continuously detected for more than the threshold
            elapsed_time = time.time() - last_detected_time
            if elapsed_time >= detection_duration_threshold:
                ambulance_detected = True
                last_detected_time = None  # Reset the timer after detection
                # Create flag file to signal Raspberry Pi
                stdin, stdout, stderr = ssh.exec_command(f"pgrep -f {RUNNING_SCRIPT}")
                pid = stdout.read().decode().strip()
        
                if pid:
            # Send a SIGTERM signal to the process to stop it
                    ssh.exec_command(f"kill -SIGTERM {pid}")
                command1 = f"python3 {SCRIPT_PATH}"
                stdin, stdout, stderr = ssh.exec_command(command1)  

    else:
        # Reset last_detected_time if not detected
        last_detected_time = None


    return frame

def process_frames():
    while not stop_event.is_set():
        if not frame_queue.empty():
            frame = frame_queue.get()
            processed_frame = detect_ambulance(frame)
            if display_frame_queue.full():
                display_frame_queue.get()
            display_frame_queue.put(processed_frame)

def display_frames():
    window_name = 'Ambulance and Emergency Vehicle Detection'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, TARGET_WIDTH, TARGET_HEIGHT)
    
    while not stop_event.is_set():
        if not display_frame_queue.empty():
            frame = display_frame_queue.get()
            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
        else:
            time.sleep(0.001)  # Short sleep to prevent busy-waiting

def main():
    print("Model class names:", model.names)
    print("Starting ambulance and emergency vehicle detection. Press 'q' to quit.")

    cap = cv2.VideoCapture(ip_cam_url)
    
    if not cap.isOpened():
        print("Error: Could not open video stream. Please check your camera URL.")
        return

    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_HEIGHT)

    # Start threads
    threads = [
        threading.Thread(target=capture_frames, args=(cap,)),
        threading.Thread(target=process_frames),
        threading.Thread(target=display_frames)
    ]
    
    for t in threads:
        t.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stop_event.set()
        for t in threads:
            t.join()
        
        cap.release()
        cv2.destroyAllWindows()
        ssh.close()  # Close SSH connection at the end of the program

if __name__ == "__main__":
    main()
