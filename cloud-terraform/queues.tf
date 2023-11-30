resource "yandex_message_queue" "cut_photo_task_queue" {
  name       = var.cut_photo_queue_name
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
}