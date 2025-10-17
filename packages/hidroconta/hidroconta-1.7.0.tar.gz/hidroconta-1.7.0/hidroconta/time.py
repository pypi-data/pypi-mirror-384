import datetime
def strftime_demeter(timestamp: datetime.datetime):
    return timestamp.strftime('%d/%m/%Y %H:%M:%S')

def strptime_demeter(timestamp: str):
    return datetime.datetime.strptime(timestamp, '%d/%m/%Y %H:%M:%S')