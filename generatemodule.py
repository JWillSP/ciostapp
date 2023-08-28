dict_turma_alias = {'EJAJ3NOTJ3E6A': 'TJ6A',
 'EJAJ3NOTJ3E6B': 'TJ6B',
 'EJAJ3NOTJ3E6C': 'TJ6C',
 'EJAJ3NOTJ3E7A': 'TJ7A',
 'EMMAT3A': '3A',
 'EMMAT3B': '3B',
 'EMMAT3C': '3C',
 'EMNOT3A': '3A',
 'EMNOT3B': '3B',
 'EMNOT3C': '3C',
 'EMVES3A': '3A',
 'EMVES3B': '3B',
 'NEMMATLCHA': '2A',
 'NEMMATLCHB': '2B',
 'NEMMATMCNA': '2C',
 'NEMMATTIA': '2D',
 'NEMMATTI2A': '2D',
 'NEMVESLCHA': '2A',
 'NEMVESLCHB': '2B',
 'NEMVESMCNA': '2C',
 'PIINT7T1A': '1A',
 'PIINT7T1B': '1B',
 'PIINT7T1C': '1C',
 'PIINT7T1D': '1D',
 'PIINT7T1E': '1E',
 'PIINT7T1F': '1F',
 'PIINT7T1G': '1G',
 'PIINT7T1H': '1H',
 'TFS3NOTF2E6A': 'TF6A',
 'TFS3NOTF2E6B': 'TF6B',
 'TFS3NOTF2E6C': 'TF6C',
 'TFS3NOTTFE7A': 'TF7A',
 'TFS3NOTTFE7B': 'TF7B'}


import pandas as pd

import hashlib
from pymongo import MongoClient
from PIL import Image, ImageDraw, ImageFont
import qrcode
from PIL import ImageOps
from trans import white_to_transparency, transp_over_back
import io
import base64
from PIL import Image
import os
def assinado_rm(secret_key, rm):
    extracted_number = int(rm) 
    validation_code = hashlib.sha256(
        (str(extracted_number) +
        secret_key).encode()).hexdigest()[:4] 
    return str(extracted_number) + validation_code


card_width =  737
card_height = 519 

flag_image = Image.open('flag.jfif')
alpha = Image.new('L', flag_image.size, 100) 
flag_image.putalpha(alpha)
resized_flag_image = flag_image.resize((card_width, card_height), resample=Image.LANCZOS)

