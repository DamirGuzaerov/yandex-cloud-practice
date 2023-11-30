resource "yandex_ydb_database_serverless" "face-db" {
  name = var.db_name

  serverless_database {
    storage_size_limit = var.db_mem
  }
}

resource "yandex_ydb_table" "faces" {
  path              = "faces/faces_col"
  connection_string = yandex_ydb_database_serverless.face-db.ydb_full_endpoint

  column {
    name     = "orig_photo"
    type     = "Utf8"
    not_null = true
  }
  column {
    name     = "face_photo"
    type     = "Utf8"
    not_null = true
  }
  column {
    name     = "face_photo_telegram_key"
    type     = "Utf8"
    not_null = false
  }
  column {
    name     = "name"
    type     = "Utf8"
    not_null = false
  }

  primary_key = ["orig_photo", "face_photo"]
}