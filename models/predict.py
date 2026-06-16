import os
from google.cloud import storage
from google.oauth2 import service_account
import io
import joblib


class Modelo():
    def __init__(self):
        pass

    def previsao_podio(self, df):

        client = storage.Client()

        bucket = client.bucket("f1-dashboard-pilotos")
        blob1 = bucket.blob("modelos/modelo_com_quali.pkl")
        blob2 = bucket.blob("modelos/encoder_com_quali.pkl")

        blob3 = bucket.blob("modelos/modelo_sem_quali.pkl")
        blob4 = bucket.blob("modelos/encoder_sem_quali.pkl")

        dados1 = blob1.download_as_bytes()
        dados2 = blob2.download_as_bytes()
        dados3 = blob3.download_as_bytes()
        dados4 = blob4.download_as_bytes()

        modelo_quali = joblib.load(io.BytesIO(dados1))
        encoder_quali = joblib.load(io.BytesIO(dados2))
        modelo = joblib.load(io.BytesIO(dados3))
        encoder = joblib.load(io.BytesIO(dados4))

        if "q1_atual" in df.columns:
            X_train_transformed = encoder_quali.transform(df)
            probs = modelo_quali.predict_proba(X_train_transformed)[:, 1]

            df_result = df.copy()
            df_result['prob_podio'] = probs
            df_result['predicao'] = modelo_quali.predict(X_train_transformed)

            predict = df_result[['id_piloto_atual', 'prob_podio', 'predicao']].sort_values('prob_podio', ascending=False)
            predict["quali"] = "True"
            json_dados = predict.to_json(orient='records', indent=4, force_ascii=False)
            blob5 = bucket.blob("previsao.json") 
            blob5.upload_from_string(
                json_dados, 
                content_type="application/json"
            )
        else:
            X_train_transformed = encoder.transform(df)

            probs = modelo.predict_proba(X_train_transformed)[:, 1]

            df_result = df.copy()
            df_result['prob_podio'] = probs
            df_result['predicao'] = modelo.predict(X_train_transformed)

            predict = df_result[['id_piloto_atual', 'prob_podio', 'predicao']].sort_values('prob_podio', ascending=False)
            predict["quali"] = "False"
            json_dados = predict.to_json(orient='records', indent=4, force_ascii=False)
            blob5 = bucket.blob("previsao.json") 
            blob5.upload_from_string(
                json_dados, 
                content_type="application/json"
            )

