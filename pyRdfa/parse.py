# -*- coding: utf-8 -*-
"""
The core parsing function of RDFa. Some details are
put into other modules to make it clearer to update/modify (eg, generation of literals, or managing the current state).

@summary: RDFa core parser processing step
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
"""

"""
$Id: parse.py,v 1.5 2011/11/15 12:18:52 ivan Exp $
$Date: 2011/11/15 12:18:52 $

Added a reaction on the RDFaStopParsing exception: if raised while setting up the local execution context, parsing
is stopped (on the whole subtree)
"""

import sys

from pyRdfa.state   		import ExecutionContext
from pyRdfa.property 		import ProcessProperty
from pyRdfa.embeddedRDF	 	import handle_embeddedRDF
from pyRdfa.host			import HostLanguage, host_dom_transforms, accept_embedded_rdf

import rdflib
from rdflib	import URIRef
from rdflib	import Literal
from rdflib	import BNode
from rdflib	import Namespace
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import Graph
	from rdflib	import RDF  as ns_rdf
	from rdflib	import RDFS as ns_rdfs
else :
	from rdflib.Graph	import Graph
	from rdflib.RDFS	import RDFSNS as ns_rdfs
	from rdflib.RDF		import RDFNS  as ns_rdf

from pyRdfa import IncorrectBlankNodeUsage, err_no_blank_node
from pyRdfa.utils import has_one_of_attributes


#######################################################################
def parse_one_node(node, graph, parent_object, incoming_state, parent_incomplete_triples) :
	"""The (recursive) step of handling a single node. See the
	U{RDFa syntax document<http://www.w3.org/TR/rdfa-syntax>} for further details.
	
	This entry just switches between the RDFa 1.0 and RDFa 1.1 versions for parsing. This method is only invoked once,
	actually, that is from the top level; the recursion then happens in the L{_parse_1_0} and L{_parse_1_1} methods for
	RDFa 1.0 and RDFa 1.1, respectively.

	@param node: the DOM node to handle
	@param graph: the RDF graph
	@type graph: RDFLib's Graph object instance
	@param parent_object: the parent's object, as an RDFLib URIRef
	@param incoming_state: the inherited state (namespaces, lang, etc)
	@type incoming_state: L{state.ExecutionContext}
	@param parent_incomplete_triples: list of hanging triples (the missing resource set to None) to be handled (or not)
	by the current node.
	@return: whether the caller has to complete it's parent's incomplete triples
	@rtype: Boolean
	"""

	# Branch according to versions.
	if incoming_state.rdfa_version >= "1.1" :
		_parse_1_1(node, graph, parent_object, incoming_state, parent_incomplete_triples)
	else :
		_parse_1_0(node, graph, parent_object, incoming_state, parent_incomplete_triples)

