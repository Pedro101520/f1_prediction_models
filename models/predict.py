import os
import streamlit as st
from google.cloud import storage
from google.oauth2 import service_account
import pickle


class Modelo():
    def __init__(self):
        pass

    def get_storage_client(self):
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return storage.Client()
        
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return storage.Client(
            credentials=credentials,
            project=credentials.project_id
        )


    def previsao_podio(self, df):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clever-axe-457319-g8-833d2d4ab67f.json"

        client = self.get_storage_client()
        bucket = client.bucket("f1-dashboard-pilotos")
        blob1 = bucket.blob("modelos/modelo_com_quali.pkl")
        blob2 = bucket.blob("modelos/encoder_com_quali.pkl")

        blob3 = bucket.blob("modelos/modelo_sem_quali.pkl")
        blob4 = bucket.blob("modelos/encoder_sem_quali.pkl")

        dados1 = blob1.download_as_bytes()
        dados2 = blob2.download_as_bytes()
        dados3 = blob3.download_as_bytes()
        dados4 = blob4.download_as_bytes()

        modelo_quali = pickle.loads(dados1)
        encoder_quali = pickle.loads(dados2)
        modelo = pickle.loads(dados3)
        encoder = pickle.loads(dados4)

        if "q1_atual" in df.columns:
            X_train_transformed = encoder_quali.transform(df)
            probs = modelo_quali.predict_proba(X_train_transformed)[:, 1]

            df_result = df.copy()
            df_result['prob_podio'] = probs
            df_result['predicao'] = modelo_quali.predict(X_train_transformed)

            predict = df_result[['id_piloto_atual', 'prob_podio', 'predicao']].sort_values('prob_podio', ascending=False)
            return predict
        else:
            X_train_transformed = encoder.transform(df)

            probs = modelo.predict_proba(X_train_transformed)[:, 1]

            df_result = df.copy()
            df_result['prob_podio'] = probs
            df_result['predicao'] = modelo.predict(X_train_transformed)

            predict = df_result[['id_piloto_atual', 'prob_podio', 'predicao']].sort_values('prob_podio', ascending=False)
            return predict

