#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to convert the TSV of BEIC (APE) publishers into a JSON for the web map
with coordinates guessed by querying the Google Maps API.
"""
#
# (C) Federico Leva e Fondazione BEIC, 2016
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#

from geopy.geocoders import GoogleV3
import json
import unicodecsv as csv
import requests
from collections import namedtuple
import re
import sys

def getCoordinates(keyword=None):
	return 

with open('EditoriPerNavigatore.csv', 'r') as csvfile:
	publishers = csv.reader(csvfile,
						delimiter='\t',
						lineterminator='\n',
						quoting=csv.QUOTE_MINIMAL,
						encoding='utf-8')
	header = next(publishers)
	print("Header of the input table: %s" % ', '.join(header) )
	data = namedtuple('data', ', '.join(header))
	data = [data._make(row) for row in publishers]
	mapdata = []

	for row in data:
		editore = row.Editore
		anno = row.AnnoInizialeDiPubblicazione
		produzione = row.Documenti
		if not produzione:
			produzione = 0
		print "Current row: %s %s" % (anno, editore)

		pos = None
		for i in range(0, len(mapdata)-1):
			if mapdata[i]['name'] == editore:
				pos = i
				break
		if not pos:
			indirizzo = "%s, %s, %s" % (row.Indirizzo, row.CAP, row.Comune)
			via = "%s, %s, %s" % (re.sub('[0-9,]+', '', row.Indirizzo), row.CAP, row.Comune)
			geolocator = GoogleV3(api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
			# geopy.geocoders.Nominatim(user_agent="BEIC-APE-0.1", country_bias="Italy", timeout=5)
			# geolocator = Mapzen(api_key="mapzen-zzzzzzz", user_agent="BEIC-APE-0.1", country_bias="Italy", timeout=1)
			try:
				location = geolocator.geocode(indirizzo)
				if not location:
					location = geolocator.geocode(via)
			except:
				print "Could not find: %s" % indirizzo
			if location and location.longitude and location.latitude:
				lo = location.longitude
				la = location.latitude
			else:
				lo = None
				la = None

			mapdata.append( {
				"produzione": [],
				"cap": row.CAP,
				"provincia": row.SiglaProvincia,
				"catalogo": row.Collegamento,
				"sito": row.SitoWeb,
				"citta": row.Comune,
				"name": row.Editore,
				"indirizzo": row.Indirizzo,
				"longitude": lo,
				"latitude": la
			} )
			pos = len(mapdata)-1
		
		mapdata[pos]['produzione'].append( { "anno": anno, "produzione": produzione } )

	with open('EditoriPerNavigatore.json', 'w') as out:
		json.dump(mapdata, out, indent=1)
