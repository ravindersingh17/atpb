import libtorrent as lt
import os

class Tor:

    self.downloads = {}
    self.save_path = os.path.expanduser("~/tor")

    def add(self, link):
        ses = lt.session()
        params = {"save_path": self.save_path}
        handle = lt.add_magnet_uri(ses, link, params)
        id = self.getminid()
        self.downloads[id] = {
                "session": ses,
                "handle": handle
                }

    def getminid(self):
        id = 1
        while True:
            if id not in self.downloads:
                return id
            id += 1

