from datahub.sources.daqbuf import Daqbuf
from datetime import datetime, timedelta
import pandas as pd
from datahub import Daqbuf, Table, Stdout


# Define channels
channels = [
"SAROP11-PBPS122:INTENSITY",
"SAROP11-PBPS122:XPOS",
"SAROP11-PBPS122:YPOS"
]

# Get current time and define time range
#now = datetime.now()
#from_time, to_time = [
#(now - timedelta(weeks=1)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
#now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
#]
from_time = "2025-03-10 12:00:00.000"
to_time = "2025-03-12 12:00:00.000"

# Define query
query = {
"channels": channels,
"start": from_time,
"end": to_time,
"bins": 2000,
}

from_time = "2025-03-10 12:00:00.000"
to_time = "2025-03-12 12:00:00.000"

# Fetch data
with Daqbuf(backend="sf-archiver", cbor=True, time_type="str") as source:
    table = Table()
    stdout = Stdout()
    source.add_listener(table)
    source.add_listener(stdout)
    source.request(query)
dataframe = table.as_dataframe(index=Table.TIMESTAMP)
# Convert index to datetime
dataframe.index = pd.to_datetime(dataframe.index)

# Print results
#print(dataframe)

print("Bins query:", query['bins'])
print("Dataframe size:", dataframe.shape)
# Print dataframe size
print("From time query:", from_time)
print("To time query:", to_time)
# Print first and last index entry
print("First index entry:", dataframe.index[0])
print("Last index entry:", dataframe.index[-1])

# Compute and print date range length in hours
date_range_hours = (dataframe.index[-1] - dataframe.index[0]).total_seconds() / 3600
print("Date range length in hours:", date_range_hours)
print(table)