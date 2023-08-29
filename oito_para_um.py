from PIL import Image, ImageDraw
import time
# a function for getting a time as integer
def get_time():
    return int(time.time())

def make_one_page(
    turma= '',
    pagina= 1,
    alunos= []
):
    # Define the size of an A4 paper in pixels at 300 dpi
    A4_WIDTH = 2480
    A4_HEIGHT = 3508

    # Define the size of each picture in cm
    PIC_WIDTH = 8.0
    PIC_HEIGHT = 5.54

    # Calculate the size of each picture in pixels at 300 dpi
    PIC_WIDTH_PX = int(PIC_WIDTH / 2.54 * 300)
    PIC_HEIGHT_PX = int(PIC_HEIGHT / 2.54 * 300)

    # Create a new blank image with the dimensions of an A4 paper
    a4_image = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
    draw = ImageDraw.Draw(a4_image)

    # Open each picture and paste it onto the A4 image
    for i, aluno in enumerate(alunos):
        img = Image.open(aluno)
        resized_image = img.resize((PIC_WIDTH_PX, PIC_HEIGHT_PX), resample=Image.LANCZOS)
        x_offset = int(i % 2 * PIC_WIDTH_PX)
        y_offset = int(i // 2 * PIC_HEIGHT_PX)
        init_x = 230
        init_y = 50
        x_point = init_x + ((i % 2)+1)*26 + x_offset
        y_point = init_y + ((i // 2)+1)*26 + y_offset

        if i // 2 == 0: 
            draw.line([(x_point, init_y + 13),
                   (x_point + PIC_WIDTH_PX, init_y + 13)], fill="black", width=1)
        if i % 2 == 0:
            draw.line([(init_x + 13, y_point),
                   (init_x + 13, y_point + PIC_HEIGHT_PX)], fill="black", width=1)
            
        # Add vertical line
        draw.line([(x_point + PIC_WIDTH_PX + 13 , y_point),
                   (x_point + PIC_WIDTH_PX + 13, y_point + PIC_HEIGHT_PX)], fill="black", width=1)
        
        # Add horizontal line
        draw.line([(x_point, y_point + PIC_HEIGHT_PX + 13),
                   (x_point + PIC_WIDTH_PX, y_point + PIC_HEIGHT_PX + 13)], fill="black", width=1)
            
        a4_image.paste(resized_image, (x_point, y_point))

    # Save the A4 image as a PDF file
    a4_image.save(f'./{turma}/pagina_as_{get_time()}_{pagina}.pdf', 'PDF', resolution=300.0)
