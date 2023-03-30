from iMES import app, socketio, host, port, TpaList, tpasresultapi
import iMES.daemons
from datetime import datetime
from tqdm import tqdm
from iMES.daemons import ProductDataMonitoring
# Точка входа в основной цикл программы
if __name__ == "__main__":
    app.logger.info(f"[{datetime.now()}] Запуск диспетчера сменных заданий.")
    ProductDataMonitoring.OnceMonitoring()
    iMES.daemons.ProductDataMonitoring.Start()
    app.logger.info(f"[{datetime.now()}] Запуск мониторинга сменных заданий.")
    iMES.daemons.ShiftTaskMonitoring.Start()
    app.logger.info(f"[{datetime.now()}] Обновление информации по оборудованию.")
    for tpa in tqdm(TpaList):
        tpa[2].Check_Downtime(tpa[0])
        tpa[2].update_pressform()
        tpa[2].data_from_shifttask()
    app.logger.info(f"[{datetime.now()}] Обновление информации по оборудованию для API.")
    for tpa in tqdm(tpasresultapi):
            tpa[2].Check_Downtime(tpa[0])
            tpa[2].update_pressform()
            tpa[2].data_from_shifttask()
    app.logger.info(f"[{datetime.now()}] Запуск диспетчера по обновлению оборудования.")
    iMES.daemons.UpdateTpaThread.start()
    iMES.daemons.UpdateMESNSThread.start()
    app.logger.info(f"[{datetime.now()}] Запуск сервера.")
    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)
