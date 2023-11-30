import json
import requests
import os
import boto3
import ydb
import ydb.iam
import re
import random
import string

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

tgkey = os.environ["TGKEY"]
PHOTO_BUCKET_NAME = os.environ["PHOTO_BUCKET"]
FACE_BUCKET_NAME = os.environ["FACE_BUCKET"]
DB_ENDPOINT = os.environ["DB_ENDPOINT"]
DB_PATH = os.environ["DB_PATH"]
API_GATEWAY_ID = os.environ["API_GATEWAY_FACES_ID"]
API_GATEWAY_PHOTOS_ID = os.environ["API_GATEWAY_PHOTOS_ID"]

# Create driver in global space.
driver = ydb.Driver(
    endpoint=DB_ENDPOINT,
    database=DB_PATH,
    credentials=ydb.iam.MetadataUrlCredentials(),
)

driver.wait(fail_fast=True, timeout=5)
pool = ydb.SessionPool(driver)


def get_face_without_name(session):
    return session.transaction().execute(
        """
          SELECT * FROM `faces/faces_col` WHERE name is null;
        """,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )


def get_face_by_name(session, name):
    return session.transaction().execute(
        """
          SELECT * FROM `faces/faces_col` WHERE name = "{}";
        """.format(name),
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )


def set_face_file_unique_id(session, face_photo_telegram_key, face_photo):
    return session.transaction().execute(
        """
        UPDATE `faces/faces_col` 
        SET face_photo_telegram_key = "{}"
        WHERE face_photo = "{}"
        """.format(face_photo_telegram_key, face_photo),
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )


def set_face_name(session, face_photo_telegram_key, name):
    return session.transaction().execute(
        """
        UPDATE `faces/faces_col` 
        SET name = "{}"
        WHERE face_photo_telegram_key = "{}"
        """.format(name, face_photo_telegram_key),
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    )


def telegram_get_file(file_id):
    url = f"https://api.telegram.org/bot{tgkey}/getFile"
    r_file = requests.get(url=url, params={"file_id": file_id})
    return r_file.json()


def telegram_download_file(file_path):
    url = f"https://api.telegram.org/file/bot{tgkey}/{file_path}"
    r_file = requests.get(url=url)
    return r_file


def upload_to_yandex_storage(bucket_name, object_name, file_content):
    s3.put_object(Bucket=bucket_name, Key=object_name, Body=file_content)


def extract_name(text):
    match = re.match(r'/find\s+(.+)', text)
    if match:
        return match.group(1)
    return None


def telegram_send_text_message(chat_id, text, message_id):
    url = f"https://api.telegram.org/bot{tgkey}/sendMessage"

    params = {"chat_id": chat_id,
              "text": text,
              "reply_to_message_id": message_id}

    r = requests.get(url=url, params=params)

    return {
        'statusCode': 200,
    }


def handler(event, context):
    update = json.loads(event["body"])
    print(update)
    if ("message" not in update):
        return {
            'statusCode': 200,
        }
    message = update["message"]
    message_id = message["message_id"]
    chat_id = message["chat"]["id"]

    if "text" in message:
        text = message["text"]
        print(f"message: {message}")
        if ("/find" in text):
            name = extract_name(text)
            if name:
                result = pool.retry_operation_sync(get_face_by_name, name=name)
                if (len(result[0].rows) > 0):
                    image_paths = []
                    for photo in result[0].rows:
                        orig_photo = photo.orig_photo
                        image_path = f"https://{API_GATEWAY_PHOTOS_ID}.apigw.yandexcloud.net/photos/{orig_photo}"
                        if(image_path not in image_paths):
                            image_paths.append(image_path)
                    media_group = [
                        {'type': 'photo', 'media': image_path}
                        for image_path in image_paths
                    ]
                    url = f'https://api.telegram.org/bot{tgkey}/sendMediaGroup'
                    
                    data = {
                        'chat_id': chat_id,
                        'media': json.dumps(media_group),
                        "reply_to_message_id": message_id
                    }
                    requests.post(url, data=data)
                    return {
                        "statusCode": 200
                    }

            return telegram_send_text_message(chat_id, "Фотографии не найдены", message_id)

        if ("reply_to_message" in message):
            reply_to_message = message['reply_to_message']
            if ("photo" in reply_to_message):
                file_id = reply_to_message['photo'][-1]['file_unique_id']
                name = message['text']
                print(f"reply_to_message in message: {message['reply_to_message']['photo'][-1]['file_unique_id']}")
                pool.retry_operation_sync(set_face_name, face_photo_telegram_key=file_id, name=name)
                return telegram_send_text_message(chat_id, "Имя успешно установлено", message_id)
        if (text.upper() == "/GETFACE"):
            result = pool.retry_operation_sync(get_face_without_name)
            if (len(result[0].rows) > 0):
                face_image_key = result[0].rows[-1].face_photo
                url = f'https://api.telegram.org/bot{tgkey}/sendPhoto'

                data = {
                    'chat_id': chat_id,
                    'photo': f"https://{API_GATEWAY_ID}.apigw.yandexcloud.net/faces/{face_image_key}.jpg",
                    "reply_to_message_id": message_id
                }

                response = requests.post(url, data=data)
                if response.status_code == 200:
                    photo_unique_id = response.json()['result']['photo'][-1]['file_unique_id']
                    print(f"response send photo: {photo_unique_id}")
                    pool.retry_operation_sync(set_face_file_unique_id, face_photo_telegram_key=photo_unique_id,
                                              face_photo=face_image_key)
                    print(f'Фото успешно отправлено:')
                else:
                    print('Ошибка отправки фото')
                return {
                    "statusCode": 200
                }
            else:
                return telegram_send_text_message(chat_id, "Фотографии без названия не найдены", message_id)
    elif "photo" in message:
        photo = message['photo']
        print(photo)
        best_quality_photo = photo[-1]['file_id']
        file_metadata = telegram_get_file(best_quality_photo)
        result_file = telegram_download_file(file_metadata['result']['file_path'])
        orig_photo_key = generate_random_string(16)
        print(f"resultFile: {result_file.json}")
        upload_to_yandex_storage("vvot12-photo", f"{orig_photo_key}.jpg", result_file.content)
        return telegram_send_text_message(chat_id, "Фотография сохранена", message_id)

    rep_text = "Ошибка"
    url = f"https://api.telegram.org/bot{tgkey}/sendMessage"
    params = {"chat_id": chat_id,
              "text": rep_text,
              "reply_to_message_id": message_id}
    r = requests.get(url=url, params=params)

    return {
        'statusCode': 200,
    }


def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for i in range(length))
    return random_string