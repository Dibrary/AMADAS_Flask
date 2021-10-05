import sys, time, datetime, openpyxl
from lxml import etree

import numpy as np
import xlrd
from decimal import *

from db_module import *
from kpi_module import *
from report_abstract import *

class Whole_Report(Report):
    def __init__(self, ana_tag, user_id, start_dt, end_dt, file_name):
        self.ana_tag = ana_tag
        self.user_id = user_id
        self.div = "ALL"
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.file_name = file_name

    def kpi_chart(self, ws): # 상속받는 Report 클래스에 정의된 추상메서드를 구현한 것, (여기선 안 쓰기 때문에 pass로 막아놓음)
        pass
    def trend_chart(self, ws, length):
        pass
    def basic_inform_cell(self, ws, start_idx, end_idx, title, value, style):
        pass

    def column_cell(self, ws, div, style): # report 상단에 기본 정보를 배치한다.
        columns = ['A','B','D','E','F','G','H']
        ws.merge_cells('B7:C7')
        ws['C7'].border = style
        column_name = ['Tag','Availability','Check','Break','MTBF','MTTR','MTTF']
        width_no = [15, 9, 10, 10, 10, 10, 10]
        for i in columns:
            ws[i + '7'] = column_name[columns.index(i)]
            ws[i + '7'].font = Font(name="맑은 고딕", size=11, bold=True)
            ws[i + '7'].alignment = Alignment(horizontal='center', vertical='center')
            ws[i + '7'].border = style
            ws.column_dimensions[i].width = width_no[columns.index(i)]
        return ws

    def data_preprocess(self, data, div): # analyzer별로, KPI정보들을 리스트에 담아서 반환한다.
        # data는 추상메서드 때문에 남겨 놓은 것;
        db_module = withDB()
        analyzer_taggs = db_module.selectAllAnalyzer() # 전체 analyzer tag를 가져온다.
        db_module.close()

        availability_list, check_list, break_list = [],[],[]
        mtbf_list, mttr_list, mttf_list = [],[],[]
        for i in range(0, len(analyzer_taggs)):
            kpimodule = KPI_module(self.start_dt, self.end_dt, self.div, analyzer_taggs[i][0])
            (availability_rate, check_rate, break_rate) = kpimodule.calculate_kpi()
            (mtbf, mttr, mttf) = kpimodule.calculate_mean_break_time()
            availability_list.append(round(availability_rate,2))
            check_list.append(round(check_rate,2))
            break_list.append(round(break_rate,2))
            mtbf_list.append(round(mtbf,2))
            mttr_list.append(round(mttr,2))
            mttf_list.append(round(mttf,2))
        return (analyzer_taggs, availability_list, check_list, break_list, mtbf_list, mttr_list, mttf_list)

    def data_array(self, ws, div, datas, linestyle, fillstyle): # 실제로 table에 데이터를 넣고, 셀테두리 디자인을 설정한다.
        # 이 함수에서 datas는 추상메서드 형식을 따르느라 넣음.
        analyzer_tag, availability_list, check_list, break_list, mtbf_list, mttr_list, mttf_list = self.data_preprocess(None, self.div)
        for i in range(8, 8+len(analyzer_tag)):
            ws.merge_cells('B' + str(i) + ':C' + str(i))
            if i%2 == 0:
                ws = self.cell_method(ws, 'A' + str(i), analyzer_tag[i - 8][0], 11)
                ws = self.cell_method(ws, 'B' + str(i), availability_list[i - 8], 11)
                ws = self.cell_method(ws, 'D' + str(i), check_list[i - 8], 11)
                ws = self.cell_method(ws, 'E' + str(i), break_list[i - 8], 11)
                ws = self.cell_method(ws, 'F' + str(i), mtbf_list[i - 8], 11)
                ws = self.cell_method(ws, 'G' + str(i), mttr_list[i - 8], 11)
                ws = self.cell_method(ws, 'H' + str(i), mttf_list[i - 8], 11)
                ws['A'+str(i)].fill,ws['B'+str(i)].fill,ws['C'+str(i)].fill,ws['D'+str(i)].fill = fillstyle, fillstyle, fillstyle, fillstyle
                ws['E'+str(i)].fill,ws['F'+str(i)].fill,ws['G'+str(i)].fill,ws['H'+str(i)].fill = fillstyle, fillstyle, fillstyle, fillstyle
            else:
                ws = self.cell_method(ws, 'A' + str(i), analyzer_tag[i - 8][0], 11)
                ws = self.cell_method(ws, 'B' + str(i), availability_list[i - 8], 11)
                ws = self.cell_method(ws, 'D' + str(i), check_list[i - 8], 11)
                ws = self.cell_method(ws, 'E' + str(i), break_list[i - 8], 11)
                ws = self.cell_method(ws, 'F' + str(i), mtbf_list[i - 8], 11)
                ws = self.cell_method(ws, 'G' + str(i), mttr_list[i - 8], 11)
                ws = self.cell_method(ws, 'H' + str(i), mttf_list[i - 8], 11)
                ws['A'+str(i)].border, ws['B'+str(i)].border, ws['C'+str(i)].border, ws['D'+str(i)].border = linestyle, linestyle, linestyle, linestyle
                ws['E' + str(i)].border, ws['F' + str(i)].border, ws['G' + str(i)].border, ws['H' + str(i)].border = linestyle, linestyle, linestyle, linestyle
        return ws

    def make_excel_report(self): # 이 파일에서 실제로 동작이 들어오는 함수다. 이 위의 메서드들은 여기서 사용하는 것들.
        headerFill, header2Fill, tableFill, thin_border, top_bottom_border = self.design_for_report()

        write_wb = openpyxl.Workbook()
        ws = write_wb.active

        ws.merge_cells('A1:F4')  # title용도 병합
        ws['A1'].fill = headerFill  # 헤더 부분에 채우기색상 적용
        ws = self.title_cell(ws, self.div, "TITLE")  # 보고서 맨 상단의 header 지정

        ws.merge_cells('G1:H2')
        ws['G1'].fill = header2Fill  # 오른쪽 헤더 부분에 채우기색상2 적용
        ws = self.cell_method(ws, 'G1', 'AMADAS', 11)

        ws = self.cell_method(ws, 'G3', 'ID', 11)
        ws = self.cell_method(ws, 'H3', self.user_id, 11)

        ws = self.column_cell(ws, self.div, top_bottom_border)
        ws = self.data_array(ws, self.div, None, top_bottom_border, tableFill)
        print("ALL report 출력")
        write_wb.save(self.file_path() + self.file_name + ".xlsx")  # 최종 파일 생성
        return "OK"
