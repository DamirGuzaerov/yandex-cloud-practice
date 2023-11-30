variable "folder_id" {
  type = string
  description = "Folder id in cloud"
}


variable "tgkey" {
  type        = string
  description = "Telegram Bot API Key"
}


variable "db_mem" {
  type        = number
  description = "Database memory"
}
variable "db_name" {
  type        = string
  description = "Database name"
}


variable "func_face_detection_name" {
  type = string
  description = "Face detection function name"
}
variable "func_face_cut_name" {
  type = string
  description = "Face cut function name"
}
variable "func_tg_bot_name" {
  type = string
  description = "Telegram bot function name"
}

variable "faces_bucket_name" {
  type = string
  description = "Faces photo object storage name"
}
variable "photo_bucket_name" {
  type = string
  description = "Faces original photo object storage name"
}

variable "cut_photo_queue_name" {
  type = string
  description = "Cut photo tasks queue name"
}


variable "face_api_name" {
  type = string
  description = "Faces Obejct storage API Gateway name"
}
variable "photo_api_name" {
  type = string
  description = "Faces Original photos Obejct storage API Gateway name"
}


variable "photo_task_queue_trigger" {
  type = string
  description = "Face cut function trigger name"
}
variable "photo_trigger_name" {
  type = string
  description = "Face detection function trigger name"
}
