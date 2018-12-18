#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to make a work list of authors/works from PIDs, quick & dirty.

"""
#
# (C) Federico Leva e Fondazione BEIC, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#

import unicodecsv as csv
from kitchen.text.converters import to_unicode, to_bytes
# This also imports other stuff and lxml did not work for me in python3
# but pywikibot is not needed for this function, just comment it out.
from BEIC_pid_upload import getMetadata

with open('BEIC-opere.csv', 'w') as csvfile:
    opere = csv.writer(csvfile,
                       delimiter='\t',
                       lineterminator='\n',
                       quoting=csv.QUOTE_MINIMAL,
                       encoding='utf-8')
    opere.writerow(['Autore', 'Opera', 'Citazione', 'Collezione', 'Soggetti', 'PID', 'System No.', 'IA', 'URL', 'Metadati'])
    # Esempio per elencare i PID di tutti i METS in DigiTool:
    # ssh dtl@atena.beic.it 'find /exlibris/dtl/j3_1/digitool/home/profile/work/ -maxdepth 1 -name "*.xml" | grep -Eo "\b[0-9]+\b"' > BEIC-pids.txt
    for pid in open('BEIC-pids.txt', 'r').read().strip().splitlines():
        pid = to_unicode(pid)
        d = None
        try:
            d = getMetadata(pid)
        except:
            pass

        if d is None:
            print "Could not find data for PID: " + pid
            continue
        if d['ia'] is True:
            ia = u"TRUE"
        else:
            ia = u""

        print "Writing metadata for PID: " + pid
        opere.writerow([to_bytes(d['author']),
                        to_bytes(d['title']),
                        to_bytes(d['fulltitle']),
                        to_bytes('; '.join(d['subjects'])),
                        to_bytes('; '.join(d['subjectsTree'])),
                        to_bytes(d['pid']),
                        to_bytes(d['sysno']),
                        to_bytes(ia),
                        to_bytes('https://gutenberg.beic.it/webclient/DeliveryManager?pid=' + d['pid']),
                        to_bytes('https://gutenberg.beic.it/webclient/MetadataManager?descriptive_only=true&pid=' + d['pid'])
                        ])
