import requests
import json
import os
from bs4 import BeautifulSoup
from iMES import app


class DirectumIntegration():
    """
        Класс предназначенный для получения
        документов с СЭД "Directum" через веб-доступ
    """

    def __init__(self):
        self.urls = {
            'Авторизация': 'https://dm.iplast.com/Authentication.asmx/Login'
        }
        # Заголовки для авторизации
        self.headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Referer': 'https://dm.iplast.com/Login.aspx',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/103.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        # Данные для входа в JSON формате
        self.session = requests.Session()

    def Authorization(self):
        """
            Функция авторизации на сайте веб-доступа для Directum.
        """

        self.logindata = json.dumps({
            'Password': '71Rg*#Eq',
            'ProviderName': 'sql',
            'Realm': 'Pink',
            'RememberMe': 'false',
            'UserName': 'Web.dostup'
        }, indent=4)
        # Создаём сессию, удобство сессии заключается в том что она хранит куки
        # Отправляем запрос на авторизацию
        try:
            post_request = self.session.post(self.urls['Авторизация'],
                                             allow_redirects=True,
                                             headers=self.headers,
                                             data=self.logindata,
                                             timeout=30)
        except requests.exceptions.Timeout or requests.exceptions.ReadTimeout:
            error = 'Превышено время ожидания от СЭД "Directum"'
            return error
        except requests.exceptions.ConnectionError:
            error = 'СЭД "Directum" принудительно разорвал соединение.'
            return error
        # Получаем код ответа, должен быть [Response 200]
        try:
            if (post_request.status_code == 200):
                response_data = json.loads(post_request.text)
                if (response_data['d']['Success'] == True):
                    app.logger.info(f"Авторизация [{post_request.status_code}]. ОК.")
                    return True
            else:
                app.logger.critical(f"Ошибка: Статус запроса [{post_request.status_code}]")
                return False
        except:
            app.logger.error(f"Авторизация [{post_request.status_code}]. Проблема.")
            app.logger.error(
                "Ошибка: 'Неизвестная ошибка при загрузке ответа в виде JSON.'")
            return False
        return 'Не удалось авторизоваться в СЭД "Directum"'

    def DirectumGetDocument(self, DocumentId: int, dtype: str):
        """
            Метод получения документа после авторизации по его ID,
            метод возвращает текст ошибки в случае не удачного получения
            документа.
            :param DocumentId - ID документа
            :param dtype - тип документа
            Типы документа:
            1. visual_instructions
            2. normative_documetation
            :returns Текст ошибки в случае неудачи
        """
        error = ""
        try:
            if (not os.path.exists('iMES/templates/Directum')):
                os.mkdir('iMES/templates/Directum')
            if (not os.path.exists('iMES/static/Directum')):
                os.mkdir('iMES/static/Directum')
            # Проверяем есть ли такой документ в папке Directum
            if (os.path.exists(f"iMES/templates/Directum/doc_{DocumentId}")):
                return
            else:
                # Получаем по запросу страницу предпросмотра документа
                url = f'https://dm.iplast.com/Doc.aspx?sys=DIRECTUM&ext=BaseWebAccess&ID={DocumentId}&view=Preview&VersionNum=lastver'
                post_request = self.session.post(
                    url=url, allow_redirects=True, headers=self.headers,
                    timeout=30)
                # Вытаскиваем из js кода хеш-код документа и преобразуем в словарь
                soup = BeautifulSoup(post_request.text, 'html.parser')
                request_jsscript_text = str(soup.find_all('script'))
                cut_text = (request_jsscript_text[request_jsscript_text.find(
                    "convertedObj"):].partition("selectedObj")[0])[14:-2]
                doc_data = json.loads(cut_text)
                # Проверяем тип документа, загружаем картинки и html
                if (doc_data['docExtension'] == ".png"):
                    frame_html = """"""
                    doc_html = """
                                <html>
                                    <head>
                                        <meta http-equiv="X-UA-Compatible" content="IE=edge">
                                    </head>
                                    <body>
                                """
                    # Создаём папку документа
                    os.mkdir(f"iMES/templates/Directum/doc_{DocumentId}")
                    os.mkdir(f"iMES/static/Directum/doc_{DocumentId}")
                    # Загружаем каждую страницу
                    for i in range(1, doc_data['pageCount'] + 1):
                        post_request = self.session.get(
                            url=f'https://dm.iplast.com/Preview.ashx/{doc_data["id"]}/{i}/?undefined',
                            allow_redirects=True, headers=self.headers,
                            timeout=30)
                        with open(
                                f"iMES/static/Directum/doc_{DocumentId}/{DocumentId}_{i}.png",
                                "wb") as htmldoc:
                            htmldoc.write(post_request.content)
                        if (i == 1):
                            # Создаём фрейм в котором будем отображать документ
                            if (dtype == 'visual_instructions'):
                                frame_html = f""" <link href="{{{{ url_for('static', filename='/css/bootstrap.css') }}}}" rel="stylesheet">
                                        <link rel="stylesheet" href="{{{{ url_for('static', filename='/css/style.css') }}}}">
                                        <div class="container">
                                            <div class="view-header primary">{self.DirectumGetDocumentName(DocumentId)}</div>
                                            <div class="d-flex justify-content-center">
                                                <iframe id="contentContainer" onload="autoResizeFrame(this);" name="previewFrame" frameborder="0"
                                                    class="previewContent previewContent_shown" src="/operator/visualinstructions/ddoc={DocumentId}&show"
                                                    style="height: 615px; width: 1280px"></iframe>
                                            </div>
                                            <div class="view-1">
                                                <div class="row">
                                                    <div class="col">
                                                        <button type="button" class="btn btn__menu btn__menu_wide btn__menu_height160 primary"></button>
                                                    </div>
                                                    <div class="col">
                                                        <button class="btn btn__menu btn__menu_wide btn__menu_height160 secondary"
                                                            onclick="location.href='/operator'">
                                                            Выход
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    """
                            elif dtype == "normative_documetation":
                                frame_html = f""" <link href="{{{{ url_for('static', filename='/css/bootstrap.css') }}}}" rel="stylesheet">
                                        <link rel="stylesheet" href="{{{{ url_for('static', filename='/css/style.css') }}}}">
                                        <div class="container">
                                            <div class="view-header primary">{self.DirectumGetDocumentName(DocumentId)}</div>
                                            <div class="d-flex justify-content-center">
                                                <iframe id="contentContainer" onload="autoResizeFrame(this);" name="previewFrame" frameborder="0"
                                                    class="previewContent previewContent_shown" src="/operator/visualinstructions/ddoc={DocumentId}&show"
                                                    style="height: 615px; width: 1280px"></iframe>
                                            </div>
                                            <div class="view-1">
                                                <div class="row">
                                                    <div class="col">
                                                        <button type="button" class="btn btn__menu btn__menu_wide btn__menu_height160 primary"
                                                            onclick="location.href='/NormDocumentation/Accept/id={DocumentId}'">
                                                            Ознакомиться
                                                        </button>
                                                    </div>
                                                    <div class="col">
                                                        <button class="btn btn__menu btn__menu_wide btn__menu_height160 secondary"
                                                            onclick="location.href='/NormDocumentation'">
                                                            Выход
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    """                                    
                            with open(
                                    f"iMES/templates/Directum/doc_{DocumentId}/{DocumentId}_frame.html",
                                    "w", encoding='utf-8') as htmldoc:
                                htmldoc.write(frame_html)
                        doc_html = doc_html + \
                            f'<div><img style="display: block;-webkit-user-select: none; pointer-events: none" src="{{{{ url_for("static", filename="Directum/doc_{DocumentId}/{DocumentId}_{i}.png") }}}}" initwidth="819" initheight="1171" class="previewImage" id="page_1"></div>'
                    doc_html = doc_html + "</body></html>"
                    # Создаём файл документа и прописываем туда стили
                    with open(
                            f'iMES/templates/Directum/doc_{DocumentId}/{DocumentId}.html',
                            'w', encoding='utf-8') as file:
                        file.write(
                            '<link rel="stylesheet" href="../../../static/css/directum.css">')
                    # А теперь и весь документ
                    with open(
                            f"iMES/templates/Directum/doc_{DocumentId}/{DocumentId}.html",
                            "a", encoding='utf-8') as htmldoc:
                        htmldoc.write(doc_html)
                elif (doc_data['docExtension'] == ".html"):
                    # Создаём директорию документа
                    os.mkdir(f"iMES/templates/Directum/doc_{DocumentId}")
                    os.mkdir(f"iMES/static/Directum/doc_{DocumentId}")
                    # Делаем запрос страницы предпросмотра и ищем все изображения для отображения в документе
                    post_request = self.session.get(
                        url=f'https://dm.iplast.com/Preview.ashx/{doc_data["id"]}/1/?undefined',
                        allow_redirects=True, headers=self.headers, timeout=30)
                    soup = BeautifulSoup(post_request.content, 'html.parser')
                    img_urls = []
                    # Запоминаем все url'ы изображений и пишем их в файлы
                    for img in soup.find_all("img"):
                        img_url = img.attrs.get("src")
                        if not img_url:
                            continue
                        else:
                            img_urls.append(img_url)
                    # Если количество url > 0
                    if len(img_urls) > 0:
                        os.mkdir(f"iMES/static/Directum/images")
                        # Сохраняем изображения из url адресов и пишем их в созданную директорию
                        for i in range(0, len(img_urls)):
                            post_request = self.session.get(
                                url=f'https://dm.iplast.com/Preview.ashx/{doc_data["id"]}/1/{img_urls[i]}',
                                allow_redirects=True, headers=self.headers,
                                timeout=30)
                            with open(
                                    f"iMES/static/Directum/images/{img_urls[i].replace('images/', '')}",
                                    "wb") as png:
                                png.write(post_request.content)

                    # Создаём фрейм в котором будем отображать html файл документа
                    if (dtype == 'visual_instructions'):
                        frame_html = f"""
                                        <link href="{{{{ url_for('static', filename='/css/bootstrap.css') }}}}" rel="stylesheet">
                                        <link rel="stylesheet" href="{{{{ url_for('static', filename='/css/style.css') }}}}">
                                        <div class="container">
                                            <div class="view-header primary">{self.DirectumGetDocumentName(DocumentId)}</div>
                                            <div class="d-flex justify-content-center">
                                                <iframe id="contentContainer" onload="autoResizeFrame(this);" name="previewFrame" frameborder="0"
                                                    class="previewContent previewContent_shown" src="/operator/visualinstructions/ddoc={DocumentId}&show"
                                                    style="height: 615px; width: 1280px"></iframe>
                                            </div>
                                            <div class="view-1">
                                                <div class="row">
                                                    <div class="col">
                                                        <button type="button" class="btn btn__menu btn__menu_wide btn__menu_height160 primary"></button>
                                                    </div>
                                                    <div class="col">
                                                        <button class="btn btn__menu btn__menu_wide btn__menu_height160 secondary"
                                                            onclick="location.href='/operator'">
                                                            Выход
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    """
                    elif dtype == "normative_documetation":
                        frame_html = f""" <link href="{{{{ url_for('static', filename='/css/bootstrap.css') }}}}" rel="stylesheet">
                                <link rel="stylesheet" href="{{{{ url_for('static', filename='/css/style.css') }}}}">
                                <div class="container">
                                    <div class="view-header primary">{self.DirectumGetDocumentName(DocumentId)}</div>
                                    <div class="d-flex justify-content-center">
                                        <iframe id="contentContainer" onload="autoResizeFrame(this);" name="previewFrame" frameborder="0"
                                            class="previewContent previewContent_shown" src="/operator/visualinstructions/ddoc={DocumentId}&show"
                                            style="height: 615px; width: 1280px"></iframe>
                                    </div>
                                    <div class="view-1">
                                        <div class="row">
                                            <div class="col">
                                                <button type="button" class="btn btn__menu btn__menu_wide btn__menu_height160 primary"
                                                    onclick="location.href='/NormDocumentation/Accept/id={DocumentId}'">
                                                    Ознакомиться
                                                </button>
                                            </div>
                                            <div class="col">
                                                <button class="btn btn__menu btn__menu_wide btn__menu_height160 secondary"
                                                    onclick="location.href='/NormDocumentation'">
                                                    Выход
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            """                      
                    # Аналогично пишем в файлы и прописываем стили
                    post_request = self.session.post(
                        url=f'https://dm.iplast.com/Preview.ashx/{doc_data["id"]}/1',
                        allow_redirects=True, headers=self.headers, timeout=30)
                    with open(
                            f"iMES/templates/Directum/doc_{DocumentId}/{DocumentId}_frame.html",
                            "w", encoding='utf-8') as htmldoc:
                        htmldoc.write(frame_html)
                    with open(
                            f'iMES/templates/Directum/doc_{DocumentId}/{DocumentId}.html',
                            'a') as file:
                        file.write(
                            '<link rel="stylesheet" href="../../../static/css/directum.css">')
                    with open(
                            f"iMES/templates/Directum/doc_{DocumentId}/{DocumentId}.html",
                            "ab") as htmldoc:
                        htmldoc.write(post_request.content)

        except requests.exceptions.ConnectionError:
            error = 'СЭД "Directum" принудительно разорвал соединение.'
            return error

        except:
            error = 'Во время загрузки документа произошла непредвиденная ошибка, попробуйте еще раз.'
            return error

    def DirectumGetDocumentName(self, DocumentId: int):
        """
        Метод предназначенный для получения наименования документа по его ID
        :param DocumentId: ID - документа
        :return: Наименование документа, 'Undefinded' в случае неудачи
        """
        url = f'https://dm.iplast.com/Doc.aspx?sys=DIRECTUM&ext=BaseWebAccess&ID={DocumentId}&view=Preview&VersionNum=lastver'
        post_request = self.session.post(
            url=url, allow_redirects=True, headers=self.headers, timeout=30)
        soup = BeautifulSoup(post_request.text, 'html.parser')
        find_name = soup.find('title')
        if (find_name != None):
            return find_name.text
        return "Undefinded"
