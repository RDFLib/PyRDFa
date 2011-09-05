# -*- coding: utf-8 -*-
"""
Handling of collections and containers as a preprocessor to the full RDFa processing. See the
U{text on the RDFa WG’s pages<http://www.w3.org/2010/02/rdfa/wiki/ContainersAndCollections>} for the details.

@summary: Transfomer to handle RDF collections and containers
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: containerscollections.py,v 1.1 2011/08/12 10:10:33 ivan Exp $
$Date: 2011/08/12 10:10:33 $
"""

from pyRdfa.utils import traverse_tree, dump

import rdflib
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf


class BIDs :
	"""Class to handle the collection and the generation of unique blank node identifiers.
	@ivar bids: set of Blank node id-s
	@ivar bidnum: the integer used to create a new id
	@ivar latestbid: the latest id that has been generated
	"""
	def __init__(self, html) :
		"""
		@param html: the top level DOM node
		"""
		self.bidnum    = 10
		self.bids      = set()
		self.latestbid = ""
		def collect(node) :
			"""Check and collect the possible bnode id-s in the file that might occur in CURIE-s. The
			function is called recursively on each node. The L{bids} variable is filled with the initial values.
			@param node: a DOM element node
			"""
			def suspect(val) :
				if len(val) > 1 :
					if val[0] == "_" and val[1] == ":" :
						self.bids.add(val)
					elif val[0] == "[" and val[-1] == "]" :
						suspect(val[1:-1])
			for value in ["about","resource","typeof"] :
				if node.hasAttribute(value) :
					for b in node.getAttribute(value).strip().split() :
						suspect(b)
			return False
		# fill the bnode collection:
		traverse_tree(html, collect)
		
	def new_id(self) :
		"""Generate a new value that can be used as a bnode id...
		@return: a string of the form _:XXXX where XXXX is unique (ie, not yet stored in the L{bids} set).
		"""
		while True :
			# Eventually that should succeed...
			val = "_:xyz%d" % self.bidnum
			self.bidnum += 1
			if not val in self.bids :
				self.bids.add(val)
				self.latestbid = val
				return val
			
	def get_latestid(self) :
		"""
		@return: the latest blank node id
		"""
		return self.latestbid
	
#################################################

class WrappedCollections :
	"""
	Handling of collections as a preprocessor to the full RDFa processing.
	See the module description for the details. This is the
	version U{using attributes <http://www.w3.org/2010/02/rdfa/wiki/Lists>}.

	@cvar blanks: collections of blank node id-s
	@type blanks: L{BIDs}
	"""
	def __init__(self, html) :
		"""
		@param html: top level DOM Node
		"""
		self.blanks = BIDs(html)
		self.look_for_triggers(html)
		
	def is_trigger(self, node) :
		"""
		Check if the node is a "trigger", ie, the head of a collection or a container
		@return: boolean
		"""
		if node.hasAttribute("collection") :
			return True 
		else :
			return False

	def look_for_triggers(self, node) :
		"""
		Recursively check the DOM tree for a "trigger" and initiate the transformation of the DOM tree at that point.
		@param node: DOM Element Node
		"""				
		if node.hasAttribute("collection") :
			if node.hasAttribute("resource") :
				self.current_subject = node.getAttribute("resource")
			elif node.hasAttribute("href") :
				self.current_subject = node.getAttribute("href")
			else :
				self.current_subject = self.blanks.new_id()
				node.setAttribute("resource", self.current_subject)
			self.handle_collection(node)				
			
		# handled the possible triggers, go for the children
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE :
				self.look_for_triggers(n)
					
	def handle_collection(self, node) :
		"""
		Handle a collection with the head at the incoming node
		@param node: DOM Element node triggering a container transformation
		"""
		def add_about(node) :
			if not self.current_subject == "" :
				node.setAttribute("about", self.current_subject)
			self.subj_lst.append(self.current_subject)
			self.current_subject = self.blanks.new_id()
			
		def update_mb(n) :
			if self.is_trigger(n) :
				return
			elif n.hasAttribute("member") :
				if n.hasAttribute("resource") or n.hasAttribute("href") or n.hasAttribute("src") :
					n.setAttribute("rel", str(ns_rdf["first"]))
				else :
					n.setAttribute("property", str(ns_rdf["first"]))
				add_about(n)
				return
			else :
				for nc in n.childNodes :
					if nc.nodeType == node.ELEMENT_NODE :
						update_mb(nc)

		self.subj_lst = []
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE :
				update_mb(n)
				
		# Link the list elements together and ground it
		for i in xrange(0,len(self.subj_lst)) :
			link_element = node.ownerDocument.createElement("list_links")
			node.appendChild(link_element)
			if not self.subj_lst[i] == "" :
				link_element.setAttribute("about", self.subj_lst[i])
			link_element.setAttribute("rel",str(ns_rdf["rest"]))
			try :
				link_element.setAttribute("resource",self.subj_lst[i+1])
			except IndexError :
				link_element.setAttribute("resource",str(ns_rdf["nil"]))


