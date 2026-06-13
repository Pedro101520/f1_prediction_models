import joblib
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

df = pd.read_csv(r"DATA\analise.csv")
df.drop(columns=["id_piloto_atual"], inplace=True)


modelo = joblib.load(r"models\fraud_detection_pipeline.pkl")
encoder = joblib.load(r"models\encoder_sem_quali.pkl")

X_train_transformed = encoder.transform(df)
predicoes = modelo.predict(X_train_transformed)

print(predicoes)