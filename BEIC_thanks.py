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
import re
from collections import defaultdict

base = wiki.Wiki("http://www.wikidata.org/w/api.php")
thankscount = defaultdict(int)
deferred = open('deferred-thanks.txt', 'a')

def getRelevantRevisions(wikiapi, title):
	revisions = set([])
	editors = set([])
	hashes = set([])
	revisionby = defaultdict()
	size_old = 0

	site = wiki.Wiki(wikiapi)
	article = page.Page(site, title)
	hist = article.getHistory(direction='newer', content=False)
	for i in hist:
		# Cannot thank unregistered users yet
		# if i['userid'] == 0:
		# continue
		if 'userhidden' in i:
			continue
		try:
			# TODO: Consider thanking for the biggest edit instead
			if not revisions or ( i['user'] not in editors
						and i['sha1'] not in hashes and i['size'] - size_old > 1000 ):
				if thankscount[i['user']] <= 5:
					revisions.add( i['revid'] )
					editors.add( i['user'] )
					revisionby[i['revid']] = i['user']
					thankscount[i['user']] += 1
				else:
					deferred.write( '%s\t%d\n' % ( wikiapi, i['revid'] ) )
			# Never thank occurrences of a text after the first.
			hashes.add( i['sha1'] )
		except KeyError:
			continue
		size_old = i['size']

	params = { 'action': 'query', 'list': 'blocks', 'bkprop': 'userid', 'bkusers': '|'.join( editors ) }
	blocked = api.APIRequest(site, params).query()
	try:
		for block in blocked['query']['blocks']:
			print 'Skipping blocked user "%s"' % block['user']
			revisions.remove( revisionby[block['user']] )
	except KeyError:
		continue

	return revisions

def getBlockedAuthors(wikiapi, revisions, history)
	site = wiki.Wiki(wikiapi)
	params = { 'action': 'query', 'list': 'blocks', 'bkprop': 'userid',  }

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
		if re.search('(ru|de|it|sv|fr)\.wikipedia', wikiapi):
			continue
		print 'Now doing "%s" via %s' % (title, wikiapi)
		revisions = getRelevantRevisions(wikiapi, title)
		print 'Found %d revisions to thank for' % len(revisions)
		thankRevisions(wikiapi, revisions)

if __name__ == "__main__":
	main()
