import boto3
import os
import json
from PIL import Image
from io import BytesIO
import random
import string
import ydb
import ydb.iam


PHOTO_BUCKET_NAME = os.environ["PHOTO_BUCKET"]
FACE_BUCKET_NAME = os.environ["FACE_BUCKET"]
DB_ENDPOINT = os.environ["DB_ENDPOINT"]
DB_PATH = os.environ["DB_PATH"]

# Create driver in global space.
driver = ydb.Driver(
    endpoint=DB_ENDPOINT,
    database=DB_PATH,
    credentials=ydb.iam.MetadataUrlCredentials(),
)

# Wait for the driver to become active for requests.

driver.wait(fail_fast=True, timeout=5)

pool = ydb.SessionPool(driver)

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for i in range(length))
    return random_string

s3 = boto3.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
)

def execute_query(session,data, orig_photo):
    # Create the transaction and execute query.
    return session.transaction().execute(
        """
          UPSERT INTO `faces/faces_col` (`orig_photo`,`face_photo`) VALUES ("{}", "{}");
        """.format(orig_photo, data),
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )

def handler(event, context):
    try:
        messageBody = json.loads(event["messages"][-1]["details"]["message"]["body"])

        # Получение параметров из event
        orig_photo = messageBody.get('orig_photo')
        coordinates = messageBody.get('coordinate')

        # Получение файла из Yandex Object Storage
        obj = s3.get_object(Bucket=PHOTO_BUCKET_NAME, Key=orig_photo)
        img_data = obj['Body'].read()

        # Загрузка изображения
        img = Image.open(BytesIO(img_data))

        # Предполагаем, что координаты заданы для прямоугольника
        left = int(coordinates[0]['x'])
        top = int(coordinates[0]['y'])
        right = int(coordinates[2]['x'])
        bottom = int(coordinates[2]['y'])

        # Вырезаем нужную часть изображения
        cropped_image = img.crop((left, top, right, bottom))

        # Сохраняем обрезанное изображение в память
        cropped_img_byte_arr = BytesIO()
        cropped_image.save(cropped_img_byte_arr, format=img.format)

        face_image_key = generate_random_string(16)
        s3.put_object(Bucket=FACE_BUCKET_NAME, Key=f'{face_image_key}.jpg', Body=cropped_img_byte_arr.getvalue())

        result = pool.retry_operation_sync(execute_query, data=face_image_key, orig_photo=orig_photo)
        #upsert_simple(session, f"{DB_PATH}/faces",f'{face_image_key}.jpg')
        # Возврат обрезанного изображения в виде байтов через ответ функции (например, в base64)
        return {
            'statusCode': 200,
            'body': cropped_img_byte_arr.getvalue()
            # 'body': base64.b64encode(cropped_img_byte_arr.getvalue()).decode('utf-8') # Если вам нужно вернуть строку base64
        }
    except Exception as e:
        print(f"error: {str(e)}")
        return {
            'statusCode': 500,
            'body': str(e)
        }