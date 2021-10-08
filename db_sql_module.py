
def analyzerCount():
    return "SELECT count(analyzer_tag) FROM analyzer_tb"

def houseCount():
    return "SELECT count(house_tag) FROM house_tb"

def analyzerNetwork():
    return "SELECT network FROM analyzer_tb WHERE analyzer_tag = (%s)"

def tagNoByAnaTag():
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) and network = (%s)"

def analyzerTag():
    return "SELECT * FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND network = (%s)"

def analyzerTagByTag():
    return "SELECT t.* FROM analyzer_tag_tb as t, analyzer_tb as a WHERE a.analyzer_tag = (%s) AND a.network = t.network AND a.analyzer_tag = t.analyzer_tag "

def analyzerTagByTag2():
    return "SELECT t.* FROM analyzer_tag_tb as t, analyzer_tb as a WHERE a.analyzer_tag = (%s) AND t.network = (%s) AND a.analyzer_tag = t.analyzer_tag "

def bottleValveByTag():
    return "SELECT m.valve_tag FROM analyzer_tb as a, refer_mapping_tb as m, reference_tb as r WHERE a.analyzer_tag = (%s) AND r.bottle_tag = (%s) AND m.network = (%s) AND r.no = m.reference_index"

def bottleExpire():
    return "SELECT r.expire_date FROM analyzer_tb as a, refer_mapping_tb as m, reference_tb as r WHERE m.reference_index = r.no AND a.analyzer_tag = (%s) AND a.network = m.network AND r.bottle_tag = (%s)"

def insertEventLog():
    return "INSERT INTO analyzer_event_tb(analyzer_tag_index, event_tag, event_type, event_dt, event_state, user_id) VALUES(%s, %s, %s, %s, %s, %s)"

def tagnoBymaintTag(): # 특정 event tag가 속한 row의 no가 몇 인지 찾는 쿼리문.
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND in_maintenance = (%s)"

def tagnoByalarmTag():
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND flow_low_alarm = (%s)"

def tagnoByfaultTag():
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND analyzer_fault = (%s)"

def tagnoBybreakTag():
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND in_breakdown = (%s)"

def tagnoByvalidTag():
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND in_validation = (%s)"

def tagnoBycalibTag():
    return "SELECT no FROM analyzer_tag_tb WHERE analyzer_tag = (%s) AND calibration = (%s)"

def firstSchedule():
    return "SELECT * FROM scheduler_tb ORDER BY start_time ASC limit 1"

def deleteFirstSchedule():
    return "DELETE FROM scheduler_tb ORDER BY start_time ASC limit 1"

def houseIndexAndNetwork():
    return "SELECT house_index, network FROM house_tb WHERE house_tag = (%s)"

def allAnalyzerTagByHouseIndex():
    return "SELECT t.* FROM analyzer_tb as n, analyzer_tag_tb as t WHERE n.house_index = (%s) AND n.network = t.network AND n.analyzer_tag = t.analyzer_tag"

def inValidTagByIndex():
    return "SELECT in_validation FROM analyzer_tag_tb WHERE no = (%s)"

def analyzerTypeByTag():
    return "SELECT analyzer_type FROM analyzer_tb WHERE analyzer_tag = (%s)"

def analyzerNodeByTag():
    return "SELECT v.validation_tag FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb as m, validation_tag_tb as v WHERE a.analyzer_tag = (%s) AND t.analyzer_tag = (%s) AND t.network = a.network AND t.no = m.analyzer_tag_index AND m.validation_tag_index = v.no"

def analyzerNodeByProcessTag():
    return "SELECT p.process_tag FROM analyzer_tb as a, analyzer_tag_tb as t, process_mapping_tb as m, process_tag_tb as p WHERE a.analyzer_tag = (%s) AND t.analyzer_tag = (%s) AND t.network = (%s) AND t.no = m.analyzer_tag_index AND m.process_tag_index = p.no "

def analyzerTagAndLIMS():
    return "SELECT a.analyzer_tag, a.network, t.lims_button, a.no FROM analyzer_tag_tb as t, analyzer_tb as a WHERE a.analyzer_tag = t.analyzer_tag AND a.network = t.network"

def processTagByTag():
    return " SELECT p.process_tag FROM analyzer_tb as a, analyzer_tag_tb as t, process_mapping_tb as m, process_tag_tb as p WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.no = m.analyzer_tag_index AND m.process_tag_index = p.no"

def analyzerProcessIndex():
    return "SELECT m.analyzer_tag_index, m.process_tag_index FROM analyzer_tb as a, analyzer_tag_tb as t, process_mapping_tb as m WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.no = m.analyzer_tag_index ORDER BY process_tag_index ASC"

def insertLIMSData():
    return "INSERT INTO lims_tb(analyzer_tag_index, process_tag_index, lims_value, start_time, check_time) VALUES(%s, %s, %s, %s, %s)"

def analyzerEventTag():
    return "SELECT a.network, a.no, t.address, a.analyzer_tag, t.no, t.in_maintenance, t.in_breakdown, t.in_validation, t.flow_low_alarm, t.analyzer_fault FROM analyzer_tb as a, analyzer_tag_tb as t WHERE a.analyzer_tag = t.analyzer_tag AND a.network = t.network "

