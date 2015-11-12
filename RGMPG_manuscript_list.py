#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to make a work list of manuscript location and code from the list at
Max-Planck-Institut für europäische Rechtsgeschichte in Frankfurt am Main,
Manuscripta juridica http://manuscripts.rg.mpg.de/, in the hardcoded range.

"""
#
# (C) Federico Leva e Fondazione BEIC, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#

import unicodecsv as csv
import requests
from lxml import html

with open('RGMPG-manuscripts.csv', 'w') as csvfile:
    opere = csv.writer(csvfile,
                       delimiter='\t',
                       lineterminator='\n',
                       quoting=csv.QUOTE_MINIMAL)
    opere.writerow(['Luogo', 'Collocazione'])
    for i in range(1, 8637):
        page = requests.get("http://manuscripts.rg.mpg.de/manuscript/%d/" % i)
        # Override encoding due to webserver bug: the HTML is UTF-8 but doesn't tell.
        # http://docs.python-requests.org/en/latest/api/#requests.Response.text
        page.encoding = 'UTF-8'
        try:
            data = html.fromstring(page.text)
        except:
            continue

        location = data.xpath('//td[text()="LOCATION"]/../td[2]/a/span/text()')[0].strip()
        manuscript = data.xpath('//td[text()="MANUSCRIPT"]/../td[2]/text()')[0]
        opere.writerow([location,
                        manuscript
                        ])
