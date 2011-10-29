# -*- coding: utf-8 -*-
"""
Simple transfomer for HTML5: add a @src for any @data, and add a @content for the @value attribute of the <data> element.

@summary: Add a top "about" to <head> and <body>
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@contact: Ivan Herman, ivan@w3.org
"""

"""
$Id: atom.py,v 1.1 2011/08/12 10:05:55 ivan Exp $
$Date: 2011/08/12 10:05:55 $
"""

def html5_extra_attributes(node, state) :
	"""
	@param node: the current node that could be modified
	@param state: current state
	@type state: L{Execution context<pyRdfa.state.ExecutionContext>}
	"""
	if node.tagName == "data" and not node.hasAttribute("content") :
		if node.hasAttribute("value") :
			note.setAttribute("content", node.getAttribute("value"))
		else :
			node.setAttribute("content","")
	elif node.hasAttribute("data") and not node.hasAttribute("src") :
		node.setAttribute("src", node.getAttribute("data"))