def analyzerParameterByTag():
    return "SELECT * FROM analyzer_tb WHERE analyzer_tag = (%s) AND network = (%s)"

def componentParameterByTag():
    return "SELECT v.validation_tag, b.reference_value, b.wl, b.cl, b.upper, b.lower, b.unit FROM analyzer_tb as a, analyzer_tag_tb as g, reference_tb as r, component_mapping_tb as b, component_tb c, validation_mapping_tb as t, validation_tag_tb as v, tag_component_mapping_tb as p WHERE a.analyzer_tag = (%s) AND r.bottle_tag = (%s) AND r.no = b.reference_index AND a.analyzer_tag = g.analyzer_tag AND a.network = g.network AND g.no = t.analyzer_tag_index AND t.validation_tag_index = v.no AND v.no = p.validation_tag_index AND p.component_index = c.no AND c.no = b.component_index"

def componentParameterByTag2():
    return "SELECT v.validation_tag, b.reference_value, b.wl, b.cl, b.upper, b.lower, b.unit FROM analyzer_tb as a, analyzer_tag_tb as g, reference_tb as r, component_mapping_tb as b, component_tb c, validation_mapping_tb as t, validation_tag_tb as v, tag_component_mapping_tb as p WHERE a.analyzer_tag = (%s) AND r.bottle_tag = (%s) AND r.no = b.reference_index AND a.analyzer_tag = g.analyzer_tag AND g.network = (%s) AND g.no = t.analyzer_tag_index AND t.validation_tag_index = v.no AND v.no = p.validation_tag_index AND p.component_index = c.no AND c.no = b.component_index"

def validationTagByTag():
    return "SELECT v.validation_tag FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb m, validation_tag_tb as v WHERE a.analyzer_tag =(%s) AND a.network = t.network AND a.analyzer_tag = t.analyzer_tag AND t.no = m.analyzer_tag_index AND m.validation_tag_index = v.no"

def validationTagByTag2():
    return "SELECT v.validation_tag FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb m, validation_tag_tb as v WHERE a.analyzer_tag =(%s) AND t.network=(%s) AND a.analyzer_tag = t.analyzer_tag AND t.no = m.analyzer_tag_index AND m.validation_tag_index = v.no"

def validationTagIndexByTag():
    return "SELECT m.analyzer_tag_index, m.validation_tag_index FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb as m, validation_tag_tb as v WHERE a.analyzer_tag = (%s) AND t.network = (%s) AND a.analyzer_tag = t.analyzer_tag AND t.no = m.analyzer_tag_index AND v.validation_tag = (%s) AND v.no = m.validation_tag_index"

def bottleIndexByTag():
    return "SELECT no FROM reference_tb WHERE bottle_tag = (%s)"

def insertValidationData():
    return "INSERT INTO validation_tb(analyzer_tag_index, reference_index, validation_tag_index, validation_type, validation_value, start_time, check_time, result, user_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"

def houseTagByAnalyzerTag():
    return "SELECT h.house_tag FROM house_tb as h, analyzer_tb as a WHERE a.analyzer_tag = (%s) AND a.house_index = h.house_index"

def validation_data_for_report():
    return "SELECT b.validation_tag, v.validation_type, v.validation_value, v.start_time, v.check_time, v.result, v.user_id FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb as m, validation_tag_tb as b, validation_tb as v WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.no = m.analyzer_tag_index AND m.validation_tag_index = b.no AND v.analyzer_tag_index = m.analyzer_tag_index AND v.validation_tag_index = m.validation_tag_index AND v.start_time >= (%s) AND v.start_time <= (%s) ORDER BY v.start_time ASC, v.check_time ASC"

def trend_data_for_report():
    return "SELECT p.no, b.process_tag, p.process_value, p.check_time FROM analyzer_tb as a, analyzer_tag_tb as t, process_mapping_tb as m, process_tag_tb as b, process_tb as p WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.no = m.analyzer_tag_index AND m.process_tag_index = b.no AND p.analyzer_tag_index = m.analyzer_tag_index AND p.process_tag_index = m.process_tag_index AND p.check_time >= (%s) AND p.check_time <= (%s) order by check_time ASC"

def maintenance_data_for_report():
    return "SELECT t.analyzer_tag, e.event_tag, e.event_type, e.event_dt, e.event_state, e.user_id FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.in_maintenance = e.event_tag AND e.event_dt >= (%s) AND e.event_dt <= (%s)"

def alarm_data_for_report():
    return "SELECT t.analyzer_tag, e.event_tag, e.event_type, e.event_dt, e.event_state, e.user_id FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.flow_low_alarm = e.event_tag AND e.event_dt >= (%s) AND e.event_dt <= (%s)"

def breakdown_data_for_kpi():
    return "SELECT t.analyzer_tag, e.event_tag, e.event_type, e.event_dt, e.event_state, e.user_id FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.in_breakdown = e.event_tag AND e.event_dt >= (%s) AND e.event_dt <= (%s)"

