import streamlit as st
import cv2
import mediapipe as mp
import numpy as np

st.title("AI Virtual Outfit Try-On Demo")
st.write("Upload an image to detect pose using MediaPipe.")

# File uploader instead of webcam
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(static_image_mode=True)

if uploaded_file:
    # Read the uploaded file as a numpy array
    file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            img,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

    st.image(img, channels="BGR")
