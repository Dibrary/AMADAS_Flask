from lxml import etree
import datetime, time
from decimal import *
import numpy as np
import random

from db_module import *


class KPI_module:
    start_dt: str
    end_dt: str
    div: str
    ana_tag: str
    dbmodule: object

    def __init__(self, start_dt, end_dt, div, ana_tag=None):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.div = div
        self.ana_tag = ana_tag
        self.dbmodule = withDB()

    def server_start_time(self): # xml파일에 기록되어 있는 server_start 시작일자시간 정보를 반환한다.
        root = (etree.parse("opc_modbus_db_ip.xml")).getroot()
        for i in root.iter("server"):  # XML 파일에서 url 찾는 코드.
            server_start_dt = i.findtext("start")
        return server_start_dt

    def total_second_method(self, sdt: str):  # 지금 - 서버시작시간을 초로 계산해줌. (total second값)
        now = datetime.datetime.now()  # KPI를 계산하는 지금 시점의 시간.
        server_total_dt = datetime.datetime.strptime(sdt, "%Y-%m-%d %H:%M:%S")
        total_time = (now - server_total_dt)  # 서버 의 총 시간(datetime 단위)
        total_seconds = round(total_time.microseconds / float(1000000)) + (
                    total_time.seconds + total_time.days * 24 * 3600)  # 서버의 총 시간(초 단위)
        return total_seconds

    def kpi_pairing_method(self, row_data: list, ana_tag: str, idx: int):  # 만일 event데이터가 홀수 개라면, OFF를 추가해서 짝을 맞춰준다.
        if row_data == None:
            pass
        else:
            if len(row_data) % 2 == 1:
                if idx == 1:
                    row_data.append((ana_tag, "LastTag", 'ALARM', datetime.datetime.now(), 'STOP', 'AUTO'))
                elif idx == 2:
                    row_data.append((ana_tag, "LastTag", 'BREAK', datetime.datetime.now(), 'STOP', 'AUTO'))
                elif idx == 3:
                    row_data.append((ana_tag, "LastTag", 'VALID', datetime.datetime.now(), 'STOP', 'AUTO'))
                elif idx == 4:
                    row_data.append((ana_tag, "LastTag", 'MAINT', datetime.datetime.now(), 'STOP', 'AUTO'))
        return row_data

    def kpi_sum_seconds(self, values: list, idx: int):  # 리스트의 데이터 중, 시간만을 이용해서 총 합계'초' 단위를 반환한다.
        if values == None:
            pass
            return 0
        else:
            sum_value = 0  # initial value
            for i in idx:
                first_event_time_value = values[i][3]
                second_event_time_value = values[i + 1][3]
                sub1 = (second_event_time_value - first_event_time_value)
                res1 = round(sub1.microseconds / float(1000000)) + (sub1.seconds + sub1.days * 24 * 3600)
                sum_value += res1
            return sum_value

    def calculate_kpi(self):
        sdt = self.server_start_time()  # 서버 시작시간 (문자열)
        total_seconds = self.total_second_method(sdt)

        alarm_row_data = self.dbmodule.dataForReport(self.start_dt, self.end_dt, "Alarm", self.ana_tag)
        break_row_data = self.dbmodule.dataForReport(self.start_dt, self.end_dt, "Breakdown", self.ana_tag)
        valid_row_data = self.dbmodule.dataForReport(self.start_dt, self.end_dt, "Check", self.ana_tag)
        maint_row_data = self.dbmodule.dataForReport(self.start_dt, self.end_dt, "Maintenance", self.ana_tag)

        alarm_data = self.kpi_pairing_method(alarm_row_data, self.ana_tag, 1)
        break_data = self.kpi_pairing_method(break_row_data, self.ana_tag, 2)
        valid_data = self.kpi_pairing_method(valid_row_data, self.ana_tag, 3)
        maint_data = self.kpi_pairing_method(maint_row_data, self.ana_tag, 4)

        alarm_idx, valid_idx, maint_idx, break_idx = [], [], [], []
        idx = [alarm_idx, valid_idx, maint_idx, break_idx]
        values = [alarm_data, valid_data, maint_data, break_data]

        for index, value in enumerate(values):
            if value == None:
                pass
            else:
                for values_idx, k in enumerate(value): # index와 값으로 반복문을 돈다.
                    for idx_idx, i in enumerate(idx):
                        if values_idx == idx_idx:
                            if k[4] == 'START':
                                idx[index].append(values_idx)
                            else:
                                pass
        alarm_second_sum, valid_second_sum, maint_second_sum, break_second_sum = 0, 0, 0, 0  # initial value
        alarm_second_sum = self.kpi_sum_seconds(alarm_data, alarm_idx)
        valid_second_sum = self.kpi_sum_seconds(valid_data, valid_idx)
        maint_second_sum = self.kpi_sum_seconds(maint_data, maint_idx)
        break_second_sum = self.kpi_sum_seconds(break_data, break_idx)  # 구간의 시간을 모두 초로 바꾼 값들. (3600으로 나누면 시간이 나온다)

        availability_rate = ((total_seconds - break_second_sum - valid_second_sum - maint_second_sum) / total_seconds) * 100
        check_rate = ((valid_second_sum + maint_second_sum) / (total_seconds - break_second_sum)) * 100
        break_rate = (break_second_sum / (total_seconds - valid_second_sum - maint_second_sum)) * 100
        return (availability_rate, check_rate, break_rate)

    def calculate_reproducibility(self, ana_tag, start_dt, end_dt, bottle_tag=None): # 재현성계산
        validation_tag = self.dbmodule.selectValidationTagByTag(ana_tag)
        component = self.dbmodule.selectComponentParameterByTag(ana_tag, bottle_tag)  # wl, cl 같은 값들 //
        reproducibility = 0

        if len(validation_tag) == 1:
            ptmr_data = self.dbmodule.selectPtmrDataByTag(
                ana_tag)  # (('1630AI155A-VV', 13, Decimal('5.50'), Decimal('1.30')),) 이렇게 들어옴.
            datas = self.dbmodule.dataForReport(start_dt, end_dt, "Validation", ana_tag)
            total_value, reference_value = [], []
            aim, wl = ptmr_data[0][2], ptmr_data[0][3]

            for i in range(0, len(datas)):
                total_value.append(round(float(datas[i][2]), 2))
            for j in range(0, len(datas)):
                reference_value.append((random.uniform((float(aim) - ((float(aim) * (float(wl) / 100)) / 2)),
                                                       (float(aim) + ((float(aim) * (float(wl) / 100)) / 2)))))
            total_std = np.std(total_value) # 표준편차.
            reference_std = np.std(reference_value) # 참조값 표준편차
            if total_std > reference_std:
                reproducibility += (100 - (reference_std / total_std) * 100)
            else:
                reproducibility += (100 - (total_std / reference_std) * 100)
        else:
            datas = self.dbmodule.dataForReport(start_dt, end_dt, "Validation", ana_tag)
            ptmr_data = self.dbmodule.selectMultiPtmrDataByTag(ana_tag, bottle_tag)
            aim, wl, reference_value, validation_value = [], [], [], []
            for i in range(0, len(ptmr_data)):
                aim.append(float(ptmr_data[i][3]))
                wl.append(float(ptmr_data[i][4]))
                reference_value.append([])
                validation_value.append([])
            count = 0
            for k in range(0, len(datas)):
                if datas[k][0] == component[0][0]:  # 첫 번째 노드만을 통해 각 노드별 데이터 갯수를 확인한다.
                    count += 1
                else:
                    pass
            # count = 3일 것.

            for m in range(0, count):  # 측정 데이터 갯수 만큼 reference_value 넣음.
                for k in range(0, len(aim)):
                    reference_value[k].append((random.uniform(
                        (float(aim[k]) - ((float(aim[k]) * (float(wl[k]) / 100)) / 2)),
                        (float(aim[k]) + ((float(aim[k]) * (float(wl[k]) / 100)) / 2)))))
            for i in range(0, len(datas)):
                for k in range(0, len(component)):
                    if datas[i][0] == component[k][0]:
                        validation_value[k].append(float(datas[i][2]))
                    else:
                        pass
            result = []
            for d in range(0, len(reference_value)):
                if np.std(validation_value[d]) > np.std(reference_value[d]):
                    result.append(100 - ((np.std(reference_value[d]) / (np.std(validation_value[d]))) * 100))
                else:
                    result.append(100 - ((np.std(validation_value[d]) / (np.std(reference_value[d]))) * 100))
            reproducibility = np.mean(result)
        return reproducibility

    def calculate_mttf_mttr(self, total_seconds: int, value: list, on_idx: list, off_idx: list, tag: str = None): # MTTF, MTTR 계산
        sum_value = 0  # initial value
        if value == 0:
            mttr = 0
            mttf = (total_seconds / 3600)
            return (mttf, mttr)
        if tag == None:
            for i, j in zip(on_idx, off_idx):
                first_event_time_value = value[i][4]
                second_event_time_value = value[j][4]
                sub1 = (second_event_time_value - first_event_time_value)
                res1 = round(sub1.microseconds / float(1000000)) + (sub1.seconds + sub1.days * 24 * 3600)
                sum_value += res1
            mttf = (((total_seconds - sum_value) / 3600) / (len(on_idx) - 1))
            mttr = ((sum_value / 3600) / len(on_idx))

        elif tag == 'reverse':
            for i, j in zip(off_idx, on_idx):
                first_event_time_value = value[i][4]
                second_event_time_value = value[j][4]
                sub1 = (second_event_time_value - first_event_time_value)
                res1 = round(sub1.microseconds / float(1000000)) + (sub1.seconds + sub1.days * 24 * 3600)
                sum_value += res1
            mttf = ((sum_value / 3600) / (len(on_idx)))
            mttr = (((total_seconds - sum_value) / 3600) / len(on_idx) - 1)

        return (mttf, mttr)

    def calculate_mean_break_time(self):  # MTBF, MTTF, MTTR을 모두 계산한다.
        sdt = self.server_start_time()  # 서버 시작시간 (문자열)
        total_seconds = self.total_second_method(sdt)
        total_hour = total_seconds / 3600  # 시간으로 변환

        break_row_data = self.dbmodule.dataForReport(self.start_dt, self.end_dt, "Breakdown", self.ana_tag)
        break_data = self.kpi_pairing_method(break_row_data, self.ana_tag, 2)  # 짝수개를 맞춰 주는 것이다.
        break_on_idx = []  # initial list
        break_off_idx = []

        tag = None

        if break_data == None:
            break_data = 0
        else:
            for values_idx, k in enumerate(break_data):
                for idx_idx, i in enumerate(break_on_idx):
                    if values_idx == 0:
                        if k[4] == 'START':
                            i.append(values_idx)
                        else:
                            break_off_idx.append(values_idx)
                            tag = 'reverse'
                    else:
                        if k[4] == 'START':
                            i.append(values_idx)  # break_idx에는 ON인 경우만 들어간다.
                        else:
                            break_off_idx.append(values_idx)

        mttf, mttr = self.calculate_mttf_mttr(total_seconds, break_data, break_on_idx, break_off_idx, tag)
        mtbf = (mttr + mttf)
        return (mtbf, mttr, mttf)