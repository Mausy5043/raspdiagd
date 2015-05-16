#!/usr/bin/env python

import time
from urllib2 import Request, urlopen
from bs4 import BeautifulSoup

_url="http://xml.buienradar.nl/"
s1  = time.time()
req = Request(_url)
print "Request         = {0}".format(time.time() - s1)
s2 = time.time()
response = urlopen(req)
print "URLopen         = {0}".format(time.time() - s2)
s3 = time.time()
output = response.read()
print "Read            = {0}".format(time.time() - s3)
s4 = time.time()
soup = BeautifulSoup(output)
print "Soup (1)        = {0}".format(time.time() - s4)

s5 = time.time()
MSwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windsnelheidms)
GRwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windrichtinggr)
ms = MSwind.replace("<"," ").replace(">"," ").split()[1]
gr = GRwind.replace("<"," ").replace(">"," ").split()[1]
print "Extracting info = {0}".format(time.time() - s5)
print 'speed: {0} m/s, direction: {1} deg, processing time: {2} s'.format(ms, gr, time.time() - s1)


s6 = time.time()
soup = BeautifulSoup(urllib2.urlopen(_url))
print "Soup (2)         = {0}".format(time.time() - s6)

s5 = time.time()
MSwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windsnelheidms)
GRwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windrichtinggr)
ms = MSwind.replace("<"," ").replace(">"," ").split()[1]
gr = GRwind.replace("<"," ").replace(">"," ").split()[1]
print "Extracting info = {0}".format(time.time() - s5)
print 'speed: {0} m/s, direction: {1} deg, processing time: {2} s'.format(ms, gr, time.time() - s1)
