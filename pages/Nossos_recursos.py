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
    ob = st.secrets["ob"]
except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    ob = os.environ["ob"]


@st.cache_resource(ttl=600)
def get_data_at_db_7(pj_):
    cluster = MongoClient(dbcred)
    db = cluster[db1]
    collection = db[pj_]
    return collection


def get_all_projects_from_endpoint():
    collection = get_data_at_db_7(ob)
    return list(collection.find({}))

def send_project_to_endpoint(project):
    # endpoint = "http://127.0.0.1:8000/projects"  
    project_data = project.dict()
    # response = requests.post(endpoint, json=project_data)
    collection = get_data_at_db_7(ob)
    
    if id_col := collection.insert_one(
        {
            "_id": iso_format(),
            **project_data
        }
        ):
        return f"objeto successfully sent to the endpoint!{id_col.inserted_id}"
    else:
        return "Error sending the objeto to the endpoint."

def update_project_in_endpoint(project_id, updated_project):
    # endpoint = f"http://127.0.0.1:8000/projects/{project_id}"
    updated_project_data = updated_project.dict()
    # response = requests.put(endpoint, json=updated_project_data)
    collection = get_data_at_db_7(ob)
    
    if collection.update_one({"_id": project_id}, {"$set": updated_project_data}):
        return "Objeto successfully updated in the endpoint!"
    else:
        return "Error updating the objeto in the endpoint."

def delete_project_in_endpoint(project_id):
    # endpoint = f"http://127.0.0.1:8000/projects/{project_id}"
    collection = get_data_at_db_7(ob)
    
    if collection.delete_one({"_id": project_id}):
        return "Objeto successfully deleted in the endpoint!"
    else:
        return "Objeto deleting the project in the endpoint."

class Project(BaseModel):
    nome: str
    descrição: str
    estado: str 



def cadastrar_projeto():
    st.header("Cadastro de objetos")
    
    # Campos do formulário
    nome = st.text_input("Nome do objeto")
    descrição = st.text_area("descrição do objeto")
    estado = st.text_input("Estado do objeto")
    
    # Botão de cadastro
    if st.button("Cadastrar"):

        project = Project(
            nome=nome,
            descrição=descrição, 
            estado=estado,
        )
        result = send_project_to_endpoint(project)

        print(result)
        if not "Error" in result:
            st.success("Objeto cadastrado com sucesso!")
            st.balloons()
        else:
            st.error("Erro ao cadastrar o objeto!")

        
        # Limpar os campos do formulário
        # st.experimental_rerun()

def atualizar_projeto():
    st.header("Atualizar objeto")
    
    # Obter todos os objetos
    projects = get_all_projects_from_endpoint()
    
    # Selecionar objeto para atualizar
    selected_objects = st.selectbox("Selecione o objeto:", projects, format_func=lambda project: project["title"])
    
    # Verificar se um objeto foi selecionado
    if selected_objects:
        # Campos do formulário com valores atuais do objeto selecionado
        nome = st.text_input("Título do objeto", selected_objects["nome"])
        descrição = st.text_area("Descrição do objeto", selected_objects["descrição"])
        estado = st.text_input("Estado", selected_objects["estado"])
        
        # Botão de atualização
        if st.button("Atualizar"):
            updated_project = Project(
                nome=nome,
                descrição=descrição, 
                estado=estado,
            )
            result = update_project_in_endpoint(selected_objects["_id"], updated_project)
            if "Error" in result:
                st.error(result)
            else:
                st.success("Projeto atualizado com sucesso!")
    
def apagar_projeto():
    st.header("Apagar objeto da listagem no banco de dados")
    
    # Obter todos os objetos
    projects = get_all_projects_from_endpoint()
    
    # Selecionar objeto para apagar
    selected_objects = st.selectbox("Selecione o objeto:", [project['nome']+'¨'+str(project["_id"]) for project in projects], key="delete_project")
    
    # Verificar se um objeto foi selecionado
    if selected_objects:
        my_id = {project['nome']+'¨'+str(project["_id"]): project["_id"] for project in projects}.get(selected_objects)
        if st.button("Apagar"):
            result = delete_project_in_endpoint(my_id)
            if "Error" in result:
                st.error(result)
            else:
                st.success("Obejeto apagado com sucesso!")
                st.snow()


# def filter_valid_projects(projects):
#     df = pd.DataFrame(projects)
#     df["start_date"] = pd.to_datetime(df["start_date"])
#     df["end_date"] = pd.to_datetime(df["end_date"])
#     today = pd.to_datetime(date.today())  # Convert today to datetime object
#     valid_projects = df[(df["start_date"] <= today) & (df["end_date"].dt.date >= today.date())]
#     return valid_projects


# Streamlit page to check valid projects for today
# def check_valid_projects():
#     st.title("Válidos para hoje")
#     projects = get_all_projects_from_endpoint()
#     if projects:
#         valid_projects = filter_valid_projects(projects)
#         if not valid_projects.empty:
#             st.dataframe(valid_projects, use_container_width=True)
#         else:
#             st.info("Sem objetos ativos no momento.")
#     else:
#         st.error("Falha em localizar objetos!")


def check_all():
    st.title("Todos objetos")
    projects = get_all_projects_from_endpoint()
    if projects:
        valid_projects = pd.DataFrame(projects)
        if not valid_projects.empty:
            st.dataframe(valid_projects, use_container_width=True)
        else:
            st.info("Sem objetos cadastrados.")
    else:
        st.error("Falha em localizar objetos!")



def main(user, logout):
    st.title("GESTÃO DE OBJETOS!")
    full_name = user
    st.markdown(
        f'### {full_name}, bem vindo sistema de gestão de objetos do CETI!'
    )
    st.button('sair', on_click=logout)
    pages = {
        "01_Listar todos objetos": check_all,
        # "02_Listar Projetos em atividade": check_valid_projects,
        "03_Cadastrar objeto": cadastrar_projeto,
        "04_Atualizar objeto": atualizar_projeto,
        "05_Apagar objeto": apagar_projeto,

    }
    st.subheader("navegação")
    selection = st.radio("Mostrar", list(pages.keys()))
    page = pages[selection]
    page()


from myecm import logador
logador(external_fucntion=main, permitions=['isAdmin'])