def check_data_for_kpi():
    return "SELECT t.analyzer_tag, e.event_tag, e.event_type, e.event_dt, e.event_state, e.user_id FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.in_validation = e.event_tag AND e.event_dt >= (%s) AND e.event_dt <= (%s)"

def whole_data_for_report():
    return "SELECT e.no, a.analyzer_tag, e.event_tag, e.event_type, e.event_dt, e.event_state, e.user_id FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.no = e.analyzer_tag_index AND e.event_dt >= (%s) AND e.event_dt <= (%s) ORDER BY e.no ASC"

def ptmrDataByTag():
    return "SELECT v.validation_tag, p.count, p.mean_value, p.deviation FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb as m, ptmr_tb as p, validation_tag_tb as v WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND a.no = m.analyzer_tag_index AND m.analyzer_tag_index = p.analyzer_tag_index AND m.validation_tag_index = p.validation_tag_index AND v.no = m.validation_tag_index"

def multiPtmrDataByTag():
    return "SELECT p.reference_index, v.validation_tag, p.count, p.mean_value, p.deviation FROM analyzer_tb as a, analyzer_tag_tb as t, validation_mapping_tb as m, ptmr_tb as p, validation_tag_tb as v,reference_tb as r WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND t.no = m.analyzer_tag_index AND m.analyzer_tag_index = p.analyzer_tag_index AND m.validation_tag_index = p.validation_tag_index AND m.validation_tag_index = v.no AND r.bottle_tag = (%s) AND r.no = p.reference_index"

def processByBetweenDate():
    return "SELECT b.process_tag, p.process_value FROM analyzer_tb as a, analyzer_tag_tb as t, process_mapping_tb as m, process_tag_tb as b, process_tb as p WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network AND a.no = m.analyzer_tag_index AND m.process_tag_index = b.no AND p.analyzer_tag_index = a.no AND p.process_tag_index = m.process_tag_index AND b.process_tag = (%s) AND p.check_time >= (%s) AND p.check_time <= (%s)"

def analyzerTagIndexByTag():
    return "SELECT t.no FROM analyzer_tb as a, analyzer_tag_tb as t WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND a.network = t.network"

def analyzerTagIndexModbusByTag():
    return "SELECT t.no FROM analyzer_tb as a, analyzer_tag_tb as t WHERE a.analyzer_tag = (%s) AND a.analyzer_tag = t.analyzer_tag AND t.network = (%s)"

def processTagIndexByProcessTag():
    return "SELECT p.no FROM process_mapping_tb as m, process_tag_tb as p WHERE m.analyzer_tag_index = (%s) AND m.process_tag_index = p.no AND p.process_tag = (%s)"

def insertLimsData():
    return "INSERT INTO lims_tb(analyzer_tag_index, process_tag_index, lims_value, start_time, check_time, result) VALUES(%s, %s, %s, %s, %s, %s) "

def manualValidationData():
    return "SELECT * FROM validation_tb WHERE check_time >= (%s) AND analyzer_tag_index = (%s) AND user_id = (%s) "

def updateValidationResult():
    return "UPDATE validation_tb SET result=(%s) WHERE start_time >= (%s)"

def selectAllAnalyzer():
    return "SELECT * FROM analyzer_tb"

def insertProcessDataRealtime():
    return "INSERT INTO process_tb(process_tag_index, analyzer_tag_index, process_value, check_time) VALUES(%s, %s, %s, %s)"

def analyzerNoByTag():
    return "SELECT * FROM analyzer_tb WHERE analyzer_tag = (%s)"

def defaultValveByTag():
    return "SELECT m.valve_pulse FROM refer_mapping_tb as m, reference_tb as r WHERE m.analyzer_tag = (%s) AND m.default = 1 AND m.reference_index = r.no"

def defaultBottleTagByTag():
    return "SELECT r.bottle_tag FROM refer_mapping_tb as m, reference_tb as r WHERE m.analyzer_tag = (%s) AND m.default = 1 AND m.reference_index = r.no"

def defaultValidationTypeByTag():
    return "SELECT validation_type FROM analyzer_tb WHERE analyzer_tag = (%s)"

def eventAlarmDatasByTag():
    return "SELECT e.* FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = (%s) AND  a.analyzer_tag = t.analyzer_tag AND t.no = e.analyzer_tag_index AND event_dt >= (%s)  AND event_dt <= (%s) AND event_type ='ALARM' ORDER BY e.event_dt ASC"

def eventMaintDatasByTag():
    return "SELECT e.* FROM analyzer_tb as a, analyzer_tag_tb as t, analyzer_event_tb as e WHERE a.analyzer_tag = (%s) AND  a.analyzer_tag = t.analyzer_tag AND t.no = e.analyzer_tag_index AND event_dt >= (%s)  AND event_dt <= (%s) AND event_type ='MAINT' ORDER BY e.event_dt ASC"

def insertExceptLogByTag():
    return "INSERT INTO fail_log_tb(object_tag, method_name, check_date) VALUES(%s, %s, %s)"

