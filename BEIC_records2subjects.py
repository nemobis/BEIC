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
out = open('subjects.csv', 'w')
reader = MARCReader(f)
writer = csv.writer(out,
		delimiter=b'\t',
		lineterminator='\n',
		quoting=csv.QUOTE_ALL,
		encoding='utf-8'
		)
writer.writerow([u'Inventario', u'Identificativo', u'Campo', 'Sottocampi'])
with open('bids.txt', 'rb') as b:
	bids = set([i.strip() for i in b])

for record in reader:
	bid = record.get_fields('001')[0].value()
	if bid in bids:
		print u"Found a match for record %s" % bid
		try:
			inv = record.get_fields('950')[0].get_subfields('e')[0]
			subjects = record.get_fields('606', '676')
			for subject in subjects:
				sl = subject.subfields
				sc = u''
				for i in range(0, len(sl)/2):
					sc = sc + u"${}{}".format(sl[i*2], sl[i*2+1])
				writer.writerow([inv, bid, subject.tag, sc])
		except IndexError:
			continue

f.close()
out.close()
