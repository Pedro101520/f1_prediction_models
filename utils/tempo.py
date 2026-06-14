import pandas as pd

def tempo_para_ms(tempo_str):
    if pd.isna(tempo_str):
        return None
    try:
        minutos, resto = tempo_str.split(':')
        segundos, ms = resto.split('.')
        return int(minutos) * 60000 + int(segundos) * 1000 + int(ms)
    except:
        return None