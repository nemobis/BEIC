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
            location = data.xpath("//span[text()='Italy and Vatican City']/following-sibling::span/text()")[0]
            # Brutal concatenation
            location2 = " ".join(data.xpath("//span[text()='Italy and Vatican City'][1]/following-sibling::span//text()"))
            opere.writerow([istcid, location, location2])
        except:
            continue

