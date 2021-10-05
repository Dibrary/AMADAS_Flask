import sys, time, datetime, openpyxl
from lxml import etree

import numpy as np
import xlrd
from decimal import *

from db_module import *
from kpi_module import *
from report_abstract import *

class Event_Report(Report): # alarm 및 maintenance EVENT와 관련된 정보만 excel파일로 만드는 기능
    def __init__(self, ana_tag, user_id, start_dt, end_dt, file_name, bottle_tag, div):
        self.ana_tag = ana_tag
        self.user_id = user_id
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.file_name = file_name
        self.bottle_tag = bottle_tag

        self.kpimodule = KPI_module(start_dt, end_dt, div, ana_tag)
        self.div = div

    def kpi_chart(self, ws):
        pass
    def trend_chart(self, ws, length):
        pass

    def basic_inform_cell(self, ws: object, start_idx: int, end_idx: int, title: list, value: list, style: object): # 기본 셀 작성 메서드
        if end_idx == 11:
            for i in range(start_idx, end_idx):
                ws.merge_cells('F' + str(i) + ':G' + str(i))
                ws = self.cell_method(ws, 'E' + str(i), title[i - start_idx], 10, True)
                ws = self.cell_method(ws, 'F' + str(i), value[i - start_idx], 10)
                ws['E' + str(i)].border, ws['G' + str(i)].border, ws['F' + str(i)].border = style, style, style
        else:
            for i in range(start_idx, end_idx):
                ws.merge_cells('A' + str(i) + ':B' + str(i))
                ws = self.cell_method(ws, 'A' + str(i), title[i - start_idx], 10, True)
                ws = self.cell_method(ws, 'C' + str(i), value[i - start_idx], 10)
                ws['A' + str(i)].border, ws['B' + str(i)].border, ws['C' + str(i)].border = style, style, style
        return ws

    def column_cell(self, ws, div, style): # report 상단에 위치하는 기본정보들의 column 생성 메서드
        columns = ['A','B','C','E','F']
        ws.merge_cells('C14:D14')
        ws['C14'].border, ws['D14'].border = style, style
        column_name = ['No','Event Tag','Event Date','State','ID']
        width_no = [8, 14, 14, 12, 10]
        for i in columns:
            ws[i + '14'] = column_name[columns.index(i)]
            ws[i + '14'].font = Font(name="맑은 고딕", size=11, bold=True)
            ws[i + '14'].alignment = Alignment(horizontal='center', vertical='center')
            ws[i + '14'].border = style
            ws.column_dimensions[i].width = width_no[columns.index(i)]
        return ws

    def data_preprocess(self, data, div): # event관련 데이터 불러와서 반환하는 메서드
        db_module = withDB()
        event_datas = db_module.selectEventDatasByTag(self.ana_tag, self.start_dt, self.end_dt, div)
        db_module.close()
        return event_datas

    def data_array(self, ws, div, datas, linestyle, fillstyle): # 실제로 event 데이터를 excel에 배치시키는 메서드
        datas = self.data_preprocess(None, self.div)
        for i in range(15, 15+len(datas)):
            ws.merge_cells('C' + str(i) + ':D' + str(i))
            if i%2 == 0:
                ws = self.cell_method(ws, 'A' + str(i), str(i - 15), 11)
                ws = self.cell_method(ws, 'B' + str(i), datas[i - 15][2], 11)
                ws = self.cell_method(ws, 'C' + str(i), datas[i - 15][4], 11)
                ws = self.cell_method(ws, 'E' + str(i), datas[i - 15][5], 11)
                ws = self.cell_method(ws, 'F' + str(i), datas[i - 15][6], 11)
                ws['A' + str(i)].fill, ws['B' + str(i)].fill, ws['C' + str(i)].fill = fillstyle, fillstyle, fillstyle
                ws['D' + str(i)].fill, ws['E' + str(i)].fill, ws['F' + str(i)].fill = fillstyle, fillstyle, fillstyle
            else:
                ws = self.cell_method(ws, 'A' + str(i), str(i - 15), 11)
                ws = self.cell_method(ws, 'B' + str(i), datas[i - 15][2], 11)
                ws = self.cell_method(ws, 'C' + str(i), datas[i - 15][4], 11)
                ws = self.cell_method(ws, 'E' + str(i), datas[i - 15][5], 11)
                ws = self.cell_method(ws, 'F' + str(i), datas[i - 15][6], 11)
                ws['A' + str(i)].border, ws['B' + str(i)].border, ws['C' + str(i)].border = linestyle, linestyle, linestyle
                ws['D' + str(i)].border, ws['E' + str(i)].border, ws['F' + str(i)].border = linestyle, linestyle, linestyle
        return ws

    def make_excel_report(self):
        headerFill, header2Fill, tableFill, thin_border, top_bottom_border = self.design_for_report()
        db_module = withDB()
        house_tag = db_module.selectHousetagByAnalyzertag(self.ana_tag)  # 단일 값으로 반환 된다.
        db_module.close()

        (availability_rate, check_rate, break_rate) = self.kpimodule.calculate_kpi()  # 각종 필요한 kpi요소
        if self.bottle_tag != None:
            reproducibility_rate = self.kpimodule.calculate_reproducibility(self.ana_tag, self.start_dt, self.end_dt, self.bottle_tag)  # 재현성 값
        else:  # trend의 경우에는 validation데이터가 아니므로 재현성 자체가 의미 없음.
            reproducibility_rate = 'None'
        (mtbf, mttr, mttf) = self.kpimodule.calculate_mean_break_time()  # 필요한 mtbf요소

        write_wb = openpyxl.Workbook()
        ws = write_wb.active

        ws.merge_cells('A1:E4')  # title용도 병합
        ws['A1'].fill = headerFill  # 헤더 부분에 채우기색상 적용
        ws = self.title_cell(ws, self.div, "TITLE")  # 보고서 맨 상단의 header 지정

        ws.merge_cells('F1:G2')
        ws['F1'].fill = header2Fill  # 오른쪽 헤더 부분에 채우기색상2 적용
        ws = self.cell_method(ws, 'F1', 'AMADAS', 11)

        label = ['House', 'Analyzer', 'Period Start', 'Period End', 'Operator']
        value = [house_tag, self.ana_tag, self.start_dt, self.end_dt, self.user_id]

        ws = self.basic_inform_cell(ws, 6, 11, label, value, thin_border)

        rate = ['Availability Rate', 'Checking Rate', 'Breakdown Rate', 'Reproducibility', 'MTBF', 'MTTF', 'MTTR']
        values = [round(float(availability_rate), 2), round(float(check_rate), 2), round(float(break_rate), 2),
                  round(float(reproducibility_rate), 2), round(float(mtbf), 2), round(float(mttf), 2), round(float(mttr), 2)]

        ws = self.basic_inform_cell(ws, 6, 13, rate, values, thin_border)

        ws = self.column_cell(ws, self.div, top_bottom_border)
        ws = self.data_array(ws, self.div, None, top_bottom_border, tableFill)

        print("Event report 출력")
        write_wb.save(self.file_path() + self.file_name + ".xlsx")  # 최종 파일 생성
        return "OK"


