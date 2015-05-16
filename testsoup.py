#!/usr/bin/env python

import time
from urllib2 import Request, urlopen
from bs4 import BeautifulSoup

s1  = time.time()
req = Request("http://xml.buienradar.nl/")
print "Request         = {0}".format(time.time() - s1)
s2 = time.time()
response = urlopen(req)
print "URLopen         = {0}".format(time.time() - s2)
s3 = time.time()
output = response.read()
print "Read            = {0}".format(time.time() - s3)
s4 = time.time()
soup = BeautifulSoup(output)
print "Soup            = {0}".format(time.time() - s4)
s5 = time.time()

MSwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windsnelheidms)
GRwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windrichtinggr)
ms = MSwind.replace("<"," ").replace(">"," ").split()[1]
gr = GRwind.replace("<"," ").replace(">"," ").split()[1]
print "Extracting info = {0}".format(time.time() - s5)

print 'speed: {0} m/s, direction: {1} deg, processing time: {2} s'.format(ms, gr, time.time() - s1)
