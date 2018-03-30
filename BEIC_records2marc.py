#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to convert a specific BEIC table format to a MARC XML file.
"""
#
# (C) Federico Leva e Fondazione BEIC, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#

from collections import namedtuple
import csv
from kitchen.text.converters import to_unicode, to_bytes
from marcxml_parser import MARCXMLRecord
from operator import attrgetter
import re
import traceback
from xml.sax.saxutils import escape

with open('Alma.csv', 'rb') as csvrecords:
	xmlout = open('Records.xml', 'w+')
	xmlout.write('<?xml version="1.0" encoding="UTF-8"?>\n'
		+ '<collection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
		+ 'xsi:schemaLocation="http://www.loc.gov/MARC21/slim '
		+ 'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" '
		+ 'xmlns="http://www.loc.gov/MARC21/slim">\n')

	records = csv.reader(csvrecords,
		delimiter=b',',
		lineterminator='\n',
		quoting=csv.QUOTE_MINIMAL,
		#encoding='utf-8'
		)
	header = next(records)
	print("Header of the input table: %s" % ', '.join(header) )
	recordsdata = namedtuple('recordsdata', ', '.join(header))
	recordsdata = [recordsdata._make(row) for row in records]
	recordsdata = sorted(recordsdata, key=attrgetter('NumeroDiControllo'))

	# Initiate with empty data
	controlnumber = None
	for row in recordsdata:
		if row.NumeroDiControllo != controlnumber:
			# If the control number is not empty, one record is ready and the next is being read
			if controlnumber:
				currentrecordcontrol = currentrecord.get_ctl_field('001')
				try:
					if currentrecordcontrol != "999test999":
						# The record must have either a 130 or a 240
						# and also either 654, 690 or 854
						xmlout.write(currentrecord.to_XML())
						print "INFO: Exported %s" % currentrecordcontrol
						if '130' not in currentrecord.datafields and '240' not in currentrecord.datafields:
							print "WARNING: the record had no 240 nor 130 field"
						if '654' not in currentrecord.datafields and '690' not in currentrecord.datafields and '854' not in currentrecord.datafields:
							print "WARNING: the record had no 654, 690 or 854 field"
					else:
						print 'WARNING: Test data left, had to skip'
				except:
					print 'WARNING: Parser failure, had to skip'
					print(traceback.format_exc())

			# Prepare empty new record and switch to the current control number
			currentrecord = MARCXMLRecord('<record><controlfield tag="001">999test999</controlfield></record>')
			controlnumber = row.NumeroDiControllo

		field = row.CodiceCampoOriginale
		# The source storage replaces spaces with slashes
		subfields = row.Sottocampi or row.SottocampiOriginali
		try:
			subfield = re.sub(r'\\', ' ', subfields)
		except UnicodeDecodeError:
			print 'ERROR: Could not remove slashes'
			print subfields
			continue

		if field in ['LDR', '001', '003', '005', '007', '008']:
			currentrecord.add_ctl_field(field, to_bytes(subfield))
			if field == 'LDR':
				currentrecord.leader = subfield
		else:
			# Split a string like '$aIT-MiFBE$bita$ereicat' into fields
			subfields = re.split('\$([a-z0-9])', subfield)
			subdict = {}
			for i in range(1, len(subfields)/2+1):
				# Convert to bytes and escape "&": marcxml_parser does not do it
				subdict.update({subfields[i*2-1]: to_bytes(escape(subfields[i*2]))})

			i1 = re.sub(r'\\', ' ', row.Indicatore1 or row.Indicatore1Originale) or ' '
			i2 = re.sub(r'\\', ' ', row.Indicatore2 or row.Indicatore2Originale) or ' '
			# Avoid: ValueError: Invalid i2 parameter 'h'!
			# Avoid: ValueError: `subfields_dict` have to contain something!
			try:
				currentrecord.add_data_field( field, i1, i2, subdict )
			except ValueError:
				print 'WARNING: Could not add one field'
				continue

	xmlout.write('</collection>\n')
	xmlout.close()
