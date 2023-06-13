import requests
import streamlit as st
import uuid
from datetime import date, datetime
import pandas as pd
from pydantic import BaseModel, Field


def date_to_uuid():
    uuid_obj = uuid.uuid5(uuid.NAMESPACE_URL, str(datetime.utcnow()))
    return str(uuid_obj)

def iso_format():
    return datetime.now().isoformat()

def str_to_date(date_string):
    format_string = "%Y-%m-%d"
    datetime_obj = datetime.strptime(date_string, format_string)
    return datetime_obj

from pymongo import MongoClient


try:
    dbcred = st.secrets["dbcred"]
    db1 = st.secrets["db1"]
    pj = st.secrets["pj"]
except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    pj = os.environ["pj"]


@st.cache_resource(ttl=600)
def get_data_at_db_7(pj_):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    collection = db[pj_]
    return collection


def get_all_projects_from_endpoint():
    collection = get_data_at_db_7(pj)
    return list(collection.find({}))

def send_project_to_endpoint(project):
    # endpoint = "http://127.0.0.1:8000/projects"  
    project_data = project.dict()
    # response = requests.post(endpoint, json=project_data)
    collection = get_data_at_db_7(pj)
    
    if id_col := collection.insert_one(
        {
            "_id": iso_format(),
            **project_data
        }
        ):
        return f"Project successfully sent to the endpoint!{id_col.inserted_id}"
    else:
        return "Error sending the project to the endpoint."

def update_project_in_endpoint(project_id, updated_project):
    # endpoint = f"http://127.0.0.1:8000/projects/{project_id}"
    updated_project_data = updated_project.dict()
    # response = requests.put(endpoint, json=updated_project_data)
    collection = get_data_at_db_7(pj)
    
    if collection.update_one({"_id": project_id}, {"$set": updated_project_data}):
        return "Project successfully updated in the endpoint!"
    else:
        return "Error updating the project in the endpoint."

def delete_project_in_endpoint(project_id):
    # endpoint = f"http://127.0.0.1:8000/projects/{project_id}"
    collection = get_data_at_db_7(pj)
    
    if collection.delete_one({"_id": project_id}):
        return "Project successfully deleted in the endpoint!"
    else:
        return "Error deleting the project in the endpoint."

class Project(BaseModel):
    title: str
    start_date: str
    end_date: str
    description: str
    authors: str
    execution_responsibles: str
    monitoring_responsibles: str

def cadastrar_projeto():
    st.header("Cadastro de Projetos")
    
    # Campos do formulário
    titulo = st.text_input("Título do projeto")
    data_inicio = st.date_input("Data de início").isoformat()
    data_fim = st.date_input("Data de fim").isoformat()
    descricao = st.text_area("Descrição do projeto")
    autores = st.text_input("Autores")
    execucao = st.text_input("Responsáveis pela execução")
    acompanhamento = st.text_input("Responsáveis pelo acompanhamento")
    
    # Botão de cadastro
    if st.button("Cadastrar"):
        print(data_fim, data_inicio)

        project = Project(
            title=titulo,
            start_date=data_inicio,
            end_date=data_fim,
            description=descricao, 
            authors=autores,
            execution_responsibles=execucao,
            monitoring_responsibles=acompanhamento
        )
        result = send_project_to_endpoint(project)

        print(result)
        if not "Error" in result:
            st.success("Projeto cadastrado com sucesso!")
            st.balloons()
        else:
            st.error("Erro ao cadastrar o projeto!")

        
        # Limpar os campos do formulário
        # st.experimental_rerun()

def atualizar_projeto():
    st.header("Atualizar Projeto")
    
    # Obter todos os projetos
    projects = get_all_projects_from_endpoint()
    
    # Selecionar projeto para atualizar
    selected_project = st.selectbox("Selecione o projeto:", projects, format_func=lambda project: project["title"])
    
    # Verificar se um projeto foi selecionado
    if selected_project:
        # Campos do formulário com valores atuais do projeto selecionado
        titulo = st.text_input("Título do projeto", selected_project["title"])
        data_inicio = st.date_input("Data de início", value=str_to_date(selected_project["start_date"])).isoformat()
        data_fim = st.date_input("Data de fim", value=str_to_date(selected_project["end_date"])).isoformat()
        descricao = st.text_area("Descrição do projeto", selected_project["description"])
        autores = st.text_input("Autores", selected_project["authors"])
        execucao = st.text_input("Responsáveis pela execução", selected_project["execution_responsibles"])
        acompanhamento = st.text_input("Responsáveis pelo acompanhamento", selected_project["monitoring_responsibles"])
        
        # Botão de atualização
        if st.button("Atualizar"):
            updated_project = Project(
                title=titulo,
                start_date=data_inicio,
                end_date=data_fim,
                description=descricao, 
                authors=autores,
                execution_responsibles=execucao,
                monitoring_responsibles=acompanhamento
            )
            result = update_project_in_endpoint(selected_project["_id"], updated_project)
            if "Error" in result:
                st.error(result)
            else:
                st.success("Projeto atualizado com sucesso!")
    
def apagar_projeto():
    st.header("Apagar Projeto")
    
    # Obter todos os projetos
    projects = get_all_projects_from_endpoint()
    
    # Selecionar projeto para apagar
    selected_project = st.selectbox("Selecione o projeto:", [project['title']+'¨'+str(project["_id"]) for project in projects], key="delete_project")
    
    # Verificar se um projeto foi selecionado
    if selected_project:
        my_id = {project['title']+'¨'+str(project["_id"]): project["_id"] for project in projects}.get(selected_project)
        if st.button("Apagar"):
            result = delete_project_in_endpoint(my_id)
            if "Error" in result:
                st.error(result)
            else:
                st.success("Projeto apagado com sucesso!")
                st.snow()


def filter_valid_projects(projects):
    df = pd.DataFrame(projects)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    today = pd.to_datetime(date.today())  # Convert today to datetime object
    valid_projects = df[(df["start_date"] <= today) & (df["end_date"].dt.date >= today.date())]
    return valid_projects


# Streamlit page to check valid projects for today
def check_valid_projects():
    st.title("Válidos para hoje")
    projects = get_all_projects_from_endpoint()
    if projects:
        valid_projects = filter_valid_projects(projects)
        if not valid_projects.empty:
            st.dataframe(valid_projects, use_container_width=True)
        else:
            st.info("Sem projetos ativos no momento.")
    else:
        st.error("Falha em localizar projetos!")


def check_all():
    st.title("Todos projetos")
    projects = get_all_projects_from_endpoint()
    if projects:
        valid_projects = pd.DataFrame(projects)
        if not valid_projects.empty:
            st.dataframe(valid_projects, use_container_width=True)
        else:
            st.info("Sem projetos ativos no momento.")
    else:
        st.error("Falha em localizar projetos!")



def main(user, logout):
    st.title("GESTÃO DE PROJETOS!")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo sistema de gestão de projetos do CETI!'
    )
    st.button('sair', on_click=logout)
    pages = {
        "01_Listar todos projetos": check_all,
        "02_Listar Projetos em atividade": check_valid_projects,
        "03_Cadastrar Projetos": cadastrar_projeto,
        "04_Atualizar projetos": atualizar_projeto,
        "05_Apagar projetos": apagar_projeto,

    }
    st.subheader("navegação")
    selection = st.radio("Mostrar", list(pages.keys()))
    page = pages[selection]
    page()


from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])