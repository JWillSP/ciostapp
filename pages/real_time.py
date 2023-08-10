import streamlit as st
import time
# import requests
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import pytz
import httpx
from PIL import Image
from io import BytesIO

st.set_page_config(layout="centered")

@st.cache_resource(ttl=3600)
def fetch_image(url: str) -> Image.Image:
    with httpx.Client() as client:
        response = client.get(url)
        image_data = BytesIO(response.content)
        img = Image.open(image_data)
        return img

def master(user, logout):
    try:
        dbcred = st.secrets["dbcred"]
        db1 = st.secrets["db1"]
        colec1 = st.secrets["colec1"]
        ci = st.secrets["ci"]
    except FileNotFoundError:
        import os
        dbcred = os.environ['dbcred']
        db1 = os.environ["db1"]
        colec1 = os.environ["colec1"]
        ci = os.environ["ci"]



    def get_date_and_time():
        tz = pytz.timezone('America/Sao_Paulo')
        date = datetime.now(tz)
        formatted_date = date.strftime('%d-%m-%Y')
        time_string = date.strftime('%H:%M:%S')
        print(formatted_date, time_string)
        return formatted_date, time_string

    @st.cache_resource(ttl=600)
    def get_data_at_db_7(food_):
        cluster = MongoClient(dbcred)
        db = cluster[db1]
        collection = db[food_]
        return collection

    @st.cache_resource(ttl=600)
    def get_data_at_db_5(colec):
        cluster = MongoClient(dbcred)
        db = cluster[db1]
        stds = list(db[colec].find())
        return stds

    
    collection = get_data_at_db_7(ci)
    pre_df = get_data_at_db_5(colec1)

    # @st.cache_data(ttl=600)
    def make__df():
        df = pd.DataFrame(pre_df)
        return df

    df = make__df()

    def get_initial_values():
        print("get_initial_values")
        return list(
            collection.find(
                {"data": get_date_and_time()[0]}
            )
        )

    def get_initial_ids():
        print("get_initial_ids")
        return [result['_id'] for result in st.session_state["colec"] ]

    st.session_state["colec"] = get_initial_values()
    st.session_state["ids"] = get_initial_ids()

    def news_resulsts(form):
        latest_results = list(collection.find(
            {
                '_id': {'$nin': st.session_state["ids"]},
                "data": get_date_and_time()[0]
            }
        ))
        quanti = len(latest_results)
        if quanti:
            provisório = [value for value in  (st.session_state["colec"] + latest_results)]
            st.session_state["ids"] = [result['_id'] for result in provisório]
            st.session_state["colec"] = provisório
        col1, col2 = form.columns(2)
        col2.metric(
            label="Registrados",
            value=f'{len( st.session_state["colec"])} alunos',
            delta=(f'{quanti} alunos' if  quanti else None),
        )
        return st.session_state["colec"]

    def update_foods(ph):
        form = ph.container()
        foods = news_resulsts(form)
        foodsdf = pd.DataFrame(foods)
        if foodsdf.empty:
            form.warning("Sem novos registros")
            time.sleep(4)
            ph.empty()
            return
        foodsdf = foodsdf.drop(columns=['_id', 'data', 'create_date'])
        foodsdf['nome'] = foodsdf['matrícula'].map(df.set_index('matrícula')['estudante'])
        foodsdf['turma'] = foodsdf['matrícula'].map(df.set_index('matrícula')['turma'])
        foodsdf['turno'] = foodsdf['matrícula'].map(df.set_index('matrícula')['turno'])
        foodsdf.sort_values(by=['hora'], ascending=True, inplace=True)
        col = form.columns(3)
        for i, row in enumerate(foodsdf.tail(3).itertuples()):
            # form.divider()
            # col = form.columns(2)
            with col[i]:
                form.image(fetch_image(url=f'https://idcio.herokuapp.com/studantdetail/pic/{1124856}/{row.matrícula}'), width=250)
                form.markdown(f'##### {row.nome} - {row.turma} - {row.turno}')
                form.write(' ')

        # foodsdf = foodsdf.set_index('nome')
        # form.table(foodsdf)
        time.sleep(4)
        ph.empty()


    def main():
        try:
            ph = st.empty()
            while True:
                update_foods(ph)
        except KeyError:
            st.error("Não há registros de checkin para hoje ainda, confira se já entraram no sistema de checkin e depois volte para essa página.")


    if 'ids' in st.session_state and 'colec' in st.session_state:
        main()

from myecm import logador
logador(external_fucntion=master, permitions=['isAdmin', 'isTeacher', 'isEnvAgent'])