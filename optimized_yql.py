#!/usr/bin/python

import urllib
import simplejson
import re

# FIXME: Consistent variable names, casing, etc.
# FIXME: Break up strings better

class Beer():
    def __init__(self, name, type, style, descr):
       self.name = self.__sanitize__(name)
       self.type = self.__sanitize__(type)
       self.style = self.__sanitize__(style)
       self.descr = self.__sanitize__(descr)

    def __str__(self):
        return "Name:%s\nType:%s\nStyle:%s\nDescription:%s\n\n" % (self.name, self.type,
                                            self.style, self.descr)

    def __sanitize__(self, arg):
        # Verify the object is a string, otherwise default it
        if (not isinstance(arg, str)):
            return "N/A"

        # Suppress multiple spaces and newlines
        return re.sub(' +', ' ', re.sub('\n', '', arg)).strip()
 
class SaucerApi():
    BOTTLE = "Bottle"
    DRAFT = "Draft"

    __btl_str__ = r"\(BTL\)"

    def __fetch_json__(self, url):
        base_url = "http://query.yahooapis.com/v1/public/yql"
        return simplejson.load(urllib.urlopen( "%s?%s" % (base_url, url)))

    def __create_detail_list__(self, res):
        size = len(res)
        ii = 0
        sep = 1
        mylist = []
        dict = {}

        # Loop through resulting list in pairs and collect 6 key,value pairs
        # and then add the dictionary to the returning list
        while ii < size: 
            key = res[ii] 
            val = res[ii + 1]

            dict[key] = val

            # End of unique pairs
            if not sep % 6:
                mylist.append(dict)
                dict = {}

            ii += 2
            sep += 1

        return mylist

    def getAllBeers(self):
        url = urllib.urlencode({"format":"json",
            "q":"select * from html where url=\"http://www.beerknurd.com/store.sub.php?store=6&sub=beer&groupby=name\" and xpath='//select[@id=\"brews\"]/option'"})

        res = self.__fetch_json__(url)

        # Hide the ugly yql/html parsing and create list of dictionaries 
        beers = []
        for tmp in res['query']['results']['option']:
            beer = {}

            beer['name'] = tmp['content'].strip()
            beer['id'] = tmp['value'].strip()
            beer['type'] = SaucerApi.DRAFT 

            # Bottle or draft?
            if re.compile(SaucerApi.__btl_str__).search(beer['name']):
                beer['type'] = SaucerApi.BOTTLE

                # Remove the bottle string in name
                beer['name'] = re.sub(SaucerApi.__btl_str__, '', beer['name'])

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
        res = self.__fetch_json__(urllib.urlencode({"format":"json", "q": q}))
        return self.__create_detail_list__(res['query']['results']['p'])

def main():
    bottles = []
    drafts = []
    saucer = SaucerApi()
    ii = 0

    beers = saucer.getAllBeers()
    ids = []

    for beer in beers:
        ids.append(beer['id'])
        ii += 1
        if ii >= 5:
            break

    details = saucer.getBeerDetails(ids)
    ii = 0

    for beer in beers:
        brew = Beer(beer['name'], beer['type'], details[ii]['Style:'],
                    details[ii]['Description:'])

        if beer['type'] == SaucerApi.BOTTLE:
            bottles.append(brew)
        else:
            drafts.append(brew)

        ii += 1
        if ii >= 5:
            break

    if len(drafts):
        print "\n\nDrafts:"
        for beer in drafts:
            print beer

    if len(bottles):
        print "\n\nBottles:"
        for beer in bottles:
            print beer


if __name__ == "__main__":
    main()
