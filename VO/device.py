class device:
    def __init__(self, ana_tag=None,
                 house_tag=None,
                 user_id=None,
                 bottle_tag=None,
                 taggs=None,
                 network=None,
                 valve_signal=None,
                 order_type=None):
        self.__analyzer_tag = ana_tag
        self.__house_tag = house_tag
        self.__taggs = taggs
        self.__network = network
        self.__user_id = user_id
        self.__valve_signal = valve_signal
        self.__order_type = order_type

    def set_taggs(self, taggs_value):
        self.__taggs = taggs_value

    def set_network(self, network_value):
        self.__network = network_value

    def get_device(self):
        return self.__device_tag

    def get_house(self):
        return self.__house_tag

    def get_taggs(self):
        return self.__taggs

    def get_network(self):
        return self.__network

    def get_user_id(self):
        return self.__user_id

    def get_valve_signal(self):
        return self.__valve_signal

    def get_order_type(self):
        return self.__order_type