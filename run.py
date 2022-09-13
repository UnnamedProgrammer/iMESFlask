import importlib,os


installed = False
def Dependency_check():
    dependences = ['flask',
                   'flask_login',
                   'pyodbc',
                   'progress',
                   'flask_socketio']
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
Dependency_check()
while installed == False:
    print(installed)
    try:    
        import importlib
        from iMES import app,socketio,host,port
        from iMES.Controller.ShiftTaskDaemon import ShiftTaskDaemon
        installed = True
    except ModuleNotFoundError:
        pass
    print(installed)
    if __name__ == "__main__":
        ShiftTaskMonitoring = ShiftTaskDaemon().Start()
        socketio.run(app,host=host,port=port,debug=True)