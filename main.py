import joblib
import pandas as pd

from flask import Flask, make_response, jsonify, request
from models.resultados import Acesso_Inicial
from models.etl_driver import Etl

app = Flask(__name__)

# df = pd.read_csv(r"DATA\analise.csv")
# df.drop(columns=["id_piloto_atual"], inplace=True)

# modelo = joblib.load(r"models\fraud_detection_pipeline.pkl")
# encoder = joblib.load(r"models\encoder_sem_quali.pkl")

# X_train_transformed = encoder.transform(df)
# predicoes = modelo.predict(X_train_transformed)

# print(predicoes)


@app.route("/predicao/formula1", methods=["GET"])
def pipeline():
    resultados = Acesso_Inicial()
    etl = Etl()
    try:
        df_inicial = resultados.results()
        etl.set_df_inicial(df_inicial)
        df = etl.quali()

        df.to_csv(r"DATA\analise.csv", index=False)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


    return jsonify({
        "message": "Modelo treinado com sucesso"
    }), 200


# if __name__ == "__main__":
#     app.run()
app.run()