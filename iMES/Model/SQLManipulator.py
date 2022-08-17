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
        self.connection = pyodbc.connect(self.connection_string)
        cursor = self.connection.cursor()
        cursor.execute(sqlcode)
        try:
            result = cursor.fetchall()
            cursor.commit()
            self.connection.close()
        except pyodbc.ProgrammingError:
            cursor.commit()
            self.connection.close() 
            return 'Результат пуст'
        return result