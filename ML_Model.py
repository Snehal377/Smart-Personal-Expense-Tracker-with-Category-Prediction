import mysql.connector
import pandas as pd 
import warnings 
warnings.filterwarnings("ignore")
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from sklearn.metrics import accuracy_score,precision_score,recall_score
import joblib
import os 
import numpy as np
import datetime


# connect to mysql 

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="live_data_project"
)

 # load transaction table into a dataframe

df = pd.read_sql("select * from transactions",conn)

# check the first few rows 
print("sample data :")
print(df.head())


# encode categorical feature 

df["user_id_enc"] =df["user_id"].astype('category').cat.codes
df["product_id_enc"]= df["product_id"].astype('category').cat.codes

# extract features from transaction time

df["transaction_hour"] = pd.to_datetime(df["transaction_time"]).dt.hour
df["transaction_dayofweek"]=pd.to_datetime(df["transaction_time"]).dt.dayofweek

#features for ml

X=df[["quantity","price","transaction_hour","transaction_dayofweek"]]
df["total"] = df["quantity"] * df["price"]
y = df["total"]

print(X.head())
print(y.head())


X=X.fillna(0)
y=y.fillna(0)


#train a sample ML Model

#split data 
X_train,X_test,y_train,y_test =train_test_split(X,y,test_size=0.2,random_state=42)

# train model

model = LinearRegression()
model.fit(X_train,y_train)

#predict 

y_pred =model.predict(X_test)

#evaluate 
print("\nModel performance")
print("Mean Squared Error :",mean_squared_error(y_test,y_pred))
print("mean absolute error :",mean_absolute_error(y_test,y_pred))
print("R2 Score :",r2_score(y_test,y_pred))
print("\n Model trained successfully")

#  SAVE MODEL 

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "data", "transaction_model.pkl")

joblib.dump(model, MODEL_PATH)

print("Model saved at:", MODEL_PATH)

# Get last transaction hour and day for reference
last_txn_time = df["transaction_time"].max()

# Prepare forecast dataframe for next 7 days (daily)
forecast_dates = [last_txn_time + pd.Timedelta(days=i) for i in range(1, 8)]
forecast_data = []

for dt in forecast_dates:
    quantity = 1  # assume default
    price = df["price"].mean()  # average transaction
    hour = dt.hour
    dayofweek = dt.weekday()
    
    X_forecast = pd.DataFrame([[quantity, price, hour, dayofweek]],
                              columns=["quantity","price","transaction_hour","transaction_dayofweek"])
    predicted_total = round(float(model.predict(X_forecast)[0]), 2)
    
    forecast_data.append({"date": dt.date(), "predicted_total": predicted_total})

forecast_df = pd.DataFrame(forecast_data)
