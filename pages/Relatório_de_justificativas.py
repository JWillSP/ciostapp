import streamlit as st
from month_week_mapping import generate_week_dictionary
import pandas as pd
from datetime import date
from datetime import datetime
import pytz
from dftoexcel import df_to_excel

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
    oc = st.secrets['ju']

except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    colec1 = os.environ["colec1"]
    oc = os.environ['ju']



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
    justies = list(
        db[oc_].find()
    )
    return justies

def show_student_occurrences():
    st.title("Justificativas por Estudante")
    all_stds = pd.DataFrame(get_all_students(colec1))
    justies = pd.DataFrame(get_data_all_occurrences(oc))
    new_all_students = all_stds[all_stds['matrícula'].isin(justies['matrícula'])]
    mapping_stds = {
        matrícula: ' - '.join((nome, matrícula, turma))  for nome, matrícula, turma in zip(new_all_students['estudante'], new_all_students['matrícula'], new_all_students['turma'])
    }
    new_all_students['buscador'] = new_all_students['matrícula'].map(mapping_stds)
    all_students = new_all_students.copy()
    student_name = st.text_input("Digite o nome do estudante, matrícula ou turma:")
    if not student_name:
        return None
    filtered_students = all_students[all_students['buscador'].str.contains(student_name, case=False)]
    if len(filtered_students) == 0:
        st.write("Nenhum estudante encontrado com a matrícula fornecida.")
        return None
    elif len(filtered_students) == 1:
        marcado = st.radio('Estudante encontrado:', filtered_students['buscador'].values.tolist())
        selected_student = all_students[all_students['buscador'] == marcado].iloc[0]
    elif len(filtered_students) > 15:
        st.write("Muitos resultados, refine sua busca!")
        return None
    else:
        st.write("Estudantes encontrados:")
        marcado = st.radio('marque o aluno correto: ', ['Marque um abaixo!'] + filtered_students['buscador'].values.tolist())
        try: 
            selected_student = all_students[all_students['buscador'] == marcado].iloc[0]
        except IndexError:
            return None
    st.write(f"Estudante: {selected_student['estudante']}")
    st.write(f"Matrícula: {selected_student['matrícula']}")
    st.write(f"Turma: {selected_student['turma']}")
    st.write(f"Turno: {selected_student['turno']}")
    student_occurrences = justies[justies['matrícula'] == selected_student['matrícula']]
    student_occurrences['inicio'] = pd.to_datetime(student_occurrences['data_init']).dt.strftime('%d/%m/%Y')
    student_occurrences['fim'] = pd.to_datetime(student_occurrences['data_end']).dt.strftime('%d/%m/%Y')
    student_occurrences['registrado_em'] = pd.to_datetime(student_occurrences['create_date']).dt.strftime('%d/%m/%Y   %H:%M:%S')
    st.write("Lista de Justificativas:")
    student_occurrences = student_occurrences.drop(columns=[
        '_id',
        'serie',
        "matrícula",
        "estudante", 
        "serie",
        "turma",
        "turno",
        'data_init',
        'data_end',
        'create_date',
        'status'
    ])
    student_occurrences = student_occurrences.set_index('registrado_em')
    # replace True for 'Sim' and False for 'Não'
    student_occurrences = student_occurrences.replace({True: "sim", False: "não", "True": "sim", "False": "não"})
    st.dataframe(student_occurrences.T, use_container_width=True)
    df_to_excel(
        student_occurrences, 
        myheader='Justificativas do estudante:',
        subheader=selected_student['estudante']
    )


def show_occurrences_by_date():
    st.title("Justificativas por Data")
    date_input = st.date_input("Selecione a data:")
    selected_date = date_input.strftime("%Y-%m-%d")

    justies = pd.DataFrame(get_data_all_occurrences(oc))
    justies['início'] = pd.to_datetime(justies['data_init'])
    justies['fim'] = pd.to_datetime(justies['data_end'])
    justies['registrado_em'] = pd.to_datetime(justies['create_date'])
    filtered_occurrences = justies[
        (justies['início'].dt.date <= pd.to_datetime(selected_date).date()) &
        (justies['fim'].dt.date >= pd.to_datetime(selected_date).date())
    ]
    
    if len(filtered_occurrences) == 0:
        st.write("Nenhuma justificativa encontrada para a data selecionada.")
    else:
        st.write("Lista de Justificativas:")
        filtered_occurrences["quem e quando"] = filtered_occurrences["estudante"] + " em " + filtered_occurrences["registrado_em"].dt.strftime('%d/%m/%Y   %H:%M:%S')
        filtered_occurrences = filtered_occurrences.drop(columns=['_id', 'serie', "estudante" , 'data_init', 'data_end', 
                'turno', 'status', 'create_date', 'registrado_em' ])
        filtered_occurrences = filtered_occurrences.set_index("quem e quando")
        filtered_occurrences = filtered_occurrences.replace({ "True": 'sim', "False": 'não', True: 'sim', False: 'não'})
        st.dataframe(filtered_occurrences, use_container_width=True)
        df_to_excel(
            filtered_occurrences, 
            myheader='Estudantes justificados na data:',
            subheader=date_input.strftime("%d/%m/%Y")
        )


