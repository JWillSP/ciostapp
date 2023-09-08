import streamlit as st
import pymongo
import bcrypt

if 'tasks' not in st.session_state:
    st.session_state.tasks =  {
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
        # "isPorter": isPorter
    }
    

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


# Conexão com o MongoDB
client = pymongo.MongoClient(dbcred)  # Altere a string de conexão conforme necessário
db = client[db1]  # Altere para o nome do seu banco de dados
collection = db[users]


# access all _id's from the collection and convert them to a list to know wich _id is already in use and wich is not e get the next _id to use
def get_all_ids_from_collection():
    collection = db[users]
    all_ids = list(collection.distinct("_id"))
    return all_ids

# get the next _id to use
def get_next_id_to_use():
    all_ids = get_all_ids_from_collection()
    return max(all_ids) + 1

def get_all_usernames_from_collection():
    collection = db[users]
    all_usernames = list(collection.distinct("username"))
    return all_usernames

# Função para registrar usuário no MongoDB
def register_user(data):
    try:
        collection.insert_one(data)
        return True
    except Exception as e:
        st.error(f"Ocorreu um erro ao registrar o usuário: {e}")
        return False

st.title("Cadastro de Usuário")

# Campos do formulário
st.session_state.tasks['username'] = st.text_input("Nome de usuário", st.session_state.tasks['username'])
st.session_state.tasks['full_name'] = st.text_input("Nome completo", st.session_state.tasks['full_name'])
st.session_state.tasks['nick'] = st.text_input("Apelido", st.session_state.tasks['nick'])
st.session_state.tasks['email'] = st.text_input("E-mail", st.session_state.tasks['email'])
st.session_state.tasks['bond1'] = st.text_area("Vínculos (separados por vírgula)", ','.join(st.session_state.tasks['bond1'])).split(",")
st.session_state.tasks['disabled'] = st.checkbox("Desabilitado", st.session_state.tasks['disabled'])
st.session_state.tasks['password'] = st.text_input("Senha", type="password", value=st.session_state.tasks['password'])
st.session_state.tasks['ch'] = st.text_input("CH", st.session_state.tasks['ch'])
st.session_state.tasks['isAdmin'] = st.checkbox("É admin?", st.session_state.tasks['isAdmin'])
st.session_state.tasks['isTeacher'] = st.checkbox("É professor?", st.session_state.tasks['isTeacher'])
st.session_state.tasks['isEnvAgent'] = st.checkbox("É agente de pátio?", st.session_state.tasks['isEnvAgent'])
# isPorter = st.checkbox("É porteiro?", False)

if st.button('limpar formulário', type='primary'):
    st.session_state.tasks = {}
    st.session_state.tasks =  {
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
        # "isPorter": isPorter
    }
    st.experimental_rerun()

# Botão para registrar
if st.button("Registrar"):
    # Verificar se o usuário já existe
    if st.session_state.tasks['username'] in get_all_usernames_from_collection():
        st.error("O usuário já existe!")
        st.stop()
    
    # Criptografar a senha
    hashed_password = bcrypt.hashpw(st.session_state.tasks['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Organizando os dados
    user_data = {
        "_id": get_next_id_to_use(),
        "username": st.session_state.tasks['username'],
        "full_name": st.session_state.tasks['full_name'],
        "nick": st.session_state.tasks['nick'],
        "email": st.session_state.tasks['email'],
        "bond1": st.session_state.tasks['bond1'],
        "disabled": st.session_state.tasks['disabled'],
        "hashed_password": hashed_password,
        "ch": st.session_state.tasks['ch'],
        "isAdmin": st.session_state.tasks['isAdmin'],
        "isTeacher": st.session_state.tasks['isTeacher'],
        "isEnvAgent": st.session_state.tasks['isEnvAgent'],
        # "isPorter": isPorter
    }
    
    # Registrar usuário
    if register_user(user_data):
        st.success("Usuário registrado com sucesso!")
        if st.button("limpar formulário"):
            st.session_state.tasks = {}
            st.session_state.tasks =  {
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
                # "isPorter": isPorter
            }
            st.experimental_rerun()