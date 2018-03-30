#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to fetch alternative names for authors from DBI.
A tab-delimited CSV named "authors-noDBI.csv" is looked up for a column "ID"
containing search terms; DBI-id and DBI-names columns are added.
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
from collections import namedtuple
import re
import sys

with open('authors-noDBI.csv', 'r') as csvauthors:
	authors = csv.reader(csvauthors,
						delimiter='\t',
						lineterminator='\n',
						quoting=csv.QUOTE_MINIMAL,
						encoding='utf-8')
	header = next(authors)
	if 'DBIid' not in header or 'DBInames' not in header:
		print("FATAL ERROR: Some column headers are missing")
		sys.exit()
	print("Header of the input table: %s" % ', '.join(header) )
	authordata = namedtuple('authordata', ', '.join(header))
	authordata = [authordata._make(row) for row in authors]

	csvdbi = open('authors-DBI.csv', 'w')
	out = csv.writer(csvdbi,
					delimiter='\t',
					lineterminator='\n',
					quoting=csv.QUOTE_MINIMAL)
	out.writerow(header)

	for row in authordata:
		foundnames = u""
		foundid = u""
		print "Current row: %s" % row.ID
		keyword = re.sub("\W", " ", row.ID, flags=re.UNICODE)
		try:
			search = requests.get('http://www.treccani.it/enciclopedia/ricerca/%s/' % keyword )
		except requests.exceptions.ConnectionError:
			continue
		results = html.fromstring(search.text)
		try:
			foundid = results.xpath('//a[contains(@href,"Dizionario-Biografico")]/@href')[0]
			foundnames = results.xpath('//a[contains(@href,"Dizionario-Biografico")]/text()')[0].strip()
		except IndexError:
			continue

		print("Found in the authority: %s %s" % (foundid, foundnames))
		row = row._replace(DBIid=foundid, DBInames=foundnames)
		out.writerow(row)

	csvdbi.close()
