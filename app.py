import streamlit as st
from PIL import Image
import numpy as np
import mediapipe as mp

st.title("AI Virtual Outfit Try-On (Cloud-Friendly)")

uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(static_image_mode=True)

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(img)

    results = pose.process(img_array)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            img_array,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
        st.success("Pose detected!")
    else:
        st.warning("No pose detected.")

    st.image(img_array)
