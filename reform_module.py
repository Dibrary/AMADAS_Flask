
def tuple_to_list(value): # tuple로 들어온 값을, list로 바꿔서 반환한다.
    if value == ():
        return None
    else:
        result = [list(value[i]) for i in range(0, len(value))]
        return result[0]