
def get_time_now() :
    current_time = datetime.datetime.now()
    formated_time=current_time.strftime("%m-%d-%Y %H:%M")
    return(formated_time)

def get_date():
    current_time = datetime.datetime.now()
    formated_time=current_time.strftime("%Y-%m-%d")
    return(formated_time)

def switch_repair(RepairType):
    if RepairType=="01":
        return 50
    elif RepairType=="02":
        return    50
    elif RepairType=="03":
        return 100
    elif RepairType=="04":
        return 150
    elif RepairType=="05":
        return 50
    elif RepairType=="06":
        return 100
    elif RepairType=="07":
        return  50

