from iMES import app
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from iMES.Model.SQLManipulator import SQLManipulator

# Метод возвращает окно наладчика


@app.route('/adjuster')
@login_required
def adjuster():
    return CheckRolesForInterface('Наладчик', 'adjuster/adjuster.html')

# Простои, неполадки и чеклисты


@app.route('/adjuster/journal')
@login_required
def adjusterJournal():
    return CheckRolesForInterface('Наладчик', 'adjuster/journal.html')

# Фиксация простоя


@app.route('/adjuster/journal/idleEnter')
@login_required
def adjusterIdleEnter():
    
    # Получение справочника причин неисправности
    sql_GetMalfunctionCause = f""" SELECT [Oid],[Name],[Status]
                                    FROM [MES_Iplast].[dbo].[MalfunctionCause] """
    malfunctionCause = SQLManipulator.SQLExecute(sql_GetMalfunctionCause)

    # Получение справочника описаний неисправности
    sql_GetMalfunctionDescription = f""" SELECT [Oid],[Name],[Status]
                                            FROM [MES_Iplast].[dbo].[MalfunctionDescription] """
    malfunctionDescription = SQLManipulator.SQLExecute(sql_GetMalfunctionDescription)
                                            
    # Получение справочника предпринятых мер
    sql_GetTakenMeasures = f""" SELECT [Oid],[Name],[Status]
                                FROM [MES_Iplast].[dbo].[TakenMeasures] """
    takenMeasures = SQLManipulator.SQLExecute(sql_GetTakenMeasures)
    
    return CheckRolesForInterface('Наладчик', 'adjuster/idles/idleEnter.html', [malfunctionCause, malfunctionDescription, takenMeasures])

# Сырье до конца выпуска


@app.route('/adjuster/RawMaterials')
@login_required
def adjusterRawMaterials():
    return CheckRolesForInterface('Наладчик', 'adjuster/rawMaterials.html')

# Фиксация отхода и брака


@app.route('/adjuster/WasteDefectFix')
@login_required
def adjusterWasteDefectFix():
    return CheckRolesForInterface('Наладчик', 'adjuster/wasteDefectFix.html')

# Сменное задание


@app.route('/adjuster/shiftTask')
@login_required
def adjusterShiftTask():
    return CheckRolesForInterface('Наладчик', 'adjuster/shiftTask.html')

# Фиксация изменений в тех. системе


@app.route('/adjuster/techSystem')
@login_required
def adjusterTechSystem():
    return CheckRolesForInterface('Наладчик', 'adjuster/techSystem.html')

# Ввод изменений в тех. системе


@app.route('/adjuster/techSystemEnter')
@login_required
def adjusterTechSystemEnter():
    return CheckRolesForInterface('Наладчик', 'adjuster/techSystemEnter.html')
