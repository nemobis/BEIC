#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to fetch alternative names for authors from CERL thesaurus.
A tab-delimited CSV named "authors-noCERL.csv" is looked up for a column "ID"
containing search terms; CERLid, CERLnames and VIAF columns are added.
"""
#
# (C) Federico Leva e Fondazione BEIC, 2016
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.2.0'
#

import unicodecsv as csv
import requests
from lxml import html
from collections import namedtuple
import re
import sys

def searchName(keyword=None):
	print("Searching: %s" % keyword)
	# Site is HTTPS, must be HTTPS as the POST won't be redirected
	try:
		search = requests.post('https://thesaurus.cerl.org/cgi-bin/search.pl',
							data={'query': keyword, 'type': 'p'})
	except requests.exceptions.ConnectionError:
		return
	results = html.fromstring(search.text)
	records = results.xpath('//a[contains(@href,"record.pl?rid=cnp")]/@href')
	return records

with open('authors-noCERL.csv', 'r') as csvauthors:
	authors = csv.reader(csvauthors,
						delimiter='\t',
						lineterminator='\n',
						quoting=csv.QUOTE_MINIMAL,
						encoding='utf-8')
	header = next(authors)
	if 'CERLid' not in header or 'CERLnames' not in header or 'ID' not in header or "VIAF" not in header:
		print("FATAL ERROR: Some column headers are missing")
		sys.exit()
	print("Header of the input table: %s" % ', '.join(header) )
	authordata = namedtuple('authordata', ', '.join(header))
	authordata = [authordata._make(row) for row in authors]

	csvcerl = open('authors-CERL.csv', 'w')
	out = csv.writer(csvcerl,
					delimiter='\t',
					lineterminator='\n',
					quoting=csv.QUOTE_MINIMAL)
	out.writerow(header)

	for row in authordata:
		foundnames = u""
		foundid = u""
		foundviaf = u""
		print "Current row: %s" % row.ID
		keyword = re.sub("\W", " ", row.ID, flags=re.UNICODE)
		records = searchName(keyword)
		if not records:
			cleankeyword = re.sub("\W", " ", re.sub("\([^)]+\)", "", row.ID), flags=re.UNICODE)
			if cleankeyword != keyword:
				keyword = cleankeyword
				records = searchName(keyword)
			if not records:
				keyword = re.sub("[0-9]", "", keyword)
				records = searchName(keyword)

		for record in records:
			foundid += "%s\n" % re.search(r'(cnp[0-9]+)', record).group(1)
			# Assumes href in form "/cgi-bin/record.pl?rid=cnp01468162"
			try:
				authority = requests.get('https://thesaurus.cerl.org' + record)
			except requests.exceptions.ConnectionError:
				continue
			data = html.fromstring(authority.text)
			names = data.xpath('//div[@id="ctvariantnames"]//div[@class="ct_content"]//div/text()')
			#print("Found names:\n")
			#print(names)
			viaf = data.xpath('//a[contains(@href,"http://viaf.org/")]/@href')[0]
			foundviaf += u"%s\n" % viaf
			for name in names:
				name = name.strip()
				if name is not "":
					foundnames += u"%s\n" % name

		print("Found in the authority: %s %s" % (foundid, foundnames))
		row = row._replace(CERLid=foundid, CERLnames=foundnames, VIAF=viaf)
		out.writerow(row)

	csvcerl.close()
