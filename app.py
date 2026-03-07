import streamlit as st
import cv2
import mediapipe as mp
import numpy as np

st.title("AI Virtual Outfit Try-On Demo")

st.write("This demo shows pose detection using MediaPipe.")

run = st.checkbox("Start Camera")

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose()

FRAME_WINDOW = st.image([])

# Use OpenCV video capture
camera = cv2.VideoCapture(0)

# Loop using while True but break with checkbox
while True:
    if not run:
        break

    ret, frame = camera.read()
    if not ret:
        st.warning("Camera not detected")
        break

    # Convert BGR to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    # Draw pose landmarks if detected
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

    # Show frame in Streamlit
    FRAME_WINDOW.image(frame, channels="BGR")

camera.release()
