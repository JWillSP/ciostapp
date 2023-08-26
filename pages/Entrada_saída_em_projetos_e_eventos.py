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
    po = st.secrets['po']
    pi = st.secrets["pi"]
    pj = st.secrets["pj"]
except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    colec1 = os.environ["colec1"]
    po = os.environ['po']
    pi = os.environ["pi"]
    pj = os.environ["pj"]


@st.cache_resource(ttl=60)
def get_data_at_db_5(colec):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    stds = list(db[colec].find())
    return stds

@st.cache_resource(ttl=60)
def get_data_at_db_3(ci_, date, pj_id):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    checkin = list(
        db[ci_].find(
            {"data": date, "project_id": pj_id}
        )
    )
    return checkin

@st.cache_resource(ttl=60)
def get_data_at_db_without_date(ci_, matrícula, pj_id):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    checkin = list(
        db[ci_].find(
            {"matrícula": matrícula, "project_id": pj_id}
        )
    )
    return checkin

@st.cache_resource(ttl=600)
def get_data_at_db_7(food_):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    collection = db[food_]
    return collection

def get_all_projects_from_endpoint():
    collection = get_data_at_db_7(pj)
    return list(collection.find({}))

def get_student_checkin_data(student_id, project_id):
    checkin_df = pd.DataFrame(get_data_at_db_without_date(pi, student_id, project_id))
    print(checkin_df)
    if not checkin_df.empty:
        checkin_df = checkin_df.set_index('matrícula')
        checkin_df = checkin_df.rename(columns={'hora': 'entrada'})
        checkin_df = checkin_df.drop(columns=['_id', 'create_date', 'project_id'])
        checkout_df = pd.DataFrame(get_data_at_db_3(po, '', project_id))
        if not checkout_df.empty:
            checkout_df = checkout_df.set_index('matrícula').rename(columns={'hora': 'saída'})
            checkin_df = checkin_df.join(checkout_df[['saída']], on='matrícula', how='left')
        checkin_df = checkin_df.set_index('data')
        return checkin_df
    return pd.DataFrame()


def check_valid_projects():
    projects = get_all_projects_from_endpoint()
    if not projects:
        st.write("Não há projetos cadastrados no momento.")
        return

    project_options = [project['title']+"_______"+project["_id"] for project in projects]
    selected_project = st.selectbox("Selecione o projeto:", project_options)
    
    st.title("Busca por Estudante")
    all_students = pd.DataFrame(get_data_at_db_5(colec1))
    student_name = st.text_input("Digite o nome do estudante:")
    filtered_students = all_students[all_students['estudante'].str.contains(student_name, case=False)]
    if len(filtered_students) == 1:
        std = filtered_students.iloc[0]
        st.write(f"Estudante encontrado: {std.estudante}")
        st.write(f"Matrícula: {std.matrícula}")
        st.write(f"Turma: {std.turma}")
        st.write(f"Turno: {std.turno}")
        checkin_data = get_student_checkin_data(std.matrícula, selected_project.split("_______")[1])

        st.write("Histórico de Entrada e Saída:")
        if checkin_data.empty:
            st.write("O aluno não realizou check-in no projeto selecionado.")
        else:
            st.write(checkin_data)

def search_by_date():
    st.header("Buscar por Data")
    projects = get_all_projects_from_endpoint()
    if not projects:
        st.write("Não há projetos cadastrados no momento.")
        return

    project_options = [project['title']+"_______"+project["_id"] for project in projects]
    selected_project = st.selectbox("Selecione o projeto:", project_options)
    
    date_input = st.date_input("Selecione a data:")
    selected_date = date_input.strftime("%d-%m-%Y")
    id_project = selected_project.split("_______")[1]
    checkin_df = pd.DataFrame(get_data_at_db_3(pi, selected_date, id_project))
    if checkin_df.empty:
        st.write("Não há registros de entrada ou saída para o projeto e data selecionados.")
    else:
        checkin_df = checkin_df.set_index('matrícula')
        checkin_df = checkin_df.rename(columns={'hora': 'entrada'})
        checkin_df = checkin_df.drop(columns=['_id', 'data', 'create_date', 'project_id'])
        all_students = pd.DataFrame(get_data_at_db_5(colec1))
        all_students = all_students.set_index('matrícula')
        checkin_df['nome'] =  all_students['estudante']
        checkin_df['turma'] = all_students['turma']
        checkin_df['turno'] = all_students['turno']
        checkout_df = pd.DataFrame(get_data_at_db_3(po, selected_date, id_project))
        if not checkout_df.empty:
            checkout_df = checkout_df.set_index('matrícula').rename(columns={'hora': 'saída'})
            checkin_df = checkin_df.join(checkout_df[['saída']], on='matrícula', how='left')
        checkin_df = checkin_df.set_index('nome')
        st.write("Registros de Entrada:")
        st.write(checkin_df)



def main(user, logout):
    st.title("CHECK-IN/OUT PROJETOS DO CETI.!")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo ao RELATÓRIO DE FREQUÊNCIA EM PROJETOS E EVENTOS!'
    )
    st.button('sair', on_click=logout)
    st.subheader("Menu")
    menu_options = ["Buscar por Aluno", "Buscar por Data"]
    selected_menu = st.radio("Selecione uma opção:", menu_options)
    
    if selected_menu == "Buscar por Aluno":
        check_valid_projects()
    elif selected_menu == "Buscar por Data":
        search_by_date()


from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])
