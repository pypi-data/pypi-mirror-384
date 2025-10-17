from mignonFramework import LoguruPlus, SendLog
from flask import Flask

loguru = LoguruPlus(level=LoguruPlus.INFO)
loguru.add_main_log_file("app", level=LoguruPlus.DEBUG)

log = loguru.getLogger()

app = Flask(__name__)

# 代理掉werkzeug和所有注册的logger
loguru.setUpLogger()

@SendLog(loguru.ERROR, format = loguru.console_format)
def sendMessageToAny(message):
    # 发送到邮箱什么的
    pass

@app.route('/')
def home():
    log.warning("Request received for the home page.")
    return "hello world"

if __name__ == '__main__':
    app.run(debug=False, port=12340, host='0.0.0.0')

