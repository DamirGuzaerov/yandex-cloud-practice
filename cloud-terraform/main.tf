terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  service_account_key_file = "key.json"
  folder_id                = var.folder_id
  zone                     = "ru-central1-a"
}

data "http" "webhook" {
  url = "https://api.telegram.org/bot${var.tgkey}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.function_tg_bot.id}"
}

