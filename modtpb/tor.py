import libtorrent as lt
import os
import asyncio
import json

class Download:
    def __init__(self):
        self.session = None
        self.handle = None
        self.chat = None
        self.magnet = None
        self.name = None
        self.completed = False

class Tor:

    def __init__(self):
        self.downloads = {}
        self.save_path = os.path.expanduser("~/tor")
        self.save_file = ".atpb"
        try:
            torData = json.loads(open(self.save_file).read())
        except FileNotFoundError:
            torData = {"completed": [], "running": []}
        for tor in torData["completed"]:
            download = Download()
            download.magnet = tor["magnet"]
            download.session = None
            download.name = tor["name"]
            download.chat = tor["chat"]
            download.handle = None
            download.completed = True

        for tor in torData["running"]:
            #TODO Use resume data
            self.add(tor["magnet"], tor["chat"], tor["id"])

    def add(self, link, chat, id = None):
        #Check duplicate torrent
        parsed_uri = lt.parse_magnet_uri(link)
        for id in self.downloads:
            if parsed_uri["name"] == self.downloads[id].name:
                return False
        download = Download()
        download.magnet = link
        download.session = lt.session()
        params = {"save_path": self.save_path}
        download.handle = lt.add_magnet_uri(download.session, link, params)
        download.name = download.handle.name()
        download.chat = chat
        if not id:
            id = self.getminid()
        self.downloads[id] = download
        return True

    def remove(self, id):
        if id not in self.downloads:
            return False
        if not self.downloads[id].completed:
            self.downloads[id].session.remove_torrent(self.downloads[id].handle)
        del self.downloads[id]
        return True


    def getminid(self):
        id = 1
        while True:
            if id not in self.downloads:
                return id
            id += 1

    def getstatus(self, downloadid):
        if downloadid not in self.downloads:
            return None
        if self.downloads[downloadid].completed:
            return (self.downloads[downloadid], 100, 0, "c")
        name = self.downloads[downloadid].name
        status = self.downloads[downloadid].handle.status()
        download = status.progress * 100
        rate = float(status.download_rate / 1000)
        ispaused = self.downloads[downloadid].session.is_paused()
        if not self.downloads[downloadid].handle.has_metadata():
            state = "m"
        elif ispaused:
            state = "p"
        else:
            state = "d"

        return (name, download, rate, state)

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

    async def eventprocess(self):
        while True:
            torrentData = {"completed": [], "running": []}
            for id in self.downloads:
                if self.downloads[id].completed:
                    torrentData["completed"].append({
                        "name": self.downloads[id].name,
                        "id": id,
                        "chat": self.downloads[id].chat,
                        "magnet": self.downloads[id].magnet,
                        })
                elif self.downloads[id].handle.status().state == lt.torrent_state_seeding:
                    self.downloads[id].session.remove_torrent(self.downloads[id].handle)
                    self.downloads[id].completed = True
                    self.downloads[id].session = None
                    torrentData["completed"].append({
                        "name": self.downloads[id].name,
                        "id": id,
                        "chat": self.downloads[id].chat,
                        "magnet": self.downloads[id].magnet,
                        })
                else:
                    handle = self.downloads[id].handle
                    session = self.downloads[id].session

                    handle.save_resume_data()
                    alerts = session.pop_alerts()

                    for alert in alerts:
                        if type(alert) == lt.save_resume_data_alert:
                            data = lt.bencode(a.resume_data)
                            open(os.path.join(self.save_path, handle.name() + ".resume"), "wb").write(data)

                    torrentData["running"].append({
                        "name": self.downloads[id].name,
                        "id": id,
                        "chat": self.downloads[id].chat,
                        "magnet": self.downloads[id].magnet,
                        })

            with open(self.save_file, "w") as sfile:
                sfile.write(json.dumps(torrentData))

            await asyncio.sleep(30)





