#!/usr/bin/env python

import time
from urllib2 import Request, urlopen
from bs4 import BeautifulSoup

s1  = time.time()
req = Request("http://xml.buienradar.nl/")
print s1 - time.time()
s2 = time.time()
response = urlopen(req)
print s2 - time.time()
s3 = time.time()
output = response.read()
print s3 - time.time()
s4 = time.time()
soup = BeautifulSoup(output)
print s4 - time.time()
s5 = time.time()

MSwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windsnelheidms)
GRwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windrichtinggr)
ms = MSwind.replace("<"," ").replace(">"," ").split()[1]
gr = GRwind.replace("<"," ").replace(">"," ").split()[1]
print s5 - time.time()

print = 'speed: {0} m/s, direction: {1} deg, processing time: {2} s'.format(ms, gr, s1 - time.time())
