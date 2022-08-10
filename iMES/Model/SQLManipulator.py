import pyodbc



class SQLManipulator():
    def __init__(self) -> None:
        self.connection_string = """
            'EAM_Iplast': 'DRIVER={ODBC Driver 18 for SQL Server};
            SERVER=WORK2-APPSERV-8;
            DATABASE=EAM_Iplast;
            UID=terminal;
            PWD=xAlTeS3dGrh7;
            TrustServerCertificate=yes'
            """
        self.connection = pyodbc.connect(self.connection_string)

    def SQLExecute(self,sqlcode: str):
        self.connection.execute(sqlcode)
        return self.connection.fetchall()