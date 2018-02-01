#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
   Extractor to validate a METS file and check the existence and content of
   the files linked from each fileSec/fileGrp/file/FLocat tag, assumed to
   contain an MD5 checksum. The "md5sum" utility is required.
"""
#
# (C) Federico Leva and Fondazione BEIC, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

from lxml import etree
import os
import subprocess

# http://lxml.de/validation.html
parser = etree.XMLParser(dtd_validation=True)
digest = open('mets.md5sum', 'w')

for dirpath, dirnames, filenames in os.walk('.'):
	for filename in [ each for each in filenames if each.endswith('.xml') ]:
		xml = os.path.join(dirpath, filename)
		try:
			mets = etree.parse(open(xml, 'r'))
			files = mets.xpath('//*[local-name()="file"]')
			for item in files:
				content = item.xpath( './*[local-name()="FLocat"]/@xlink:href',
					namespaces={"xlink": "http://www.w3.org/1999/xlink"} )[0]
				checksum = item.xpath('./@CHECKSUM')[0]
				digest.write("%s  %s\n" % (checksum, os.path.normpath(os.path.join(dirpath, content)) ) )
		except:
			pass

check = subprocess.call(["md5sum", "-c", "--status", "mets.md5sum"])
if check == 0:
	print("SUCCESS: The METS content has been verified correctly.")
else:
	print("ERROR: The checksum validation has failed.")
