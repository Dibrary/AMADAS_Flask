# import sys
# sys.path.append('D:\\anaconda\\envs\\mypy\\Library\\bin')


from flask import Flask, jsonify, render_template
import flask
from subprocess import call
from flask_socketio import SocketIO, send, join_room,leave_room, emit, close_room, rooms, disconnect
import time
from threading import *
from lxml import etree
import psutil # cpu 와 ram 사용률 확인 용도.

from db_module import *
from opc_controller import *
from modbus_controller import *

from Analyzer_state_module import *
from Scheduler_module import *
from LIMS_recognize_module import *
from process_controller import *
from report_controller import *
from dcs_start_controller import *
from VO.report import report
from VO.device import device
from VO.lims import LIMS

global loop_cnt, thread_cnt
loop_cnt = 10 # 무한루프 내에서 주기 변경 용.
thread_cnt = 2 # 전체 무한루프 time.sleep 시간(초단위)

# TODO 이 부분은 실제 Controller로 진입하기 전 전처리 용도.
def selector(ana_tag): # analyzer_tag정보를 토대로, DB에서 SELECT한 후, network와 taggs 정보를 반환한다.
    db = withDB()
    network = db.selectAnalyzerNetwork(ana_tag)
    taggs = db.selectAnalyzerTag(ana_tag, network)
    db.close()
    return taggs, network


def controller_selector(network, taggs, ana_tag, user_id=None): # network 정보에 따라서 Controller객체를 다르게 생성해서 반환한다.
    result = None
    if network[0] == "MODBUS":
        result = ModbusController(ana_tag, taggs, user_id) # ModbusController 인스턴스 생성하면서 파라미터 전달한다.
    elif network[0] == "OPC":
        result = OpcController(ana_tag, taggs, user_id) # OpcController 인스턴스 생성하면서 파라미터 전달한다.
    return result


def report_selector(report_data): # report_type에 따라 다른 인스턴스의 메서드로 연결해 준다.
    result = ""
    report_type = report_data.get_report_type()
    if report_type == "Validation":
        rc = ReportController(report_data)
        result = rc.validation_report()
    elif report_type == "Trend":
        rc = ReportController(report_data)
        result = rc.trend_report()
    elif report_type == "Alarm":
        rc = ReportController(report_data)
        result = rc.alarm_report()
    elif report_type == "Maintenance":
        rc = ReportController(report_data)
        result = rc.maintenance_report()
    elif report_type == "Whole":  # 전체 analyzer의 KPI에 대한 정보를 요약한 report
        rc = ReportController(report_data)
        result = rc.all_kpi_report()
    return result


app = Flask(__name__)
# app.secret_key = "mysecret"
socket_io = SocketIO(app, cors_allowed_origins="*") # cors_allowed_origins 설정을 해 줘야 CORS 위배 에러가 안 뜬다.

# TODO 이 부분 부터 실제 web 요청 매핑
@app.route("/dashboard")
def dashboard_flask(): # 단순히 memory, cpu 가용 상태 확인 할 용도. (FLASK가 제대로 동작하고 있는지도 확인할 요량)
    cpu = psutil.cpu_percent(interval=None, percpu=False)
    ram = dict(psutil.virtual_memory()._asdict())["percent"]
    return render_template("layout.html", ram=ram, cpu=cpu)


@app.route("/validation/<ana_tag>/<user_id>/<bottle_tag>")
def request_validation(ana_tag, user_id, bottle_tag): # validation request 신호를 받아서 해당 Controller로 전달한다.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK" # analyzer_tag_tb에 데이터가 등록되어있지 않은 경우
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.request_validation(bottle_tag) # 실질적으로 동작하는 인스턴스의 메서드는 request_validation이다.
    return result


