#!/usr/bin/python

import urllib2
from icalendar import Calendar, Event

url = "http://www.google.com/calendar/ical/gjedeer%40gmail.com/private-95b1577f5087910771796a5de667a7a5/basic.ics"

# throws HTTPError
def get_parsed():
    fical = urllib2.urlopen(url)
    return Calendar.from_string(fical.read())

cal = get_parsed()
for event in cal.walk():
    if type(event) is Event:
        print event['SUMMARY']
        print event['DTSTART'].dt
