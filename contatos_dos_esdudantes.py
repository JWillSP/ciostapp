import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import base64
import io
import cv2
import numpy as np
from PIL import Image

def back_image(image):
    xpl2 = image.convert('RGB')
    img_buf = io.BytesIO()
    xpl2.save(img_buf, format='JPEG', quality=95)
    value_got = img_buf.getvalue()
    encodado = base64.b64encode(value_got).decode('ascii')
    return encodado

def b64pic(image_pil):
    return 'data:image/jpg;base64,' + back_image(image_pil)


def get_image(upload_first=False):
    options = ["Câmera", "Upload de foto"]
    if upload_first:
        options.reverse()

    choice = st.radio("Escolha o método de aquisição da imagem", options)
    if choice == "Câmera":
        file = st.camera_input(
            label="Tire a foto clicando no botão abaixo"
        )
    else:
        file = st.file_uploader("Faça upload de uma imagem da sua galeria", type=["png", "jpg", "jpeg"])

    def correct_image_orientation(image):
        """Corrige a orientação de uma imagem com base em seus metadados EXIF."""
        try:
            exif_data = image._getexif()
            orientation_tag = 274  # The orientation tag ID in EXIF data
            if exif_data is not None and orientation_tag in exif_data:
                orientation = exif_data[orientation_tag]
                if orientation == 2:
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    image = image.rotate(180)
                elif orientation == 4:
                    image = image.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 5:
                    image = image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 6:
                    image = image.rotate(-90, expand=True)
                elif orientation == 7:
                    image = image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass
        return image

    if file:
        PIL_img = Image.open(file)
        PIL_img = correct_image_orientation(PIL_img)
        img = np.array(PIL_img)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        haar_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        faces_rect = haar_cascade.detectMultiScale(gray_img, 1.1, 9)
        for (x, y, w, h) in faces_rect:
            factor = 1.7
            new_w = int(w*factor)
            new_h = int(h*factor)
            hfivefourthdif = int((5/4)*new_w) - new_h
            desloc_x = int(0.06*w)
            desloc_y = int(0.06*h)
            dif_w = int((new_w - w)/2)
            dif_h = int((new_h - h)/2)
            cv2.rectangle(
                img,
                (x - dif_w, y - dif_h - desloc_y),
                (x + w + dif_w, y + h + dif_h - desloc_y + hfivefourthdif),
                (0, 200, 0),
                2
            )
            # cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            facezoom = 0.65
            new_dif_h = int(dif_h*facezoom)
            sq_x1 = x - new_dif_h
            sq_y1 = y - new_dif_h - desloc_y
            sq_x2 = x + h + new_dif_h
            sq_y2 = y + h + new_dif_h - desloc_y
            cv2.rectangle(
                img,
                (sq_x1, sq_y1),
                (sq_x2, sq_y2),
                (200, 0, 0),
            )
            break

        st.image(img, caption='Rosto encontrado', use_column_width=True)
        cinco_quartos = PIL_img.crop((x - dif_w, y - dif_h - desloc_y, x + w + dif_w, y + h + dif_h - desloc_y + hfivefourthdif))
        squared = PIL_img.crop((sq_x1, sq_y1, sq_x2, sq_y2))
        resized_img = cv2.resize(np.array(squared), (64, 64), interpolation=cv2.INTER_AREA)
        main_resized_img = cv2.resize(np.array(cinco_quartos), (160, 200), interpolation=cv2.INTER_AREA)
        b64_pic = b64pic(Image.fromarray(main_resized_img))
        b64_thumb = b64pic(Image.fromarray(resized_img))
        return b64_pic, b64_thumb
    
