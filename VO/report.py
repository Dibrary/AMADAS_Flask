class report:
    def __init__(self, report_type, ana_tag, user_id, start_datetime, end_datetime, bottle_tag, file_name):
        self.__report_type = report_type
        self.__ana_tag = ana_tag
        self.__user_id = user_id
        self.__start_datetime = start_datetime
        self.__end_datetime = end_datetime
        self.__bottle_tag = bottle_tag
        self.__file_name = file_name

    def get_report_type(self):
        return self.__report_type

    def get_device_tag(self):
        return self.__ana_tag

    def get_user_id(self):
        return self.__user_id

    def get_start_datetime(self):
        return self.__start_datetime

    def get_end_datetime(self):
        return self.__end_datetime

    def get_bottle_tag(self):
        return self.__bottle_tag

    def get_file_name(self):
        return self.__file_name