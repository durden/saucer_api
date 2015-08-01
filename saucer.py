"""Module for retrieving current beers offered by Houston area Flying Saucer"""

import re
import urllib2
import time

from BeautifulSoup import BeautifulSoup


class Saucer():
    """API for users to retreive beer information from Flying Saucer"""
    BOTTLE = "Bottle"
    DRAFT = "Draft"
    CAN = "Can"
    CASK = "Cask"

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

        dict_ = {}
        for tr in res:
            tds = tr.findAll('td')

            # key value pairs
            if len(tds) != 2:
                continue

            dict_[str(tds[0].string)] = str(tds[1].string)

        self.create_details += time.time() - t1

        return dict_

    def get_all_beers(self):
        """Fetch all beer type/names from saucer website
            - Return list of dictionaries with keys: id, type, name
        """

        # Hide the ugly yql/html parsing and create list of dictionaries
        beers = []
        btl = re.compile(Saucer.__btl_str, re.I)
        cask = re.compile(Saucer.__cask_str, re.I)
        can = re.compile(Saucer.__can_str, re.I)

        url = 'http://www.beerknurd.com/store.sub.php?store=6&sub=beer&groupby=name'
        f = urllib2.urlopen(url)
        soup = BeautifulSoup(f.read())
        brews = soup.find('select', id='brews')

        for tag in brews:
            name = str(tag.string.strip())
            if not name:
                continue

            beer = {}
            beer['id'] = str(tag['value'].strip())
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

        all_details = []
        for id_ in beers:
            url = 'http://www.beerknurd.com/store.beers.process.php?brew=%s' % (id_)
            f = urllib2.urlopen(url)

            soup = BeautifulSoup(f.read())
            trs = soup.findAll('tr')

            details = self.__create_detail_list(trs)

            # Saucer html will return None for everything if a beer doesn't
            # exist so remove it from return.
            values = details.values()
            if values == ['None'] * len(values):
                continue

            all_details.append(details)

        t1 = time.time()
        return all_details
