#!/usr/bin/env python
"""
Run the pyRdfa package locally, ie, on a local file
"""
# You may want to adapt this to your environment...
import sys, getopt, platform

sys.path.insert(0,"/Users/ivan/Source/PythonModules/pyRdfa-3.0")

from pyRdfa.Utils import URIOpener
from rdflib.Graph import Graph
from rdflib.plugin 		import register
from rdflib.syntax 		import parsers
	
RDFa_header_1  = 'text/html'
RDFa_header_2  = 'applications/xhtml+xml'
Turtle_header  = 'text/turtle'
RDF_XML_header = 'application/rdf+xml' 

def test(uri) :
	acceptHeader = { 'Accept' : 'application/rdf+xml;q=0.2, text/turtle;q=0.9'}
#	acceptHeader = { 'Accept' : 'application/rdf+xml'}
	opener = URIOpener(uri, acceptHeader)
	if opener.content_type.find(RDFa_header_1) != -1 or opener.content_type.find(RDFa_header_2) != -1 :
		print "this is an RDfa file"
	elif opener.content_type.find(Turtle_header) != -1 :
		print "this is turtle"
		register("turtle", parsers.Parser, "RDFClosure.parsers.N3Parser","N3Parser")
		g = Graph()
		for l in opener.data :
			print l
		#g.parse(opener.data,format="turtle")
		#for (s,p,o) in g :
		#	print s,p,o
	elif opener.content_type.find(RDF_XML_header) != -1 :
		print "this is rdf/xml"
		g = Graph()
		g.parse(opener.data)
		for (s,p,o) in g :
			print s,p,o
	else :
		print "Unrecognized file type"
	
	
	#print opener.content_type
	##g = Graph()
	##g.parse(opener.data)
	##print g
	#for l in opener.data :
	#	print l



if __name__ == '__main__' :
	test(sys.argv[1])