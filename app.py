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

camera = cv2.VideoCapture(0)

while run:
    ret, frame = camera.read()

    if not ret:
        st.write("Camera not detected")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

    FRAME_WINDOW.image(frame)

camera.release()