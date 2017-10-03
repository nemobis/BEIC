#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to extract holdings strings from ISTC given a list of codes.

"""
#
# (C) Federico Leva e Fondazione BEIC, 2017
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#

import unicodecsv as csv
import requests
from lxml import html

with open('ISTC-holdings.csv', 'w') as csvfile:
    opere = csv.writer(csvfile,
                       delimiter='\t',
                       lineterminator='\n',
                       quoting=csv.QUOTE_MINIMAL)
    opere.writerow(['Codice ISTC', 'Collocazione', 'Tutte le collocazioni'])
    for istcid in open('ISTC-ids.txt', 'r').read().strip().splitlines():
        page = requests.get("http://data.cerl.org/istc/%s" % istcid)
        try:
            data = html.fromstring(page.text)
            # data.xpath("//h3[text()='Holdings']/following-sibling::div[position()=1]/span/text()")
            locations = data.xpath("//h3[text()='Holdings']/following-sibling::div[@class='ample-display-line']//span[contains(@class,'ample-display-content')]/text()")
            for location in locations:
                opere.writerow([istcid, location])
        except:
            continue

