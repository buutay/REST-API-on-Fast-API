from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from uuid import uuid4
from PIL import Image
import os
import mimetypes
import time
from time import sleep


#инициализация FastAPI
app = FastAPI()

# Директория для хранения загружаемых файлов
UP_DIR = "./files/"
MIN_PICTURE = "./mini_pic/"
def ffmpeg(file_path_vid: str ,file_path_save: str):
    ff = "ffmpeg -i " + file_path_vid +" -ss 00:00:00 -vframes 1 "+file_path_save+" -y"
    os.system(ff)

# Создаем папки
os.makedirs(UP_DIR, exist_ok=True)
os.makedirs(MIN_PICTURE, exist_ok=True)
@app.put("/api/files/")
async def upload_file(file: UploadFile = File(...)):
    # Генерация UUID для файла
    file_id = uuid4()
    # Сохраняем файл
    file_path = os.path.join(UP_DIR, f"{file_id}_{file.filename}")
    # Чтение файла
    contents = await file.read()
    # Записываем файл
    with open(file_path, "wb") as f:
        f.write(contents)
    # Получение размера файла
    file_size = os.path.getsize(file_path)
    #Определяем mimetype файла
    mimetype = mimetypes.guess_type(file_path)
    #Проверяем, файл картинка или видео
    if ("image" in mimetype[0]) or ("video" in mimetype[0]): 
    # Возвращение информации о файле
       return {"uuid": str(file_id), "size": file_size, "mime": mimetype[0]}
    else:
       raise HTTPException(status_code=500,detail="File is not an image or video")
       return {"File is not an image or video"}
@app.put("/api/files/{file_uuid}")
async def update_item(file_uuid: str, length: int | None = None, width: int | None = None ): #длина и ширина --- опциональные параметры
    #находим файл по UUID с перебором for
    #рассматриваем случай без создания миниаютр (None в размерах)
    k = 0 #флаг для найденного файла
    if (width == None) and (length == None): 
        for filename in os.listdir(UP_DIR):
            if file_uuid in filename:
                k = k+1 
                mime = mimetypes.guess_type(f"{UP_DIR}/{filename}") #узнаем тип файла 
                if "image" in mime[0]: #cлучай с фото
                    return FileResponse(f"{UP_DIR}/{filename}")
                if "video" in mime[0]: #случай с видео
                    full_path_video = f"{UP_DIR}{filename}" #путь к видео
                    file_path_frame = os.path.join(MIN_PICTURE, f"frame_{file_uuid}.png") #путь к кадру
                    ffmpeg(full_path_video, file_path_frame) #запускаем ffmpeg для обработки видео
                    sleep(5) #дожидаемся 
                    return FileResponse(file_path_frame) #отправляем файл
    #рассмотрим случай, когда указан только один параметр
    if ((width == None) and (length != None)) or (((width != None) and (length == None))):
        if ((width == None) and (length != None)):
           raise HTTPException(status_code=500,detail="Width parameter not specified") #высылаем ошибку
           return {"width parameter not specified"} #записываем комментарий в файл
        if ((width != None) and (length == None)):
           raise HTTPException(status_code=500,detail="Length parameter not specified")
           return {"Length parameter not specified"}
       
    #рассмотрим случай, когда указаны оба параметра
    if (width != None) and (length != None):
        for filename in os.listdir(UP_DIR):
            if file_uuid in filename:
                k = k+1
                mime = mimetypes.guess_type(f"{UP_DIR}/{filename}") #проверяем тип файла
                if "image" in mime[0]:
                    #фиксируем путь к файлу миниатюры
                    file_path_mini = os.path.join(MIN_PICTURE, f"mini_{filename}")
                    #фиксируем путь к исходному файлу
                    filename_full = f"{UP_DIR}/{filename}"
                    try: #пробуем создать миниатюру
                        with Image.open(filename_full) as img: #делаем сокращение
                            img.thumbnail((length,width)) #создаем миниатюру
                            img.save(file_path_mini) #записываем миниатюру
                            return FileResponse(file_path_mini) #возвращаем файл
                    except Exception as e: #высылаем ошибку в случае неудачи
                        raise HTTPException(status_code=500,detail="Could not create thumbnail.")
                if "video" in mime[0]:
                    full_path_video = f"{UP_DIR}{filename}" #путь к видео
                    file_path_frame = os.path.join(MIN_PICTURE, f"frame_{file_uuid}.png") #путь к кадру
                    ffmpeg(full_path_video, file_path_frame) #запускаем ffmpeg
                    sleep(5) #выжидаем для сознания 
                    try: #пробуем выполнить 
                        with Image.open(file_path_frame) as img: #делаем сокращение
                            img.thumbnail((length,width)) #создаем миниатюру
                            img.save(file_path_frame) #записываем файл
                            return FileResponse(file_path_frame) #возвращаем файл
                    except Exception as e:
                        raise HTTPException(status_code=500,detail="Could not create thumbnail.") #возращаем ошибку в случае неудачи 
                    return FileResponse(file_path_frame)

 
