#!/usr/bin/env python3
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
from pymarc import Record, Field, XMLWriter
from operator import attrgetter
import pickle
import re
import traceback
from xml.sax.saxutils import escape

def createEmptyAuthority(topical=False, classification=False):
	leader = '00000nz  a2200000n  4500'
	fixed = ' ||a||||a|||          ||a|||||| d'
	if topical:
		fixed = ' ||a|||||a||          ||a|||||| d'
	if classification:
		fixed = 'aaaaaaba'
		leader = '00000nw  a2200000n  4500'

	record = Record(leader=leader)
	record.add_field( Field(tag='001', data='999test999') )
	record.add_field( Field(tag='003', data='IT-MiFBE') )
	record.add_field( Field(tag='005', data=datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S.0') ) )
	record.add_field( Field(tag='008', data=(datetime.datetime.utcnow().strftime('%y%m%d') + fixed)) )

	if classification:
		record.add_field( Field(tag='084',
						indicators=['0', ' '],
						subfields = ['a', 'ddc', 'c', 'WebDewey', 'q', 'IT-MiFBE', 'e', 'ita' ] ) )
	record.add_field( Field(tag='040',
						indicators=[' ', ' '],
						subfields = ['a', 'IT-MiFBE', 'b', 'ita', 'c', 'IT-MiFBE', 'e', 'reicat' ] ) )
	return record

def removeSubfields(field, subfields):
	""" Takes an arrays and removes an array of strings and the strings appearing next to them. """
	for needle in subfields:
		if needle not in field:
			continue
		target = field.index(needle)
		# Remove the subfield name and the next item i.e. the content
		discard = field.pop(target)
		try:
			discard = field.pop(target)
		except IndexError:
			# For some reason this subfield was empty.
			pass

	return field

def main():
	# Assumes CSV file in the same format as produced by one BEIC DB
	# mdb-export -d"\t" input.accdb BibliographicRecords > BibliographicRecords.csv
	with open('BibliographicRecords.csv', 'r') as csvrecords:
		xmlout = open('BibliographicRecords.xml', 'wb+')
		xmloutc = open('BibliographicRecordsComponents.xml', 'wb+')
		xmlouth = open('BibliographicRecordsHosts.xml', 'wb+')
		writer = XMLWriter(xmlout)
		writerc = XMLWriter(xmloutc)
		writerh = XMLWriter(xmlouth)

		# FIXME: Handle double quotes.
		records = csv.reader(csvrecords,
			delimiter='\t',
			lineterminator='\n',
			quoting=csv.QUOTE_MINIMAL,
			#encoding='utf-8'
			)
		header = next(records)
		print("Header of the input table: %s" % ', '.join(header) )
		recordsdata = namedtuple('recordsdata', ', '.join(header))
		recordsdata = [recordsdata._make(row) for row in records]
		# The input table is not sorted but we read it sequentially by control number
		recordsdata = sorted(recordsdata, key=attrgetter('NumeroDiControllo'))

		# Initiate with empty data
		controlnumber = None
		currentrecord = None
		currentrecord_ishost = None
		currentrecord_iscomponent = None
		authorities = {}
		for field in ['100', '110', '111', '130', '150', '151', '153']:
			authorities[field] = {}
		for row in recordsdata:
			if row.Escludere == "1":
				continue
			if row.NumeroDiControllo != controlnumber:
				# If the control number is not empty, one record is ready and the next is being read
				if currentrecord and controlnumber:
					currentrecordcontrol = currentrecord.get_fields('001')[0].value()
					try:
						if currentrecordcontrol != "999test999":
							# The record seems to have been completed. Write it out.
							if currentrecord_iscomponent:
								# Split the components to their own XML.
								writerc.write(currentrecord)
								xmloutc.write(b'\n')
							elif currentrecord_ishost:
								# Split the hosts to their own XML.
								writerh.write(currentrecord)
								xmlouth.write(b'\n')
							else:
								writer.write(currentrecord)
								xmlout.write(b'\n')
							print("INFO: Exported %s" % currentrecordcontrol) # FIXME check  get_fields
							# The record must have either a 130 or a 240
							# and also either 654, 690 or 854
							# All records are expected to have certain fields, except components (mostly CMP- and ART-).
							if not currentrecord_iscomponent:
								if '130' not in currentrecord and '240' not in currentrecord:
									print("WARNING: the record had no 240 nor 130 field")
								if '654' not in currentrecord and '690' not in currentrecord and '854' not in currentrecord:
									print("WARNING: the record had no 654, 690 or 854 field")
						else:
							print('ERROR: Test data left, had to skip')
					except:
						print('ERROR: Parser failure, had to skip')
						print(currentrecord.as_json())
						print(traceback.format_exc())

				# Prepare empty new record and switch to the current control number
				currentrecord = Record()
				currentrecord.add_field( Field(tag='001', data='999test999') )
				controlnumber = row.NumeroDiControllo
				# Reset host/component status
				currentrecord_ishost = None
				currentrecord_iscomponent = None

			# Host/component status needs to be checked at every row
			# Because the first row is not guaranteed to declare it
			if "Host" in row.LivelloBibliografico:
				currentrecord_ishost = True
			elif "Component" in row.LivelloBibliografico:
				currentrecord_iscomponent = True
			field = row.CodiceCampo or row.CodiceCampoOriginale
			subfieldsraw = row.Sottocampi or row.SottocampiOriginali
			# The source storage replaces spaces with slashes
			try:
				subfield = re.sub(r'\\', ' ', subfieldsraw)
			except UnicodeDecodeError:
				print('ERROR: Could not remove slashes')
				print(subfieldsraw)
				continue

			if field in ['001', '003', '005', '007', '008']:
				if field == '001':
					# Remove test control number
					currentrecord.remove_fields('001')
				currentrecord.add_field( Field(tag=field, data=subfield))
			elif field == 'LDR':
				currentrecord.leader = subfield
			else:
				# Split a string like '$aIT-MiFBE$bita$ereicat' into fields
				subdict = re.split('\$([a-z0-9])', subfieldsraw)
				# Remove the first empty string from before the dollar sign
				if '' in subdict:
					subdict.remove('')
				subdictindex = subfieldsraw # FIXME: hash

				i1 = re.sub(r'\\', ' ', row.Indicatore1 or row.Indicatore1Originale) or ' '
				i2 = re.sub(r'\\', ' ', row.Indicatore2 or row.Indicatore2Originale) or ' '
				# Avoid: ValueError: Invalid i2 parameter 'h'!
				# Avoid: ValueError: `subfields_dict` have to contain something!
				try:
					# Continue adding data to the bibliographic record, to be picked up
					# later and written out to XML above when no more data is found.
					currentrecord.add_field( Field( tag=field, indicators=[i1, i2], subfields=subdict ) )
					# Switch to collecting data for authorities
					if field in ['100', '700']:
						authorities['100'][subdictindex] = subdict
					if field in ['110', '710', '852']:
						# We'll need to pass an expunged version to the authority record
						subdict = removeSubfields(subdict, ['4', 'e', 'n', 'j'])
						if field in ['852']:
							subdict.extend(['ind1', '2', 'ind2', ' '])
						subdictindex = pickle.dumps(subdict)
						authorities['110'][subdictindex] = subdict
					if field in ['111']:
						authorities['111'][subdictindex] = subdict
					if field in ['130', '240', '730', '830']:
						subdict = removeSubfields(subdict, ['v', 'n'])
						authorities['130'][subdictindex] = subdict
					if field in ['650', '654']:
						authorities['150'][subdictindex] = subdict
					if field in ['751']:
						authorities['151'][subdictindex] = subdict
					if field in ['082']:
						authorities['153'][subdictindex] = subdict
				except ValueError:
					print('WARNING: Could not add one field')
					continue

		writer.close()
		writerc.close()
		writerh.close()

	with open('Authority.xml', 'wb+') as xmlauth:
		writer = XMLWriter(xmlauth)
		for field in authorities:
			for authority in authorities[field]:
				subfields = authorities[field][authority]
				record = createEmptyAuthority(
					topical=(field == '150'),
					classification=(field == '153')
				)
				# Remove subfields which don't apply within authority records.
				subfields = removeSubfields(subfields, ['ind1', 'ind2', '4'])
				# TODO: Aren't we supposed to keep some of those indicators?
				i1 = ' '
				i2 = ' '
				if field in ['130']:
					i1 = ' '
					i2 = '0'
				if field in ['150', '151', '153']:
					subfields = removeSubfields(subfields, ['2'])
				if field in ['153']:
					subfields = removeSubfields(subfields, ['q'])
				if field in ['150', '153']:
					i1 = i2 = ' '
				if field in ['153']:
					# Split the subjects from the $9 into $h and $j. Example source 082:
					# "$a704.942$9Soggetti speciali nelle belle arti e arti decorative. Figure umane$2WebDewey$qIT-MiFBE"
					if '9' in subfields:
						index9 = subfields.index('9')
						subj = subfields[index9+1]
						subfields = removeSubfields(subfields, ['9'])
					try:
						subj = subj.split('. ')
					except:
						subj = None
					if subj:
						subfields.extend(['j', subj.pop()])
						for sub in subj:
							subfields.extend(['h', subj.pop()])

				try:
					record.add_field( Field(tag=field, indicators=[i1, i2], subfields=subfields) )
					record.remove_fields('001')
					record.add_field( Field(tag='001', data=to_bytes(hashlib.md5(to_bytes(subfields)).hexdigest())) )
					writer.write(record)
					xmlauth.write(b'\n')
				except KeyError:
					print("ERROR: No buono!")
					print(subfields)
				except ValueError:
					print("ERROR: Empty subfields!")
					print(subfields)
				except IndexError:
					print("ERROR: Cannot write XML! Probably some broken subfield list.")
					print(subfields)
		writer.close()


if __name__ == '__main__':
	main()
