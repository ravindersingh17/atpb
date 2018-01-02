import re
from bs4 import BeautifulSoup as BS
import aiohttp

async def getsearches(search):
    SITE = 'https://tpbunblocked.org'
    results = []

    rep = lambda x, y: x + y if len(y) == 2 else x + "0" + y
    match = re.search("(\d{1,2})-(\d{1,2})", search)
    if match: search = re.sub("(\d{1,2})-(\d{1,2})", rep("S", match.group(1)) + rep("E", match.group(2)), search)

    async with aiohttp.ClientSession() as session:
        async with session.get(SITE + '/s/', params = {"q": search}) as serverres:
            response = await serverres.text()

    soup = BS(response, 'html.parser')
    links = soup.find_all('a','detLink')
    desc = soup.find_all('font', 'detDesc')


    seedleechlist = []
    seedleech = soup.find_all(align="right")

    for s in seedleech:
        seedleechlist.append(s.text)
    returnData = []
    for i in range(len(links)):
        detail = re.search("Uploaded\s*(.*?), Size\s*(.*?), ULed by (.*)", desc[i].text)
        returnData.append({
                'text': links[i].text,
                'date': detail.group(1),
                'size': detail.group(2),
                'uploader': detail.group(3),
                'desc': desc[i].text,
                'seeders': (seedleechlist[i*2], seedleechlist[i*2+1]),
                'link': SITE + links[i]['href']
                })
    return returnData

async def gettorrent(link):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as serverres:
            response = await serverres.text()
    soup = BS(response, 'html.parser')
    return soup.find('a', title='Get this torrent')['href']
