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
            SERVER=192.168.107.43;
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
            try:
                connection = pyodbc.connect(self.connection_string)
                cursor = connection.cursor()
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
                self.app.logger.error(f"[{datetime.now()}] {error} {sqlcode}")
                break
        return result