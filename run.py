import importlib
import os


def Dependency_check():
    dependences = ['flask',
                   'flask_login',
                   'pyodbc',
                   'progress',
                   'flask_socketio',
                   'simple-websocket',
                   'requests',
                   'bs4']
    not_install = []
    for dependency in dependences:
        try:
            check_module = importlib.import_module(dependency)
        except ModuleNotFoundError:
            not_install.append(dependency)
    if(len(not_install) > 0):
        install_str = "pip install"
        for module in not_install:
            install_str = f"{install_str} {module}"
        try:
            os.system(install_str)
        except:
            pass


while True:
    try:
        from iMES import app, socketio, host, port
        import simple_websocket
        break
    except ModuleNotFoundError:
        Dependency_check()
if __name__ == "__main__":
    from iMES.Controller.ShiftTaskDaemon import ShiftTaskDaemon
    from iMES.Controller.ProductionDataDaemon import ProductionDataDaemon
    ShiftTaskMonitoring = ShiftTaskDaemon()
    ShiftTaskMonitoring.Start()
    ProductDataMonitoring = ProductionDataDaemon()
    ProductDataMonitoring.Start()
    socketio.run(app, host=host, port=port, debug=True, use_reloader=False)
