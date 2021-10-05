class LIMS:
    def __init__(self, ana_tag, process_tag, start_datetime, end_datetime, lims_value):
        self.__ana_tag = ana_tag
        self.__process_tag = process_tag
        self.__start_datetime = start_datetime
        self.__end_datetime = end_datetime
        self.__lims_value = lims_value

    def get_device_tag(self):
        return self.__ana_tag

    def get_process_tag(self):
        return self.__process_tag

    def get_start_datetime(self):
        return self.__start_datetime

    def get_end_datetime(self):
        return self.__end_datetime

    def get_lims_value(self):
        return self.__lims_value