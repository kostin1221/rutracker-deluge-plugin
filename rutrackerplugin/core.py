#
# core.py
#
# Copyright (C) 2009 Kostin Dmitrij [DsTr] <kostindima@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
import urllib2
import re
import os

from HTMLParser import HTMLParser

DEFAULT_PREFS = {
    "test":"NiNiNi"
}

class RutrackerParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.__nav_tag = False
        self.__data_index = 0
        self.__razdelz = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            for attr in attrs:
                if attr[0].encode('utf-8') == "class" and attr[1].encode('utf-8') == "nav" :
                    self.__nav_tag = True


    def handle_endtag(self, tag):
        if tag == "td":
            self.__nav_tag = False

    def handle_data(self, data):
        if self.__nav_tag:
            if self.__data_index > 1:
                self.__razdelz.append(data.encode("utf-8").strip())
            self.__data_index = self.__data_index + 1

    def get_razdelz(self):
        return self.__razdelz


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("rutrackerplugin.conf", DEFAULT_PREFS)


        component.get("EventManager").register_event_handler("TorrentAddedEvent", self._on_torrent_added)

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def set_config(self, config):
        "sets the config dictionary"
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config

    def _on_torrent_added(self, torrent_id):
        """called on torrent add event"""
        #get the torrent by torrent_id

        torrent = component.get("TorrentManager")[torrent_id]

        torrent_name = torrent.get_status(["name"])["name"]
        torrent_comment = torrent.torrent_info.comment().decode("utf8", "ignore")

        if torrent_comment.startswith("http://rutracker.org/forum/viewtopic.php?t="):


            try: ulo = urllib2.urlopen(torrent_comment)
            except URLError, e:
                print e.reason

            html_text = ulo.read().decode('cp1251')

            html_text_without_js = re.compile(r'<script[^>]+>.*?</script>', re.DOTALL).sub('', html_text.encode("utf-8"))

            parser = RutrackerParser()
            parser.feed(html_text_without_js.decode("utf-8"))
            parser.close()

            razdel_list = parser.get_razdelz()
            dest_path = ""
            for razdel in razdel_list:
                dest_path = os.path.join(dest_path, razdel)

            options = torrent.get_options()
           # print torrent.state

          #  if torrent.is_seed:
          #      print "seeded\n"

       #     new_options = {"move_completed" : True}
            if not options["move_completed_path"].endswith(dest_path):
                if options["move_completed"]:
                    dest_path = os.path.join(options["move_completed_path"], dest_path)
                else:
                    dest_path = os.path.join(options["download_location"], dest_path)

            print dest_path
            options["move_completed_path"] = dest_path
            options["move_completed"] = True
            torrent.set_options(options)

        print "added torrent: " + torrent_name
        #print "\n" + torrent.get_status(["name"])["comment"]
        print torrent_comment

