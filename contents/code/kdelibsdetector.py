#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from PyQt4.QtCore import QLibraryInfo, QPluginLoader
import os.path

main_plugin_path = str(QLibraryInfo.location(QLibraryInfo.PluginsPath))
designer_plugin_path = os.path.join(main_plugin_path, 'designer')
kdewidgets_path = os.path.join(designer_plugin_path, 'kdewidgets.so')
kdelibs_present = QPluginLoader(kdewidgets_path).load()
