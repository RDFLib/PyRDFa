#!/usr/bin/env python
""" The RDF interfaces of the RDFa API.

For more details, see L{the RDFa API specification<http://www.w3.org/TR/rdfa-api/#the-rdf-interfaces>}


"""
from rdflib	import URIRef, Literal, BNode
from rdflib	import Literal
from rdflib	import BNode
import rdflib
if rdflib.__version__ >= "3.0.0" :
	from rdflib	import Graph
else :
	from rdflib.Graph	import Graph


class IRI(URIRef) :
	"""
	RDF Resource, ie, an IRI
	@ivar value: The lexical representation of the IRI reference. Readonly. 
	@ivar origin: The node that specifies the IRI's value in the RDFa markup. Readonly. 
	"""
	_readonly = ["value", "origin"]
	def __new__(cls, value, origin = None) :
		"""
		@param value: The lexical representation of the IRI reference.
		@param origin:  The node that specifies the IRI's value in the RDFa markup.
		"""
		rt = URIRef.__new__(cls, value)
		rt.value       = value
		rt.origin	   = origin
		rt.initialized = True
		return rt

	def __repr__(self):
		return "RDFa API IRI('%s')" % self.value

	def __setattr__(self, attr, val) :
		if "initialized" in self.__dict__ and attr in IRI._readonly :
			raise AttributeError, "'%s' is a read only attribute for %s" % (attr, type(self))
		URIRef.__setattr__(self, attr, val)

class PlainLiteral(Literal) :
	"""
	RDF Plain Literal, with possible language tag
	@ivar language: A two character language string, normalized to lowercase. Readonly.
	@ivar value: The lexical value of the literal encoded in the character encoding of the source document. Readonly. 
	@ivar origin: The node that specifies the IRI's value in the RDFa markup. Readonly. 
	"""
	_readonly = ["language", "value", "origin" ]
	def __new__(cls, value, lang = None, origin = None) :
		"""
		RDF Plain Literal, with possible language tag
		@param language: A two character language string, normalized to lowercase.
		@param value: The lexical value of the literal encoded in the character encoding of the source document. 
		@param origin: The node that specifies the IRI's value in the RDFa markup. 
		"""
		if lang : lang = lang.lower()
		rt = Literal.__new__(cls, value, lang)
		rt.value       = value
		# Note that the 'language' attribute in the RDFa API PlainLiteral and the RDFLib.Literal coincide,
		# hence there is no need to make an explicit assignment
		rt.origin	   = origin
		rt.initialized = True
		return rt

	def __repr__(self):
		if self.language == None :
			return "RDFa API PlainLiteral('%s')" % self.value
		else :
			return "RDFa API PlainLiteral('%s'@%s)" % (self.value,self.language)
			
	def __str__(self) :
		if self.language == None :
			return "%s" % self.value
		else :
			return "%s@%s" % (self.value,self.language)
			
	def __setattr__(self, attr, val) :
		if "initialized" in self.__dict__ and attr in PlainLiteral._readonly :
			raise AttributeError, "'%s' is a read only attribute for %s" % (attr, type(self))
		Literal.__setattr__(self, attr, val)

class TypedLiteral(Literal) :
	"""
	RDF Typed Literal
	@ivar datatype: Datatype URI. Readonly.
	@type datatype: L{IRI<IRI>}
	@ivar value: The lexical value of the literal encoded in the character encoding of the source document. Readonly. 
	@ivar origin: The node that specifies the IRI's value in the RDFa markup. Readonly. 
	"""
	_readonly = ["type", "value", "origin"]
	def __new__(cls, value, datatype, origin = None) :
		"""
		RDF Typed Literal
		@param datatype: Datatype URI.
		@type datatype: L{IRI<IRI>}
		@param value: The lexical value of the literal encoded in the character encoding of the source document. 
		@param origin: The node that specifies the IRI's value in the RDFa markup.
		@raise TypeError: in case the datatype is not an IRI
		"""
		if isinstance(datatype, IRI) :
			rt = Literal.__new__(cls, value, datatype=datatype)
			rt.value	   = value
			rt.type		   = datatype
			rt.origin	   = origin
			rt.initialized = True
			return rt
		else :
			raise TypeError, "'%s' instance is initialized with an inappropriate type: %s" % (cls, type(datatype))

	def __repr__(self):
		return "RDFa API TypedLiteral('%s'^^%s)" % (self.value, self.datatype)
			
	def __str__(self) :
		return "%s^^%s" % (self.value, self.datatype)
			
	def __setattr__(self, attr, val) :
		if "initialized" in self.__dict__ and attr in TypedLiteral._readonly :
			raise AttributeError, "'%s' is a read only attribute for %s" % (attr, type(self))
		Literal.__setattr__(self, attr, val)
		
	def valueOf(self) : return self.toPython()

