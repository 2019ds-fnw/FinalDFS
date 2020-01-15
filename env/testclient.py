import sys
import os
sys.path.append('/usr/lib/python2.7/site-packages')
import rpyc

conn =rpyc.connect('10.24.1.27',32131)
cResult =conn.root.test(11)
conn.close()
 
print cResult