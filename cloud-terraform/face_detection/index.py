import json
import requests
import os
import boto3
import base64

# Создайте функцию, которая кодирует файл и возвращает результат.
def encode_file(file_to_encode):
    file_content = file_to_encode.read()
    return base64.b64encode(file_content).decode('utf-8')

API_KEY = os.environ["API_KEY"]
QUEUE_NAME = os.environ["QUEUE_NAME"]
session = boto3.session.Session()

s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net'
)

sqs = session.client(
    service_name='sqs',
    endpoint_url='https://message-queue.api.cloud.yandex.net',
    region_name='ru-central1'
)

def send_face_data_to_queue(queue_url, orig_photo, coordinates):
    # Формирование сообщения
    message_body = json.dumps({
        "orig_photo": orig_photo,
        "coordinate": coordinates
    })

    url = sqs.get_queue_url(QueueName=QUEUE_NAME)
    # Отправка сообщения в очередь
    response = sqs.send_message(QueueUrl=url["QueueUrl"], MessageBody=message_body)
    print(f"RESPONSE FROM SENDING MESSAGE {response}")
    return response

def handler(event, context):
    event = event['messages'][-1]['details']
    bucket_name = event.get('bucket_id')
    object_id = event.get('object_id')

    # Проверка наличия параметров bucket_name и object_id
    if not bucket_name or not object_id:
        print("bucket_name or object_id is not correct")
        return {
            'statusCode': 400,
            'body': 'Missing bucket_name or object_id parameter'
        }

    try:
        # Получение изображения из Object Storage
        response = s3.get_object(Bucket=bucket_name, Key=object_id)
        print(f"bucket response: {response}")
        image_content = response['Body']

        # Формирование запроса для Yandex Vision API
        vision_api_url = 'https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze'

        headers = {
            'Authorization': f'Api-Key {API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'analyze_specs': [
                {
                    'content': encode_file(image_content),
                    'features': [
                        {
                            'type': 'FACE_DETECTION',
                        }
                    ]
                }
            ]
        }

        # Отправляем запрос в Yandex Vision API
        vision_response = requests.post(vision_api_url, headers=headers, json=payload)

        # Обработка и возврат ответа от Yandex Vision API
        if vision_response.ok:
            faces = vision_response.json()["results"][-1]["results"][-1]["faceDetection"]["faces"]
            print(faces)
            for face in faces:
                coordinates = face['boundingBox']['vertices']
                send_face_data_to_queue("QUEUE_URL",object_id,coordinates)
            return {
                'statusCode': 200,
                'body': vision_response.json()
            }
        else:
            print(vision_response)
            return {
                'statusCode': vision_response.status_code,
                'body': 'Error processing the image.'
            }

    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': str(e)
        }