class BlankNode(BNode) :
	"""
	RDF Blank Node
	@ivar value: The temporary identifier of the BlankNode. Readonly. 
	@ivar origin: The node that specifies the IRI's value in the RDFa markup. Readonly. 
	"""
	_readonly = ["value", "origin"]
	def __new__(cls, origin = None) :
		"""
		RDF Blank Node
		@ivar origin: The node that specifies the IRI's value in the RDFa markup. 
		"""
		rt = BNode.__new__(cls)
		rt.value	   = rt
		rt.origin	   = origin
		rt.initialized = True
		return rt

	def __repr__(self):
		return "RDFa API BlankNode('_:%s')" % self.value
			
	def __str__(self) : 
		return "_:%s" % self.value
			
	def __setattr__(self, attr, val) :
		if "initialized" in self.__dict__ and attr in BlankNode._readonly :
			raise AttributeError, "'%s' is a read only attribute for %s" % (attr, type(self))
		BNode.__setattr__(self, attr, val)
		
class _origins :
	"""Internal representation of origins, bundled in one class. Used in the ConjunctiveGraph as a 'context' for a triple"""
	def __init__(self, subject_o, predicate_o, object_o) :
		self.s_origin	= subject_o
		self.p_origin	= predicate_o
		self.o_origin	= object_o
	#def __eq__(self, other) :
	#	if isinstance(other, _origins) :
	#		return self.s_origin == other.s_origin and self.p_origin == self.p_origin and self.o_origin == other.o_origin
	#	else :
	#		return False
	#def __ne__(self,other) :
	#	return not self.__eq__(other)
		
class RDFTriple :
	"""
	RDF Triple
	@ivar subject: Subject of the triple. Readonly. 
	@ivar predicate: Predicate of the triple. Readonly. 
	@ivar object: Object of the triple. Readonly. 
	"""
	_readonly = ["subject", "predicate", "object", "origin"]
	def __init__(self, subject, predicate, object, origins = None) :
		"""
		RDF Triple
		@ivar subject: Subject of the triple. Readonly. 
		@ivar predicate: Predicate of the triple. Readonly. 
		@ivar object: Object of the triple. Readonly.
		@raise TypeError: If the RDF restrictions on subject, predicate, resp, object values are not followed (eg, if predicate is a Blank Node)
		"""
		# Type checks and possible exceptions
		if not( isinstance(subject, IRI) or isinstance(subject, BlankNode) ) :
			raise TypeError, "Subject of a triple must be an IRI or a Blank Node; received %s" % type(subject)
		
		if not( isinstance(predicate, IRI) ) :
			raise TypeError, "Predicate of a triple must be an IRI; received %s" % type(predicate)

		if not( isinstance(object, IRI) or isinstance(object, BlankNode) or isinstance(object,TypedLiteral) or isinstance(object,PlainLiteral) ) :
			raise TypeError, "Object of a triple must be an IRI, Blank Node, or a Literal; received %s" % type(predicate)
		
		self.subject	= subject
		self.predicate	= predicate
		self.object		= object
		if origins :
			self.origin = origins
		else :
			self.origin	= _origins(subject.origin, predicate.origin, object.origin)
		self.initialized = True

	def __repr__(self):
		return "RDF Triple(%s,%s,%s)" % (self.subject, self.predicate, self.object)
			
	def __str__(self) : 
		return "(%s,%s,%s)" % (str(self.subject), str(self.predicate), str(self.object))
		
	def __setattr__(self, attr, val) :
		if "initialized" in self.__dict__ and attr in RDFTriple._readonly :
			raise AttributeError, "'%s' is a read only attribute for %s" % (attr, type(self))
		else :
			self.__dict__[attr] = val			

###############################################################################################

if __name__ == "__main__" :
	a = IRI("http://www.w3.org")
	b = PlainLiteral("namivan")
	c = PlainLiteral("namivan","HU")
	d = TypedLiteral("namivan", IRI("http://www.w3.org/integer"))
	e = BlankNode()
	print c
	t = RDFTriple(e,a,b)
	print t
	
	
	
	