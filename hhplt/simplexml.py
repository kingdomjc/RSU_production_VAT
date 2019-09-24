# Copyright (C) 2005 Ales Smrcka
# Use of this software is subject to the terms of the GNU General
# Public License
#

from xml.dom import minidom, Node

def parsepath(path):
	"""internal use only: parsepath(path) - transform path like 'node/subnode(attr1=value,attr2=value2)[2]/subsubnode' into processible structure"""
	# remove first and last '/'
	if path[0] == '/': path=path[1:]
	if path[-1] == '/': path=path[:-1]
	el = path.split('/')
	elements=[]
	for e in el:
		where=0 # state in finite automaton
		element=u''
		attrs={}
		idx=''
		attrname=u''
		attrvalue=u''
		for c in e:
			if where==0: # inside element
				if c == '(': where=1
				elif c == '[': where=4
				else: element += c
			elif where==1: # inside attribute name
				if c == '=': where=2
				else: attrname += c
			elif where==2: # inside attribute value
				if c == ',' or c == ')':
					attrs[attrname] = attrvalue
					attrname=u''
					attrvalue=u''
				if c == ',': where=1
				elif c == ')': where=3
				else: attrvalue += c
			elif where==3: # before element index
				if c == '[': where=4
			elif where==4: # inside element index
				if c == ']': idx=int(idx); where=5
				else: idx += c
		if idx == '': idx=-1
		elements.append((element, attrs, idx))
	return elements

def element_childs(node, nextelement):
	"""internal use only: node (xml.dom.Node), nextelement: ('name',{attrs values},idx)"""
	results=[]
	i=0
	for c in node.childNodes:
		# child is element type and name matches
		if c.nodeType == Node.ELEMENT_NODE and c.nodeName == nextelement[0]:
			# check for attribute values
			attrok=True
			for (name, value) in nextelement[1].items():
				try:
					# try look for an attribute
					if c.getAttribute(name) != value:
						attrok=False
						break
				except:
					# attribute does not exist
					attrok=False
					break
			# attributes are ok
			if attrok==True:
				# index of element is fine
				if nextelement[2] == -1 or i == nextelement[2]:
					results.append(c)
				i += 1
	return results

class xmldoc:
	def __init__(self, filename=""):
		self.filename=""
		self.dom=None
		if filename != "":
			self.load(filename)
	
	def __nonzero__(self):
		return self.dom == None
	
	def load(self, filename):
		"""load(filename) - load source XML data from filename"""
		self.dom = minidom.parse(filename)
		self.filename = filename

	def load_string(self, string):
		"""loadString(string) - read source XML data from string"""
		self.dom = minidom.parseString(string)
		
	def save(self, filename=''):
		"""save(filename='') - save XML data into filename"""
		if not filename and not self.filename:
			raise "You must select filename"
		if not filename and self.filename:
			filename = self.filename
		f=open(filename, 'w')
		f.write(self.toxml())
		f.close()

	def toxml(self):
		"""toxml() - return XML data as string"""
		return self.dom.toxml().encode('utf-8')
			
	def root(self):
		"""root() - return document element"""
		return xmlelement(self.dom.documentElement)

	def __getitem__(self, path):
		"""self[path] - return xmlelement object appropriate to path"""
		elements=self.elements(path)
		if len(elements)==0:
			return None
		elif len(elements)==1:
			return elements[0]
		else:
			return elements
		
	def elements(self, path):
		"""element(path) - return xmlelement object appropriate to path. path must be unicode string if it contains any non ascii characters"""
		epath = parsepath(path)
		if epath[0][0] != self.dom.documentElement.nodeName:
			raise "Wrong path was set - root element does not match"
		nodes=[self.dom.documentElement]
		del epath[0] # delete root element and start with next elements
		for e in epath:
			childnodes=[]
			for n in nodes:
				childnodes += element_childs(n, e)
			nodes = childnodes
		return list(xmlelement(n) for n in nodes)
		
class xmlelement:
	def __init__(self, node):
		if type(node) == str:
			self.element = minidom.Element(node)
			self.name = node
		elif node.nodeType != Node.ELEMENT_NODE:
			raise "node must be type of Node.ELEMENT_NODE"
		else:
			self.element = node
			self.name = self.element.nodeName
			self._updatedata()	# set self.data and self.value
		
	def __nonzero__(self):
		return True
		
	def _strip_value(self):
		self.value = u''
		prev = u''
		for c in self.data.strip():
			if c.isspace() and not prev.isspace():
				self.value += ' '
			elif not c.isspace():
				self.value += c
			prev = c
		return self.value

	def _updatedata(self):
		# create and set self.data with all data inside this element
		# also create and set self.value as brute-stripped self.data
		self.data = u''
		for node in self.element.childNodes:
			if node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
				self.data += node.data
		self._strip_value()
		return self.data

	def __str__(self):
		return self.value
	
	def set_value(self, value):
		"""set_value(value) - sets new value (data) of element. value must be unicode string if it contains any non ascii characters"""
		# at first: delete all text child nodes
		for node in self.element.childNodes:
			if node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
				self.element.removeChild(node)
		textNode = minidom.Text()
		textNode._set_data(value)
		self.element.insertBefore(textNode, self.element.firstChild)
		self._updatedata()
		return self.value
	
	def attr(self, name, value=None):
		"""attr(name, value=None) - get or set value of attribute. name or value must be unicode strings if it contain any non ascii characters"""
		if value == None:
			return self.element.getAttribute(name)
		else:
			return self.element.setAttribute(name, value)
	
	def removeattr(self, name):
		"""removeattr(name) - remove attribute. name must be unicode string if it contains any non ascii characters"""
		self.element.removeAttribute(name)
		
	def __getitem__(self, path):
		"""self[path] - return xmlelement object appropriate to path"""
		elements=self.elements(path)
		if len(elements)==0:
			return None
		elif len(elements)==1:
			return elements[0]
		else:
			return elements

	def elements(self, path):
		"""element(path) - return list of xmlelements appropriate to path. path must be unicode string if it contains any non ascii characters"""
		epath = parsepath(path)
		nodes=[self.element]
		for e in epath:
			childnodes=[]
			for n in nodes:
				childnodes += element_childs(n, e)
			nodes = childnodes
		return list(xmlelement(n) for n in nodes)

	def toxml(self):
		"""toxml() - return XML form as string"""
		return self.element.toxml().encode('utf-8')

	def newchild(self, elementname):
		"""newchild(name) - create and return new child element. name must be unicode string if it contains any non ascii characters"""
		child = minidom.Element(elementname)
		self.element.appendChild(child)
		return xmlelement(child)

	def appendchild(self, element):
		"""appendchild(element) - append new child xmlelement"""
		self.element.appendChild(element.element)

	def insertbefore(self, newelement, refelement):
		"""insertbefore(newelement, refelement) - insert child element before refelement\nand remove it from its old position if any"""
		newelement.remove()
		self.element.insertBefore(newelement.element, refelement.element)
	
	def movebefore(self, refelement):
		"""movebefore(refelement) - move this element before refelement"""
		self.remove()
		self.element.insertBefore(self.element, refelement.element)
		
	def moveafter(self, refelement):
		"""movebefore(refelement) - move this element before refelement"""
		self.remove()
		self.element.insertBefore(self.element, refelement.element)
	
	def remove(self):
		"""remove() - remove this element from its parent"""
		if self.element and self.element.parentNode:
			self.element.parentNode.removeChild(self.element)

