#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script to convert a MARCXML dump into a series of XML files à la OAI-PMH.
"""
#
# (C) Federico Leva e Fondazione BEIC, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.0.1'
#

from datetime import datetime
from xml.sax import handler
from xml.sax import make_parser
import sys

class EmitRecord(handler.ContentHandler):
	def __init__(self):
		self.inIdentifier = False
		self.inRecord = False

	def startElement(self, name, attrs):
		if name not in ["record", "controlfield"]:
			return

		if name == "record":
			self.inRecord = True
			print makeWrappedRecord(self.identifier, self.originalrecord)
			self.originalrecord = ''

		if name == "controlfield" and attrs.getValue("tag") == "001":
			self.inIdentifier = True
			self.identifier = ''

	def characters(self, content):
		if self.inRecord:
			self.originalrecord += content

		if self.inIdentifier:
			self.identifier += content

	def endElement(self, name, attrs):
		if name not in ["record", "controlfield"]:
			return

		if name == "record":
			self.inRecord = False

		if name == "controlfield":
			self.inIdentifier = False

def getOaiHeader():
	return '<?xml version="1.0" encoding="UTF-8" ?>\
	<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">\
	<responseDate>' + datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') + '</responseDate>\
	<request></request>\
	<ListRecords>'

def makeWrappedRecord(identifier, record):
	return "<record><header><identifier>{}</identifier><datestamp>{}</datestamp></header><metadata>{}</metadata></record>".format(
		identifier, datetime.utcnow().strftime('%Y-%m-%d'), record)

if __name__ == '__main__':
	parser = make_parser()
	parser.setFeature(handler.feature_namespaces, 0)
	dh = EmitRecord()
	parser.setContentHandler(dh)
	print getOaiHeader()
	parser.parse(sys.argv[0])
	print "</ListRecords></OAI-PMH>"


