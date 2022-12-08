cd /home/imes/inet_pub/imes_pythonflask
if ! command -v pip
then
    echo "pip not installing"
    echo "trying to installing pip"
    sudo yum install python3-pip
fi
if command -v pip
then
    if ! command -v virtualenv
    then
        echo "virtualenv not installed"
        echo "Installing virtualenv"
        pip install virtualenv
    fi
    if command -v virtualenv
    then
        FILE=requirements.txt
        if ! test -f "$FILE";
        then
            echo "requirements.txt not exists in directory\n"
            echo "Creating requirements.txt file in directory\n"
            touch requirements.txt
            echo "flask" >> requirements.txt
            echo "flask_login" >> requirements.txt
            echo "pyodbc" >> requirements.txt
            echo "progress" >> requirements.txt
            echo "flask_socketio" >> requirements.txt
            echo "requests" >> requirements.txt
            echo "bs4" >> requirements.txt
            echo "eventlet==0.30.2" >> requirements.txt
            echo "gunicorn==20.1.0" >> requirements.txt
        fi
        if ! test -f "mesenv"
        then
            virtualenv -p python3.9 mesenv
        fi
        source mesenv/bin/activate
        pip install -r requirements.txt 
        gunicorn -c gunicorn.py --worker-class eventlet -w 1 run:app
    fi
fi