#######################################################################
def _parse_1_1(node, graph, parent_object, incoming_state, parent_incomplete_triples) :
	"""The (recursive) step of handling a single node. See the
	U{RDFa syntax document<http://www.w3.org/TR/rdfa-syntax>} for further details.
	
	This is the RDFa 1.1 (and higher) version.

	@param node: the DOM node to handle
	@param graph: the RDF graph
	@type graph: RDFLib's Graph object instance
	@param parent_object: the parent's object, as an RDFLib URIRef
	@param incoming_state: the inherited state (namespaces, lang, etc)
	@type incoming_state: L{state.ExecutionContext}
	@param parent_incomplete_triples: list of hanging triples (the missing resource set to None) to be handled (or not)
	by the current node.
	@return: whether the caller has to complete it's parent's incomplete triples
	@rtype: Boolean
	"""

	# Update the state. This means, for example, the possible local settings of
	# namespaces and lang
	state = None
	state = ExecutionContext(node, graph, inherited_state=incoming_state)

	#---------------------------------------------------------------------------------
	# Handle the special case for embedded RDF, eg, in SVG1.2. 
	# This may add some triples to the target graph that does not originate from RDFa parsing
	# If the function return TRUE, that means that an rdf:RDF has been found. No
	# RDFa parsing should be done on that subtree, so we simply return...
	if state.options.host_language in accept_embedded_rdf and node.nodeType == node.ELEMENT_NODE and handle_embeddedRDF(node, graph, state) : 
		return	

	#---------------------------------------------------------------------------------
	# calling the host language specific massaging of the DOM
	if state.options.host_language in host_dom_transforms and node.nodeType == node.ELEMENT_NODE :
		for func in host_dom_transforms[state.options.host_language] : func(node, state)

	#---------------------------------------------------------------------------------
	# First, let us check whether there is anything to do at all. Ie,
	# whether there is any relevant RDFa specific attribute on the element
	#
	if not has_one_of_attributes(node, "href", "resource", "about", "property", "rel", "rev", "typeof", "src", "vocab", "prefix") :
		# nop, there is nothing to do here, just go down the tree and return...
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE : parse_one_node(n, graph, parent_object, state, parent_incomplete_triples)
		return

	#-----------------------------------------------------------------
	# The goal is to establish the subject and object for local processing
	# The behaviour is slightly different depending on the presense or not
	# of the @rel/@rev attributes
	current_subject = None
	current_object  = None
	typed_resource	= None

	if has_one_of_attributes(node, "rel", "rev")  :
		# in this case there is the notion of 'left' and 'right' of @rel/@rev
		# in establishing the new Subject and the objectResource

		# set first the subject
		if node.hasAttribute("about") :
			current_subject = state.getURI("about")
			if node.hasAttribute("typeof") : typed_resource = current_subject
			
		# get_URI may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			current_subject = parent_object
		else :
			state.reset_list_mapping(origin = current_subject)
		
		# set the object resource
		current_object = state.getResource("resource", "href", "src")
			
		if node.hasAttribute("typeof") and not node.hasAttribute("about") :
			if current_object == None :
				current_object = BNode()
			typed_resource = current_object
		
		if not node.hasAttribute("inlist") and current_object != None :
			# In this case the newly defined object is, in fact, the head of the list
			# just reset the whole thing.
			state.reset_list_mapping(origin = current_object)

	elif  node.hasAttribute("property") and not has_one_of_attributes(node, "content", "datatype") :
		# this is the case when the property may take hold of @src and friends...
		if node.hasAttribute("about") :
			current_subject = state.getURI("about")
			if node.hasAttribute("typeof") : typed_resource = current_subject

		# get_URI_ref may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			current_subject = parent_object
		else :
			state.reset_list_mapping(origin = current_subject)

		if typed_resource == None and node.hasAttribute("typeof") :
			typed_resource = state.getResource("resource", "href", "src")
			if typed_resource == None :
				typed_resource = BNode()
			current_object = typed_resource
		else :
			current_object = current_subject
			
	else :
		# in this case all the various 'resource' setting attributes
		# behave identically, though they also have their own priority
		current_subject = state.getResource("about", "resource", "href", "src")
			
		# get_URI_ref may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			if node.hasAttribute("typeof") :
				current_subject = BNode()
			else :
				current_subject = parent_object
		else :
			state.reset_list_mapping(origin = current_subject)

		# in this case no non-literal triples will be generated, so the
		# only role of the current_object Resource is to be transferred to
		# the children node
		current_object = current_subject
		if node.hasAttribute("typeof") : typed_resource = current_subject
		
	# ---------------------------------------------------------------------
	## The possible typeof indicates a number of type statements on the typed resource
	for defined_type in state.getURI("typeof") :
		if typed_resource :
			graph.add((typed_resource, ns_rdf["type"], defined_type))

	# ---------------------------------------------------------------------
	# In case of @rel/@rev, either triples or incomplete triples are generated
	# the (possible) incomplete triples are collected, to be forwarded to the children
	incomplete_triples  = []
	for prop in state.getURI("rel") :
		if not isinstance(prop,BNode) :
			if node.hasAttribute("inlist") :
				if current_object != None :
					state.add_to_list_mapping(prop, current_object)
				else :
					incomplete_triples.append((None, prop, None))
			else :
				theTriple = (current_subject, prop, current_object)
				if current_object != None :
					graph.add(theTriple)
				else :
					incomplete_triples.append(theTriple)
		else :
			state.options.add_warning(err_no_blank_node % "rel", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	for prop in state.getURI("rev") :
		if not isinstance(prop,BNode) :
			theTriple = (current_object,prop,current_subject)
			if current_object != None :
				graph.add(theTriple)
			else :
				incomplete_triples.append(theTriple)
		else :
			state.options.add_warning(err_no_blank_node % "rev", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	# ----------------------------------------------------------------------
	# Generation of the literal values. The newSubject is the subject
	# A particularity of property is that it stops the parsing down the DOM tree if an XML Literal is generated,
	# because everything down there is part of the generated literal. 
	if node.hasAttribute("property") :
		ProcessProperty(node, graph, current_subject, state, typed_resource).generate_1_1()

	# ----------------------------------------------------------------------
	# Setting the current object to a bnode is setting up a possible resource
	# for the incomplete triples downwards
	if current_object == None :
		object_to_children = BNode()
	else :
		object_to_children = current_object

	#-----------------------------------------------------------------------
	# Here is the recursion step for all the children
	for n in node.childNodes :
		if n.nodeType == node.ELEMENT_NODE : 
			_parse_1_1(n, graph, object_to_children, state, incomplete_triples)

	# ---------------------------------------------------------------------
	# At this point, the parent's incomplete triples may be completed
	for (s,p,o) in parent_incomplete_triples :
		if s == None and o == None :
			# This is an encoded version of a hanging rel for a collection:
			incoming_state.add_to_list_mapping( p, current_subject )
		else :
			if s == None : s = current_subject
			if o == None : o = current_subject
			graph.add((s,p,o))

	# Generate the lists, if any and if this is the level where a new list was originally created	
	if state.new_list and not state.list_empty() :
		for prop in state.get_list_props() :
			vals  = state.get_list_value(prop)
			heads = [ BNode() for r in vals ] + [ ns_rdf["nil"] ]
			for i in xrange(0, len(vals)) :
				graph.add( (heads[i], ns_rdf["first"], vals[i]) )
				graph.add( (heads[i], ns_rdf["rest"],  heads[i+1]) )
			# Anchor the list
			graph.add( (state.get_list_origin(), prop, heads[0]) )

	# -------------------------------------------------------------------
	# This should be it...
	# -------------------------------------------------------------------
	return


##################################################################################################################
def _parse_1_0(node, graph, parent_object, incoming_state, parent_incomplete_triples) :
	"""The (recursive) step of handling a single node. See the
	U{RDFa syntax document<http://www.w3.org/TR/rdfa-syntax>} for further details.
	
	This is the RDFa 1.0 version.

	@param node: the DOM node to handle
	@param graph: the RDF graph
	@type graph: RDFLib's Graph object instance
	@param parent_object: the parent's object, as an RDFLib URIRef
	@param incoming_state: the inherited state (namespaces, lang, etc)
	@type incoming_state: L{state.ExecutionContext}
	@param parent_incomplete_triples: list of hanging triples (the missing resource set to None) to be handled (or not)
	by the current node.
	@return: whether the caller has to complete it's parent's incomplete triples
	@rtype: Boolean
	"""

	# Update the state. This means, for example, the possible local settings of
	# namespaces and lang
	state = None
	state = ExecutionContext(node, graph, inherited_state=incoming_state)

	#---------------------------------------------------------------------------------
	# Handle the special case for embedded RDF, eg, in SVG1.2. 
	# This may add some triples to the target graph that does not originate from RDFa parsing
	# If the function return TRUE, that means that an rdf:RDF has been found. No
	# RDFa parsing should be done on that subtree, so we simply return...
	if state.options.host_language in accept_embedded_rdf and node.nodeType == node.ELEMENT_NODE and handle_embeddedRDF(node, graph, state) : 
		return	

	#---------------------------------------------------------------------------------
	# calling the host language specific massaging of the DOM
	if state.options.host_language in host_dom_transforms and node.nodeType == node.ELEMENT_NODE :
		for func in host_dom_transforms[state.options.host_language] : func(node, state)

	#---------------------------------------------------------------------------------
	# First, let us check whether there is anything to do at all. Ie,
	# whether there is any relevant RDFa specific attribute on the element
	#
	if not has_one_of_attributes(node, "href", "resource", "about", "property", "rel", "rev", "typeof", "src") :
		# nop, there is nothing to do here, just go down the tree and return...
		for n in node.childNodes :
			if n.nodeType == node.ELEMENT_NODE : parse_one_node(n, graph, parent_object, state, parent_incomplete_triples)
		return

	#-----------------------------------------------------------------
	# The goal is to establish the subject and object for local processing
	# The behaviour is slightly different depending on the presense or not
	# of the @rel/@rev attributes
	current_subject = None
	current_object  = None
	prop_object		= None

	if has_one_of_attributes(node, "rel", "rev")  :
		# in this case there is the notion of 'left' and 'right' of @rel/@rev
		# in establishing the new Subject and the objectResource
		current_subject = state.getResource("about","src")
			
		# get_URI may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			if node.hasAttribute("typeof") :
				current_subject = BNode()
			else :
				current_subject = parent_object
		else :
			state.reset_list_mapping(origin = current_subject)
		
		# set the object resource
		current_object = state.getResource("resource", "href")
		
	else :
		# in this case all the various 'resource' setting attributes
		# behave identically, though they also have their own priority
		current_subject = state.getResource("about", "src", "resource", "href")
		
		# get_URI_ref may return None in case of an illegal CURIE, so
		# we have to be careful here, not use only an 'else'
		if current_subject == None :
			if node.hasAttribute("typeof") :
				current_subject = BNode()
			else :
				current_subject = parent_object
			current_subject = parent_object
		else :
			state.reset_list_mapping(origin = current_subject)

		# in this case no non-literal triples will be generated, so the
		# only role of the current_object Resource is to be transferred to
		# the children node
		current_object = current_subject
		
	# ---------------------------------------------------------------------
	## The possible typeof indicates a number of type statements on the new Subject
	for defined_type in state.getURI("typeof") :
		graph.add((current_subject, ns_rdf["type"], defined_type))

	# ---------------------------------------------------------------------
	# In case of @rel/@rev, either triples or incomplete triples are generated
	# the (possible) incomplete triples are collected, to be forwarded to the children
	incomplete_triples  = []
	for prop in state.getURI("rel") :
		if not isinstance(prop,BNode) :
			theTriple = (current_subject, prop, current_object)
			if current_object != None :
				graph.add(theTriple)
			else :
				incomplete_triples.append(theTriple)
		else :
			state.options.add_warning(err_no_blank_node % "rel", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	for prop in state.getURI("rev") :
		if not isinstance(prop,BNode) :
			theTriple = (current_object,prop,current_subject)
			if current_object != None :
				graph.add(theTriple)
			else :
				incomplete_triples.append(theTriple)
		else :
			state.options.add_warning(err_no_blank_node % "rev", warning_type=IncorrectBlankNodeUsage, node=node.nodeName)

	# ----------------------------------------------------------------------
	# Generation of the literal values. The newSubject is the subject
	# A particularity of property is that it stops the parsing down the DOM tree if an XML Literal is generated,
	# because everything down there is part of the generated literal. 
	if node.hasAttribute("property") :
		ProcessProperty(node, graph, current_subject, state).generate_1_0()

	# ----------------------------------------------------------------------
	# Setting the current object to a bnode is setting up a possible resource
	# for the incomplete triples downwards
	if current_object == None :
		object_to_children = BNode()
	else :
		object_to_children = current_object

	#-----------------------------------------------------------------------
	# Here is the recursion step for all the children
	for n in node.childNodes :
		if n.nodeType == node.ELEMENT_NODE : 
			_parse_1_0(n, graph, object_to_children, state, incomplete_triples)

	# ---------------------------------------------------------------------
	# At this point, the parent's incomplete triples may be completed
	for (s,p,o) in parent_incomplete_triples :
		if s == None and o == None :
			# This is an encoded version of a hanging rel for a collection:
			incoming_state.add_to_list_mapping( p, current_subject )
		else :
			if s == None : s = current_subject
			if o == None : o = current_subject
			graph.add((s,p,o))

	# -------------------------------------------------------------------
	# This should be it...
	# -------------------------------------------------------------------
	return


