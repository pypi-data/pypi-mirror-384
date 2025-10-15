from datahub import *
import datetime

def get_data(ch, t_start, t_stop):
    query = {
        "channels": ch,
        "start": str(t_start),
        "end": str(t_stop)
    }
    with Daqbuf(backend="sf-archiver") as source:
        stdout = Stdout()
        table = Table()
        source.add_listener(table)
        source.add_listener(stdout)
        source.request(query)
        data = table.data[ch]
        values = [val[ch] for val in data] if len(data) > 0 else []
    return values

time_start = datetime.datetime(2024,11,18,6,59,0)
time_stop  = datetime.datetime(2024,11,18,7,0,0)

while (True):
  for ch in ["SF-STAT-AR-SHUTDOWN:DT", "SF-STAT-AR-SETUP:DT", "SF-STAT-AR-MD:DT", "SF-STAT-AR-BLD:DT",
           "SF-STAT-AR-USER:DT", "SF-STAT-AR-SHUTDOWN:UT", "SF-STAT-AR-SETUP:UT", "SF-STAT-AR-MD:UT",
           "SF-STAT-AR-BLD:UT", "SF-STAT-AR-USER:UT", "SF-STAT-AT-SHUTDOWN:DT", "SF-STAT-AT-SETUP:DT",
           "SF-STAT-AT-MD:DT", "SF-STAT-AT-BLD:DT", "SF-STAT-AT-USER:DT", "SF-STAT-AT-SHUTDOWN:UT",
           "SF-STAT-AT-SETUP:UT", "SF-STAT-AT-MD:UT", "SF-STAT-AT-BLD:UT", "SF-STAT-AT-USER:UT"]:
    data = get_data(ch, time_start, time_stop)
    print("OK ---> " , ch)
    #print(data)
