import pandas as pd
import streamlit as st
from pymongo import MongoClient
from PIL import Image
import base64
import io
from contatos_dos_esdudantes import get_image

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

def get_all_have_pic():
    collection = db[pics]
    all_have_pic = collection.distinct('_id')
    return all_have_pic


def fetch_image(matrícula: str) -> Image.Image:
    col_pix = db[pics]
    std_pic = col_pix.find_one({'_id': matrícula})
    if std_pic:
        return std_pic['pic']
    else:
        return None

def upload_pic_and_thumb(rm, pic, thumb):
    pic_ = pic[pic.find(',') + 1:]
    thumb_ = thumb[thumb.find(',') + 1:]
    dic_ = {
        "_id": rm,
        "pic": pic_,
        "thumb": thumb_,
        "ext": "jpg",
        "extthumb": "jpg"
    }
    collection = db[pics]
    update_result = collection.update_one(
        {
            "_id": rm
        },
        {
            "$set": dic_
        },
        upsert=True
    )

    if update_result.upserted_id:
        return f"Fotos enviadas! Com id: {update_result.upserted_id}"
    elif update_result.modified_count:
        return "Fotos atualizadas com sucesso!"
    else:
        return "Erro ao enviar as fotos."


@st.cache_data(ttl=3600)
def get_data_at_db():
    collection1 = db[colec1] 
    all_stds = pd.DataFrame(list(collection1.find()))
    return all_stds


picscolection = db[pics] 


def main(user, logout):
    all_stds = get_data_at_db()
    mapping_stds = {
        matrícula: ' - '.join(
            (nome, matrícula, turma)
        ) 
        for nome, matrícula, turma
        in zip(
            all_stds['estudante'],
            all_stds['matrícula'],
            all_stds['turma']
        )
    }
    all_stds['buscador'] = all_stds['matrícula'].map(mapping_stds)
    # selecionar se vai exibir os estudantes sem fotos ou com fotos
    sem_pic = all_stds[~all_stds['matrícula'].isin(get_all_have_pic())]
    com_pic = all_stds[all_stds['matrícula'].isin(get_all_have_pic())]
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric(label='Estudantes SEM fotos', value=len(sem_pic))
    with col_b:
        st.metric(label='Estudantes COM fotos', value=len(com_pic))
    with col_c:
        st.metric(label='Total de Estudantes', value=len(all_stds))
    st.title("TIRAR FOTOS DOS ESTUDANTES")

    exibir = st.radio('EXIBIR:', ['Estudantes SEM fotos', 'Estudantes COM fotos'])
    if exibir == 'Estudantes SEM fotos':
        all_students = sem_pic
    else:
        all_students = com_pic

    def select_turmas():
        todas_turmas = all_students['turma'].unique().tolist()
        todas_turmas.sort()
        todas_turmas.insert(0, 'TURMAS')
        turma = st.selectbox('Selecione a turma:'.upper(), todas_turmas)
        if turma == 'TURMAS':
            return None
        estudantes_da_turma = all_students[all_students['turma'] == turma]
        marcado = st.radio('Estudante encontrado:', estudantes_da_turma['buscador'].values.tolist())
        selected_student = estudantes_da_turma[estudantes_da_turma['buscador'] == marcado]
        std = selected_student.iloc[0]
        student_id = std.matrícula
        student_name_db = std.estudante
        return std.buscador, student_name_db, student_id

    def search_student():
        student_name = st.text_input("Digite o nome do estudante, matrícula ou turma:".upper(), value='digite aqui')
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
        elif len(filtered_students) > 20:
            st.write("Muitos resultados, refine sua busca!")
            return None
        else:
            st.write("Estudantes encontrados:")
            marcado = st.radio('marque o aluno correto: ', ['Marque alguém!'] + filtered_students['buscador'].values.tolist())

            selected_student = all_students[all_students['buscador'] == marcado]
            try: 
                std = selected_student.iloc[0]
            except IndexError:
                return None
            student_id = std.matrícula
            student_name_db = std.estudante
            return std.buscador, student_name_db, student_id
    st.divider()
    metodo = st.radio('Selecione o método de busca: ', ['Turma', 'Alunos Avulsos'])
    st.divider()
    if metodo == 'Turma':
        result = select_turmas()

    if metodo == 'Alunos Avulsos':
        result = search_student()

    if result:
        received = fetch_image(result[2])
        if received is None:
            st.divider()
            st.write('CADASTRAR FOTO DO ESTUDANTE!')
            try: 
                pic, thumb = get_image(upload_first=True)
            except TypeError:
                return None
            st.write('principal')
            st.markdown(f'<img src="{pic}" />', unsafe_allow_html=True)
            st.success(str(len(f'~<img src="{pic}" />')//1024) + ' KB')
            st.write('miniatura')
            st.markdown(f'<img src="{thumb}" />', unsafe_allow_html=True)
            st.success(str(len(f'~<img src="{thumb}" />')//1024) + ' KB')
            if st.button('Enviar foto para o banco de dados'):
                upload_pic_and_thumb(result[2], pic, thumb)
                st.success('Foto enviada com sucesso!')
        else:
            st.write(result[0])
            st.markdown(f'<img src="data:image/jpg;base64,{received}" />', unsafe_allow_html=True)
            # image_data = base64.b64decode(bytes(received, 'utf-8'))
            # image = Image.open(io.BytesIO(image_data))
            # print(image.size)
            # st.image(image, caption=f'{result[1]} - {result[2]}', width=250)
            st.divider()
            st.write('ATUALIZAR FOTO:')
            try:
                pic, thumb = get_image(upload_first=True)
            except TypeError:
                return None
            st.write('principal')
            st.markdown(f'<img src="{pic}" />', unsafe_allow_html=True)
            st.success(str(len(f'~<img src="{pic}" />')//1024) + ' KB')
            st.write('miniatura')
            st.markdown(f'<img src="{thumb}" />', unsafe_allow_html=True)
            st.success(str(len(f'~<img src="{thumb}" />')//1024) + ' KB')
            if st.button('Enviar foto para o banco de dados'):
                upload_pic_and_thumb(result[2], pic, thumb)
                st.success('Foto enviada com sucesso!')

main(user='user', logout='logout')