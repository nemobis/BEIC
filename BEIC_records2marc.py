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
__version__ = '0.2.0'
#

from collections import namedtuple
import csv
import datetime
import hashlib
from kitchen.text.converters import to_unicode, to_bytes
from marcxml_parser import MARCXMLRecord
from operator import attrgetter
import pickle
import re
import traceback
from xml.sax.saxutils import escape

def createEmptyAuthority(topical=False, classification=False):
	record = MARCXMLRecord('<record><controlfield tag="001">999authority999</controlfield></record>')
	record.leader = '00000nz  a2200000n  4500'
	record.add_ctl_field('003', 'IT-MiFBE')
	record.add_ctl_field('005', datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S.0'))
	fixed = ' ||a||||a|||          ||a|||||| d'
	if topical:
		fixed = ' ||a|||||a||          ||a|||||| d'
	if classification:
		fixed = 'aaaaaaba'
		record.add_data_field('084', '0', ' ', {'a': 'ddc', 'c': 'WebDewey', 'q': 'IT-MiFBE', 'e': 'ita' })
	record.add_ctl_field('008', datetime.datetime.utcnow().strftime('%y%m%d') + fixed)
	record.add_data_field('040', ' ', ' ', {'a': 'IT-MiFBE', 'b': 'ita', 'c': 'IT-MiFBE', 'e': 'reicat' })
	return record

def getXmlHeader():
	return '<?xml version="1.0" encoding="UTF-8"?>\n'
	+ '<collection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
	+ 'xsi:schemaLocation="http://www.loc.gov/MARC21/slim '
	+ 'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" '
	+ 'xmlns="http://www.loc.gov/MARC21/slim">\n'

with open('BibliographicRecords.csv', 'rb') as csvrecords:
	xmlout = open('BibliographicRecords.xml', 'w+')
	xmlout.write(getXmlHeader())

	records = csv.reader(csvrecords,
		delimiter=b'\t',
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
	authorities = {}
	for field in ['100', '110', '111', '130', '150', '151', '153']:
		authorities[field] = {}
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

		field = row.CodiceCampo or row.CodiceCampoOriginale
		subfieldsraw = row.Sottocampi or row.SottocampiOriginali
		# The source storage replaces spaces with slashes
		try:
			subfield = re.sub(r'\\', ' ', subfieldsraw)
		except UnicodeDecodeError:
			print 'ERROR: Could not remove slashes'
			print subfieldsraw
			continue

		if field in ['LDR', '001', '003', '005', '007', '008']:
			currentrecord.add_ctl_field(field, to_bytes(subfield))
			if field == 'LDR':
				currentrecord.leader = subfield
		else:
			# Split a string like '$aIT-MiFBE$bita$ereicat' into fields
			subfields = re.split('\$([a-z0-9])', subfieldsraw)
			subdict = {}
			for i in range(1, len(subfields)/2+1):
				# Convert to bytes and escape "&": marcxml_parser does not do it
				subdict.update({subfields[i*2-1]: to_bytes(escape(subfields[i*2]))})
				subdictindex = pickle.dumps(subdict)

			i1 = re.sub(r'\\', ' ', row.Indicatore1 or row.Indicatore1Originale) or ' '
			i2 = re.sub(r'\\', ' ', row.Indicatore2 or row.Indicatore2Originale) or ' '
			# Avoid: ValueError: Invalid i2 parameter 'h'!
			# Avoid: ValueError: `subfields_dict` have to contain something!
			try:
				currentrecord.add_data_field( field, i1, i2, subdict )
				if field in ['100', '700']:
					authorities['100'][subdictindex] = subdict
				if field in ['110', '710', '852']:
					no = subdict.pop('4', '')
					no = subdict.pop('e', '')
					no = subdict.pop('n', '')
					no = subdict.pop('j', '')
					subdictindex = pickle.dumps(subdict)
					authorities['110'][subdictindex] = subdict
				if field in ['111']:
					authorities['111'][subdictindex] = subdict
				if field in ['130', '240', '730', '830']:
					authorities['130'][subdictindex] = subdict
				if field in ['650', '654']:
					authorities['150'][subdictindex] = subdict
				if field in ['751']:
					authorities['151'][subdictindex] = subdict
				if field in ['082']:
					authorities['153'][subdictindex] = subdict
			except ValueError:
				print 'WARNING: Could not add one field'
				continue

	xmlout.write('</collection>\n')
	xmlout.close()

with open('Authority.xml', 'w+') as xmlauth:
	xmlauth.write(getXmlHeader())
	for field in authorities:
		for authority in authorities[field]:
			subfields = authorities[field][authority]
			record = createEmptyAuthority(
				topical=(field == '150'),
				classification=(field == '153')
			)
			i1 = subfields.pop('ind1', ' ')
			i2 = subfields.pop('ind2', ' ')
			# Remove subfields which don't apply within authority records.
			no = subfields.pop('4', '')
			if field in ['150', '151', '153']:
				no = subfields.pop('2', '')
			if field in ['153']:
				no = subfields.pop('q', '')
			if field in ['150', '153']:
				i1 = i2 = ' '
			if field in ['153']:
				try:
					subs = subfields.pop('9', '')[0].split('. ')
				except:
					subs = None
				if subs:
					subfields['j'] = subs.pop()
					subfields['h'] = []
					for sub in subs:
						# FIXME: Allow multiple
						subfields['h'].append(subs.pop())

			try:
				record.add_data_field(field, i1, i2, subfields)
				record.add_ctl_field('001', to_bytes(hashlib.md5(str(subfields)).hexdigest()))
				xmlauth.write(record.to_XML())
			except KeyError:
				print "No buono!"
				print subfields
			except ValueError:
				print "ERROR: Empty subfields!"
				print subfields
	xmlauth.write('</collection>\n')