@app.route("/semiauto/<ana_tag>/<user_id>")
def semi_auto_validation(ana_tag, user_id):  # semi_auto_validation 도중에, 사용자가 값을 저장하고자 할 때 누르는 버튼 받는 메서드.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.change_semi_auto_tag() # 실질적으로 동작하는 인스턴스의 메서드는 change_semi_auto_tag다.
    return result # 예외 발생시 NotOK 반환됨.


@app.route("/stop_manual_validation/<ana_tag>/<user_id>")
def stop_manual_validation(ana_tag, user_id): # manual_validation을 멈추기 위한 신호를 Controller로 전달하는 메서드다.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.stop_manual_validation() # 실질적으로 동작하는 인스턴스의 메서드는 stop_manual_validation이다.
    return result


@app.route("/maintenance/<ana_tag>/<user_id>")
def request_maintenance(ana_tag, user_id): # maintenance request신호를 Controller로 전달하는 메서드다.
    Scheduler_check()
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.request_maintenance() # 실질적으로 동작하는 인스턴스의 메서드는 request_maintenance다.
    return result # 네트워크 도중 에러가 생기면 ERROR가 반환됨.


@app.route("/smaintenance/<ana_tag>/<user_id>")
def start_maintenance(ana_tag, user_id): # start maintenance 신호를 Controller로 전달한다.
    print("start_maintenance")
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.start_maintenance() # 실질적으로 동작하는 인스턴스의 메서드는 start_maintenance다.
    return result # 네트워크 도중 에러가 생기면 ERROR 반환함.


@app.route("/stopmaintenance/<ana_tag>/<user_id>")
def stop_maintenance(ana_tag, user_id): # stop maintenance 신호를 Controller에 전달한다.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.stop_maintenance() # 실질적으로 동작하는 인스턴스의 메서드는 stop_maintenance다.
    return result # 네트워크 도중 에러가 생기면 ERROR 반환함.


@app.route("/calibration/<ana_tag>/<user_id>")
def calibration(ana_tag, user_id): # calibration신호를 Controller에 전달한다.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag, user_id)
    result = controller.calibration() # 실질적으로 동작하는 인스턴스의 메서드는 calibration이다.
    return result # 네트워크 도중 에러가 생기면 ERROR 반환함.


@app.route("/dashboardhouse")
def Allhousestate():
    pass


@app.route("/housestate/<house_tag>")
def housestate(house_tag):
    pass


@app.route("/anastate/<house_tag>")
def analyzerstate_for_house(house_tag):  # House 화면 들어갔을 때 analyzer 상태 나타냄
    db = withDB()
    values = db.selectHouseIndexAndNetwork(house_tag)
    if values == (): return "CHECK"
    network, index = values[1], values[0]
    taggs = db.selectAllAnalyzerTagByHouseIndex(index)
    db.close()

    controller = controller_selector([network], taggs, house_tag)
    result = controller.analyzer_state_for_house()
    return result # 에러 발생시 6이 반환된다

@app.route("/analyzerstate/<ana_tag>")
def analyzerstate_for_analyzer(ana_tag):  # Analyzer 화면 들어갔을 때 analyzer 상태 나타냄
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag)
    result = controller.analyzer_state_for_analyzer()
    return result

@app.route("/checkPermit/<ana_tag>")
def check_dcs_permit(ana_tag): # dcs에서 permit신호를 1로 변경 했는지를 확인한다.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag)
    result = controller.check_dcs_permit()
    return result

@app.route("/checkDcsStart/<ana_tag>")
def check_dcs_start_validation(ana_tag): # dcs_start_validation신호가 1로 되었는지를 확인한다.
    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag)
    result = controller.check_dcs_start_validation()
    return result

