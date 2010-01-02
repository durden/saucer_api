"""Module for retrieving current beers offered by Houston area Flying Saucer"""

import re
import urllib
import time

import simplejson


def fetch_json(url):
    """Fetch json representation of given url"""
    return simplejson.load(urllib.urlopen("%s?%s" % (Saucer.BASE_URL, url)))


class Saucer():
    """API for users to retreive beer information from Flying Saucer"""
    BOTTLE = "Bottle"
    DRAFT = "Draft"
    CAN = "Can"
    CASK = "Cask"

    BASE_URL = "http://query.yahooapis.com/v1/public/yql"
    __btl_str = r"\(BTL\)"
    __can_str = r"\(CAN\)"
    __cask_str = r"\(CASK\)"

    def __init__(self):
        """Create instance of Saucer API"""
        self.create_details = 0.0
        self.fetch = 0.0
        self.san = 0.0

    def reset_stats(self):
        """Reset debug stat collection details"""
        self.create_details = 0.0
        self.fetch = 0.0
        self.san = 0.0

    def __sanitize(self, arg):
        """Cleanup string/dictionary by compressing whitespace characters"""
        t1 = time.time()
        ret = "N/A"

        if (isinstance(arg, unicode) or isinstance(arg, str)):
            # Suppress multiple whitespace characters and leading/trailing
            # whitespace
            ret = re.sub('\s+', ' ', arg).strip()

        # Sometimes there are some weird stuff in the scraped text, so just
        # try to treat it a like a dictionary with 'content' as key
        if (isinstance(arg, dict)):
            try:
                ret = re.sub('\s+', ' ', arg['content']).strip()
            except KeyError:
                pass

        t2 = time.time()
        self.san += (t2 - t1)
        return ret

    def __create_detail_list(self, res):
        """Translate res into list of dictionaries
            - Treat res as list of key/value pairs (size must be even)
        """
        t1 = time.time()

        size = len(res)
        ii = 0
        mylist = []
        mydict = {}

        if size % 2:
            raise Exception("Invalid result (%s)" % (res))

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

        self.create_details += time.time() - t1

        return mylist

    def get_all_beers(self):
        """Fetch all beer type/names from saucer website
            - Return list of dictionaries with keys: id, type, name
        """

        url = urllib.urlencode({"format": "json",
            "q": "select * from html where url=\"" + \
                "http://www.beerknurd.com/store.sub.php?" + \
                "store=6&sub=beer&groupby=name\" and " + \
                "xpath='//select[@id=\"brews\"]/option'"})

        res = fetch_json(url)

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

    def get_beer_details(self, beers):
        """Fetch beer details from saucer website
            - Treat beers as list of ids (retrieved from get_all_beers method)
              to fetch details about
        """

        xpath = "xpath='//table/tr/td/p'"
        query = "select * from html where ("
        ii = 0

        for beer in beers:
            if ii:
                query += " or "

            query += "url=\"http://www.beerknurd.com/" + \
                     "store.beers.process.php?brew=%s\"" % (beer)
            ii = 1

        query += ") and %s " % (xpath)
        t1 = time.time()
        res = fetch_json(urllib.urlencode({"format": "json", "q": query}))
        self.fetch += time.time() - t1

        try:
            return self.__create_detail_list(res['query']['results']['p'])
        # Maybe no results came back b/c beers were invalid, etc.
        except KeyError:
            return []
