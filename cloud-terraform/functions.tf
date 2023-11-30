data "archive_file" "bot_zip" {
  output_path = "bot.zip"
  type        = "zip"
  source_dir  = "bot"
}

data "archive_file" "face_cut_zip" {
  output_path = "face_cut.zip"
  type        = "zip"
  source_dir  = "face_cut"
}

data "archive_file" "face_detection_zip" {
  output_path = "face_detection.zip"
  type        = "zip"
  source_dir  = "face_detection"
}


resource "yandex_function" "function_face_detection" {
  name               = var.func_face_detection_name
  user_hash          = data.archive_file.face_detection_zip.output_base64sha256
  runtime            = "python311"
  entrypoint         = "index.handler"
  memory             = "128"
  execution_timeout  = "10"
  service_account_id = yandex_iam_service_account.sa.id
  tags               = ["my_tag"]
  content {
    zip_filename = "face_detection.zip"
  }
  environment = {
    AWS_ACCESS_KEY_ID     = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    AWS_SECRET_ACCESS_KEY = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
    AWS_DEFAULT_REGION    = "ru-central1-a"
    API_KEY               = yandex_iam_service_account_api_key.sa-api-key.secret_key
    QUEUE_NAME            = yandex_message_queue.cut_photo_task_queue.name
    TGKEY                 = var.tgkey
  }
}

resource "yandex_function" "function_face_cut" {
  name               = var.func_face_cut_name
  user_hash          = data.archive_file.face_cut_zip.output_base64sha256
  runtime            = "python311"
  entrypoint         = "index.handler"
  memory             = "128"
  execution_timeout  = "10"
  service_account_id = yandex_iam_service_account.sa.id
  tags               = ["face_cut"]
  content {
    zip_filename = "face_cut.zip"
  }
  environment = {
    AWS_ACCESS_KEY_ID     = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    AWS_SECRET_ACCESS_KEY = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
    AWS_DEFAULT_REGION    = "ru-central1-a"
    PHOTO_BUCKET          = yandex_storage_bucket.photo.bucket
    FACE_BUCKET           = yandex_storage_bucket.faces.bucket
    DB_ENDPOINT           = yandex_ydb_database_serverless.face-db.ydb_full_endpoint
    DB_PATH               = yandex_ydb_database_serverless.face-db.database_path
  }
}

resource "yandex_function" "function_tg_bot" {
  name               = var.func_tg_bot_name
  user_hash          = data.archive_file.bot_zip.output_base64sha256
  runtime            = "python311"
  entrypoint         = "index.handler"
  memory             = "128"
  execution_timeout  = "10"
  service_account_id = yandex_iam_service_account.sa.id
  tags               = ["face_bot"]
  content {
    zip_filename = "bot.zip"
  }
  environment = {
    TGKEY                 = var.tgkey
    AWS_ACCESS_KEY_ID     = yandex_iam_service_account_static_access_key.sa-static-key.access_key
    AWS_SECRET_ACCESS_KEY = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
    AWS_DEFAULT_REGION    = "ru-central1-a"
    PHOTO_BUCKET          = yandex_storage_bucket.photo.bucket
    FACE_BUCKET           = yandex_storage_bucket.faces.bucket
    DB_ENDPOINT           = yandex_ydb_database_serverless.face-db.ydb_full_endpoint
    DB_PATH               = yandex_ydb_database_serverless.face-db.database_path
    API_GATEWAY_FACES_ID  = yandex_api_gateway.face-photos-api.id
    API_GATEWAY_PHOTOS_ID = yandex_api_gateway.photos-api.id
  }
}

resource "yandex_function_iam_binding" "bot-iam" {
  function_id = yandex_function.function_tg_bot.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}