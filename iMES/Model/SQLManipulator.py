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
        result = cursor.fetchall()
        self.connection.close()
        return result