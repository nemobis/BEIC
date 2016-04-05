#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to upload images from BEIC.it to Wikimedia Commons.

"""
#
# (C) Federico Leva e Fondazione BEIC, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.3'
#

#import pywikibot
#import pywikibot.data.api
#from pywikibot import config
#from upload import UploadRobot
import requests
from lxml import html
import sys
import os
import re
from collections import namedtuple
import csv
from kitchen.text.converters import to_unicode

class BEICRobot:

    def __init__(self, filename):
        self.repo = pywikibot.Site('commons', 'commons')
        self.filename = filename
        if not os.path.exists(self.filename):
            pywikibot.output('Cannot find %s. Try providing the absolute path.'
                             % self.filename)
            sys.exit(1)

    def run(self, filename):
        with open(filename, 'r') as f:
            source = csv.reader(f, delimiter='\t')
            header = next(source)
            pywikibot.output("Header of the input table: " + ', '.join(header) )
            titles = namedtuple('titles', ', '.join(header))
            titles = [titles._make(row) for row in source]

        if not titles:
            pywikibot.output("We were not able to extract the data to work on. Exiting.")
            return

        for row in titles:
            if not (row.pid and row.path):
                pywikibot.output("We can't do anything without PID and path, skip: " + row)
                continue

            pid = to_unicode(row.pid)
            if os.path.isfile(row.path):
               path = to_unicode(row.path)
            else:
                # Missing extension or other mistake?
                dirname = os.path.abspath(os.path.dirname(row.path))
                pywikibot.output("Will look for a file in directory: " + row.pid)
                chance = [f for i, f in enumerate(os.listdir(dirname))
                         if f.startswith(os.path.basename(row.path))]
                if len(chance) == 1:
                    path = to_unicode(dirname + "/" + chance[0])
                    pywikibot.output("We found: " + path)
                else:
                    pywikibot.output("Exploring files with prefix " + os.path.basename(row.pid))
                    chance = [f for i, f in enumerate(os.listdir(dirname))
                          if f.startswith(os.path.basename(row.pid))]
                    if len(chance) == 1:
                        path = to_unicode(dirname + "/" + chance[0])
                    else:
                        pywikibot.output("Can't find nor guess file for PID: " + row.pid)
                        path = False

            fid = u""
            note = u""
            try:
                fid = to_unicode(row.fid)
                note = to_unicode(row.note)
            except:
                pywikibot.output("Error while fetching note or fid")

            if pid and path:
                pywikibot.output("Going to process PID: " + pid)
                self.processPID(pid, path, fid, note)

    def processPID(self, pid, path, fid=u"", note=u""):
        d = self.getMetadata(pid)

        if d is None:
            pywikibot.output("Could not retrieve data for PID: " + pid)
            return
        # TODO: make optional
        if d['ia'] is True:
            pywikibot.output("Not going to upload Internet Archive book: " + pid)
            with open("BEIC-IA-pids.txt", mode='a') as f:
                    f.write(pid.encode("utf-8")+"\n")
            return False
        if d['title'] == u"":
            pywikibot.output("WARNING: No title found for PID: " + pid)

        try:
            # We can finally produce a filename it.wikisource likes!
            commons = re.split("(,| :)", d['author'])[0] + u" - " + d['title'] + u", " + d['year'] \
                + " - " + os.path.basename(path)
        except:
            # Well, almost
            commons = re.split("(,| :)", d['author'])[0] + u" - " + d['title'] + u" - " \
                + os.path.basename(path)

        # Ensure the title isn't invalid
        commons = re.sub(r"[<>\[\]|{}?]", "", commons)
        if ( len(commons) > 200 ):
            cut = len(commons) - 200
            commons = commons[cut:]

        pywikibot.output("The filename on MediaWiki will be: " + commons)

        categories = u""
        for sub in d['subjects']:
            categories = categories + u"[[Category:" + to_unicode(sub) + u"]]\n"

        description = u"""{{Book
|Author         = %s
|Title          = %s
|Publisher      = %s
|City           = %s
|Language       = %s
|Date           = {{other date|CE| %s }}
|Description    = {{it|1= %s. %s }}
|Source         = {{BEIC|pid= %s |id= %s }}
|Institution    = {{Institution:BEIC}}
|Permission     = {{PD-old-100-1923}}
}}