#################################################
# Trigger-less collection

class SimpleCollection :
	"""
	Handling of collections as a preprocessor to the full RDFa processing.
	See the module description for the details. This is the
	version U{using attributes <http://www.w3.org/2010/02/rdfa/wiki/Lists>}.

	@cvar blanks: collections of blank node id-s
	@type blanks: L{BIDs}
	"""
	def __init__(self, html) :
		"""
		@param html: top level DOM Node
		"""
		self.blanks = BIDs(html)
		self.process_list_headers(html)
		
	def process_list_headers(self, node) :
		"""
		Check if the common children of this parent constitute one or more collections
		"""
		lists = {}
		for nc in node.childNodes :
			if nc.nodeType == node.ELEMENT_NODE :
				if nc.hasAttribute("member") :
					# bingo... if there is a property or a rel here
					if nc.hasAttribute("property") :
						predicate = nc.getAttribute("property")
						origin    = "property"
					elif nc.hasAttribute("rel") :
						predicate = nc.getAttribute("rel")
						origin    = "rel"
					else :
						continue # Not a list element
					if predicate not in lists :
						lists[predicate] = [(nc, origin)]
					else :
						lists[predicate].append((nc, origin))
		
		# Now handle the lists if there are any:
		for pr in lists :
			self.handle_list(node, pr, lists[pr])
			
		# Go to the next level
		for nc in node.childNodes :
			if nc.nodeType == node.ELEMENT_NODE :
				self.process_list_headers(nc)
				
	def handle_list(self, parent, predicate, nodes) :
		# First, the list header has to be created; this is an artificial extra node. For traceability,
		# it is appended to the parent, although it could be anywhere
		link_element = parent.ownerDocument.createElement("list_links")
		parent.appendChild(link_element)
		link_element.setAttribute("rel",predicate)
		current_subject = self.blanks.new_id()
		link_element.setAttribute("resource",current_subject)
		
		# Next, each node is processed by setting the link attributes and creating a new 'connect' triple
		for i in range(0,len(nodes)) :
			(node, origin) = nodes[i]
			# modify the node's RDFa attributes
			node.setAttribute(origin, str(ns_rdf["first"]))
			node.setAttribute("about", current_subject)
			# now a new link element has to be created
			link_element = parent.ownerDocument.createElement("list_links")
			parent.appendChild(link_element)
			link_element.setAttribute("about", current_subject)
			link_element.setAttribute("rel",str(ns_rdf["rest"]))
			if i == len(nodes) - 1 :
				# this is the last element, so we have to 'ground' the list
				link_element.setAttribute("resource",str(ns_rdf["nil"]))
			else :
				current_subject = self.blanks.new_id()
				link_element.setAttribute("resource",current_subject)



def containers_collections(html, option) :
	"""
	The main transformer entry point. See the module description for details.
	@param html: a DOM node for the top level html element
	@param option: invocation options (not used in this module)
	@type option: L{Options<pyRdfa.Options>}
	"""
	#h = WrappedCollections(html)
	h = SimpleCollection(html)
	#dump(html)
	
############
"""
$Log: containerscollections.py,v $
Revision 1.1  2011/08/12 10:10:33  ivan
*** empty log message ***

Revision 1.8  2011/03/08 10:50:14  ivan
*** empty log message ***

Revision 1.7  2010/11/19 13:52:52  ivan
*** empty log message ***

Revision 1.6  2010/11/02 14:56:46  ivan
*** empty log message ***

Revision 1.5  2010/08/27 13:45:44  ivan
Added cvs log placeholder

"""

