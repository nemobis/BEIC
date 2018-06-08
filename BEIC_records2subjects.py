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
__version__ = '0.2.0'
#
from pymarc import MARCReader
import pymarc.exceptions
import requests
import unicodecsv as csv
import re
from time import sleep

# Make sure it's UTF-8
# yaz-marcdump -i marc -f marc8 -t utf8 -o marc input.mrc > input.utf8.mrc

out = open('subjects.csv', 'w')
writer = csv.writer(out,
		delimiter=b'\t',
		lineterminator='\n',
		quoting=csv.QUOTE_ALL,
		encoding='utf-8'
		)
writer.writerow([u'Inventario', u'Identificativo', u'Campo', 'Sottocampi'])
with open('bids.txt', 'rb') as b:
	bids = set([i.strip() for i in b if i])

for bid in bids:
	print(u"== {} ==".format(bid))
	sleep(0.5)
	sbnurl = "http://opac.sbn.it/opacsbn/opaclib?db=solr_iccu&select_db=solr_iccu&nentries=1&from=1&searchForm=opac/iccu/error.jsp&resultForward=opac/iccu/scarico_uni.jsp&do_cmd=search_show_cmd&format=unimarc&rpnlabel=BID%3D{}&rpnquery=%40attrset+bib-1++%40attr+1%3D1032+%40attr+4%3D2+%22{}%22&totalResult=1&fname=none".format(bid, bid)
	sbn = requests.get(sbnurl)
	try:
		reader = None
		reader = MARCReader(sbn.text)
		record = reader.next()
	except pymarc.exceptions.RecordLengthInvalid as e:
		print("ERROR: Invalid record for BID: {}".format(bid))
		print(e.message)
		print(sbn.text.encode('utf8'))
		continue

	try:
		inv = u''
		subjects = record.get_fields('601', '602', '603', '604', '605', '606', '607', '608', '609', '676')
		for subject in subjects:
			# Extract the subfields as dictionary and concatenate them back
			sl = subject.subfields
			sc = u''
			for i in range(0, len(sl)/2):
				sc = sc + u"${}{}".format(sl[i*2], sl[i*2+1])
			writer.writerow([inv, bid, subject.tag, sc])
	except IndexError:
		continue

out.close()
