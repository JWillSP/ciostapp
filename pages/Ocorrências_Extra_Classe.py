import streamlit as st
from month_week_mapping import generate_week_dictionary
import pandas as pd
from datetime import date
from datetime import datetime
import pytz

obj = {
    "matouAula": "Matou aula",
    "postoForaAula": "Foi posto para fora da aula",
    "chegouAtrasado": "Chegou atrasado",
    "atrapalhouOutraSala": "Atrapalhando o andamento de outra sala",
    "outraSala": "Foi achado em outra sala",
    "outroAmbiente": "Foi achado em outro ambiente (quadra, campo etc...)",
    "teveMauEstar": "Teve mau estar",
    "liberado": "Liberado para casa sob consentimento da família",
    "semCarteirinha": "Não trouxe ou recusou mostrar a carteirinha",
    "outrasOcorrencias": "Ocorrências adicionais",  # Note que isso é apenas um placeholder, pois o valor real deve vir da textarea
    "by": "Registrado por"
}


def convert_date(date):
    ndate = date.str.split('.').str[0]
    return pd.to_datetime(ndate, format='%Y-%m-%dT%H:%M:%S')

current_year = date.today().year
month_week_mapping = generate_week_dictionary(current_year)

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
    oc = st.secrets['oc']

except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    colec1 = os.environ["colec1"]
    oc = os.environ['oc']



@st.cache_resource(ttl=60)
def get_all_students(colec):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    stds = list(db[colec].find())
    return stds

@st.cache_resource(ttl=60)
def get_data_all_occurrences(oc_):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    occurrences = list(
        db[oc_].find()
    )
    return occurrences

def show_student_occurrences():
    st.title("Ocorrências por Estudante")
    all_students = pd.DataFrame(get_all_students(colec1))
    occurrences = pd.DataFrame(get_data_all_occurrences(oc))
    print(all_students.head())
    print(occurrences.head())
    new_all_students = all_students[all_students['matrícula'].isin(occurrences['matrícula'])]
    mapping_stds = {
        matrícula: ' - '.join((nome, matrícula, turma))  for nome, matrícula, turma in zip(new_all_students['estudante'], new_all_students['matrícula'], new_all_students['turma'])
    }
    new_all_students['buscador'] = new_all_students['matrícula'].map(mapping_stds)

    student_name = st.text_input("Digite o nome do estudante, matrícula ou turma:")
    filtered_students = new_all_students[new_all_students['buscador'].str.contains(student_name, case=False)]
    if len(filtered_students) == 0:
        st.write("Nenhum estudante encontrado com a matrícula fornecida.")
    elif len(filtered_students) > 1:
        new_all_students = new_all_students.set_index('buscador')
        st.dataframe(new_all_students["_id"], use_container_width=True)
    else:
        selected_student = filtered_students.iloc[0]
        st.write(f"Estudante: {selected_student['estudante']}")
        st.write(f"Matrícula: {selected_student['matrícula']}")
        st.write(f"Turma: {selected_student['turma']}")
        st.write(f"Turno: {selected_student['turno']}")
        student_occurrences = occurrences[occurrences['matrícula'] == selected_student['matrícula']]
        student_occurrences['selectedDate'] = pd.to_datetime(student_occurrences['selectedDate'])
        student_occurrences['data'] = student_occurrences['selectedDate'].dt.strftime('%d/%m/%Y   %H:%M:%S')
        st.write("Lista de Ocorrências:")
        student_occurrences = student_occurrences.drop(columns=[
            '_id',
            'serie',
            'selectedDate',
            "matrícula",
            "estudante", 
            "serie",
            "turma",
            "turno"
        ])
        student_occurrences = student_occurrences.rename(columns=obj)
        student_occurrences = student_occurrences.set_index('data')
        # replace True for 'Sim' and False for 'Não'
        student_occurrences = student_occurrences.replace({True: "sim", False: "-", "True": "sim", "False": "-"})
        st.dataframe(student_occurrences.T, use_container_width=True)


