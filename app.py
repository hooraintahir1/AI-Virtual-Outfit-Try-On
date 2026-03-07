import cv2
import mediapipe as mp
import streamlit as st
import numpy as np

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

st.title("Virtual Outfit Try-On Demo")

run = st.checkbox('Start Camera')

FRAME_WINDOW = st.image([])

camera = cv2.VideoCapture(0)

while run:
    ret, frame = camera.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS)

    FRAME_WINDOW.image(frame)

camera.release()