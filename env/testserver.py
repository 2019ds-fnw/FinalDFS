import sys
import os
sys.path.append('/usr/lib/python2.7/site-packages')
import rpyc

from rpyc import Service
from rpyc.utils.server import ThreadedServer
 
class TestService(Service):
    def exposed_test(self, num):
        return 1 + num
 
sr = ThreadedServer(TestService, port=2131)
sr.start()