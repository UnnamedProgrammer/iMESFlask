import pyodbc



class SQLManipulator():
    @classmethod
    def SQLExecute(self,sqlcode):
        self.connection_string = """
            DRIVER={ODBC Driver 18 for SQL Server};
            SERVER=OFC-APPSERV-13;
            DATABASE=MES_Iplast;
            UID=terminal;
            PWD=xAlTeS3dGrh7;
            TrustServerCertificate=yes;
            """
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
            except pyodbc.ProgrammingError:
                continue
        return result