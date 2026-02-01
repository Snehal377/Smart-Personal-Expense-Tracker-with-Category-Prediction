from fastapi import FastAPI
from pydantic import BaseModel 
import joblib
import numpy as np 
import os

#load trained model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "data", "transaction_model.pkl")

model = joblib.load(MODEL_PATH)

app=FastAPI(title="Transaction Predication API")

#input schema 

class TransactionInput(BaseModel):
    quantity:int
    price:float
    transaction_hour:int
    transaction_dayofweek:int

@app.post("/predict")
def predict_total(data: TransactionInput):
    X=np.array([[
        data.quantity,
        data.price,
        data.transaction_hour,
        data.transaction_dayofweek
    ]])
    Predication=model.predict(X)[0]

    return {
           "predicted_total":round(float(Predication),2)
    }
