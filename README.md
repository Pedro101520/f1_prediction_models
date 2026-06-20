**Dashboard:** https://formula1-analytics-project.streamlit.app

**Repositório do ETL:** https://github.com/Pedro101520/API_ETL_F1

Repositório do dashboard: https://github.com/Pedro101520/F1_Analytics

Estes códigos foram desenvolvidos com o objetivo de prever o pódio da Fórmula 1 através de um método de classificação, utilizando a biblioteca **XGBoost**.

## Tecnologias Utilizadas
- Python
- Flask
- Google Cloud (Storage, Cloud Run, Cloud Scheduler)
- XGBoost
- Pandas
- Docker
- API Jolpica
- API Open-Meteo
- FastF1

## Visão geral da arquitetura

O projeto segue o seguinte fluxo:

```
Acesso das informações salvas pela etapa da API de ETL que fiz (Link está no inicio da documentação)
        ↓
Feature Engineering (sem Data Leakage)
        ↓
Treino dos modelos (XGBClassifier)
        ↓
Modelos salvos (.pkl) no Google Cloud Storage
        ↓
ETL para dados que serão usados exclusivamente no predict do modelo
        ↓
API de predição (Cloud Run + Cloud Scheduler)
        ↓
Dashboard Streamlit
```

## Como funciona

Após realizar o ETL, defini o target como **0** para pilotos que não chegaram ao pódio e **1** para pilotos que chegaram ao pódio. Como o objetivo é prever o pódio, resolvi usar a função `XGBClassifier`, recomendada pela própria documentação do XGBoost para esse tipo de problema.

A API que faz o ETL de clima utiliza o **FastF1** para buscar informações históricas de clima das corridas, que são usadas para montar a base de treino junto com os dados da Jolpica.

Após escolher a função e definir o target, segui as seguintes etapas:

**1. Separação dos dados em treino e teste:**
```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
```

**2. Tratamento de features categóricas, aplicando One Hot Encoder:**
```python
onehotencoder = ColumnTransformer(transformers=[
    ('OneHot', OneHotEncoder(handle_unknown='ignore'), ['id_circuito_atual', 'id_equipe_atual', 'status'])
], remainder='passthrough')
```

**3. Busca de hiperparâmetros com RandomizedSearchCV**, realizando treinamentos cruzados para encontrar os melhores hiperparâmetros dentre os indicados:
```python
param_grid = {
    "max_depth": [3, 4, 5],
    "learning_rate": [0.01, 0.03, 0.05],
    "n_estimators": [300, 500, 700, 1000],
    "scale_pos_weight": [2, 3],
    "subsample": [0.7, 0.8, 0.9],
    "colsample_bytree": [0.6, 0.7, 0.8],
    "min_child_weight": [5, 7, 10],
    "gamma": [0.2, 0.4, 0.6],
    "reg_alpha": [0, 0.1, 0.5],
    "reg_lambda": [1, 1.5, 2],
}

xgb_model = xgb.XGBClassifier(random_state=42)

grid_search = RandomizedSearchCV(xgb_model, param_grid, cv=10, scoring="f1", n_iter=150, n_jobs=-1, verbose=2, random_state=42)
grid_search.fit(X_train_transformed, y_train)

best_xgb = grid_search.best_estimator_

print("Melhores parâmetros:", grid_search.best_params_)
print("Melhor acurácia:", grid_search.best_score_)
```

### Explicando os hiperparâmetros

| Hiperparâmetro | Descrição |
|---|---|
| `max_depth` | Profundidade de cada árvore |
| `learning_rate` | Define o quanto cada árvore contribui para corrigir os erros da anterior |
| `n_estimators` | Quantidade de árvores do modelo |
| `subsample` | Quantidade de dados utilizada no treinamento de cada árvore |
| `colsample_bytree` | Define quantas features são usadas por árvore |
| `scale_pos_weight` | **Destaque especial**: através dele foi possível ajustar o peso das classes desbalanceadas — já que em cada corrida há apenas 3 vagas no pódio contra um número muito maior de pilotos que não chegam lá |
| `gamma` | Define o ganho mínimo que uma divisão precisa ter para ser aceita na árvore |
| `reg_alpha` | Faz com que valores muito pequenos sejam eliminados, levando-os a zero |
| `reg_lambda` | Penaliza valores muito grandes após a criação da árvore, evitando que o modelo exagere |

## Destaques
- Todas as etapas do treinamento foram pensadas para evitar **Data Leakage** (vazamento de dados)
- Foram treinados **2 modelos**: um com informações anteriores à Qualifying e outro com informações posteriores à Qualifying

## Métricas dos modelos

O desempenho do modelo tem um teto natural: corridas de F1 envolvem eventos imprevisíveis a partir de dados pré-corrida (safety car, chuva, falhas mecânicas, estratégia em tempo real), que limitam estruturalmente a acurácia alcançável por qualquer modelo treinado em dados históricos. Os resultados obtidos estão alinhados a esse limite, e não indicam um problema de modelagem a ser corrigido com mais tuning.

- Dados Pré qualifying
<img width="526" height="390" alt="image" src="https://github.com/user-attachments/assets/dfa5edbf-0b75-4fef-a337-8e1ee7f6cff7"/>

- Dados Pós qualifying
<img width="547" height="384" alt="image" src="https://github.com/user-attachments/assets/2d2ffe78-0c44-4d46-86ba-64343e56e55b"/>

## Após o treinamento
- Os modelos treinados foram salvos em `.pkl` em um bucket do Google Cloud Storage
- Um ETL próprio para o modelo busca as informações referentes à rodada que se quer prever, executa o predict e retorna a probabilidade de cada piloto ir ou não ao pódio
- Para manter tudo atualizado automaticamente, criei APIs auxiliares hospedadas no Cloud Run e agendadas via Cloud Scheduler: uma API de ETL para a próxima rodada e uma API de execução dos modelos
- Utilizei Docker para criar a imagem e realizar o deploy da API no Cloud Run
