import re
import urllib
import time

from django.utils import simplejson


class Saucer():
    BOTTLE = "Bottle"
    DRAFT = "Draft"
    CAN = "Can"
    CASK = "Cask"

    create_details = 0.0
    fetch = 0.0
    san = 0.0

    __btl_str = r"\(BTL\)"
    __can_str = r"\(CAN\)"
    __cask_str = r"\(CASK\)"

    def reset_stats(self):
        Saucer.create_details = 0.0
        Saucer.fetch = 0.0
        Saucer.san = 0.0

    def __sanitize(self, arg):
        x = time.time()

        ret = "N/A"

        if (isinstance(arg, unicode)):
            # Suppress multiple whitespace characters and leading/trailing
            # whitespace
            ret = re.sub('\s+', ' ', arg).strip()

        # Sometimes there are some weird stuff in the scraped text, so just
        # try to treat it a like a dictionary with 'content' as key
        if (isinstance(arg, dict)):
            try:
                # Suppress multiple whitespace characters and leading/trailing
                # whitespace
                ret = re.sub('\s+', ' ', arg['content']).strip()
            except KeyError:
                pass

        y = time.time()
        Saucer.san += (y - x)

        return ret

    def __fetch_json(self, url):
        base_url = "http://query.yahooapis.com/v1/public/yql"
        return simplejson.load(urllib.urlopen( "%s?%s" % (base_url, url)))

    def __create_detail_list(self, res):
        x = time.time()

        size = len(res)
        ii = 0
        mylist = []
        mydict = {}

        # Loop through resulting list in pairs and collect 6 key,value pairs
        # and then add the dictionary to the returning list
        while ii < size:
            key = self.__sanitize(res[ii])
            val = self.__sanitize(res[ii + 1])

            # Handles the case that some entries might not have 6 unique pairs
            # so if we already have the key, this entry is another dictionary
            if key in mydict:
                mylist.append(mydict)
                mydict = {}

            mydict[key] = val

            # Last go around in loop, save it
            if ii + 2 >= size:
                mylist.append(mydict)

            ii += 2

        y = time.time()
        Saucer.create_details += (y - x)

        return mylist

    def getAllBeers(self):
        url = urllib.urlencode({"format":"json",
            "q":"select * from html where url=\"http://www.beerknurd.com/store.sub.php?store=6&sub=beer&groupby=name\" and xpath='//select[@id=\"brews\"]/option'"})

        res = self.__fetch_json(url)

        # Hide the ugly yql/html parsing and create list of dictionaries 
        beers = []
        btl = re.compile(Saucer.__btl_str, re.I)
        cask = re.compile(Saucer.__cask_str, re.I)
        can = re.compile(Saucer.__can_str, re.I)

        for tmp in res['query']['results']['option']:
            name = tmp['content']

            beer = {}
            beer['id'] = tmp['value'].strip()
            beer['type'] = Saucer.DRAFT 
            beer['name'] = self.__sanitize(name)

            # Serving type
            if btl.search(name):
                beer['type'] = Saucer.BOTTLE
                beer['name'] = self.__sanitize(btl.sub('', name))
            elif cask.search(name):
                beer['type'] = Saucer.CASK
                beer['name'] = self.__sanitize(cask.sub('', name))
            elif can.search(name):
                beer['type'] = Saucer.CAN
                beer['name'] = self.__sanitize(can.sub('', name))

            beers.append(beer)

        return beers

    def getBeerDetails(self, beers):
        xpath= "xpath='//table/tr/td/p'"
        q = "select * from html where ("
        ii = 0

        for beer in beers:
            if ii:
                q += " or "

            q += "url=\"http://www.beerknurd.com/store.beers.process.php?brew=%s\"" % (beer)
            ii = 1
        q += ") and %s " % (xpath)

        x = time.time()

        res = self.__fetch_json(urllib.urlencode({"format":"json", "q": q}))

        y = time.time()
        Saucer.fetch += (y - x)

        try:
            return self.__create_detail_list(res['query']['results']['p'])
        # Maybe no results came back b/c beers were invalid, etc.
        except KeyError:
            return []
