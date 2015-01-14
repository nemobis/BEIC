#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to upload images from BEIC.it to Wikimedia Commons.

"""
#
# (C) Federico Leva, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.1'
#

import pywikibot
import pywikibot.data.api
from pywikibot import config
from upload import UploadRobot
import requests
from lxml import html
import sys
import os
import re
from collections import namedtuple
import csv

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

        if titles:
            for row in titles:
                if row.pid and row.path:
                    pid = row.pid
                    path = row.path
                else:
                    pywikibot.output("We can't do anything without PID and path, skip: " + row)
                    pass
                fid = ""
                note = ""
                if row.fid:
                    fid = row.fid
                if row.note:
                    note = row.note

                pywikibot.output("Going to process PID: " + pid)
                self.processPID(pid, path, fid, note)

    def processPID(self, pid, path, fid="", note=""):

        author = ""
        title = ""
        fulltitle = ""
        publisher = ""
        year = ""
        place = ""
        language = ""
        categories = ""

        digitool = requests.get("http://131.175.183.1/webclient/MetadataManager?descriptive_only=true&pid=" + pid)
        data = html.fromstring(digitool.text)

        # http://www.w3.org/TR/xpath/#path-abbrev
        # There should be at least one of these...
        try:
            title = data.xpath('//td[text()="Uniform Title"]/../td[5]/text()')[0]
        except:
            try:
                title = data.xpath('//td[text()="Main Uni Title"]/../td[5]/text()')[0]
            except:
                try:
                    title = data.xpath('//td[text()="Main Title"]/../td[5]/text()')[0]
                except:
                    pywikibot.output("WARNING: No title found for PID: " + pid)
        try:
            fulltitle = re.sub(r"\n", "", data.xpath('//td[text()="Pref. Cit. Note"]/../td[5]/text()')[0] )
            language = data.xpath('//td[text()="Language Code"]/../td[5]/text()')[0]
        except:
            fulltitle = title

        # The pseudo-field "a" is not always in the same position (row)
        # For following-sibling etc. see http://www.w3.org/TR/xpath/#section-Location-Steps
        try:
            if data.xpath('//td[text()="Personal Name"]/../td[4]/text()')[0] == 'a':
                author = data.xpath('//td[text()="Personal Name"]/../td[5]/text()')[0]
            else:
                author = data.xpath('//td[text()="Personal Name"]/../following::td[text()="a"][1]/../td[last()]/text()')[0]
        # TODO: Reduce redundancy
        except:
            if data.xpath('//td[text()="A.E. Pers. Name"]/../td[4]/text()')[0] == 'a':
                author = data.xpath('//td[text()="A.E. Pers. Name"]/../td[5]/text()')[0]
            else:
                author = data.xpath('//td[text()="A.E. Pers. Name"]/../following::td[text()="a"][1]/../td[last()]/text()')[0]
        try:
            place = data.xpath('//td[text()="Imprint"]/../td[5]/text()')[0]
            year = data.xpath('//td[text()="Imprint"]/../following-sibling::tr[position()=2]/td[3]/text()')[0]
            publisher = data.xpath('//td[text()="Imprint"]/../following-sibling::tr[position()=1]/td[3]/text()')[0]
            # We can finally produce a filename it.wikisource likes!
            commons = re.split("(,| :)", author)[0] + " - " + title + ", " + year + " - " + path
        except:
            # Well, almost
            commons = re.split("(,| :)", author)[0] + " - " + title + " - " + path

        # Ensure the title isn't invalid
        commons = re.sub(r"[<>\[\]|{}]", "", commons)
        commons = commons[:200]

        pywikibot.output("The filename on MediaWiki will be: " + commons)

        subjects = data.xpath('//td[text()="Subject-Top.Trm"]/../td[5]/text()')
        subjects = subjects + data.xpath('//td[text()="Local subject"]/../td[5]/text()')
        for sub in subjects:
            categories = categories + "[[Category:" + sub + "]]\n"

        description =            u"{{Book " + \
        "\n|Author         = " + author +    \
        "\n|Translator     = " + \
        "\n|Editor         = " + \
        "\n|Title          = " + title +     \
        "\n|Subtitle       = " + \
        "\n|Volume         = " + \
        "\n|Edition        = " + \
        "\n|Publisher      = " + publisher + \
        "\n|Printer        = " + \
        "\n|City           = " + place +     \
        "\n|Language       = " + language +  \
        "\n|Date           = {{other date|CE| " + year + " }}" \
        "\n|Description    = {{it|1= " + fulltitle + ". " + note + " }}" \
        "\n|Source         = {{BEIC|pid= " + pid + " |id= " + fid +  " }}" \
        "\n|Institution    = {{Institution:BEIC}}" \
        "\n|Permission     = {{PD-old-100-1923}}" \
        "\n|Other_versions = " \
        "\n|Linkback       = " \
        "}}" + "\n\n" + categories

        pywikibot.output("Going to try upload with this information" + \
        " we assembled: " + description)

        upload = UploadRobot(path, description=description, useFilename=commons,
                             keepFilename=True, verifyDescription=False)
        upload.run()

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
