#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to extract publisher data from BEIC's APE records in UNIMARC format.
"""
#
# (C) Federico Leva e Fondazione BEIC, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#
from pymarc import MARCReader
import unicodecsv as csv
import re

# Make sure it's UTF-8
# yaz-marcdump -i marc -f marc8 -t utf8 -o marc input.mrc > input.utf8.mrc

f = open('input.mrc', 'rb')
out = open('publishers.csv', 'w')
reader = MARCReader(f)
writer = csv.writer(out,
		delimiter=b',',
		lineterminator='\n',
		quoting=csv.QUOTE_MINIMAL,
		encoding='utf-8'
		)
writer.writerow([u'Città', u'Editore', u'Anno', 'Concatenato'])

for record in reader:
	try:
		pub = record.get_fields('210')[0]
		city = pub.get_subfields('a')[0]
		pubname = pub.get_subfields('c')[0]
		year = pub.get_subfields('d')[0]
		# Remove noisy specifications
		strip = re.sub(r'([\[\]\\]|c(?=[0-9])|(?<=[0-9])[?!-]+$|stampa )', '', pub.value())
		writer.writerow([city, pubname, year, strip])
	except IndexError:
		continue

f.close()
out.close()
