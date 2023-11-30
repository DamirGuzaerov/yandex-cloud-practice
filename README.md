# yandex-cloud-practice
Телеграм бот с использованием сервисов Yandex Cloud

Чтобы можно было создать ресурсы с помощью terraform нужно сгенерировать авторизованный ключ следуя следующей инструкции:
https://cloud.yandex.ru/docs/tutorials/infrastructure-management/terraform-quickstart#get-credentials

Далее применить команду (message queue могут не создасться с первого раза, в таком случае команду следует выполнить повторно)
`terraform apply`

И ввести входные параметры:

`folder_id` - идентификатор каталога в облаке
`tgkey` - токен вашего telegram бота


Готовый вариант телеграм бота: @Vvot12FaceBot
