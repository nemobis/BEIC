#!/usr/bin/python
"""
Script to thank contributors to articles linked to a list of Wikidata IDs.
Q# (integers) must be placed one per line in a "qids.txt" file.

"""
#
# (C) Federico Leva e Fondazione BEIC, 2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
#
# Needs wikitools 1.3
from wikitools import wiki
from wikitools import api
from wikitools import page
import time

base = wiki.Wiki("http://www.wikidata.org/w/api.php")

def getRelevantRevisions(wikiapi, title):
	revisions = set([])
	editors = set([])
	hashes = set([])
	size_old = 0

	site = wiki.Wiki(wikiapi)
	article = page.Page(site, title)
	hist = article.getHistory(direction='newer', content=False)
	for i in hist:
		# Cannot thank unregistered users yet
		# if i['userid'] == 0:
		#	continue
		if 'userhidden' in i:
			continue
		if not revisions or ( i['userid'] not in editors
					   and i['sha1'] not in hashes and i['size'] - size_old > 500 ):
			revisions.add( i['revid'] )
			editors.add( i['userid'] )
			hashes.add( i['sha1'] )
		size_old = i['size']

	return revisions

def thankRevisions(wikiapi, revisions):
	thanker = wiki.Wiki(wikiapi)
	thanker.login("Federico Leva (BEIC)", "****")
	for revision in revisions:
		# Should use getToken()
		params = { 'action':'query', 'meta':'tokens' }
		token = api.APIRequest(thanker, params).query()['query']['tokens']['csrftoken']
		params = { 'action': 'thank', 'rev': revision, 'token': token }
		try:
			request = api.APIRequest(thanker, params).query()
		except:
			print "Thanking for revision %d failed!" % revision
		time.sleep(7)

def getPages():
	qids = open('qids.txt', 'r')
	apiMap = getApiMap()
	for qid in qids:
		qid = qid.strip()
		print "Now looking into %s" % qid
		params = { 'action': 'wbgetentities', 'props' : 'sitelinks', 'ids': 'Q' + qid }
		request = api.APIRequest(base, params)
		result = request.query()
		try:
			sitelinks = result['entities']['Q' + qid]['sitelinks']
		except:
			continue
		for sitelink in sitelinks:
			# We ignore specials
			if sitelink in apiMap:
				wikiapi = apiMap[sitelink]
				yield [ wikiapi, sitelinks[sitelink]['title'] ]
	raise StopIteration

def getApiMap():
	apiMap = {}
	request = api.APIRequest(base, { 'action': 'sitematrix' })
	query = request.query()
	result = query['sitematrix']
	# Two extra items, count and specials
	for i in range( len(result) - 2 ):
		for site in result[str(i)]['site']:
			apiMap.update( { site['dbname']: site['url'] + '/w/api.php' } )
	return apiMap

def main():
	for [wikiapi, title] in getPages():
		#if wikiapi != u'https://ru.wikipedia.org/w/api.php':
		#	continue
		print 'Now doing "%s" via %s' % (title, wikiapi)
		revisions = getRelevantRevisions(wikiapi, title)
		print 'Found %d revisions to thank for' % len(revisions)
		thankRevisions(wikiapi, revisions)

if __name__ == "__main__":
	main()