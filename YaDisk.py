import os
import requests

class YaUploader:
    def __init__(self, file_path: str):
        """
        partition() разбивает строку на три части: все что слева от разделителя, сам разделитель,
        то что справа от разделителя. Если разделитель не найден, то возвращается исходная строка
        и две пустых строки (т.е. в любом случае возвращается кортеж из 3 элементов).
        """

        #путь без указания диска
        self.file_path = file_path.partition(':')[2]
        #диск
        self.disk=file_path.partition(':')[0]
        #полный путь
        self.full_path=file_path
        #самая правая в иерархии папка, в которой собственно и содержатся файлы
        """
        Возвращает кортеж, содержащий часть перед последним шаблоном, сам шаблон, и часть после шаблона.
        Если шаблон не найден, возвращается кортеж, содержащий две пустых строки, а затем саму строку
        """
        self.last_folder=file_path.rpartition('\\')[2]

        #теперь получим самую правую в иерархии папку, в которой собственно и содержатся файлы
        for d, dirs, files in os.walk(file_path):
            print(d)
            print(dirs)
            for f in files:
                print(f'Файл для загрузки: {f}')

        print(f'Загружаем файлы на Яндекс.Диск в директорию: /{self.last_folder}')

        # Получаем token:
        self.token = 'AgAAAAAEjRl2AADLWxu9VDr8q0N4sZ1GeLmmCtI'
        self.token_prefix= 'OAuth'

    def _get_files_from_folder(self) -> list:
        """Метод получает списко файлов из каталога по пути self.file_path и
        возвращает список файлов для дальнейшей работы"""

        # 1. изменяем текущий каталог на переданный
        # 2. возврашаем перечень файлов в каталоге в виде списка

        #переходим в заданный каталог. Он становится текущим, рабочим:
        os.chdir(self.full_path)
        #список файлов и директорий (!)
        #file_list=os.listdir()

        #а вот можно гарантированно получить список только файлов в текущем каталоге (без папок)
        #os.walk возвращает объект-генератор
        #Здесь в качестве аргумента передано значение «.», которое обозначает верхушку дерева:

        file_list=[]
        for d, dirs, files in os.walk('.'):
            for f in files:
                #file=os.path.abspath(str(f))
                file_list.append(f)

        #контрольная печать
        print(f'Список файлов для загрузки: \n{file_list}')
        return file_list

    def upload(self):
        """Метод загруджает файлы по списку file_list на яндекс диск"""
        file_list = self._get_files_from_folder()
        #print(file_list)

        # Тут ваша логика
        # ШАГ 1. Запрашиваем URL для загрузки:
        """
        Запрос URL для загрузки. Сообщив API Диска желаемый путь для загружаемого файла, 
        получаем URL для обращения к загрузчику файлов.
        """

        method_get_url = 'GET'
        method_upload_file = 'PUT'
        URL = 'https://cloud-api.yandex.net:443'
        RESOURCE = '/v1/disk/resources/upload'
        headers = {'Authorization': f'{self.token_prefix} {self.token}'}

        #цикл по списку файлов
        for file in file_list:
            #параметры запроса URL для загрузки: путь + файл!!!!!!!!
            params = {'path': f'/{self.last_folder}/{file}'}
            # запрашиваем у сервера URL для загрузки файла
            resp = requests.request(method_get_url, URL + RESOURCE, params=params, headers=headers)
            resp_json = resp.json()
            #print(resp_json)

            #Здесь проверка ответа должна быть реализована!

            #загрузка файла на Яндекс.Диск:
            # формируем запрос
            url_upload = resp_json['href']
            with open(file, "rb") as f:
                up_load = requests.request(method_upload_file, url_upload, data=f, headers=headers)

                #print(up_load)
                # проверка кода ответа
                if up_load.status_code == 201:
                    print(f'File {file} is successfull uploaded!')
                elif up_load.status_code == 202:
                    print(f'Файл {file} принят сервером, но еще не был перенесен непосредственно в Яндекс.Диск')
                elif up_load.status_code == 412:
                    print(f'При дозагрузке файла {file} был передан неверный диапазон в заголовке Content-Range')
                    return 2
                elif up_load.status_code == 413:
                    print(f'Размер файла {file} превышает 10 ГБ.')
                    return 3
                elif up_load == 413:
                    print(f'Размер файла {file} превышает 10 ГБ.')
                    return 4
                else:
                    print('Some kind error during file {file} upload!')
                    return -1

    def create_folder(self):
        """метод создает папку на яндекс.диске с таким же именем как и в self.last_folder"""
        # Формируем запрос:

        method = 'PUT'
        URL = 'https://cloud-api.yandex.net:443'
        RESOURCE = '/v1/disk/resources'

        params = {'path': f'/{self.last_folder}'}
        headers = {'Authorization': f'{self.token_prefix} {self.token}'}

        """
        без токена получем такой ответ:
        {'message': 'Не авторизован.', 'description': 'Unauthorized', 'error': 'UnauthorizedError'}

        с токеном такой:
        {'operation_id': '7e4e791743756055422ec89d3731154350db2aab383e51e2c2e095e81c63ab4b', 
        'href': 'https://uploader23j.disk.yandex.net:443/upload-target/20200630T160331.503.utd.coeoj9xa8cfsd9qadacox7sa9-k23j.11937437',
         'method': 'PUT', 'templated': False}
        """

        # запрашиваем сервер
        resp = requests.request(method, URL + RESOURCE, params=params, headers=headers)
        resp_json = resp.json()
        #print(resp_json)

        #проверка кода ответа
        if resp.status_code == 201:
            print(f'Папка {self.last_folder} успешно создана!')
            return 0
        elif resp.status_code == 409:
            print(f'Folder {self.last_folder} already exists!')
            return 1
        else:
            print(f'Some kind error during folder {self.last_folder} create!')
            return -1

if __name__ == '__main__':
    target_path=input('Введите путь до папки на компьютере: ')
    uploader = YaUploader(target_path)
    uploader.create_folder()
    result = uploader.upload()