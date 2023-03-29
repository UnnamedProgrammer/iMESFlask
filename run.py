from iMES import app, socketio, host, port, TpaList
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
    for ip in tqdm(TpaList.keys()):
        for tpa in TpaList[ip]:
            tpa[2].Check_Downtime(tpa[0])
            tpa[2].update_pressform()
            tpa[2].data_from_shifttask()
    app.logger.info(f"[{datetime.now()}] Запуск диспетчера по обновлению оборудования.")
    iMES.daemons.UpdateTpaThread.start()
    app.logger.info(f"[{datetime.now()}] Запуск сервера.")
    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)