def show_occurrences_by_week():
    st.title("Justificativas por Semana")
    
    selected_option = st.selectbox("Selecione a semana do ano:", list(month_week_mapping.keys()))
    week_number = month_week_mapping[selected_option]
    
    justies = pd.DataFrame(get_data_all_occurrences(oc))
    justies['date_init'] = pd.to_datetime(justies['data_init'])
    justies['date_end'] = pd.to_datetime(justies['data_end'])
    justies['registrado_em'] = pd.to_datetime(justies['create_date'])

    filtered_occurrences = justies[
        (justies['date_init'].dt.isocalendar().week <= week_number) &
        (justies['date_end'].dt.isocalendar().week >= week_number)
    ]
    
    if len(filtered_occurrences) == 0:
        st.write("Nenhuma justificativa encontrada para a semana selecionada.")
    else:
        st.write("Lista de Justificativas:")
        filtered_occurrences['início'] = filtered_occurrences['date_init'].dt.strftime('%d/%m/%Y')
        filtered_occurrences['fim'] = filtered_occurrences['date_end'].dt.strftime('%d/%m/%Y')
        filtered_occurrences["quem e quando"] = filtered_occurrences["estudante"] + " em " + filtered_occurrences["registrado_em"].dt.strftime('%d/%m/%Y   %H:%M:%S')
        filtered_occurrences = filtered_occurrences.drop(
            columns=[
                '_id', 'serie',  "estudante" , 'data_init', 'data_end', 
                'turno', 'status', 'date_init', 'date_end', 'create_date', 'registrado_em'
        ])
        filtered_occurrences = filtered_occurrences.set_index("quem e quando")
        filtered_occurrences_em_tela = filtered_occurrences.replace({ "True": True, "False": False})
        filtered_occurrences_file = filtered_occurrences.replace({ "True": 'sim', "False": 'não', True: 'sim', False: 'não'})
        st.dataframe(filtered_occurrences_em_tela, use_container_width=True)
        df_to_excel(
            filtered_occurrences_file, 
            myheader='Estudantes justificados na semana:',
            subheader=selected_option
        )

def show_occurrences_by_month():
    st.title("Justificativas por Mês")
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
    
    justies = pd.DataFrame(get_data_all_occurrences(oc))
    justies['início'] = pd.to_datetime(justies['data_init'])
    justies['fim'] = pd.to_datetime(justies['data_end'])
    justies['registrado_em'] = pd.to_datetime(justies['create_date'])
    filtered_occurrences = justies[
        (justies['início'].dt.month <= month_number) &
        (justies['fim'].dt.month >= month_number)
        ]
    
    if len(filtered_occurrences) == 0:
        st.write("Nenhuma justificativa encontrada para o mês selecionado.")
    else:
        st.write("Lista de Justificativas:")
        filtered_occurrences['data'] = filtered_occurrences['registrado_em'].dt.strftime('%d/%m/%Y   %H:%M:%S')
        filtered_occurrences["quem e quando"] = filtered_occurrences["estudante"] + " em " + filtered_occurrences["data"]
        filtered_occurrences['início'] = filtered_occurrences['início'].dt.strftime('%d/%m/%Y')
        filtered_occurrences['fim'] = filtered_occurrences['fim'].dt.strftime('%d/%m/%Y')
        filtered_occurrences = filtered_occurrences.drop(columns=[
            '_id', 'serie', "estudante" , "data",
            'data_init', 'data_end', 
                'turno', 'status',  'registrado_em',
                'create_date'

        ])
        filtered_occurrences = filtered_occurrences.set_index("quem e quando")
        filtered_occurrences = filtered_occurrences.replace({ "True": 'sim', "False": 'não', True: 'sim', False: 'não'})
        st.dataframe(filtered_occurrences, use_container_width=True)
        df_to_excel(
            filtered_occurrences, 
            myheader='Estudantes justificados no mês:',
            subheader=month_name
        )



def main(user, logout):
    st.title("RELATÓRIOS DE JUSTIFICATIVAS")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo ao relatório de justificativas do CETI.!'
    )
    st.button('sair', on_click=logout)
    st.subheader("Menu")
    menu_options = ["Justificativas por Estudante", "Justificativas por Data", "Justificativas por Semana", "Justificativas por Mês"]
    selected_menu = st.radio("Selecione uma opção:", menu_options)
    
    if selected_menu == "Justificativas por Estudante":
        show_student_occurrences()
    elif selected_menu == "Justificativas por Data":
        show_occurrences_by_date()
    elif selected_menu == "Justificativas por Semana":
        show_occurrences_by_week()
    elif selected_menu == "Justificativas por Mês":
        show_occurrences_by_month()


from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])
