import pandas as pd
import requests
import time

from datetime import datetime
from flask import jsonify

ANO_ATUAL = datetime.now().year

class Acesso_Inicial:

    def results(self):
        lista_resultados = []
        rodada = 1
        while True:
            try:
                acesso = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{rodada}/results/").json()
                races = acesso["MRData"]["RaceTable"]["Races"]
            except Exception as e:
                return jsonify({
                    "erro": e
                }), 500

            if not races:
                break
            else:
                for race in races:
                    results = race["Results"]
                    circuito = race["Circuit"]["circuitId"]

                    for result in results:
                        lista_resultados.append({
                            "temporada_atual": acesso["MRData"]["RaceTable"]["season"],
                            "rodada_atual": acesso["MRData"]["RaceTable"]["round"],
                            "id_circuito_atual": circuito,
                            "id_piloto_atual": result["Driver"]["driverId"],
                            "id_equipe_atual": result["Constructor"]["constructorId"],
                            "posicao_corrida_anterior": result["positionText"],
                            "posicao_ultima_corrida": result["position"],
                            "target": result["position"],
                            "grid_anterior": result["grid"],
                            "status": result["status"],
                            "pontos_anterior_individual": result["points"]
                        })
                rodada += 1
            time.sleep(1)
                        
        df_inicio = pd.DataFrame(lista_resultados)
        df_inicio = df_inicio.astype({"temporada_atual": int, "rodada_atual": int}).sort_values(by=["temporada_atual", "rodada_atual"], ascending=True)

        return df_inicio