def make_card(student_dict, secret_key):
    card = Image.new('RGB', (card_width, card_height), color='white')
    card.paste(resized_flag_image, (0, 0), resized_flag_image)

    escudo = Image.open('CETI_TRANS.png')
    transp_over_back(
            card,
            escudo,
            resize=(150, 136),
            pos=(1, 4)
        )
    header_font1 = ImageFont.truetype('Altair-Bold Trial.ttf', size=22)
    school_name_ = "COLÉGIO ESTADUAL DE TEMPO INTEGRAL"
    school_width = header_font1.getlength(school_name_)
    school_draw = ImageDraw.Draw(card)
    school_draw.text(((card_width-school_width)/2, 35), school_name_, font=header_font1, fill='black', align='center')

    header_font1 = ImageFont.truetype('Altair-Bold Trial.ttf', size=18)
    school_name_2 = "DE BARRA DO CHOÇA"
    school_width = header_font1.getlength(school_name_2)
    school_draw = ImageDraw.Draw(card)
    school_draw.text(((card_width-school_width)/2, 60), school_name_2, font=header_font1, fill='black', align='center')

    header_font2 = ImageFont.truetype('Roboto-Regular.ttf', size=16)
    school_address = "AVENIDA BELA VISTA - BAIRRO BELA VISTA"
    address_width = header_font2.getlength(school_address)
    address_draw = ImageDraw.Draw(card)
    address_draw.text(((card_width-address_width)/2, 90), school_address, font=header_font2, fill='black', align='center')

    student_name = student_dict['estudante'] 
    print(len(student_name))
    if len(student_name) > 50:
        fsize = 20
    if len(student_name) > 48:
        fsize = 24
    if len(student_name) > 45:
        fsize = 25
    elif len(student_name) > 42:
        fsize = 26
    elif len(student_name) > 39:
        fsize = 27
    elif len(student_name) > 36:
        fsize = 28
    elif len(student_name) > 33:
        fsize = 29
    elif len(student_name) > 30:
        fsize = 30
    elif len(student_name) > 27:
        fsize = 32
    elif len(student_name) > 24:
        fsize = 34
    elif len(student_name) > 21:
        fsize = 36
    elif len(student_name) > 18:
        fsize = 38
    else:
        fsize = 42

    name_font = ImageFont.truetype('Louis George Cafe.ttf', size=fsize)
    name_width = name_font.getlength(student_name)
    name_draw = ImageDraw.Draw(card)
    name_draw.text(((card_width-name_width)/2, 130), student_name, font=name_font, fill='black', align='center')

    student_picture = Image.open( student_dict['pic'])
    student_picture_width, student_picture_height = student_picture.size
    picture_ratio = min(card_width*1.025/student_picture_width, card_height*0.5125/student_picture_height)
    resized_student_picture = student_picture.resize((int(student_picture_width*picture_ratio), int(student_picture_height*picture_ratio)), resample=Image.LANCZOS)
    bordered_student_picture = ImageOps.expand(resized_student_picture, border=5, fill='gray')
    card.paste(bordered_student_picture, (int(card_width/2 - bordered_student_picture.width) -1, 178))

    qr_code = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
    qr_code.add_data(assinado_rm(secret_key=secret_key, rm=student_dict['matrícula']))
    qr_code.make(fit=True)
    qr_code_image = qr_code.make_image(fill_color="black", back_color="white")
    qr_code_width, qr_code_height = qr_code_image.size
    qr_code_ratio = min(card_width*1.058/qr_code_width, card_height*0.529/qr_code_height)
    resized_qr_code_image = qr_code_image.resize((int(qr_code_width*qr_code_ratio), int(qr_code_height*qr_code_ratio)), resample=Image.LANCZOS)
    bordered_qrx = ImageOps.expand(resized_qr_code_image, border=0, fill='gray')
    # card.paste(bordered_qrx, (int((card_width - bordered_qrx.width)/2) , 460))
    # qr_code_image_ = white_to_transparency(resized_qr_code_image)
    card.paste(bordered_qrx, (int(card_width/2 + 1) , 178))


    DC_TURNO_COR = {
        'MATUTINO': 'seagreen',
        'VESPERTINO': 'gold',
        'NOTURNO': 'darkturquoise',
        'PERÍODO INTEGRAL DE 7 HORAS': 'sandybrown',
        'INTEGRAL 7H': 'sandybrown',
    }
    draw = ImageDraw.Draw(card)
    height = 45
    y0 = 454
    draw.rectangle((0, y0, card_width, y0 + height), fill=DC_TURNO_COR[student_dict['turno']]) # gold - ves, sandybrown - int, darkturquoise - not , seagreen - mat
    DC_LOCAL_COR = {
        'SEDE DO MUNICÍPIO': ('lightslategray', 'black'),
        'Não utiliza transporte escolar': ('lightslategray', 'black'),
    }
    back_, fore_ = DC_LOCAL_COR.get(student_dict['local'], ('purple', 'whitesmoke'))
    draw = ImageDraw.Draw(card)
    height = 20
    y0 = 499
    draw.rectangle((0, y0, card_width, y0 + height), fill=back_)#   whitesmoke

    class_font = ImageFont.truetype('Roboto-Regular.ttf', size=24)
    class_name = student_dict.get('turma')
    period_name = student_dict.get('turno').replace('PERÍODO INTEGRAL DE 7 HORAS', 'PERÍODO INTEGRAL')
    class_text = f"{class_name} - {period_name} - 2023"
    class_width = class_font.getlength(class_text)
    class_draw = ImageDraw.Draw(card)
    class_draw.text(
        ((card_width-class_width)/2, 462),
        class_text,
        font=class_font,
        fill='black' if student_dict['turno'] != 'MATUTINO' else 'whitesmoke',
        align='center'
    )
    class_font = ImageFont.truetype('Roboto-Regular.ttf', size=18)
    local_name = student_dict.get('local').replace('SEDE DO MUNICÍPIO', 'SEDE').replace('Não utiliza transporte escolar', 'NÃO utiliza transporte escolar')
    class_width = class_font.getlength(local_name)
    local_draw = ImageDraw.Draw(card)
    local_draw.text(((card_width-class_width)/2, 498), local_name, font=class_font, fill=fore_, align='center') # whitesmoke

    turma_alias = dict_turma_alias[student_dict.get('turma')]
    if 'TJ' in turma_alias or 'TF' in turma_alias:
        class_font = ImageFont.truetype('LilitaOne-Regular.ttf', size=64)
        col_alias = '\n'.join(list(turma_alias)).replace('1', '1°').replace('2', '2°').replace('3', '3°')
        class_width = class_font.getlength(col_alias.splitlines()[0])
        local_draw = ImageDraw.Draw(card)
        local_draw.text((50, 176), col_alias, font=class_font, fill='black', align='center')
    else:
        class_font = ImageFont.truetype('LilitaOne-Regular.ttf', size=82)
        col_alias = '\n'.join(list(turma_alias)).replace('1', '1°').replace('2', '2°').replace('3', '3°')
        class_width = class_font.getlength(col_alias.splitlines()[0])
        local_draw = ImageDraw.Draw(card)
        local_draw.text((50, 225), col_alias, font=class_font, fill='black', align='left')
    f = ImageFont.truetype('Louis George Cafe.ttf', size=38)
    class_width = f.getlength(student_dict.get('matrícula'))
    txt=Image.new('L', (int(class_width), 60))
    d = ImageDraw.Draw(txt)
    d.text((0, 0),  student_dict.get('matrícula'),  font=f, fill=255)
    w=txt.rotate(90,  expand=1)
    card.paste(ImageOps.colorize(w, (0, 0, 0), (0, 0, 0)), (637, int(316 - class_width/2)),  w)
    imgByteArr = io.BytesIO()
    card.save(imgByteArr, format='PNG')
    # to_return = imgByteArr.getvalue()
    return imgByteArr

from oito_para_um import make_one_page

def generate(df7x, collection, mysel=[], secret_key=''):
    me = df7x[df7x['matrícula'].isin(mysel)]
    me = me.drop_duplicates(subset=['matrícula'])

    for i in range(0, me.shape[0], 10):
        print(f'iteração {i}')
        list_of_8 = []
        sliced = me.iloc[i:i+10]
        dict_of_8 = sliced.T.to_dict().values()
        for data in dict_of_8:
            doc = next(collection.find({"_id" : data['matrícula']}))
            pic = doc['pic']
            new_bytes = base64.b64decode(bytes(pic,'utf-8'))
            img = io.BytesIO(new_bytes)
            list_of_8.append({
                **data,
                'pic': img
            })
        gerador = (make_card(item, secret_key) for item in list_of_8)

        make_one_page(turma="recorte12", pagina=i+1, alunos=gerador)

    from PyPDF2 import PdfMerger, PdfFileReader
    # for each directory join all pdfs into one

    for turma in ['recorte12']:
        pdfs = [f'./{turma}/{pdf}' for pdf in os.listdir(f'./{turma}')]
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(f'./results/{turma}.pdf')
        merger.close()
        for pdf in pdfs:
            os.remove(pdf)