@app.route("/limscompare/<ana_tag>/<process_tag>/<start_dt>/<end_dt>/<lims_value>")
def lims_compare(ana_tag, process_tag, start_dt, end_dt, lims_value): # lims 결과 입력하면 이쪽으로 들어와서 비교가 수행된다. (lims_value : str)
    start_datetime = (
            end_dt[0:4] + "-" + end_dt[4:6] + "-" + end_dt[6:8] + " " +
            end_dt[8:10] + ":" + end_dt[10:12] + ":" + end_dt[12:14]
    )
    end_datetime = (
            end_dt[0:4] + "-" + end_dt[4:6] + "-" + end_dt[6:8] + " " +
            end_dt[8:10] + ":" + end_dt[10:12] + ":" + end_dt[12:14]
    )

    taggs, network = selector(ana_tag)
    if taggs == (): return "CHECK"
    controller = controller_selector(network, taggs, ana_tag)
    lims_data = LIMS(process_tag=process_tag, start_datetime=start_datetime,
                     end_datetime=end_datetime,lims_value=lims_value)
    result = controller.lims_comparison(lims_data)
    print(result, "lims compare result", type(result))
    return str(result)

@app.route('/periodchange/<no>')
def period_change(no): # 무한루프 반복 주기를 변경할 요량으로 만들어 놓음.
    try:
        global loop_cnt
        loop_cnt = no
        return "OK" # 정상으로 바뀌면 OK가 반환되게.
    except:
        return "NotOK"


@app.route("/report/<ana_tag>/<user_id>/<report_type>/<start_dt>/<end_dt>/<bottle_tag>/<file_name>")
def make_report(ana_tag, user_id, report_type, start_dt, end_dt, bottle_tag, file_name): # report를 생성하는 요청이 들어오면 여기서 정보 전달한다.
    start_datetime = (
            end_dt[0:4] + "-" + end_dt[4:6] + "-" + end_dt[6:8] + " " +
            end_dt[8:10] + ":" + end_dt[10:12] + ":" + end_dt[12:14]
    ) # 0000-00-00 00:00:00꼴
    end_datetime = (
            end_dt[0:4] + "-" + end_dt[4:6] + "-" + end_dt[6:8] + " " +
            end_dt[8:10] + ":" + end_dt[10:12] + ":" + end_dt[12:14]
    )

    report_data = report(ana_tag=ana_tag, user_id=user_id,
                         report_type=report_type, start_datetime= start_dt, end_datetime=end_dt,
                         bottle_tag=bottle_tag, file_name=file_name)
    result = report_selector(report_data)
    return result


@socket_io.on("message")
def request(message): # socket.io가 동작하는 부분으로, validation 도중에 값 전송을 담당한다.
    data = message.split("/")
    print(data, "들오나?")
    order_type, ana_tag, valve_signal, user_id, bottle_tag = (
        data[0],
        data[1],
        data[2],
        data[3],
        data[4]
    )

    print("message : " + message)
    to_client = dict()
    result = None
    taggs, network = selector(ana_tag)

    if network[0] == "MODBUS":
        mc = ModbusController(ana_tag, taggs)
        result = mc.start_Validation(valve_signal, order_type, user_id, bottle_tag)

    elif network[0] == "OPC":
        oc = OpcController(ana_tag, taggs)
        result = oc.start_Validation(valve_signal, order_type, user_id, bottle_tag)

    to_client["result"] = result
    to_client["type"] = ana_tag
    send(to_client, broadcast=True)


def realtime_infinit_loop():
    global loop_cnt
    global thread_cnt
    cnt = 1
    while thread_cnt:
        global loop_cnt
        time.sleep(1) # 1 sec interval
        Analyzer_state_logs()
        # Scheduler_check()
        Lims_trigger()
        # DCS_start_validation()
        if cnt == loop_cnt: # 80초 마다 반복.
            # Lims_db_data() # AUTO_LIMS값 읽기, LIMS DB를 IP로 찾아서 값을 받는다.
            # read_realtime_process_value() # version 4개 모두 정상동작 확인 완료.
            cnt = 0
        cnt += 1

if __name__ == "__main__":
    loop_process = Thread(target=realtime_infinit_loop, args=(), daemon=True)
    loop_process.start()
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)

