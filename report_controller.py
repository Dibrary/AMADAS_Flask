from db_module import *
from validation_report import *
from event_report import *
from multi_validation_report import *
from all_kpi_report import *


class ReportController: # 각종 report 생성 객체와 연결하는 중간 역할.
    ana_tag: str
    user_id: str
    start_dt: str
    end_dt: str
    bottle_tag: str
    file_name: str

    def __init__(self, ana_tag, user_id, start_dt, end_dt, bottle_tag, file_name):
        self.ana_tag = ana_tag
        self.user_id = user_id
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.file_name = file_name
        self.bottle_tag = bottle_tag

        self.dbmodule = withDB()

    def error_save(self, div): # report 생성 도중에 어떤 에러가 발생하면 DB에 기록되게 함.
        db = withDB()
        if div == "VALID":
            db.insertExceptLogByTag(self.ana_tag, "validation_report")
            print("Check Validation Report Method")
        elif div == "ALARM":
            db.insertExceptLogByTag(self.ana_tag, "alarm_report")
            print("Check Alarm Report Method")
        elif div == "MAINT":
            db.insertExceptLogByTag(self.ana_tag, "maintenance_report")
            print("Check Maintenance Report Method")
        elif div == "TREND":
            db.insertExceptLogByTag(self.ana_tag, "trend_report")
            print("Check Trend Report Method")
        elif div == "ALL":
            db.insertExceptLogByTag(self.ana_tag, "all_kpi_report")
            print("Check All KPI Report Method")
        db.close()

    def validation_report(self):
        try:
            result = ''
            valid_tag = self.dbmodule.selectValidationTagByTag(self.ana_tag)
            if len(valid_tag) == 1:
                vr = Validation_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name, "Validation",
                                       self.bottle_tag)
                result = vr.make_excel_report()
            else:
                mtr = Multi_Validation_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name,
                                              "Validation", self.bottle_tag)
                result = mtr.make_excel_report()
            return result
        except Exception as e:
            self.error_save("VALID")
            return "ERROR"

    def alarm_report(self):
        try:
            result = ''
            vr = Event_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name, self.bottle_tag, "Alarm")
            result = vr.make_excel_report()
            return result
        except Exception as e:
            self.error_save("ALARM")
            return "ERROR"


    def maintenance_report(self):
        try:
            result = ''
            vr = Event_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name, self.bottle_tag, "Maintenance")
            result = vr.make_excel_report()
            return result
        except Exception as e:
            self.error_save("MAINT")
            return "ERROR"

    def trend_report(self):
        try:
            result = ''
            valid_tag = self.dbmodule.selectValidationTagByTag(self.ana_tag)
            if len(valid_tag) == 1:
                tr = Validation_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name, "Trend")
                result = tr.make_excel_report()
            else:
                mtr = Multi_Validation_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name,
                                              "Trend")
                result = mtr.make_excel_report()
            return result
        except Exception as e:
            self.error_save("TREND")
            return "ERROR"

    def all_kpi_report(self):
        try:
            result = ''
            wr = Whole_Report(self.ana_tag, self.user_id, self.start_dt, self.end_dt, self.file_name)
            result = wr.make_excel_report()
            return result
        except Exception as e:
            self.error_save("ALL")
            return "ERROR"