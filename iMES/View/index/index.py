import socketio
from iMES import socketio
from iMES import app
from flask import redirect, render_template, request
from flask_socketio import SocketIO, emit
from iMES.Model.UserModel import UserModel
from iMES.Model.ModelMain import ModelView
from flask_login import login_required, login_user, logout_user
from iMES import login_manager

userModel = ModelView()

@app.route("/")
def index():
    deviceTPA = userModel.GetAllTPA(request)
    tpaIndex = list(deviceTPA.keys())
    # Код закоментирован до тех пор пока не появится авторизация
    # for filename in os.listdir("iMES/templates/Directum"):
    #     shutil.rmtree('iMES/templates/Directum/'+filename)
    # for filename in os.listdir("iMES/static/Directum"):
    #     shutil.rmtree('iMES/static/Directum/'+filename)
    # try:
    #     shutil.rmtree('iMES/static/Directum/images')
    # except:
    #     pass

    return redirect(f"/tpa/{tpaIndex[0]}")

@app.route("/tpa/<string:tpaIndex>")
def mainView(tpaIndex):
    TPAList, deviceTPA = userModel.GetAllTPA(request)
    return render_template("index.html", tpaIndex = tpaIndex, TPAList = TPAList, deviceTPA = deviceTPA)

@app.route("/getTrend")
def GetTrend():
    trend = '[{ "y": "0", "x": "2022-07-01 07:01:08.637" },{ "y": "15", "x": "2022-07-01 14:00:08.570" }]'
    return trend

@app.route("/getPlan")
def GetPlan():
    plan = '[{ "y": "0", "x": "2022-07-01 07:00:00" },{ "y": "25", "x": "2022-07-01 19:00:00" }]'
    return plan

@app.route("/Auth/PassNumber=<string:passnumber>")
def Authorization(passnumber):
    user = UserModel()
    login_user(user=user)
    print(user.is_active)
    socketio.emit('AnswerAfterConnection','hello client, i give to you card: '+passnumber)
    return 'Logged'

@login_manager.user_loader
def load_user(id):
    return UserModel

@app.route('/login')
def login():
    return render_template('Show_error.html',error="Доступ запрещен, приложите ключ карту",ret='/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@socketio.on(message='connecting')
def socket_connected(data):
    pass