import subprocess

from flask import Flask, jsonify, render_template, request

from core import process_manager
from utils import get_history_state, get_lawsuit_state, get_users_submits_state, user_is_active

app = Flask(__name__)


@app.route('/')
@app.route('/index')
@app.route('/home')
def sendings_for_cession():
    """Рендер страницы с реестрами отправок
    """
    return render_template('index.html')


@app.route('/getstate', methods=['GET'])
def get_state():
    response = get_users_submits_state()
    return jsonify(response)

#TODO: добавлена проверка активности пользователя
@app.route('/startsubmit', methods=['GET'])
def start_submit():
    user=request.args.get('username')
    if user_is_active(user):
        return 'У пользователя активна подача', 400
    subprocess.Popen(
        [
            fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe",
            fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\dispatcher.py",
            "--user_name", user
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    if user_is_active(owner=user, wait_time_out=True):
        return jsonify({'success':True})
    else:
        return 'Не удалось вернуть результат, попытайтесь снова через 10 минут', 400


@app.route('/getresult', methods=['POST'])
def get_result_submit():
    lawsuit = int(request.form['lawsuitId'])
    response = get_lawsuit_state(lawsuit)
    return jsonify(response)


@app.route('/gethistory', methods=['GET'])
def get_history_submits():
    period=request.args.get('period')
    response=get_history_state(period)
    return jsonify(response)

# PARSER 

