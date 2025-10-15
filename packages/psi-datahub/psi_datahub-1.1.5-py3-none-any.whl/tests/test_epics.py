import unittest
from datahub import *

url = "localhost:54321"
filename = "/Users/gobbo_a/dev/back/epics.h5"
channels = ["TESTIOC:TESTCALCOUT:Input", "TESTIOC:TESTSINUS:SinCalc", "TESTIOC:TESTWF2:MyWF"]
start = None
end = 3.0
query = {
    "channels": channels,
    "start": start,
    "end": end
}



class EpicsTest(unittest.TestCase):
    def setUp(self):
        self.source = Epics(url=url)

    def tearDown(self):
        cleanup()


    def test_listeners(self):
        hdf5 = HDF5Writer(filename)
        stdout = Stdout()
        table = Table()
        #self.source.set_id("bsread")
        self.source.add_listener(hdf5)
        self.source.add_listener(stdout)
        self.source.add_listener(table)
        self.source.request(query)
        dataframe = table.as_dataframe()
        print (dataframe.columns)
        if channels:
            self.assertEqual(list(dataframe.keys()), channels)

    def test_rel_tm(self):
        stdout = Stdout()
        #self.source.set_id("bsread")
        self.source.add_listener(stdout)
        self.source.req("TESTIOC:TESTSINUS:SinCalc", 0.0, 1.0)

    def test_rel_id(self):
        stdout = Stdout()
        #self.source.set_id("bsread")
        self.source.add_listener(stdout)
        self.source.req("TESTIOC:TESTSINUS:SinCalc", 0, 1)

if __name__ == '__main__':
    unittest.main()
