#!/usr/bin/env python
# encoding: utf-8
"""
downloader.py

Created by Thomas Mangin on 2011-12-01.
Copyright (c) 2011 Exa Networks. All rights reserved.
"""

from threading import Thread
from Queue import Empty

from .logger import Logger
logger = Logger()

from .http import HTTPFetcher,HTTPResponse

# http://tools.ietf.org/html/rfc2616#section-8.2.3
# Says we SHOULD keep track of the server version and deal with 100-continue
# I say I am too lazy - and if you want the feature use this software as as rev-proxy :D

class Download (object):
	"""A Thread which download pages"""
	def __init__(self):
		self._download_loop = None              # The download co-routine
		self.connect = set()                    # New connections to establish
		self.open = set()                       # Connection established but not yet write able
		self.fetchers = set()                   # the http object to now use

	def newFetcher (self, pipe):
		# XXX: readline could fail
		_cid,action,host,_port,request = pipe.readline().replace('\\n','\n').replace('\\r','\r').split(' ',4)
		cid = int(_cid)
		port = int(_port)

		# XXX: what to do ..
		# http://tools.ietf.org/html/rfc2616#section-14.10

		if action == 'request':
			logger.download('we need to download something on %s:%d' % (host,port))
			self.connect.add(HTTPFetcher(cid,host,port,request))
		elif action == 'response':
			logger.download('direct response to %s' % cid)
			self.fetchers.add(HTTPResponse(cid,host.replace('_',' '),request))
		else:
			raise RuntimeError('%s is an invalid action' % action)

	def connectFetchers (self):
		for fetcher in set(self.connect):
			logger.download('sending request on behalf of %s' % fetcher.cid)
			# True if we finished sending the request to the web server
			if fetcher.connect():
				# We now need to read from this object in the select loop
				self.connect.remove(fetcher)
				self.open.add(fetcher)

	def available (self,fetcher):
		self.fetchers.add(fetcher)
		self.open.remove(fetcher)
	
	def finish (self,fetcher):
		self.connect.discard(fetcher.cid)
		self.open.discard(fetcher.cid)
		self.fetchers.discard(fetcher)

	def stop (self):
		self.connect = set()
		self.open = set()
		self.fetchers = set()
