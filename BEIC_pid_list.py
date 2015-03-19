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

import csv
from kitchen.text.converters import to_unicode, to_bytes
# This also imports other stuff and lxml did not work for me in python3
# but pywikibot is not needed for this function, just comment it out.
from BEIC_pid_upload import getMetadata

with open('BEIC-opere.csv', 'w') as csvfile:
    opere = csv.writer(csvfile,
                       delimiter='\t',
                       lineterminator='\n',
                       quoting=csv.QUOTE_MINIMAL)
    opere.writerow(['Autore', 'Opera', 'Collezione', 'PID', 'System No.', 'IA', 'URL', 'Metadati'])
    for pid in open('BEIC-pids.txt', 'r').read().strip().splitlines():
        pid = to_unicode(pid)
        d = getMetadata(pid)

        if d is None:
            print "Could not find data for PID: " + pid
            continue
        if d['ia'] is True:
            ia = u"TRUE"
        else:
            ia = u""

        opere.writerow([to_bytes(d['author']),
                        to_bytes(d['title']),
                        to_bytes(', '.join(d['subjects'])),
                        to_bytes(d['pid']),
                        to_bytes(d['sysno']),
                        to_bytes(ia),
                        to_bytes('http://gutenberg.beic.it/webclient/DeliveryManager?pid=' + d['pid']),
                        to_bytes('http://131.175.183.1/webclient/MetadataManager?descriptive_only=true&pid=' + d['pid'])
                        ])
