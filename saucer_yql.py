#!/usr/bin/python

import urllib
import simplejson
import re
import sys

from api.saucer import Saucer

class Beer():
    def __init__(self, name, type, style, descr):
       self.name = name
       self.type = type
       self.style = style
       self.descr = descr

    # Really only used for printing for csv output
    def csv(self):
        # Subs for uploading to app engine with uploader class
        self.name = re.sub('"', '""', self.name)
        self.type = re.sub('"', '""', self.type)
        self.style = re.sub('"', '""', self.style)
        self.descr = re.sub('"', '""', self.descr)
        return "\"%s\",\"%s\",\"%s\",\"%s\"\n" % (self.name, self.type,
                                            self.style, self.descr)

    def __str__(self):
        return "Name:%s\nType:%s\nStyle:%s\nDescription:%s\n\n" % (self.name, self.type,
                                            self.style, self.descr)
 
def main(file, max):
    saucer = Saucer()
    bottles = []
    drafts = []
    ids = []
    ii = 0
    group = 20

    if max < group:
        group = max

    beers = saucer.getAllBeers()

    for beer in beers:
        ids.append(beer['id'])
        ii += 1
        if ii >= group:
            break

    details = saucer.getBeerDetails(ids)
    ii = 0

    for beer in beers:
        brew = Beer(beer['name'], beer['type'], details[ii]['Style:'],
                    details[ii]['Description:'])

        if beer['type'] == Saucer.BOTTLE:
            bottles.append(brew)
        else:
            drafts.append(brew)

        ii += 1

        if (max > 0 and ii >= max) or ii >= len(details):
            break

    if len(drafts):
        if file is None:
            print "\n\nDrafts:\n"

        for beer in drafts:
            if file is None:
                print beer
            else:
                file.write("%s" % beer.csv())

    if len(bottles):
        if file is None:
            print "\n\nBottles:\n"

        for beer in bottles:
            if file is None:
                print beer
            else:
                file.write("%s" % beer.csv())


if __name__ == "__main__":
    file = None
    max = 0

    # FIXME: Catch errors
    if len(sys.argv) > 1:
        max = int(sys.argv[1])

    if len(sys.argv) > 2:
        file = open(sys.argv[2], 'w')

    main(file, max)

    if file is not None:
        file.close()
