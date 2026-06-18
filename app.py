import joblib
import pandas as pd
import os

from flask import Flask, jsonify
from models.resultados import Acesso_Inicial
from models.etl_driver import Etl
from models.predict import Modelo

app = Flask(__name__)

@app.route("/predicao/formula1", methods=["POST"])
def pipeline():
    resultados = Acesso_Inicial()
    etl = Etl()
    modelo = Modelo()
    try:
        df_inicial = resultados.results()
        etl.set_df_inicial(df_inicial)
        df = etl.quali()
        modelo.previsao_podio(df)
        df.to_csv(r"D:\pedro\Documents\modelo_f1\DATA\a.csv")
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


    return jsonify({
        "message": "Modelo treinado com sucesso"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)