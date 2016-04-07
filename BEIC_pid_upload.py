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
__version__ = '0.1.4'
#

try:
    import pywikibot
    import pywikibot.data.api
    from pywikibot import config
    from upload import UploadRobot
except:
    pass
import requests
# Alternative but not shipped by default: https://pythonhosted.org/uritools/
from urlparse import urljoin
from lxml import html
import sys
import os
import re
from collections import namedtuple
import csv
from kitchen.text.converters import to_unicode

class BEICRobot:

    def __init__(self, filename, material=None, method='local'):
        self.repo = pywikibot.Site('commons', 'commons')
        self.filename = filename
        self.material = material
        self.method = method
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
            if not (row.pid):
                pywikibot.output("We can't do anything without PID, skip: " + row)
                continue
            if self.method == 'local' and not row.path:
                pywikibot.output("We can't do anything without path, skip: " + row)
                continue

            pid = to_unicode(row.pid)
            if self.method == 'local':
                path = self.getLocalPath(row)
            if self.method == 'download':
                path = self.getFileFromPid(row)

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
            else:
                pywikibot.output("ERROR: PID or path missing")

    def getLocalPath(self, row):
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
        return path

    def getFileFromPid(self, row):
        pid = row.pid
        digitool = requests.get("http://gutenberg.beic.it/webclient/DeliveryManager?pid=" + pid)
        data = html.fromstring(digitool.text)
        frame = data.xpath( '//frame[contains(@src,%s)]/@src' % pid )[0]
        digitool = requests.get(urljoin(digitool.url, frame))
        data = html.fromstring(digitool.text)
        image = data.xpath( '//img[contains(@alt,%s)]/@src' % pid )[0]
        content = requests.get(urljoin(digitool.url, image))
        path = '/tmp/' + pid
        pywikibot.output("DOWNLOAD %s to %s from %s" % (content.status_code, path, content.url))
        with open(path, "wb") as local:
            local.write(content.content)
        return path

    def processPID(self, pid, path, fid=u"", note=u""):
        d = getMetadata(pid)

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
            if self.material == 'photo':
                if d['geographicname'] and d['yearfixed']:
                    d['title'] = "%s (%s, %s)" % ( d['title'], d['geographicname'], d['yearfixed'] )
                commons = "Paolo Monti - %s - BEIC %s.jpg" % ( d['title'], pid)
            else:
                # We can finally produce a filename it.wikisource likes!
                commons = re.split("(,| :)", d['author'])[0] + u" - " + d['title'] \
                    + u", " + d['year'] + " - " + os.path.basename(path)
        except:
            # Well, almost
            commons = re.split("(,| :)", d['author'])[0] + u" - " + d['title'] + u" - " \
                + os.path.basename(path)

        # Ensure the title isn't invalid
        commons = re.sub(r"[<>\[\]|{}?]", "", commons)
        if ( len( commons ) > 200 ):
            cut = len( commons ) - 200
            commons = commons[cut:]

        pywikibot.output("The filename on MediaWiki will be: " + commons)

        categories = u""
        for sub in d['subjects'] + d['subjectsTree']:
            categories = categories + u"[[Category:" + to_unicode(sub) + u"]]\n"

        if self.material == 'photo':
            description = u"""
{{Photograph
 |photographer       = {{Creator:Paolo Monti}}
 |title              = %s
 |description        = %s
 |depicted people    =
 |depicted place     = %s
 |date               = %s
 |medium             = %s
 |dimensions         = %s
 |institution        = {{Institution:BEIC}}
 |department         =
 |references         =
 |object history     =
 |exhibition history =
 |credit line        =
 |notes              =
 |accession number   = %s
 |source             = {{BEIC|pid= %s |id= %s |collezione=Monti}}
 |permission         = {{cc-by-sa-4.0}}
 |inscriptions       = %s
 |other_versions     =
}}

%s""" % ( d['title'], d['fulltitle'], d['geographicname'], d['yearfixed'],
    d['physical-a'], d['physical-b'], d['sysno'], d['pid'], d['sysno'],
    re.sub("\n\s+", "", "\n*" + "\n*".join(d['general'])),
    re.sub("\n\s+", "", categories) )

        else:
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

%s""" % ( d['author'], d['title'], d['publisher'], d['place'], d['language'],
         d['year'], d['fulltitle'], d['note'], d['pid'], d['fid'], categories )
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
            os.remove(path)
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
        digitool = requests.get("http://gutenberg.beic.it/webclient/MetadataManager?descriptive_only=true&pid=" + pid)
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

    d['subjects'] = d['subjectsTree'] = []
    d['subjects'] = data.xpath('//td[text()="Local subject" or text()="Capt. Supp.Mat."]/../td[5]/text()')
    d['subjectsTree'] = data.xpath('//td[text()="Subject-Top.Trm" or text()="Indx Term Unco"]/../td[5]/text()')

    try:
        d['geographicname'] = u""
        d['yearfixed'] = u""
        d['physical-a'] = d['physical-b'] = u""
        d['general'] = u""
        d['yearfixed'] = re.search(
            r's([0-9]{4})\b',
            to_unicode(data.xpath('//td[text()="Fixed Data"]/../td[2]/pre/text()')[0]),
        ).group(1)
        d['geographicname'] = data.xpath('//td[text()="751"]/../td[5]/text()')[0]
        d['physical-a'] = to_unicode(data.xpath('//td[text()="Physical Des."]/../td[5]/text()')[0])
        d['physical-b'] = to_unicode(data.xpath('//td[text()="Physical Des."]/../following-sibling::tr[position()=2]/td[3]/text()')[0])
        d['general'] = data.xpath('//td[text()="General Note"]/../td[5]/text()')
    except:
        pass

    # When system number isn't available, default to control number.
    # (IT-MiFBE)mets.bibit.ia00372300 vs. MNG-90001438 + c. no. ID IT-MiFBE
    d['sysno'] = to_unicode( ( data.xpath('//td[text()="System No."]/../td[5]/text()')
        + data.xpath('//td[text()="Control No."]/../td[2]/pre/text()') )[0] )
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
    material = None
    method = 'local'
    for arg in pywikibot.handle_args(args):
        if arg:
            if arg.startswith('-file'):
                filename = arg[6:]
            if arg.startswith('-photo'):
                material = 'photo'
            if arg.startswith('-download'):
                method = 'download'

    bot = BEICRobot(filename, material, method)
    bot.run(filename)

if __name__ == "__main__":
    main()
