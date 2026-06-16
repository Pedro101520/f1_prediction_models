import pandas as pd
import requests
import time

from datetime import datetime, timezone
from utils.tempo import tempo_para_ms

ANO_ATUAL = datetime.now().year

class Etl():
    def __init__(self):
        self.df_inicio = None
        self.count_abandono = None
        self.proxima_rodada = None
        self.pilotos = None
        self.circuito = None
        self.equipe = None
        self.df_grid = None
        self.df_team = None
        self.df_driver = None
        self.df = None
        self.merge = None

    
    def set_df_inicial(self, df):
        self.df_inicio = df
        self.proxima_rodada = self.df_inicio[(self.df_inicio["temporada_atual"] == ANO_ATUAL)]["rodada_atual"].max()
        self.count_abandono = self.count_abandono = self.df_inicio[(self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["rodada_atual"] <= self.proxima_rodada) & (self.df_inicio["status"] == "Retired") & (self.df_inicio["id_piloto_atual"] == "max_verstappen")]["posicao_corrida_anterior"]
        self.acesso_api()
        self.pilotos = self.df_inicio[(self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["rodada_atual"] == self.proxima_rodada)]["id_piloto_atual"]
        self.equipe = self.df_inicio[(self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["rodada_atual"] == self.proxima_rodada)]["id_equipe_atual"]


    def acesso_api(self):
        try:
            self.circuito = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{self.proxima_rodada + 1}/circuits/").json()["MRData"]["CircuitTable"]["Circuits"][0]["circuitId"]
        except Exception as e:
            raise Exception(f"Erro ao acessar API: {e}")
        

    def results_processados(self):
        grid = []

        try:
            acesso_results = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{self.proxima_rodada}/results/").json()
            results = acesso_results["MRData"]["RaceTable"]["Races"][0]["Results"]
        except Exception as e:
            raise Exception(f"Erro results_processados: {e}")

        for result in results:
            grid_1 = self.df_inicio[(self.df_inicio["rodada_atual"] <= self.proxima_rodada) & (self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["id_piloto_atual"] == result["Driver"]["driverId"])]["grid_anterior"]
            grid_1 = pd.to_numeric(grid_1, errors="coerce").tail(3).sum()

            posicao_1 = self.df_inicio[(self.df_inicio["rodada_atual"] <= self.proxima_rodada) & (self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["id_piloto_atual"] == result["Driver"]["driverId"])]["posicao_ultima_corrida"]
            posicao_1 = pd.to_numeric(posicao_1, errors="coerce").tail(3).sum()
            
            grid.append({
                "temporada_atual": int(acesso_results["MRData"]["RaceTable"]["season"]),
                "rodada_atual": int(acesso_results["MRData"]["RaceTable"]["round"]),
                "id_piloto_atual": result["Driver"]["driverId"],
                "grid_anterior": result["grid"],
                "posicao_ultima_corrida": int(result["position"]),
                "count_abandono": result["positionText"],
                "pontos_anterior_individual": result["points"],
                "media_posicao_ganha_anterior": f"{(grid_1 - posicao_1)/3:.2f}",
                "status": result["status"],
            })

        self.df_grid = pd.DataFrame(grid)
        self.df_grid["media_posicao_ganha_anterior"] = self.df_grid["media_posicao_ganha_anterior"].astype(float)
    
    def results_equipe(self):
        infos_equipe = []

        try:
            acesso_equipe = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{self.proxima_rodada}/constructorstandings/").json()
            teams = acesso_equipe["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"]
        except Exception as e:
            raise Exception(f"Erro: {e}")
        for team in teams:
            infos_equipe.append({
                "temporada_atual": int(acesso_equipe["MRData"]["StandingsTable"]["season"]),
                "rodada_atual": int(acesso_equipe["MRData"]["StandingsTable"]["round"]),
                "id_equipe_atual": team["Constructor"]["constructorId"],
                "posicao_equipe_anterior": team["position"],
                "pontos_equipe_anterior": team["points"],
                "vitorias_equipe_anterior": team["wins"]
            })
        self.df_team = pd.DataFrame(infos_equipe)
    
    def results_piloto(self):
        infos_piloto = []

        try:
            acesso_piloto = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/driverstandings/").json()
            drivers = acesso_piloto["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
        except Exception as e:
            raise Exception(f"Erro piloto: {e}")
        for driver in drivers:
            df_posicao_1 = self.df_inicio[(self.df_inicio["rodada_atual"] <= self.proxima_rodada) & (self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["id_piloto_atual"] == driver["Driver"]["driverId"])]["posicao_ultima_corrida"]
            count_abandono = self.df_inicio[( (self.df_inicio["temporada_atual"] == ANO_ATUAL) & (self.df_inicio["rodada_atual"] <= self.proxima_rodada) & (self.df_inicio["id_piloto_atual"] == driver["Driver"]["driverId"]) ) & ( (self.df_inicio["status"] == 'Retired') | (self.df_inicio["status"] == "Did not start") )]["status"].count()

            infos_piloto.append({
                "temporada_atual": int(acesso_piloto["MRData"]["StandingsTable"]["season"]),
                "rodada_atual": self.proxima_rodada,
                "id_piloto_atual": driver["Driver"]["driverId"],
                "pontos_anterior": driver["points"],
                "posicao_camp_anterior": driver["position"],
                "num_vitorias_anterior": driver["wins"],
                "media_ultimas_3_anterior": f"{pd.to_numeric(df_posicao_1, errors='coerce').tail(3).reset_index(drop=True).mean():.2f}",
                "media_ultimas_5_anterior": f"{pd.to_numeric(df_posicao_1, errors='coerce').tail(5).reset_index(drop=True).mean():.2f}",
                "qtde_abandonos_anterior": count_abandono
            })
        self.df_driver = pd.DataFrame(infos_piloto)
        self.df_driver["media_ultimas_3_anterior"] = self.df_driver["media_ultimas_3_anterior"].astype(float)
        self.df_driver["media_ultimas_5_anterior"] = self.df_driver["media_ultimas_5_anterior"].astype(float)
        self.df_driver["tendencia_desempenho"] = (self.df_driver["media_ultimas_3_anterior"] - self.df_driver["media_ultimas_5_anterior"]).round(2)

    def df_base(self):
        self.df = pd.DataFrame({
            'temporada_atual': ANO_ATUAL,
            'rodada_atual': self.proxima_rodada,
            'id_piloto_atual': self.pilotos,
            "id_circuito_atual": self.circuito,
            'id_equipe_atual': self.equipe,
        })
    
    def merges(self):
        self.results_processados()
        self.results_equipe()
        self.results_piloto()
        self.df_base()
        
        df_merge1 = pd.merge(
            self.df,
            self.df_grid,
            on=["temporada_atual", "rodada_atual", "id_piloto_atual"],
            how="left"
        )

        df_merge2 = pd.merge(
            df_merge1,
            self.df_team,
            on=["temporada_atual", "rodada_atual", "id_equipe_atual"],
            how="left"
        )

        df_merge3 = pd.merge(
            df_merge2,
            self.df_driver,
            on=["temporada_atual", "rodada_atual", "id_piloto_atual"],
            how="left"
        )

        df_merge3.drop(columns=["count_abandono"], inplace=True)
        self.merge = df_merge3
    
    def etl_clima(self):
        self.merges()

        try:
            acesso_circuito = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{self.proxima_rodada+1}/circuits/").json()
            latitude = acesso_circuito["MRData"]["CircuitTable"]["Circuits"][0]["Location"]["lat"]
            longetude = acesso_circuito["MRData"]["CircuitTable"]["Circuits"][0]["Location"]["long"]

            data_corrida = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{self.proxima_rodada+1}/").json()
            hora = data_corrida["MRData"]["RaceTable"]["Races"][0]["time"]
            data = data_corrida["MRData"]["RaceTable"]["Races"][0]["date"]

            acesso_clima = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longetude}&start_date={data}&end_date={data}&hourly=temperature_2m,relative_humidity_2m,precipitation,shortwave_radiation,surface_temperature&timezone=auto").json()
        except Exception as e:
            raise Exception(f"Erro clima: {e}")

        dt = datetime.strptime(f"{data}T{hora}", "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=timezone.utc)
        openmeteo_time = dt.strftime("%Y-%m-%dT%H:%M")

        indice_clima = 0
        hourly = acesso_clima["hourly"]["time"]
        for indice, valor in enumerate(hourly):
            if valor == openmeteo_time:
                indice_clima = indice
                break

        temp_ar_media_api = acesso_clima["hourly"]["temperature_2m"][indice_clima:indice_clima+3]
        temp_pista_media_api = acesso_clima["hourly"]["surface_temperature"][indice_clima:indice_clima+3]
        umidade_media_api = acesso_clima["hourly"]["relative_humidity_2m"][indice_clima:indice_clima+3]
        precipitation_api = acesso_clima["hourly"]["precipitation"][indice_clima:indice_clima+3]

        temp_ar_media = f"{sum(temp_ar_media_api) / len(temp_ar_media_api):.2f}"
        temp_pista_media = f"{sum(temp_pista_media_api) / len(temp_pista_media_api):.1f}"
        umidade_media = f"{sum(umidade_media_api) / len(umidade_media_api):.2f}"
        corrida_molhada = int(sum(precipitation_api) > 0)
        perc_voltas_chuva = f"{len([x for x in precipitation_api if x > 0]) / len(precipitation_api) * 100:.2f}"

        self.merge["temp_ar_media"] = float(temp_ar_media)
        self.merge["temp_pista_media"] = float(temp_pista_media)
        self.merge["umidade_media"] = float(umidade_media)
        self.merge["corrida_molhada"] = corrida_molhada
        self.merge["perc_voltas_chuva"] = float(perc_voltas_chuva)
            
    
    def quali(self):
        self.etl_clima()

        try:
            acesso_results = requests.get(f"https://api.jolpi.ca/ergast/f1/{ANO_ATUAL}/{self.proxima_rodada+1}/qualifying/").json()
            quali_results = acesso_results["MRData"]["RaceTable"]["Races"]
        except Exception as e:
            raise Exception(f"Erro: {e}")

        if not quali_results:
            self.merge["rodada_atual"] = self.proxima_rodada + 1
            return self.merge
        else:
            quali_temp = acesso_results["MRData"]["RaceTable"]["Races"][0]

            quali_results = acesso_results["MRData"]["RaceTable"]["Races"][0]["QualifyingResults"]
            info_quali = []
            
            for quali in quali_results:
                info_quali.append({
                    "posicao_quali_atual": int(quali["position"]),
                    "q1_atual": quali.get("Q1", None),
                    "q2_atual": quali.get("Q2", None),
                    "q3_atual": quali.get("Q3", None),
                    "id_piloto_atual": quali["Driver"]["driverId"],
                    "rodada_atual": self.proxima_rodada,
                    "temporada_atual": int(quali_temp["season"])
                })
            df_quali = pd.DataFrame(info_quali)

            df_quali['q1_atual'] = df_quali['q1_atual'].apply(tempo_para_ms)
            df_quali['q2_atual'] = df_quali['q2_atual'].apply(tempo_para_ms)
            df_quali['q3_atual'] = df_quali['q3_atual'].apply(tempo_para_ms)

            menor_tempo = df_quali["q3_atual"].min()

            q3_rodada = []
            for value_q3 in df_quali['q3_atual']:
                if pd.notna(value_q3) and value_q3 != '':
                    dif = value_q3 - menor_tempo
                    q3_rodada.append(dif)
                else:
                    q3_rodada.append(None)

            df_quali["dif_para_pole_atual"] = q3_rodada 

            self.merge = pd.merge(
                self.merge,
                df_quali,
                on=["temporada_atual", "rodada_atual", "id_piloto_atual"],
                how="left"
            )
            self.merge["rodada_atual"] = self.proxima_rodada + 1
            return self.merge
        
