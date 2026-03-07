import streamlit as st
from PIL import Image
import numpy as np
import mediapipe as mp

st.title("AI Virtual Outfit Try-On Demo")
st.write("Upload an image and see pose detection in action!")

# Upload image
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(static_image_mode=True)

if uploaded_file:
    # Open image
    img = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(img)

    # Process pose
    results = pose.process(img_array)

    # Draw landmarks if pose detected
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            img_array,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
        st.success("Pose detected!")
    else:
        st.warning("No pose detected.")

    # Display the image
    st.image(img_array)
