import streamlit as st
import pymongo
import bcrypt

def make_new_user_base_dict():
    st.session_state.newsures =  {
        "username": '',
        "full_name": '',
        "nick": '',
        "email": '',
        "bond1": [],
        "disabled": '',
        'password': '',
        "ch": '',
        "isAdmin": False,
        "isTeacher": True,
        "isEnvAgent": False,
    }

if 'newsures' not in st.session_state:
    make_new_user_base_dict()
    

try:
    dbcred = st.secrets["dbcred"]
    db1 = st.secrets["db1"]
    users = st.secrets["users"]
    colec1 = st.secrets["colec1"]
except FileNotFoundError:
    import os
    dbcred = os.environ['dbcred']
    db1 = os.environ["db1"]
    users = os.environ["users"]
    colec1 = os.environ["colec1"]



client = pymongo.MongoClient(dbcred)  # Altere a string de conexão conforme necessário
db = client[db1]  # Altere para o nome do seu banco de dados
collection = db[users]


def get_all_ids_from_collection():
    collection = db[users]
    all_ids = list(collection.distinct("_id"))
    return all_ids

def get_next_id_to_use():
    all_ids = get_all_ids_from_collection()
    return max(all_ids) + 1

def get_all_usernames_from_collection():
    collection = db[users]
    all_usernames = list(collection.distinct("username"))
    return all_usernames

def register_user(data):
    try:
        collection.insert_one(data)
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro ao registrar o usuário: {e}")
        return False

def main(full_name, logout):
    if st.button("sair"):
        logout()

    st.title("Cadastro de Usuário")
    if type(st.session_state.newsures) != dict:
        make_new_user_base_dict()
        st.experimental_rerun()

    st.session_state.newsures['username'] = st.text_input("Nome de usuário", st.session_state.newsures['username'])
    st.session_state.newsures['full_name'] = st.text_input("Nome completo", st.session_state.newsures['full_name'])
    st.session_state.newsures['nick'] = st.text_input("Apelido", st.session_state.newsures['nick'])
    st.session_state.newsures['email'] = st.text_input("E-mail", st.session_state.newsures['email'])
    st.session_state.newsures['bond1'] = st.text_area("Vínculos (separados por vírgula)", ','.join(st.session_state.newsures['bond1'])).split(",")
    st.session_state.newsures['disabled'] = st.checkbox("Desabilitado", st.session_state.newsures['disabled'])
    st.session_state.newsures['password'] = st.text_input("Senha", type="password", value=st.session_state.newsures['password'])
    st.session_state.newsures['ch'] = st.text_input("CH", st.session_state.newsures['ch'])
    st.session_state.newsures['isAdmin'] = st.checkbox("É admin?", st.session_state.newsures['isAdmin'])
    st.session_state.newsures['isTeacher'] = st.checkbox("É professor?", st.session_state.newsures['isTeacher'])
    st.session_state.newsures['isEnvAgent'] = st.checkbox("É agente de pátio?", st.session_state.newsures['isEnvAgent'])

    if st.button('limpar formulário', type='primary'):
        make_new_user_base_dict()
        st.experimental_rerun()

    if st.button("Registrar"):
        if st.session_state.newsures['username'] in get_all_usernames_from_collection():
            st.error("O usuário já existe!")
            st.stop()
        
        hashed_password = bcrypt.hashpw(st.session_state.newsures['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = {
            "_id": get_next_id_to_use(),
            "username": st.session_state.newsures['username'],
            "full_name": st.session_state.newsures['full_name'],
            "nick": st.session_state.newsures['nick'],
            "email": st.session_state.newsures['email'],
            "bond1": st.session_state.newsures['bond1'],
            "disabled": st.session_state.newsures['disabled'],
            "hashed_password": hashed_password,
            "ch": st.session_state.newsures['ch'],
            "isAdmin": st.session_state.newsures['isAdmin'],
            "isTeacher": st.session_state.newsures['isTeacher'],
            "isEnvAgent": st.session_state.newsures['isEnvAgent'],
        }
        
        if register_user(user_data):
            st.success("Usuário registrado com sucesso!")
            if st.button("limpar formulário"):
                st.session_state.newsures = {}
                st.session_state.newsures =  {
                    "username": '',
                    "full_name": '',
                    "nick": '',
                    "email": '',
                    "bond1": [],
                    "disabled": '',
                    'password': '',
                    "ch": '',
                    "isAdmin": False,
                    "isTeacher": True,
                    "isEnvAgent": False,
                }
                st.experimental_rerun()

from myecm import logador
logador(external_fucntion=main, permitions=['isSuperUser'])