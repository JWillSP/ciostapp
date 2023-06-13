import streamlit as st
import time
# import requests
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import pytz

def master(user, logout):
    st.title("MONITORAMENTO DA FILA DO REFEITÓRIO EM TEMPO REAL")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo ao acompanhemento do serviço do restaurante!'
    )
    st.button('sair', on_click=logout)
    selecionado = st.selectbox("Selecione a refeição", ["Selecione aqui", "café da manhã", "Almoço", "Lanche da tarde", "Ceia"])

    if selecionado != "Selecione aqui":
        fk = {
            "café da manhã": "f1",
            "Almoço": "f2",
            "Lanche da tarde": "f3",
            "Ceia": "f4"
        }[selecionado]
        print(fk)
        try:
            dbcred = st.secrets["dbcred"]
            db1 = st.secrets["db1"]
            colec1 = st.secrets["colec1"]
            food = st.secrets[fk]
            ci = st.secrets["ci"]
        except FileNotFoundError:
            import os
            dbcred = os.environ['dbcred']
            db1 = os.environ["db1"]
            colec1 = os.environ["colec1"]
            food = os.environ[fk]
            ci = os.environ["ci"]

        st.title(f"Lista de atendimento: {selecionado.upper()}!")

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
    
        @st.cache_resource(ttl=600)
        def get_data_at_db_3(ci_):
            cluster = MongoClient(dbcred)
            db = cluster[db1]
            checkin = list(db[ci_].find({"data": get_date_and_time()[0]}))
            return checkin
        print(food)
        collection = get_data_at_db_7(food)
        pre_df = get_data_at_db_5(colec1)
        checkin = get_data_at_db_3(ci)


        # @st.cache_data(ttl=600)
        def make__df():
            df = pd.DataFrame(pre_df)
            checkin_df = pd.DataFrame(checkin)
            return df, checkin_df

        df, checkin_df = make__df()



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

        def news_resulsts(form, número_que_vieram):
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
            col1.metric(
                label="Registrados",
                value=f'{len( st.session_state["colec"])} alunos',
                delta=(f'{quanti} alunos' if  quanti else None),
            )
            col2.metric(
                label="Esperados",
                value=f'{número_que_vieram - len( st.session_state["colec"])} alunos',
                delta=(f'-{quanti} alunos' if  quanti else None),
            )
            return st.session_state["colec"]

        def update_foods(ph, número_que_vieram):
            form = ph.container()
            foods = news_resulsts(form, número_que_vieram)
            foodsdf = pd.DataFrame(foods)
            if foodsdf.empty:
                form.warning("Sem novos registros")
                time.sleep(4)
                ph.empty()
                return
            foodsdf = foodsdf.drop(columns=['_id', 'data', 'create_date'])
            foodsdf['nome'] = foodsdf['matrícula'].map(df.set_index('matrícula')['estudante'])
            foodsdf['turma'] = foodsdf['matrícula'].map(df.set_index('matrícula')['turma'])
            foodsdf.sort_values(by=['hora'], ascending=False, inplace=True)
            foodsdf = foodsdf.set_index('nome')
            form.table(foodsdf)
            time.sleep(4)
            ph.empty()


        def main():
            data_lambda = {
                "f1": lambda x: 'INT' in x or 'MAT' in x,
                "f2": lambda x: 'INT' in x,
                "f3": lambda x: 'INT' in x or 'VES' in x,
                "f4": lambda x: 'NOT' in x,
            }
            def for_filter(entrada):
                return data_lambda[fk](entrada)

            try:
                que_vieram = df[df['matrícula'].isin(checkin_df['matrícula'])]
                lista_de_turmas = que_vieram['turma'].unique()
                print(lista_de_turmas)
                new_lista_de_turmas = list(filter(for_filter, lista_de_turmas))
                print(new_lista_de_turmas)
                que_vieram_ = que_vieram[que_vieram['turma'].isin(new_lista_de_turmas)]
                número_que_vieram = len(que_vieram_)
                ph = st.empty()
                while True:
                    update_foods(ph, número_que_vieram)
            except KeyError:
                st.error("Não há registros de checkin para hoje ainda, confira se já entraram no sistema de checkin e depois volte para essa página.")


        if 'ids' in st.session_state and 'colec' in st.session_state:
            main()

from myecm import logador
logador(external_fucntion=master, permitions=['isAdmin'])