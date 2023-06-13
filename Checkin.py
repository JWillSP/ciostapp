import streamlit as st
import requests
import pandas as pd
from datetime import date
from datetime import datetime
import pytz

def get_date_and_time():
    tz = pytz.timezone('America/Sao_Paulo')
    date = datetime.now(tz)
    formatted_date = date.strftime('%d-%m-%Y')
    time_string = date.strftime('%H:%M:%S')
    print(formatted_date, time_string)
    return formatted_date, time_string


import time
# import requests
from pymongo import MongoClient
import pandas as pd


try:
    dbcred = st.secrets["dbcred"]
    db1 = st.secrets["db1"]
    colec1 = st.secrets["colec1"]
    co = st.secrets['co']
    ci = st.secrets["ci"]
except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    colec1 = os.environ["colec1"]
    co = os.environ['co']
    ci = os.environ["ci"]


@st.cache_resource(ttl=60)
def get_data_at_db_5(colec):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    stds = list(db[colec].find())
    return stds

@st.cache_resource(ttl=60)
def get_data_at_db_3(ci_, date):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    checkin = list(db[ci_].find({"data": date}))
    return checkin


@st.cache_resource(ttl=60)
def get_checkin_data(ci_, std_id):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    checkin = list(db[ci_].find({"matrícula": std_id}))
    return checkin

# get_checkout_data
@st.cache_resource(ttl=60)
def get_checkout_data(co_, std_id):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    checkout = list(db[co_].find({"matrícula": std_id}))
    return checkout

def check_valid_projects():
    st.title("Entrada e Saída no dia de hoje")
    checkin_df  = pd.DataFrame(get_data_at_db_3(ci, get_date_and_time()[0]))
    try:
        checkin_df = checkin_df.set_index('matrícula')
        checkin_df = checkin_df.rename(columns={'hora': 'entrada'})
        checkin_df = checkin_df.drop(columns=['_id', 'data', 'create_date'])
        all_students = pd.DataFrame(get_data_at_db_5(colec1))
        all_students = all_students.set_index('matrícula')
        checkin_df['nome'] =  all_students['estudante']
        checkin_df['turma'] = all_students['turma']
        checkin_df['turno'] = all_students['turno']
        checkout_df = pd.DataFrame(get_data_at_db_3(co, get_date_and_time()[0]))
        if not checkout_df.empty:
            checkout_df = checkout_df.set_index('matrícula')
            checkin_df['saída'] = checkout_df['hora']
        print(checkin_df)
        checkin_df = checkin_df.set_index('nome')
        if not checkin_df.empty:
            st.dataframe(checkin_df, use_container_width=True)
        else:
            st.error("Falha em localizar entradas e saídas!")
    except KeyError:
        st.error("Falha em localizar entradas e saídas!")


def check_all():
    st.title("Escolha a data")
    datex = st.date_input("Data", value=date.today())
    datexx = datex.strftime('%d-%m-%Y')
    checkin_df  = pd.DataFrame(get_data_at_db_3(ci, datexx))
    try:
        checkin_df = checkin_df.set_index('matrícula')
        checkin_df = checkin_df.rename(columns={'hora': 'entrada'})
        checkin_df = checkin_df.drop(columns=['_id', 'data', 'create_date'])
        all_students = pd.DataFrame(get_data_at_db_5(colec1))
        all_students = all_students.set_index('matrícula')
        checkin_df['nome'] =  all_students['estudante']
        checkin_df['turma'] = all_students['turma']
        checkin_df['turno'] = all_students['turno']
        checkout_df = pd.DataFrame(get_data_at_db_3(co, datexx))
        if not checkout_df.empty:
            checkout_df = checkout_df.set_index('matrícula')
            checkin_df['saída'] = checkout_df['hora']
        print(checkin_df)
        checkin_df = checkin_df.set_index('nome')
        if not checkin_df.empty:
            st.dataframe(checkin_df, use_container_width=True)
        else:
            st.error("Falha em localizar entradas e saídas!")
    except KeyError:
        st.error("Falha em localizar entradas e saídas!")


def search_student():
    st.title("Busca por Estudante")
    all_students = pd.DataFrame(get_data_at_db_5(colec1))
    mapping_stds = {
        matrícula: ' - '.join((nome, matrícula, turma))  for nome, matrícula, turma in zip(all_students['estudante'], all_students['matrícula'], all_students['turma'])
    }
    all_students['buscardor'] = all_students['matrícula'].map(mapping_stds)

    student_name = st.text_input("Digite o nome do estudante, matrícula ou turma:")
    filtered_students = all_students[all_students['buscardor'].str.contains(student_name, case=False)]
    if len(filtered_students) == 1:
        std = filtered_students.iloc[0]
        st.write(f"Estudante encontrado: {std.estudante}")
        st.write(f"Matrícula: {std.matrícula}")
        st.write(f"Turma: {std.turma}")
        st.write(f"Turno: {std.turno}")

        student_id = std.matrícula
        checkin_df = pd.DataFrame(get_checkin_data(ci, student_id))
        if not checkin_df.empty:
            checkin_df = checkin_df.sort_values('data')
            checkin_df = checkin_df.rename(columns={'hora': 'entrada'})
            checkin_df = checkin_df.drop(columns=['_id', 'create_date', "matrícula"])
            checkout_df = pd.DataFrame(get_checkout_data(co, student_id))
            if not checkout_df.empty:
                checkout_df = checkout_df.set_index('data')
                to_map = {k:v for k,v in zip(checkout_df.index, checkout_df.hora)}
                checkin_df['saída'] = checkin_df['data'].map(to_map)
            print(checkin_df)
            st.dataframe(checkin_df, use_container_width=True)
        else:
            st.warning("Nenhum check-in encontrado para este estudante.")
    elif len(filtered_students) > 1:
        st.warning("Mais de um estudante encontrado. Por favor, especifique a busca.")
        filtered_students = filtered_students.set_index("_id")
        st.dataframe(filtered_students['buscardor'], use_container_width=True)
    else:
        st.warning("Nenhum estudante encontrado com o nome fornecido.")


def main(user, logout):
    st.title("CHECK-IN/OUT CETI")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo ao relatório de entrada e saída de alunos no prédio do CETI!'
    )
    st.button('sair', on_click=logout)
    pages = {
        "Busca por Estudante": search_student,
        "Escolher uma data": check_all,
    }
    st.subheader("Navegação")
    selection = st.radio("Opções", list(pages.keys()))
    page = pages[selection]
    page()


from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])