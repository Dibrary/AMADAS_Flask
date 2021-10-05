
import scipy.stats
import numpy as np
from decimal import *
import random
import copy
import datetime, time
import math

from db_module import *

q90 = [0.941, 0.765, 0.642, 0.56, 0.507, 0.468, 0.437, 0.412, 0.392, 0.376, 0.361, 0.349, 0.338, 0.329,
       0.32, 0.313, 0.306, 0.3, 0.295, 0.29, 0.285, 0.281, 0.277, 0.273, 0.269, 0.266, 0.263, 0.26]
q95 = [0.97, 0.829, 0.71, 0.625, 0.568, 0.526, 0.493, 0.466, 0.444, 0.426, 0.41, 0.396, 0.384, 0.374, 0.365, 0.356,
       0.349, 0.342, 0.337, 0.331, 0.326, 0.321, 0.317, 0.312, 0.308, 0.305, 0.301, 0.29] # 95%
q99 = [0.994, 0.926, 0.821, 0.74, 0.68, 0.634, 0.598, 0.568, 0.542, 0.522, 0.503, 0.488, 0.475, 0.463, 0.452, 0.442,
       0.433, 0.425, 0.418, 0.411, 0.404, 0.399, 0.393, 0.388, 0.384, 0.38, 0.376, 0.372] # 99%

Q90 = {n:q for n,q in zip(range(3,len(q90)+1), q90)}
Q95 = {n:q for n,q in zip(range(3,len(q95)+1), q95)}
Q99 = {n:q for n,q in zip(range(3,len(q99)+1), q99)}

t_values = [4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262]
chi2_values = [5.99, 7.82, 9.49, 11.07, 12.59, 14.07, 15.51, 16.92]
f_values = [9.28, 6.39, 5.05, 4.28, 3.79, 3.44, 3.18, 2.98]

def dixon_test(data:list, left:float=True, right:float=True, q_dict=Q95):

    assert(left or right), 'At least one of the variables, `left` or `right`, must be True.'
#     assert(len(data) >= 3), 'At least 3 data points are required'
    assert(len(data) <= max(q_dict.keys())), 'Sample size too large'

    sdata = sorted(data) # 관측치 오름차순으로 정렬.
    Q_mindiff, Q_maxdiff = (0,0), (0,0)

    # Q값 계산.
    if left:
        Q_min = (sdata[1] - sdata[0])
        try:
            Q_min /= (sdata[-1] - sdata[0])
        except ZeroDivisionError:
            pass
        Q_mindiff = (Q_min - q_dict[len(data)], sdata[0])

    if right:
        Q_max = abs((sdata[-2] - sdata[-1]))
        try:
            Q_max /= abs((sdata[0] - sdata[-1]))
        except ZeroDivisionError:
            pass
        Q_maxdiff = (Q_max - q_dict[len(data)], sdata[-1])

    if not Q_mindiff[0] > 0 and not Q_maxdiff[0] > 0:
        outliers = [None, None]

    elif Q_mindiff[0] == Q_maxdiff[0]:
        outliers = [Q_mindiff[1], Q_maxdiff[1]]

    elif Q_mindiff[0] > Q_maxdiff[0]:
        outliers = [Q_mindiff[1], None]

    else:
        outliers = [None, Q_maxdiff[1]]

    return outliers

def Anderson_pvalue(Value:float):
    AD = Value*(1 + (.75/50) + 2.25/(50**2))
#     print("Adjusted A^2 = ", AD)
    if AD >= .6:
        p = math.exp(1.2937 - 5.709*AD - .0186*(AD**2))
    elif AD >=.34:
        p = math.exp(.9177 - 4.279*AD - 1.38*(AD**2))
    elif AD >.2:
        p = 1 - math.exp(-8.318 + 42.796*AD - 59.938*(AD**2))
    else:
        p = 1 - math.exp(-13.436 + 101.14*AD - 223.73*(AD**2))
#     print("p = ", p) # 해당 통계치를 P-value로 환산 한 코드.
    return p


class LIMS_statistics:
    def __init__(self, ana_tag: str, process_tag: str, start_dt: str, end_dt: str, lims_value,
                 process_values: tuple):
        self.ana_tag = ana_tag
        self.process_tag = process_tag
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.lims_value = lims_value
        self.process_values = process_values

    def single_lims_compare(self):
        total_process_value = []
        for i in range(0, len(self.process_values)):
            total_process_value.append(float(self.process_values[i][1]))

        process_AVG = np.mean(total_process_value)
        print(total_process_value, "토탈 프로세스 값.")

        result = float(self.lims_value) - process_AVG
        return round(result, 2)


