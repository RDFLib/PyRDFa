#!/usr/bin/env python
# -*- coding: utf-8 -*-


from xml.dom.minidom import parse, parseString
from datetime import date

def one_entry(term) :
	return "\t'%s'\t\t\t: 'http://www.w3.org/1999/xhtml/vocab#%s'," % (term,term)

def getText(nodelist):
	rc = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
	return ''.join(rc)

def manage_dom(dom) :
	for record in dom.getElementsByTagName("record") :
		term = ""
		desc = ""
		for child in record.childNodes :
			if child.nodeType == child.ELEMENT_NODE and child.nodeName == "value" :
				term = getText(child.childNodes)
		if term != "describedby" :
			print one_entry(term.encode('utf-8'))
			
#############################			
Header = """initial_context["http://www.w3.org/2011/rdfa-context/html-rdfa-1.1"].terms = {"""
Footer = """
	'p3pv1'				: 'http://www.w3.org/1999/xhtml/vocab#p3pv1',
	'transformation'	: 'http://www.w3.org/2003/g/data-view#transformation',
	'itsRules'			: 'http://www.w3.org/1999/xhtml/vocab#itsRules',
	'role'				: 'http://www.w3.org/1999/xhtml/vocab#role',
}
"""

if __name__ == '__main__':
	print Header
	dom = parse('/Users/ivan/W3C/WWW/2011/rdfa-context/link-relations.xml')
	manage_dom(dom)
	print Footer


