#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to wrap records from a MARCXML dump into a series of XML files à la OAI-PMH.
Tested with input MARCXML made by yaz-marcdump from SbnWeb binary MARC export, like:
$ yaz-marcdump -f utf8 -t utf8 -i marc -o marcxml in.clean.mrc > out.xml
Control character are left:
$ grep '[[:cntrl:]][HI]' in.marc

Usage: ./BEIC_marcxml2oaipmh.py <input.xml> <outprefix>
"""
#
# (C) Federico Leva e Fondazione BEIC, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#

from datetime import datetime
from lxml import etree
import re
import sys

def getOaiHeader():
	return """<?xml version="1.0" encoding="UTF-8" ?>
	<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
	<responseDate>""" + datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') + """</responseDate>
	<request></request>
	<ListRecords>
	"""

def getOaiFooter():
	return "</ListRecords>\n</OAI-PMH>"

def makeWrappedRecord(identifier, record):
	return "<record>\n<header>\n<identifier>{}</identifier>\n<datestamp>{}</datestamp>\n</header>\n<metadata>\n{}</metadata>\n</record>".format(
		identifier, datetime.utcnow().strftime('%Y-%m-%d'), record)

def makeOutputFile(recordcount):
	filenumber = str(recordcount / 1000).zfill(4)
	oai = open(sys.argv[2] + '-' + filenumber + '.xml', 'w')
	oai.write(getOaiHeader())
	return oai

if __name__ == '__main__':
	marcxml=open(sys.argv[1], 'r')
	oai = makeOutputFile(0)
	curidentifier = ''
	recordcount = 0

	for event, elem in etree.iterparse(marcxml):
		# The name of the element will be prefixed with the namespace, for instance:
		# end <Element {http://www.loc.gov/MARC21/slim}record at 0x7fd5cfc20fc8>
		if event == "end" and elem.tag.endswith("controlfield") and "001" in elem.attrib.values():
			curidentifier = elem.text
			print "Found identifier {}".format(curidentifier)
		if event == "end" and elem.tag.endswith("subfield") and "a" in elem.attrib.values() and elem.text:
			# The "asterisk" for sorting is given as two prefixes [[:cntrl:]][HI] in
			# the original MRC, but control characters are removed in XML conversion
			elem.text = re.sub(r"H([A-Z\d\[\]].*\W)I(\w)", r"\1\2", elem.text, re.UNICODE)
		if event == "end" and elem.tag.endswith("record"):
			recordcount += 1
			if recordcount % 1000 == 0:
				# 1000 records done. Close current file and open a new one.
				oai.write(getOaiFooter())
				oai = makeOutputFile(recordcount)

			fullrecord = etree.tostring(elem)
			if re.findall("<leader>.{6}us", fullrecord):
				# È una collana, non serve visualizzare
				continue
			oai.write(makeWrappedRecord(curidentifier, fullrecord))
			elem.clear()
			curidentifier = ''