class Analysis_of_Variance:
    def __init__(self, ana_tag, validation_tag, validation_type, validation_value, start_time, check_time, component,
                 bottle_tag, user_id=None):
        self.ana_tag = ana_tag
        self.validation_tag = validation_tag
        self.validation_type = validation_type
        self.validation_value = validation_value
        self.start_time = start_time
        self.check_time = check_time
        self.component = component
        self.bottle_tag = bottle_tag
        self.user_id = user_id

    def singl_AD_check(self): # Anderson Darling test 한다.
        print(self.validation_value, "AD 가기 전")
        try:
            AD_value = scipy.stats.anderson(self.validation_value)
        except:
            AD_value = 0.05
        return AD_value

    def singl_dixon_test_method(self): # Dixon Q test를 한다.
        results = copy.deepcopy(self.validation_value)
        dixon_result = dixon_test(results)
        while 1:
            if len(results) < 3:
                break
            else:
                dixon_result = dixon_test(results)
                if ((dixon_result[0] == None) and (dixon_result[1] == None)):
                    break
                else:
                    results.remove(dixon_result[1]) if dixon_result[0] == None else results.remove(dixon_result[0])
        return results

    def singl_dixon_conditional_sentence(self, result): # Dixon Q test 결과를 걸러낸다.
        bool_result = None
        if ((result == []) or
                (result == [0, 0]) or
                (result == [0, 0, 0]) or
                (result == [0, 0, 0, 0]) or
                (result == [0, 0, 0, 0, 0]) or
                (result == [0, 0, 0, 0, 0, 0]) or
                (result == [0, 0, 0, 0, 0, 0, 0]) or
                (result == [0, 0, 0, 0, 0, 0, 0, 0]) or
                (result == [0, 0, 0, 0, 0, 0, 0, 0, 0]) or
                (len(result) <= 2)):
            bool_result = False # 위의 조건에 하나라도 해당이 되면 Dixon-Q test에서 통과하지 못한 것.
        else:
            bool_result = True
        return bool_result


    def singl_make_random_aim_values(self, aim, wl, cl): # reference_value(aim_value)에 대해 random값을 만든다. (분포를 생성)
        aim_values = []
        for i in range(0, len(self.validation_value)):
            aim_values.append(random.uniform((float(aim) - ((float(aim) * (float(wl) / 100)) / 2)),
                                             (float(aim) + ((float(aim) * (float(wl) / 100)) / 2))))
            # aim-(aim*wl%) 부터 aim+(aim*wl%) 까지의 범위로 random값이 aim_values에 들어가게 한다.
        return aim_values

    def singl_F_value(self, aim): # F-value 계산
        result = (np.var(aim) / np.var(self.validation_value)) if (np.var(self.validation_value) > np.var(aim)) else (
                    np.var(self.validation_value) / np.var(aim))  # 분모에 큰 값이 들어가게 조건문 추가함.
        return result

    def singl_chi2_method(self, aim): # chi2-value 계산
        chi2_datas = []
        for i in range(0, len(self.validation_value)):
            VD = [float(self.validation_value[i]), float(aim)]
            chi2_datas.append(VD)
        return chi2_datas

    def singl_result_method(self, statistic_value, chi2_value, F): # 통계 결과를 반환한다. (지금 table이 총 10까지 밖에 없다.)
        for i in range(3, 11):
            if len(self.validation_value) == i:
                if statistic_value > t_values[i - 3]:
                    if chi2_value > chi2_values[i - 3]:
                        return ["NotOK", "F"] if F > f_values[i - 3] else ["NotOK", "Chi2"]
                    else:
                        return ["NotOK", "T"]
                else:
                    return ["OK", "OK"]

    def singl_save_data(self, result): # single노드의 경우 결과를 DB에 저장하는 것.
        db = withDB()
        print(self.validation_tag, self.validation_value, self.check_time, result, "DB 들어가기 전.")
        for i in range(0, len(self.validation_value)):  # 측정한 값들을 모두 DB에 저장한다.
            db.insertValidationData(self.ana_tag, self.validation_tag, self.validation_type, self.validation_value[i],
                                    self.start_time, self.check_time[i], result[1], self.bottle_tag, self.user_id)
        db.close()

    def singl_manual_save_data(self, result): # single노드의 경우 manual로 측정한 것 DB에 저장하는 것.
        db = withDB()
        db.updateValidationManualData(self.start_time, result[1], self.user_id)
        db.close()

    def divide_multi_component(self, length, div): # 다중노드의 경우, component를 각각 나누는 것.
        result = []
        if div == "AIM":
            for i in range(0, length):
                result.append(self.component[i][1])
        elif div == "WL":
            for i in range(0, length):
                result.append(self.component[i][2])
        elif div == "CL":
            for i in range(0, length):
                result.append(self.component[i][3])
        return result

    def multi_value_divide(self): # 다중노드의 경우 value를 나누는 것.
        value = []
        for s in range(0, len(self.component)):
            value.append([])

        for i in range(0, len(self.validation_value)):
            for m in range(0, len(self.component)):
                if (i % len(self.component)) == m:
                    value[m].append(self.validation_value[i])
        print(value, "분류된 값")
        return value

    def multi_AD_check(self, value): # 다중노드일 때 Anderson darling test.
        AD_value = []
        for i in range(0, len(value)):
            AD_value.append(scipy.stats.anderson(value[i]))

        sum_flag = 0
        for j in range(0, len(value)):
            if AD_value[j][0] >= 0.05:  # AD_test의 P-value 구한다.
                sum_flag += 1
        return sum_flag

    def multi_chi2_method(self, result, aim): # 다중 노드일 때 chi2값 계산.
        test = []
        for k in range(0, len(aim)):
            test.append([])

        for i in range(0, len(result[0])):
            for j in range(0, len(aim)):
                if (j % len(result[0])) == j:
                    test[j].append([result[j][i], float(aim[j])])

        print(test, "카이제곱 중간 값.")
        result = []
        for m in range(0, len(test)):
            result.append(float((scipy.stats.chisquare(test[m]))[0][0]))
        return result

    def multi_make_random_aim_values(self, aim, wl, cl): # 다중노드일 때 reference_value(aim_value)를 기준으로 분포 생성하는 메서드
        aim_values = []
        for j in range(0, len(aim)):
            aim_values.append([])

        for i in range(0, len(self.validation_value)):
            for k in range(0, len(aim)):
                if k % len(aim) == k:
                    aim_values[k].append(random.uniform((float(aim[k]) - ((float(aim[k]) * (float(wl[k]) / 100)) / 2)),
                                                        (float(aim[k]) + ((float(aim[k]) * (float(wl[k]) / 100)) / 2))))
        return aim_values

    def multi_F_method(self, aim_values, result): # 다중노드일 때 F-value 계산
        F_values = []
        for i in range(0, len(result)):
            F_values.append(np.var(result[i]) / np.var(aim_values[i]))  # 여기는 그냥  [1,2,3,4] 이렇게 순차로 들어감
        return F_values

    def multi_AVG_method(self, result): # 다중노드일 때 평균 계산
        AVG_values = []
        for j in range(0, len(result)):  # 여기는 그냥  [1,2,3,4] 이렇게 순차로 들어감
            AVG_values.append(np.mean(result[j]))
        return AVG_values

    def multi_STD_method(self, result): # 다중노드일 때 표준편차 계산
        STD_values = []
        for i in range(0, len(result)):  # 여기는 그냥  [1,2,3,4] 이렇게 순차로 들어감
            if np.std(result[i]) == 0:
                STD_values.append(0.001)
            else:
                STD_values.append(np.std(result[i]))
        return STD_values

    def multi_std_error_method(self, STD_values, result): # 다중노드일 때 표준에러 계산
        std_error = []
        for i in range(0, len(STD_values)):
            std_error.append((STD_values[i] * (len(result[i]) * 0.5)) / len(result[i]))
        return std_error

    def multi_statistic_value_method(self, AVG_values, aim, STD_Errors): # 다중노드일 때 '(평균값 - 기준값)/표준오차' 계산
        result = []
        for i in range(0, len(aim)):
            result.append(abs(AVG_values[i] - float(aim[i])) / STD_Errors[i])
        return result

    def multi_result_method(self, statistic_values, chi_values, F_values, result): # 다중노드일 때 result값 계산
        static_result = []

        for i in range(3, 11):
            for k in range(0, len(result)):
                if len(result[k]) == i:
                    if statistic_values[k] > t_values[i - 3]:
                        if chi_values[k] > chi2_values[i - 3]:
                            static_result.append("F") if (F_values[k] > f_values[i - 3]) else static_result.append(
                                "Chi2")
                        else:
                            static_result.append("T")
                    else:
                        static_result.append("OK")
        return static_result

    def multi_save_data(self, static_result, result): # 다중노드 결과 및 데이터를 저장한다.
        print("multi_save_data", result, static_result)
        db = withDB()
        for i in range(0, len(result[0])):  # 측정한 값들을 모두 DB에 저장한다.
            for k in range(0, len(static_result)):
                if i % len(result[0]) == i:
                    db.insertValidationData(self.ana_tag, self.validation_tag[k], self.validation_type, result[k][i],
                                            self.start_time, self.check_time[i], static_result[k], self.bottle_tag,
                                            self.user_id)
        db.close()

    def multi_manual_save_data(self, static_result, result): # 다중노드일 때 manual로 측정한 데이터, 결과를 저장한다.
        print("multi manual save data")
        db = withDB()
        for i in range(0, len(result[0])):
            for k in range(0, len(static_result)):
                if i%len(result[0]) == i:
                    db.updateValidationManualData(self.start_time, static_result[k], self.user_id)
        db.close()
        

    def single_auto_statistics(self): # 단일노드의 경우 통계 검사 메서드
        aim = self.component[0][1]
        wl = self.component[0][2]
        cl = self.component[0][3]
        AD_result = self.singl_AD_check()
        if type(AD_result) != float: # AD_test에서 모두 같은 값이 나와버리면 float으로 반환된다.
            if (AD_result)[0] >= 0.05:
                result = self.singl_dixon_test_method()
                if self.singl_dixon_conditional_sentence(result):
                    print("All Data is outlier")
                    result = ["NotOK", "Q"]
                    self.singl_save_data(result)
                    return result[0]
                else:
                    aim_values = self.singl_make_random_aim_values(aim, wl, cl)  # 측정된 결과 값 만큼, aim값을 생성한다.(분산이 존재해야 하므로, )
                    F = self.singl_F_value(aim_values)

                    AVG, STD = np.mean(self.validation_value), np.std(self.validation_value)
                    if STD == 0:
                        STD = 0.001  # 예외 처리.
                    STD_Error = ((STD * (len(self.validation_value) * 0.5)) / len(self.validation_value))  # 표준오차
                    statistic_value = (abs(AVG - float(aim)) / STD_Error)
                    chi2_value = (scipy.stats.chisquare(self.singl_chi2_method(float(aim))))[0][0]

                    result = self.singl_result_method(statistic_value, chi2_value, F)

                    if self.validation_type != "MANUAL":
                        self.singl_save_data(result)
                    elif self.validation_type == "MANUAL":
                        self.singl_manual_save_data(result)
                    return result[0]
        else:
            result = ["NotOK", "AD"]
            self.singl_save_data(result)
            return result[0]

    def multi_auto_statistics(self):
        count = len(self.component)  # 컴포넌트 갯수. (이게 validation value 구성 값의 갯수다.)
        aim = self.divide_multi_component(count, "AIM")
        wl = self.divide_multi_component(count, "WL")
        cl = self.divide_multi_component(count, "CL")

        result = self.multi_value_divide()  # 각 값을 나눠서 리스트 안의 리스트로 구성.
        AD_test_p_value = self.multi_AD_check(result)  # 각 값 그룹 별로 AD테스트, p_value 통과 갯수
        if count == AD_test_p_value:  # 이게 같다는 것은 해당 그룹의 모든 그룹이 AD테스트를 통과했다는 것.
            chi_values = self.multi_chi2_method(result, aim)  # 카이제곱의 결과가 들어있다.(카이제곱 검정을 위한 전처리 아님.)
            aim_values = self.multi_make_random_aim_values(aim, wl, cl)  # aim, wl을 이용해서 분산이 존재하는 aim 군집값을 생성함.
            F_values = self.multi_F_method(aim_values, result)
            AVG_values = self.multi_AVG_method(result)
            STD_values = self.multi_STD_method(result)
            STD_Errors = self.multi_std_error_method(STD_values, result)
            statistic_values = self.multi_statistic_value_method(AVG_values, aim, STD_Errors)
            static_result = self.multi_result_method(statistic_values, chi_values, F_values, result)

            if self.validation_type != "MANUAL":       self.multi_save_data(static_result, result)
            elif self.validation_type == "MANUAL":     self.multi_manual_save_data(static_result, result)

            if "Chi2" in static_result:
                return ["NotOK", "Chi2"]
            elif "T" in static_result:
                return ["NotOK", "T"]
            elif "F" in static_result:
                return ["NotOK", "Chi2"]
            else:
                return ["OK", "OK"]
        else:
            print("data set is not standard")
            return ["NotOK", "AD"]