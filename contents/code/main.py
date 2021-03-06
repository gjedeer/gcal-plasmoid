#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from PyKDE4.kdecore import *
from PyKDE4.kio import *

import datetime
import os.path
import os
import hashlib

import sys

from icalendar import Calendar, Event
from localtz import LocalTimezone
from kdelibsdetector import kdelibs_present

from dateutil import rrule, tz
items = []

class GoogleAgendaApplet(plasmascript.Applet):
    def __init__(self,parent,args=None):
        print sys._getframe().f_code.co_name
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
        print sys._getframe().f_code.co_name
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
        print sys._getframe().f_code.co_name
        main_dir = str(KStandardDirs.locateLocal("data", "gcal-agenda"))
        dirs = [main_dir] + list(parts)
        return os.path.join(*dirs)

    def initDataDir(self):
        print sys._getframe().f_code.co_name
        path = self.getDataPath()

        if not os.path.exists(path):
            os.mkdir(path, 0700)

    def configChanged(self):
        """
        Config has been changed - refresh display
        Inherited from plasmascript.Applet
        """
        print sys._getframe().f_code.co_name
        self.fromGeneralConfig()
        plasmascript.Applet.configChanged(self)
        self.fetchData()
        self.displayData()
        self.update()

    def fromGeneralConfig(self):
        """
        Get values from plasma config and store in properties
        """
        print sys._getframe().f_code.co_name
        self.interval, success = self.general_config.readEntry("interval", 1).toInt()
        self.max_events, success = self.general_config.readEntry("max_events", 10).toInt()
        qurls = self.general_config.readEntry("urls", QStringList(QString("http://www.mozilla.org/projects/calendar/caldata/PolishHolidays.ics"))).toStringList()
        self.urls = [str(x) for x in qurls]
        self.cache_ical = self.general_config.readEntry("cache_ical", True).toBool()


    def fromCache(self):
        print sys._getframe().f_code.co_name
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
        print sys._getframe().f_code.co_name
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
        print sys._getframe().f_code.co_name
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
        print sys._getframe().f_code.co_name
        self.items = [item for item in self.items if not item['url'] == url]
        rv = []

        def helper(E,f):
            if f in E:
                return E[f]
            else:
                return None
        freq_dict = dict(zip(("YEARLY", "MONTHLY", "WEEKLY", "DAILY",
           "HOURLY", "MINUTELY", "SECONDLY"),range(7)))
        day_dict = dict(zip(("MO", "TU", "WE", "TH", "FR", "SA", "SU"),range(7)))
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

                    
                dt = [dt]
                date = [date]
                time = [time]
                if 'RRULE' in event:
                    # deal with repeated events
                    e_rrule = event['RRULE']
                    
                    freq = freq_dict[e_rrule['FREQ'][0]]
                    
                    dtstart = dt[0]
                    interval = helper(e_rrule,'INTERVAL')
                    if interval is None:
                        interval = 1
                    wkst = helper(e_rrule,'WKST')
                    if wkst is not None:
                        wkst = day_dict[wkst[0]]
                    count = helper(e_rrule,'COUNT')
                    if count is not None:
                        count = count[0]
                    until = helper(e_rrule,'UNTIL')
                    if until is not None:
                        until =until[0]
                        until = until.astimezone(LocalTimezone())
                    bysetpos = helper(e_rrule,'BYSETPOS')
                    bymonth = helper(e_rrule,'BYMONTH')
                    bymonthday = helper(e_rrule,'BYMONTHDAY')
                    byyearday = helper(e_rrule,'BYYEARDAY')
                    byeaster = helper(e_rrule,'BYEASTER')
                    byweekno = helper(e_rrule,'BYWEEKNO')
                    byweekday = helper(e_rrule,'BYDAY')
                    if byweekday is not None:
                        byweekday = [day_dict[bwd] for bwd in byweekday]
                    byhour = helper(e_rrule,'BYHOUR')
                    byminute = helper(e_rrule,'BYMINUTE')
                    bysecond = helper(e_rrule,'BYSECOND')
                    
                    rrule_list = list(rrule.rrule(freq,
                                            dtstart=dtstart,
                                            interval=interval,
                                            wkst=wkst,
                                            count=count,
                                            until=until,
                                            bysetpos=bysetpos,
                                            bymonth=bymonth,
                                            bymonthday=bymonthday,
                                            byyearday=byyearday,
                                            byeaster=byeaster,
                                            byweekno=byweekno,
                                            byweekday=byweekday,
                                            byhour=byhour,
                                            byminute=byminute,
                                            bysecond=bysecond).between(
                                                datetime.datetime.now(tz=tz.tzlocal()),
                                                datetime.datetime.now(tz=tz.tzlocal()) + datetime.timedelta(days=365),
                                                inc=True
                                            ))
                    
                    date = [rr.date() for rr in rrule_list]
                    dt= [rr for rr in rrule_list]
                    time= [rr.timetz() for rr in rrule_list]

                
                

                loc = ''
                if 'LOCATION' in event and not event['LOCATION'] =='' :
                    loc = 'Location: '
                    loc += event['LOCATION']

                for (d_,dt_,t_) in zip(date,dt,time):
                    if d_ >= datetime.date.today():
                        rv.append({
                            'dt': dt_,
                            'date': d_,
                            'time': time,
                            'summary': unicode(event['SUMMARY']),
                            'url': url,
                            'loc':loc
                        })
        self.items += rv
        self.items.sort(key=lambda row: row['dt'])

    def displayData(self):
        """
        Display data from self.items on screen
        """

        print sys._getframe().f_code.co_name
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

        # Don't display warning when kdelibs5-dev is missing
        if False and not kdelibs_present:
            for text in ('ERROR', 'package "kdelibs5-dev"', 'or "kdelibs5-plugins"', 'is missing', 'settings will be', 'broken'):
                label = Plasma.Label(self.applet)
                label.setText(text)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("""
                            font-weight: 700;
                            color: red;
                            """)
                self.list.addItem(label)
            tooltip = Plasma.ToolTipContent()
            tooltip.setMainText('Your system is missing a package')
            tooltip.setSubText('A library "kdewidgets.so" has not been found on your system. This library is usually found in a package called "kdelibs5-plugins" or "kdelibs-dev" which can be installed using a package manager in your system.\nIf you don\'t install it, plasmoid settings will fail to work properly')
            tooltip.setAutohide(False)
            Plasma.ToolTipManager.self().setContent(self.applet, tooltip)
            Plasma.ToolTipManager.self().registerWidget(self.applet)

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
            summaryLabel.setToolTip(item['loc'])

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
