#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from PyKDE4.kdecore import KConfig, KConfigGroup

import urllib2
import datetime

from icalendar import Calendar, Event
from localtz import LocalTimezone

items = []

class GoogleAgendaApplet(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
        self.items = []
        self.interval = 1   # minutes
        self.max_events = 10
        self.urls = []
 
    def init(self):
        self.general_config = self.config("General")
#        self.toGeneralConfig()
        self.fromGeneralConfig()
        self.resize(200, 200)
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.setHasConfigurationInterface(True)
        self.fetchData()

        # in miliseconds
        self.startTimer(1000 * 60 * self.interval)
        self.list = None

        self.displayData()

    def configChanged(self):
        self.fromGeneralConfig()
        plasmascript.Applet.configChanged(self)
        self.displayData()
        self.update()

    def fromGeneralConfig(self):
        self.interval, success = self.general_config.readEntry("interval", 1).toInt()
        self.max_events, success = self.general_config.readEntry("max_events", 10).toInt()
        qurls = self.general_config.readEntry("urls", QStringList(QString("http://www.mozilla.org/projects/calendar/caldata/PolishHolidays.ics"))).toStringList()
        self.urls = [str(x) for x in qurls]

    def toGeneralConfig(self):
        qurls = QStringList()
        for url in urls:
            qurls.append(QString(url))

        self.general_config.writeEntry("urls", qurls)
        

    def fetchData(self):
        global items
        rv = []
        for url in urls:
            try:
                fical = urllib2.urlopen(url)
                for event in Calendar.from_string(fical.read()).walk():
                    if type(event) is Event:
                        dt = None
                        add = False
                        if type(event['DTSTART'].dt) is datetime.date:
                                dt = datetime.datetime.combine(event['DTSTART'].dt, datetime.time.min)
                                dt = dt.replace(tzinfo=LocalTimezone())
                                date = event['DTSTART'].dt
                                time = None

                        if type(event['DTSTART'].dt) is datetime.datetime:
                                dt = event['DTSTART'].dt
                                if dt.tzname():
                                    dt = dt.astimezone(LocalTimezone())
                                else:
                                    dt = dt.replace(tzinfo=LocalTimezone())
                                date = dt.date()
                                time = dt.timetz()

                        if date >= datetime.date.today():
                            rv.append({
                                'dt': dt,
                                'date': date,
                                'time': time,
                                'summary': unicode(event['SUMMARY']),
                            })
                            
                self.error = None
                            
            except urllib2.HTTPError, e:
                self.error = str(e)
                print self.error

        rv.sort(key=lambda row: row['dt'])
        self.items = rv
                    
    def displayData(self):
        oldlist = None
        if self.list:
            oldlist = self.list
            for i in range(oldlist.count()):
                item = oldlist.itemAt(0)
                oldlist.removeAt(0)
                del item

        self.list = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.applet.setLayout(self.list)

        if oldlist:
            del oldlist

        last_date = None
        num_events = 0
        for item in self.items:
            if item['date'] != last_date:
                last_date = item['date']
                strDate = item['date'].strftime('%d %B %Y')
                dateLabel = Plasma.Label(self.applet)
                dateLabel.setText(strDate)
                dateLabel.setAlignment(Qt.AlignCenter)
                dateLabel.setStyleSheet("""
                                        font-weight: 700;
                                        color: blue;
                                        """)
                self.list.addItem(dateLabel)

            summary = ''
            if item['time']:
                summary += item['dt'].strftime('%H:%M')
                summary += " "
            summary += item['summary']
            summaryLabel = Plasma.Label(self.applet)
            summaryLabel.setText(summary)
            self.list.addItem(summaryLabel)

            num_events += 1
            if self.max_events > 0 and num_events >= self.max_events:
                break
            

    def timerEvent(self, event):
        self.fetchData()
        self.displayData()
        self.update()

 
#    def paintInterface(self, painter, option, rect):
#        painter.save()
#        painter.setPen(Qt.black)
#        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, self.formatted)
#        painter.restore()
 
def CreateApplet(parent):
    return GoogleAgendaApplet(parent)
