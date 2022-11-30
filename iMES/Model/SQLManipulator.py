import pyodbc

class SQLManipulator():
    def __init__(self) -> None:
        self.connection_string = """
            DRIVER={ODBC Driver 18 for SQL Server};
            SERVER=OFC-APPSERV-13;
            DATABASE=MES_Iplast;
            UID=terminal;
            PWD=xAlTeS3dGrh7;
            TrustServerCertificate=yes;
        """
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
            except pyodbc.ProgrammingError as Error:
                print(Error)
                break
        return result