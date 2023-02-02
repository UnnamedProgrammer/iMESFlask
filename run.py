import importlib
import os

from iMES import app, socketio, host, port

# Точка входа в основной цикл программы
if __name__ == "__main__":
    socketio.run(app, host=host, port=port)
