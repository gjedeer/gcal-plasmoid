#!/usr/bin/python
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
 
class HelloWorldApplet(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
 
    def init(self):
        self.resize(200, 200)
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        # No configuration interface supported
        self.setHasConfigurationInterface(False)
 
    def paintInterface(self, painter, option, rect):
        painter.save()
        painter.setPen(Qt.white)
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, "Hello developers-blog.org!")
        painter.restore()
 
def CreateApplet(parent):
    return HelloWorldApplet(parent)