def show_occurrences_by_date():
    st.title("Ocorrências por Data")
    date_input = st.date_input("Selecione a data:")
    selected_date = date_input.strftime("%Y-%m-%d")

    occurrences = pd.DataFrame(get_data_all_occurrences(oc))
    occurrences['selectedDate'] = convert_date(occurrences['selectedDate'])
    filtered_occurrences = occurrences[occurrences['selectedDate'].dt.date == pd.to_datetime(selected_date).date()]
    
    if len(filtered_occurrences) == 0:
        st.write("Nenhuma ocorrência encontrada para a data selecionada.")
    else:
        st.write("Lista de Ocorrências:")
        filtered_occurrences['hora'] = filtered_occurrences['selectedDate'].dt.strftime('%H:%M:%S')
        filtered_occurrences["quem e quando"] = filtered_occurrences["estudante"] + " às " + filtered_occurrences["hora"]
        filtered_occurrences = filtered_occurrences.drop(columns=['_id', 'serie', 'selectedDate', "estudante" , "hora"])
        filtered_occurrences = filtered_occurrences.set_index("quem e quando")
        filtered_occurrences = filtered_occurrences.replace({ "True": True, "False": False})
        filtered_occurrences = filtered_occurrences.rename(columns=obj)
        st.dataframe(filtered_occurrences, use_container_width=True)



def show_occurrences_by_week():
    st.title("Ocorrências por Semana")
    
    selected_option = st.selectbox("Selecione a semana do ano:", list(month_week_mapping.keys()))
    week_number = month_week_mapping[selected_option]
    
    occurrences = pd.DataFrame(get_data_all_occurrences(oc))
    occurrences['selectedDate'] = convert_date(occurrences['selectedDate'])
    filtered_occurrences = occurrences[
        (occurrences['selectedDate'].dt.isocalendar().week == week_number)
    ]
    
    if len(filtered_occurrences) == 0:
        st.write("Nenhuma ocorrência encontrada para a semana selecionada.")
    else:
        st.write("Lista de Ocorrências:")
        filtered_occurrences['data'] = filtered_occurrences['selectedDate'].dt.strftime('%d/%m/%Y   %H:%M:%S')
        filtered_occurrences["quem e quando"] = filtered_occurrences["estudante"] + " em " + filtered_occurrences["data"]
        filtered_occurrences = filtered_occurrences.drop(columns=['_id', 'serie', 'selectedDate', "estudante" , "data"])
        filtered_occurrences = filtered_occurrences.set_index("quem e quando")
        filtered_occurrences = filtered_occurrences.replace({ "True": True, "False": False})
        filtered_occurrences = filtered_occurrences.rename(columns=obj)
        st.dataframe(filtered_occurrences, use_container_width=True)



def show_occurrences_by_month():
    st.title("Ocorrências por Mês")
    dic_month_name_number = { 
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12
    }
    month_name = st.selectbox("Selecione o mês:", list(dic_month_name_number.keys()))
    
    try:
        month_number = dic_month_name_number.get(month_name)
    except ValueError:
        st.write("falha eu escolher o mês")
        return
    
    occurrences = pd.DataFrame(get_data_all_occurrences(oc))
    occurrences['selectedDate'] = convert_date(occurrences['selectedDate'])
    filtered_occurrences = occurrences[occurrences['selectedDate'].dt.month == month_number]
    
    if len(filtered_occurrences) == 0:
        st.write("Nenhuma ocorrência encontrada para o mês selecionado.")
    else:
        st.write("Lista de Ocorrências:")
        filtered_occurrences['data'] = filtered_occurrences['selectedDate'].dt.strftime('%d/%m/%Y   %H:%M:%S')
        filtered_occurrences["quem e quando"] = filtered_occurrences["estudante"] + " em " + filtered_occurrences["data"]
        filtered_occurrences = filtered_occurrences.drop(columns=['_id', 'serie', 'selectedDate', "estudante" , "data"])
        filtered_occurrences = filtered_occurrences.set_index("quem e quando")
        filtered_occurrences = filtered_occurrences.replace({ "True": True, "False": False})
        filtered_occurrences = filtered_occurrences.rename(columns=obj)
        st.dataframe(filtered_occurrences, use_container_width=True)



def main(user, logout):
    st.title("RELATÓRIOS DE OCORRÊNCIAS EXTRA-CLASSE")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo ao relatório de occorrências extra-classe do CETI.!'
    )
    st.button('sair', on_click=logout)
    st.subheader("Menu")
    menu_options = ["Ocorrências por Estudante", "Ocorrências por Data", "Ocorrências por Semana", "Ocorrências por Mês"]
    selected_menu = st.radio("Selecione uma opção:", menu_options)
    
    if selected_menu == "Ocorrências por Estudante":
        show_student_occurrences()
    elif selected_menu == "Ocorrências por Data":
        show_occurrences_by_date()
    elif selected_menu == "Ocorrências por Semana":
        show_occurrences_by_week()
    elif selected_menu == "Ocorrências por Mês":
        show_occurrences_by_month()


from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])
