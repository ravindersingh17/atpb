import libtorrent as lt
import os

class Download:
    def __init__(self):
        self.session = None
        self.handle = None
        self.chat = None

class Tor:

    def __init__(self):
        self.downloads = {}
        self.save_path = os.path.expanduser("~/tor")

    def add(self, link, chat):
        download = Download()
        download.session = lt.session()
        params = {"save_path": self.save_path}
        download.handle = lt.add_magnet_uri(download.session, link, params)
        download.chat = chat
        id = self.getminid()
        self.downloads[id] = download

    def getminid(self):
        id = 1
        while True:
            if id not in self.downloads:
                return id
            id += 1

    def getstatus(self, downloadid):
        if downloadid not in self.downloads:
            return None
        status = self.downloads[downloadid].handle.status()
        download = status.progress * 100
        rate = status.download_rate
        ispaused = self.downloads[downloadid].session.is_paused()
        if not self.downloads[downloadid].handle.has_metadata():
            state = "metadata"
        elif ispaused:
            state = "paused"
        else:
            state = "downloading"

        return (download, rate, state)

    def pause(self, downloadid):
        if downloadid not in self.downloads:
            return None
        self.downloads[downloadid].session.pause()
        return True

    def resume(self, downloadid):
        if downloadid not in self.downloads:
            return None
        self.downloads[downloadid].session.resume()
        return True

    def getallstatus(self):
        retval = {}
        for id in self.downloads:
            retval[id] = self.getstatus(id)
        return retval

    def pauseall(self):
        for id in self.downloads:
            self.pause(id)

    def resumeall(self):
        for id in self.downloads:
            self.resume(id)


