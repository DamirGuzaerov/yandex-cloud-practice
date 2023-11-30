resource "yandex_function_trigger" "cut_photo_task_queue_trigger" {
  name = var.photo_task_queue_trigger
  message_queue {
    queue_id           = yandex_message_queue.cut_photo_task_queue.arn
    service_account_id = yandex_iam_service_account.sa.id
    batch_size         = "1"
    batch_cutoff       = "10"
  }
  function {
    id                 = yandex_function.function_face_cut.id
    service_account_id = yandex_iam_service_account.sa.id
  }
}

resource "yandex_function_trigger" "photo-trigger" {
  name        = var.photo_trigger_name
  labels      = {}
  object_storage {
    bucket_id    = yandex_storage_bucket.photo.id
    create       = true
    batch_cutoff = "10"
    batch_size   = "1"
    delete       = false
    update       = false
  }
  function {
    id                 = yandex_function.function_face_detection.id
    service_account_id = yandex_iam_service_account.sa.id
  }
}