import requests
import json
import pyodbc

class UnloadShiftTaskFrom1C():
    """
        Класс предназначенный для выгрузки сменных заданий из 1C в базу данных iMES
        по http запросу в веб-сервис 1С
    """

    def __init__(self) -> None:
        self.connection_string = """
                                    DRIVER={ODBC Driver 18 for SQL Server};
                                    SERVER=OFC-APPSERV-13;
                                    DATABASE=MES_Iplast;
                                    UID=terminal;
                                    PWD=xAlTeS3dGrh7;
                                    TrustServerCertificate=yes;
                                """

    def GetShiftTask(self,timeshift: int, date: str):
        """
            Метод для получения сменного задания 
            params: for example int timeshift = 1,2,...;
            params: str date = "20220722";
            params: int NomenclatureGroup;
        """
        task_url = f"http://mes:4439/IplMES/hs/MES/GetProductionAssignment?Date={date}000000&Smena=Smena={str(timeshift)}"
        request = requests.get(url=task_url)
        task_data = json.loads(request.content)
        self.connection = pyodbc.connect(self.connection_string)
        cursor = self.connection.cursor()
        cursor.execute("""
                        SELECT	NG.Code,
                                Equip.Oid,
                                Equip.Name
                        FROM [MES_Iplast].[dbo].[Equipment] AS Equip,
                            [MES_Iplast].[dbo].[NomenclatureGroup] AS NG
                        WHERE NG.Oid = Equip.NomenclatureGroup AND 
                            Equip.EquipmentType = '906CC328-F2E7-47D3-B99A-B524597C998F' AND
                            NG.Oid = Equip.NomenclatureGroup
                        ORDER BY Equip.Name ASC
                      """)
        tpas = cursor.fetchall()
        tpa_dict = {} # Словарь формата: "'Номенклатурная группа': {'Oid': 'Значение','Наименование ТПА': 'Значение'}"
        for tpa in tpas:
            tpa_dict[tpa[0]] = {"Oid":tpa[1],"Name":tpa[2]}
        print(tpa_dict)
        # for task in task_data:
        #     cursor.execute(f"""INSERT INTO ShiftTask (
        #                         Shift
        #                         Equipment,
        #                         Ordinal,
        #                         Product,
        #                         Specification,
        #                         Traits,
        #                         ExtraTraints,
        #                         PackingScheme,
        #                         PackingCount,
        #                         SocketCount,
        #                         ProductCount,
        #                         Cycle,
        #                         Weight,
        #                         ProductURL,
        #                         PackingURL,
        #                     ) VALUES (
        #                         {task['Shift']},
        #                         {tpa_dict[task['oid']]['Oid']},
        #                         {}
        #                     )""" )
        

        # print(tpa_dict)

        # Shift
        # Equipment
        # Ordinal
        # Product
        # Specification
        # Traits
        # ExtraTraints
        # PackingScheme
        # PackingCount
        # SocketCount
        # ProductCount
        # Cycle
        # Weight
        # ProductURL
        # PackingURL

        


ShiftTaskObj = UnloadShiftTaskFrom1C()
ShiftTaskObj.GetShiftTask(1, '20220722')
