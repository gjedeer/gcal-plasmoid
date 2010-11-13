#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from PyKDE4.kdecore import *
from PyKDE4.kio import *

import urllib2
import datetime
import os.path
import os
import hashlib

from icalendar import Calendar, Event
from localtz import LocalTimezone

items = []

class GoogleAgendaApplet(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
        # List of all events sorted by date, populated in fetchData()
        self.items = []
        # Refresh interval, in minutes
        self.interval = 1
        # Max number of displayed events, 0 for unlimited
        self.max_events = 10
        # iCal calendar URLs
        self.urls = []
        # KDE jobs - to make sure they won't be garbage collected
        self.jobs = set()
        # Whether to cache downloaded ical files
        self.cache_ical = True
 
    def init(self):
        """
        Called by Plasma upon initialization
        """
        self.initDataDir()
        self.general_config = self.config("General")
        self.fromGeneralConfig()
        self.resize(200, 200)
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.setHasConfigurationInterface(True)
        self.fetchData()

        self.fromCache()

        # in miliseconds
        self.startTimer(1000 * 60 * self.interval)
        self.list = None

        self.displayData()

    def getDataPath(self, *parts):
        main_dir = str(KStandardDirs.locateLocal("data", "gcal-agenda"))
        dirs = [main_dir] + list(parts)
        return os.path.join(*dirs)

    def initDataDir(self):
        path = self.getDataPath()

        if not os.path.exists(path):
            os.mkdir(path, 0700)

    def configChanged(self):
        """
        Config has been changed - refresh display
        Inherited from plasmascript.Applet
        """
        self.fromGeneralConfig()
        plasmascript.Applet.configChanged(self)
        self.fetchData()
        self.displayData()
        self.update()

    def fromGeneralConfig(self):
        """
        Get values from plasma config and store in properties
        """
        self.interval, success = self.general_config.readEntry("interval", 1).toInt()
        self.max_events, success = self.general_config.readEntry("max_events", 10).toInt()
        qurls = self.general_config.readEntry("urls", QStringList(QString("http://www.mozilla.org/projects/calendar/caldata/PolishHolidays.ics"))).toStringList()
        self.urls = [str(x) for x in qurls]
        self.cache_ical = self.general_config.readEntry("cache_ical", True).toBool()
        print "CAHCE ICAL", self.cache_ical

#unused
    def toGeneralConfig(self):
        qurls = QStringList()
        for url in self.urls:
            qurls.append(QString(url))

        self.general_config.writeEntry("urls", qurls)
        

    def fromCache(self):
        for url in self.urls:
            if len(url.strip()) == 0:
                continue

            hashed_url = hashlib.sha224(url).hexdigest()
            fname = self.getDataPath(hashed_url) + ".ical"
            try:
                self.parseFile(url, open(fname).read())
            except IOError:
                pass

    def fetchData(self):
        """
        Fetch data from ical files, parse them and insert into self.items
        On communication error, sets self.error
        """
        rv = []
        for url in self.urls:
            if len(url.strip()) == 0:
                continue

            job = KIO.storedGet(KUrl(url.strip()), KIO.Reload, KIO.HideProgressInfo)
            QObject.connect(job, SIGNAL("result(KJob*)"), self.jobFinished)
            self.jobs.add(job)

    def jobFinished(self, job):
        """
        Callback of KIO network handler
        """
        if job.error():
            print "JOB FOR URL %s RETURNED ERROR!" % str(job.url())
            return
        url = str(job.url().url())
        data = str(job.data())

        self.parseFile(url, data)
        self.displayData()
        self.update()

        # Let the garbage collector do its job
        self.jobs.remove(job)

        # Write job to cache
        if self.cache_ical:
            hashed_url = hashlib.sha224(url).hexdigest()
            fname = self.getDataPath(hashed_url) + ".ical"
            open(fname, 'w').write(data)


    def parseFile(self, url, contents):
        """
        Parse the file and place it in self.items
        contents may come stright from network callback (jobFinished) or cache
        """
        self.items = [item for item in self.items if not item['url'] == url]
        rv = []
        for event in Calendar.from_string(contents).walk():
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
                        'url': url,
                    })
        self.items += rv
        self.items.sort(key=lambda row: row['dt'])

    def displayData(self):
        """
        Display data from self.items on screen
        """

        # Remove old labels from layout
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

        # Holds last event date so we know when to insert date header
        last_date = None
        # Counter of displayed events
        num_events = 0

        for item in self.items:
            if item['date'] != last_date:
                # Insert date header
                last_date = item['date']
                qDate = QDate(item['date'].year, item['date'].month, item['date'].day)
                strDate = qDate.toString('d MMMM yyyy')
                dateLabel = Plasma.Label(self.applet)
                dateLabel.setText(strDate)
                dateLabel.setAlignment(Qt.AlignCenter)
                dateLabel.setStyleSheet("""
                                        font-weight: 700;
                                        color: blue;
                                        """)
                self.list.addItem(dateLabel)

            # Prepare label with event text
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
        """
        Called by timer every self.interval minutes
        """
        print "timer"
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
