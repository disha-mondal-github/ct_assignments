import streamlit as st
import numpy as np
import joblib

# Load the trained model
model = joblib.load('iris_model.pkl')

# Streamlit App Config
st.set_page_config(page_title="iris flower classifier", page_icon="🌸")
st.title("🌸 iris flower species prediction")
st.markdown("enter the flower features below to predict the species.")

# Input sliders (lowercase names)
sepal_length = st.slider("sepal_length (cm)", 4.0, 8.0, 5.4)
sepal_width = st.slider("sepal_width (cm)", 2.0, 4.5, 3.4)
petal_length = st.slider("petal_length (cm)", 1.0, 7.0, 1.3)
petal_width = st.slider("petal_width (cm)", 0.1, 2.5, 0.2)

# Prediction on button click
if st.button("predict species"):
    input_data = np.array([[sepal_length, sepal_width, petal_length, petal_width]])
    prediction = model.predict(input_data)

    species = ["Iris-setosa", "Iris-versicolor", "Iris-virginica"]
    st.success(f"The predicted species is: **{prediction[0]}** 🌼")

