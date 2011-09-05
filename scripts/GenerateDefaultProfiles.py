#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run the pyRdfa package locally to generate an updated version of the default profile module...
"""
# You may want to adapt this to your environment...
import sys, getopt, platform

sys.path.insert(0,"/Users/ivan/Source/PythonModules/pyRdfa-3.0")

from pyRdfa import pyRdfa
from pyRdfa.ProfileCache import CachedProfile

profile_uris = [
	"http://www.w3.org/profile/rdfa-1.1",
	"http://www.w3.org/profile/html-rdfa-1.1",
]

########################################################################################
_header = """
# -*- coding: utf-8 -*-
\"\"\"
Built-in version of the default profile contents. The code may use this directly instead of caching the
vocabulary.

@summary: Management of vocabularies, terms, and their mapping to URI-s.
@requires: U{RDFLib package<http://rdflib.net>}
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}

@var default_profiles: prefix for the XHTML vocabulary URI (set to 'xhv')
\"\"\"

\"\"\"
$Id:  $
$Date:  $
\"\"\"

class Wrapper :
	pass
	
default_profiles = {
"""

def generate_header(outp) :
	outp.write(_header)
	for uri in profile_uris :
		outp.write("\t\"%s\" : Wrapper(),\n" % uri)
	outp.write("}\n\n")
		
		
def process_one_profile(uri, outp) :
	def print_dictionary(name,dict) :
		outp.write("%s = {\n" % name)
		for k in dict :
			outp.write("\t'%s'\t: '%s',\n" % (k,dict[k]))
		outp.write("}\n\n")
	
	dname = "default_profiles[\"%s\"]" % uri
	
	prof = CachedProfile(uri, None, False)
	print_dictionary("%s.ns" % dname, prof.ns)
	print_dictionary("%s.terms" % dname,prof.terms)
	if prof.vocabulary :
		outp.write("%s.vocabulary = \"%s\"\n\n" % (dname, prof.vocabulary))
	else :
		outp.write("%s.vocabulary = \"\"\n\n" % dname)
	
	
_footer = """


\"\"\"
$Log: $
\"\"\"
"""
def generate_footer(outp) :
	outp.write(_footer)	


def main(outp) :
	generate_header(outp)
	for uri in profile_uris : process_one_profile(uri,outp)
	


if __name__ == '__main__':
	main(sys.stdout)


	