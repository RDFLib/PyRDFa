# -*- coding: utf-8 -*-
"""
For more details, see U{the RDFa API specification<http://www.w3.org/TR/rdfa-api/#data-store>}

@summary: RDFa Literal generation
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: Literal.py,v 1.10 2010/10/29 16:30:22 ivan Exp $
$Date: 2010/10/29 16:30:22 $
"""



"""
The Data Store interface .

For more details, see L{the RDFa API specification<http://www.w3.org/TR/rdfa-api/#data-store>}

Testing change/
"""
from rdflib	import URIRef
from rdflib	import Literal
from rdflib	import BNode
from rdflib	import ConjunctiveGraph


from pyRdfa.API import IRI, PlainLiteral, TypedLiteral, BlankNode, RDFTriple
from pyRdfa.API.RDF import _origins


class DataStore(ConjunctiveGraph) :
	def __init__(self) :
		# no real initialization here, this acts as a placeholder only
		ConjunctiveGraph.__init__(self)
		self.__emptyContext = _origins(None, None, None)
		
	# mimics the attribute reach for size
	def __getattr__(self, attr) :
		if attr == "size" :
			return self.__len__()
			
	def add(self, triple ) :
		self.store.add((s, p, o), context=triple.origin, quoted=False)		
			
	def createIRI(self, value, origin = None) :
		return IRI(value, origin)
			
	def createPlainLiteral(self, value, lang = None, origin = None) :
		return PlainLiteral(value, lang, origin)

	def createTypedLiteral(self, value, datatype, origin = None) :
		return TypedLiteral(value, datatype, origin)
		
	def createBlankNode(self, origin = None) :
		return BlankNode(origin)
		
	def createTriple(self, subject, predicate, object) :
		return RDFTriple(subject, predicate, object)
		
	def filter(self, subject = None, predicate = None, object = None, element = None, filter = None) :
		if filter == None :
			for s,p,o,ctx in self.quads((subject,predicate,object)) :
				yield RDFTriple(s,p,o,ctx)
		else :
			for s,p,o,ctx in self.quads((subject,predicate,object)) :
				triple = RDFTriple(s,p,o,ctx)
				if filter.match(triple) :
					yield triple
	
	def clear(self) :
		# this may go wrong, test it!
		for (s,p,o) in self.triples((None,None,None)) : self.remove((s,p,o))
	
	def forEach(self, callback) :
		for s,p,o,ctx in self.quads((None,None,None)) : callback(s,p,o,ctx)
		
		
		
if __name__ == "__main__" :
	store = DataStore()
	s = store.createIRI("http://www.w3.org","http://www.nami.van")
	p = store.createIRI("http://pred.ica.te")
	o = store.createPlainLiteral("namivan")
	
	print s.origin
	
	triple = RDFTriple(s,p,o)

	print triple.origin
	print triple.origin.s_origin
	
	store.add(triple)
	def f(s,p,o, ctx) :
		print s,p,o, ctx
	store.forEach(f)
	print store.serialize(format="n3")
	
	