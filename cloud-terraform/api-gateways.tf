resource "yandex_api_gateway" "face-photos-api" {
  name = var.face_api_name

  spec = <<-EOF
    openapi: 3.0.0
    info:
      title: "Face Photos API"
      version: "1.0.0"
    paths:
      /faces/{file}:
        get:
          summary: Serve face photos file from Yandex Cloud Object Storage
          parameters:
            - name: file
              in: path
              required: true
              schema:
                type: string
          x-yc-apigateway-integration:
            type: object_storage
            bucket: vvot12-faces
            object: '{file}'
            error_object: error.html
            service_account_id: ${yandex_iam_service_account.sa.id}
  EOF
}

resource "yandex_api_gateway" "photos-api" {
  name = var.photo_api_name

  spec = <<-EOF
    openapi: 3.0.0
    info:
      title: "Face Photos API"
      version: "1.0.0"
    paths:
      /photos/{file}:
        get:
          summary: Serve original face photos file from Yandex Cloud Object Storage
          parameters:
            - name: file
              in: path
              required: true
              schema:
                type: string
          x-yc-apigateway-integration:
            type: object_storage
            bucket: vvot12-photo
            object: '{file}'
            error_object: error.html
            service_account_id: ${yandex_iam_service_account.sa.id}
  EOF
}
