import imp
import pyodbc
from datetime import datetime

class SQLManipulator():
    """
        Класс подключения к базе данных выполняющий передачу запроса в БД и 
        получения ответа
    """
    def __init__(self,_app) -> None:
        # Строка подключения
        self.connection_string = """
            DRIVER={ODBC Driver 18 for SQL Server};
            SERVER=OFC-APPSERV-13;
            DATABASE=MES_Iplast;
            UID=terminal;
            PWD=xAlTeS3dGrh7;
            TrustServerCertificate=yes;
        """
        self.app = _app

    # Метод отправляющий запрос на сервер БД
    @classmethod
    def SQLExecute(self,sqlcode):
        result = []
        while True:
            connection = pyodbc.connect(self.connection_string)
            cursor = connection.cursor()
            try:
                cursor.execute(sqlcode)
                try:
                    result = cursor.fetchall()
                    cursor.commit()
                    cursor.close()
                    connection.close()
                    break
                except:
                    result = []
                    cursor.commit()
                    cursor.close()
                    connection.close()
                    break
            except pyodbc.ProgrammingError as error:
                self.app.logger.warning(f"[{datetime.now()}] {error}")
                break
        return result