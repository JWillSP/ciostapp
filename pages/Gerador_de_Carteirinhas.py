# import time
# import jwt
# import time
# import numpy as np
# from cader import normalizador
# import json 
# from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from pymongo import MongoClient

try:
    dbcred = st.secrets["dbcred"]
    db1 = st.secrets["db1"]
    pics = st.secrets["pics"]
    creds = st.secrets["creds"]
    colec1 = st.secrets["colec1"]
    secret_key = st.secrets["secret_key"]

except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    pics = st.secrets["pics"]
    creds = st.secrets["creds"]
    colec1 = os.environ["colec1"]
    secret_key = os.environ["secret_key"]

cluster = MongoClient(dbcred)
db = cluster[db1]


# Defina uma lista para armazenar as tarefas
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
    
@st.cache_data(ttl=3600)
def get_data_at_db():
    collection1 = db[colec1] 
    all_stds = pd.DataFrame(list(collection1.find()))
    return all_stds


picscolection = db[pics] 

df7x = get_data_at_db()

@st.cache_data(ttl=3600)
def get_local():
    collection = db[creds] 
    all_creds = pd.DataFrame(list(collection.find()))
    return all_creds

local = get_local()

df7x['local'] = df7x['matrícula'].apply(lambda x: local.set_index('matrícula')['transporte'].to_dict().get(x, 'SEDE DO MUNICÍPIO'))

def main(user, logout):
    st.title("GERADOR DE CARTEIRINHAS")
    all_students = get_data_at_db()
    mapping_stds = {
            matrícula: ' - '.join((nome, matrícula, turma))  for nome, matrícula, turma in zip(all_students['estudante'], all_students['matrícula'], all_students['turma'])
        }
    all_students['buscador'] = all_students['matrícula'].map(mapping_stds)
    def select_turmas():
        todas_turmas = all_students['turma'].unique().tolist()
        todas_turmas.sort()
        todas_turmas.insert(0, 'TURMAS')
        turma = st.selectbox('Selecione a turma:', todas_turmas)
        if turma == 'TURMAS':
            return pd.DataFrame()
        estudantes_da_turma = all_students[all_students['turma'] == turma]
        return estudantes_da_turma
    

    def search_student():
        st.markdown("## BUSCAR ESTUDANTE")
        student_name = st.text_input("Digite o nome do estudante, matrícula ou turma:", value='digite aqui')
        filtered_students = all_students[all_students['buscador'].str.contains(student_name, case=False)]
        if len(filtered_students) == 0:
            st.write('')
            return None
        elif len(filtered_students) == 1:
            marcado = st.radio('Estudante encontrado:', filtered_students['buscador'].values.tolist())
            selected_student = all_students[all_students['buscador'] == marcado]
            std = selected_student.iloc[0]
            student_id = std.matrícula
            student_name_db = std.estudante
            return std.buscador, student_name_db, student_id
        elif len(filtered_students) > 15:
            st.write("Muitos resultados, refine sua busca!")
            return None
        else:
            st.write("Estudantes encontrados:")
            marcado = st.radio('marque o aluno correto: ', ['Marque um abaixo!'] + filtered_students['buscador'].values.tolist())

            selected_student = all_students[all_students['buscador'] == marcado]
            try: 
                std = selected_student.iloc[0]
            except IndexError:
                return None
            student_id = std.matrícula
            student_name_db = std.estudante
            return std.buscador, student_name_db, student_id
            
    metodo = st.radio('Selecione o método de busca: ', ['Turma', 'Alunos Avulsos'])
    if metodo == 'Turma':
        st.session_state.tasks = [(aluno.buscador, aluno.estudante, aluno.matrícula) for aluno in select_turmas().itertuples()]

    if metodo == 'Alunos Avulsos':
        if result := search_student():

            col_a, col_b, col_c = st.columns(3)
            if result not in st.session_state.tasks:
                with col_a:
                    if st.button('Adicionar Estudante'):
                        st.session_state.tasks.append(result)
                        st.experimental_rerun()
            if result in st.session_state.tasks:
                with col_b:
                    if st.button('Remover Estudante'):
                        st.session_state.tasks.remove(result)
                        st.experimental_rerun()
            if st.session_state.tasks != []:
                with col_c:
                    if st.button('Remover Todos'):
                        st.session_state.tasks = []
                        st.experimental_rerun()

            # Mostre as tarefas existentes em uma lista
    if st.session_state.tasks:
        st.write('#### Lista de Estudantes para Gerar Carteirinhas:')
        for task in st.session_state.tasks:
            st.write(task[0])
    
        if st.button('Gerar Carteirinhas'):
            from generatemodule import generate
            generate(
                df7x,
                picscolection,
                mysel=[stdz[2] for stdz in st.session_state.tasks],
                secret_key=secret_key
                )
            with open("./results/recorte12.pdf", "rb") as file:
                btn = st.download_button(
                    label="Download do resultado",
                    data=file,
                    file_name="carteirinhas.pdf",
                    mime="application/pdf"
                )   
    else:
        st.write('Adicione estudantes para gerar carteirinhas')

from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])
