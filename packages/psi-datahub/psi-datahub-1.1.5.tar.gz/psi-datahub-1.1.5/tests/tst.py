
from datahub import *


with Daqbuf(backend="sf-databuffer", cbor=True, parallel=True) as source:
    table = Table()
    source.add_listener(table)

    source.req("SAT-CVME-TIFALL5:EvtSet", 21928758437, 21928758467)
    print(len(table.data["SAT-CVME-TIFALL5:EvtSet"]))
    dataframe = table.as_dataframe(Table.PULSE_ID)
    print(dataframe)

    table.close()
    source.req("SAT-CVME-TIFALL5:EvtSet", -1.0, 0.0)
    print(len(table.data["SAT-CVME-TIFALL5:EvtSet"]))
    dataframe = table.as_dataframe(Table.TIMESTAMP)
    print(dataframe)


    source.req("SAT-CVME-TIFALL5:EvtSet", -11.0, -9.0)
    print(len(table.data["SAT-CVME-TIFALL5:EvtSet"]))
    dataframe = table.as_dataframe(Table.TIMESTAMP)
    print(dataframe)
    table.clear()
    source.req("SAT-CVME-TIFALL5:EvtSet", "2024-06-26 16:00:00",
               "2024-06-26 16:19:00")
    print(len(table.data["SAT-CVME-TIFALL5:EvtSet"]))
    dataframe = table.as_dataframe(Table.TIMESTAMP)
    print(dataframe)