%s""" % (d['author'], d['title'], d['publisher'], d['place'], d['language'],
         d['year'], d['fulltitle'], d['note'], d['pid'], d['fid'], d['categories'])
        # Ugly http://comments.gmane.org/gmane.comp.python.lxml.devel/5054
        # Hopefully all fixed with https://pythonhosted.org/kitchen/api-text-converters.html

        pywikibot.output("Going to try upload with this information: ")
        pywikibot.output(description)

        # FIXME: No way to avoid being prompted if the file already exists. Patch upload.py?
        try:
            upload = UploadRobot(path, description=description,
                                 useFilename=commons, keepFilename=True,
                                 verifyDescription=False, ignoreWarning=True, aborts=True)
            upload.run()
        except:
            pywikibot.output("ERROR: The upload could not be completed.")

def getMetadata(pid):

    # Reminder what to get:
    d = {}
    d['author'] = u""
    d['title'] = u""
    d['fulltitle'] = u""
    d['publisher'] = u""
    d['year'] = u""
    d['place'] = u""
    d['language'] = u""
    d['sysno'] = u""

    try:
        digitool = requests.get("http://131.175.183.15/webclient/MetadataManager?descriptive_only=true&pid=" + pid)
        data = html.fromstring(digitool.text)
    except:
        return None

    if data.xpath("//td[contains(text(),'CaSfIA')]"):
        d['ia'] = True
    else:
        d['ia'] = False

    # http://www.w3.org/TR/xpath/#path-abbrev
    # There should be at least one of these...
    try:
        d['title'] = to_unicode(data.xpath('//td[text()="Uniform Title"]/../td[5]/text()')[0])
    except:
        try:
            d['title'] = to_unicode(data.xpath('//td[text()="Main Uni Title"]/../td[5]/text()')[0])
        except:
            try:
                d['title'] = to_unicode(data.xpath('//td[text()="Main Title"]/../td[5]/text()')[0])
            except:
                pass
    d['title'] = re.sub(r"  +", " ", re.sub(r"\n", "", d['title']) )
    try:
        d['fulltitle'] = re.sub(r"  +", " ",
                           re.sub(r"\n", "",
                           to_unicode(data.xpath('//td[text()="Pref. Cit. Note"]/../td[5]/text()')[0])
                           ) )
        d['language'] = to_unicode(data.xpath('//td[text()="Language Code"]/../td[5]/text()')[0])
    except:
        d['fulltitle'] = d['title']

    # The pseudo-field "a" is not always in the same position (row)
    # For following-sibling etc. see http://www.w3.org/TR/xpath/#section-Location-Steps
    try:
        if data.xpath('//td[text()="Personal Name"]/../td[4]/text()')[0] == 'a':
            d['author'] = to_unicode(data.xpath('//td[text()="Personal Name"]/../td[5]/text()')[0])
        else:
            d['author'] = to_unicode(data.xpath('//td[text()="Personal Name"]/../following::td[text()="a"][1]/../td[last()]/text()')[0])
    # TODO: Reduce redundancy
    except:
        try:
            if data.xpath('//td[text()="A.E. Pers. Name"]/../td[4]/text()')[0] == 'a':
                d['author'] = to_unicode(data.xpath('//td[text()="A.E. Pers. Name"]/../td[5]/text()')[0])
        except:
            try:
                d['author'] = to_unicode(data.xpath('//td[text()="A.E. Pers. Name"]/../following::td[text()="a"][1]/../td[last()]/text()')[0])
            except:
                pass
    try:
        d['place'] = to_unicode(data.xpath('//td[text()="Imprint"]/../td[5]/text()')[0])
        d['year'] = to_unicode(data.xpath('//td[text()="Imprint"]/../following-sibling::tr[position()=2]/td[3]/text()')[0])
        d['publisher'] = to_unicode(data.xpath('//td[text()="Imprint"]/../following-sibling::tr[position()=1]/td[3]/text()')[0])
    except:
        pass

    d['subjects'] = []
    d['subjects'] = data.xpath('//td[text()="Local subject" or text()="Capt. Supp.Mat."]/../td[5]/text()')
    # Campi spezzettati, spesso ridondanti
    # d['subjectsTree'] = data.xpath('//td[text()="Subject-Top.Trm"]

    try:
        d['yearfixed'] = re.search(
            to_unicode(data.xpath('//td[text()="Fixed Data"]/../td[2]/text()')[0]),
            r's([0-9]{4}) '
        ).group(0)
        d['geographicname'] = data.xpath('//td[text()="751"]/../td[5]/text()')[0]
        d['physical'] = []
        d['physical']['a'] = to_unicode(data.xpath('//td[text()="Physical Des."]/../td[5]/text()')[0])
        d['physical']['b'] = to_unicode(data.xpath('//td[text()="Physical Des."]/../following-sibling::tr[position()=2]/td[3]/text()')[0])
        d['general'] = data.xpath('//td[text()="General Note"]/../td[5]/text()')
    except:
        pass

    d['sysno'] = to_unicode(data.xpath('//td[text()="System No."]/../td[5]/text()'))
    if d['sysno'] == []:
        d['sysno'] = u""
    d['pid'] = to_unicode(pid)

    return d

def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """

    # process all global bot args
    # returns a list of non-global args
    for arg in pywikibot.handle_args(args):
        if arg:
            if arg.startswith('-file'):
                filename = arg[6:]

    bot = BEICRobot(filename)
    bot.run(filename)

if __name__ == "__main__":
    main()
