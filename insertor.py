#!/usr/local/bin/python

import os
import sys

"""
00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
"""

from stream import Stream

labels = ["NML","JJP"]


class Node:
	def __init__(self):
		self.children = []
		self.leaf = False
		self.word = ""
	def read(self, stream, start = 0):
		self.name = stream.readWord('(')
		
		#this is for sentences that begin with 2 open brackets with no space between, eg: ((SINV
		if len(self.name) > 0:
			if self.name[-1] == "(":
				self.name = self.name[:-1]
				stream.back()

		self.start = start		
		length = 0
		
		while True:
			#read nextchar
			nextchar = stream.get()
			
			if nextchar.isspace():
				continue
			elif nextchar == ')':
				break
			elif nextchar == '(':
				child = Node()
				length += child.read(stream,start+length)
				self.children.append(child)
			else: #must be leaf
				if not self.leaf:
					self.leaf = True
					length += 1
				
				self.word += nextchar

		self.end = start+length-1

		return length

	def show(self, level = 0):
		if self.leaf:
			print "  "*level+"("+self.name,self.word+")"
		else:
			print "  "*level+"("+self.name
			for child in self.children:
				child.show(level+1)
			print "  "*level+")"
	def expand(self, num):
		children = self.children[num].children
		children.reverse() #so they go in the right way later
		del self.children[num]
		for child in children:
			self.children.insert(num,child)
	def factor(self, num1, num2, label):
		newnode = Node()
		newnode.name = label
		newnode.start = self.children[num1].start
		newnode.end = self.children[num2].end
		
		for j in range(num1,num2+1):
			newnode.children.append(self.children[num1])
			del self.children[num1] 
			#the others will move down into num1's position

		self.children.insert(num1,newnode)
	def inorder(self, labels=[]):
		if self.leaf:
			return [self]

		res = []
		for child in self.children:
			if labels == [] or child.leaf or child.name in labels:
				res += child.inorder(labels)
		
		return res
	def diff(self, compnode, labels = []):
		nolabels = len(labels) == 0
		if self.name != compnode.name:
			return True
		if len(self.children) != len(compnode.children):
			return True
		for child, compchild in zip(self.children,compnode.children):
			if child.name in labels or nolabels:
				if child.diff(compchild, labels):
					return True
		return False
		
	def length(self,labels):
		if self.leaf:
			return 1
			
		length =0
		for child in self.children:
			if child.name in labels or labels == []:
				length += child.length(labels)
			else:
				length += 1
		return length
	
	#tell the node where it starts, and it'll tell you where it ends, plus where its children do
	def spans(self, start=0, labels = []):
		resspans = {}
		total = 0
		for i,child in enumerate(self.children):
			if child.leaf:
				total += 1
			else:
				#print "recursing from",self.name
				length, recspans = child.spans(start+total,labels)
				
				if child.name in labels or labels == []:
					for key in recspans:
						value = recspans[key]
						resspans[key] = value
					#resspans += recspans

					resspans[(start+total,start+total+length-1)] = child#.name
					#resspans.append((start+total,start+total+length-1))
				total += length
				
						
		return total, resspans		
		
	
	def ptb_show(self, level = 0):
		if self.leaf:
			#result = "("+self.name+' '+self.word+'|'+str(self.start)+'|'+str(self.end)+")"+' '
			result = "("+self.name+' '+self.word+")"+' '
		else:
			#result = "("+self.name+'|'+str(self.start)+'|'+str(self.end)+' '
			result = "("+self.name+' '

	
			newlining = False
			for i,child in enumerate(self.children):
				if child.leaf:
					if child.name == "," or child.name == 'CC':
						newlining = True
				else:
					if self.name != "":
						newlining = True
				
				if newlining:
					result += '\n'+"  "*(level+1)
			
				result += child.ptb_show(level+1)
				
				if child.leaf:
					if child.name != ',':
						newlining = False
			result += ")"
		return result
	
	def insert(self,start,end,label,depth=0):
		#print "\t"*depth, self.name
		for child in self.children:
			if not child.leaf:
				if child.insert(start,end,label, depth+1):
					return True
	
		if self.start <= start and self.end >= end:
			print "found at",self.start,self.end
			#now just figure out which children
			for i,child in enumerate(self.children):
				#print "child s:",child.start,"e:",child.end
				if child.start == start:
					cstart = i
				if child.end == end:
					cend = i
			self.factor(cstart,cend,label)
			return True

		return False
				
	
	
if len(sys.argv) != 4:
	print "usage:"
	print "\t./insertor.py <Treebank source directory> <output directory> <structure file>"
	sys.exit()
	
indir = sys.argv[1]
outdir = sys.argv[2]
structure = sys.argv[3]

def finalslash(word):
	if word[-1] != "/":
		return word + "/"
	else:
		return word
indir = finalslash(indir)
outdir = finalslash(outdir)

files = os.listdir(indir)
files.sort()
try:
	junk = os.listdir(outdir)
except OSError:
	os.mkdir(outdir)


sfile = open(structure)
slines = sfile.readlines()
sfile.close()
supto = 0


for fname in files:
	print "OPENING NEW FILE:",fname
	
	f = open(indir+fname)
	data = f.read()
	f.close()
	
	newf = open(outdir+fname,'w')	
	newf.write('\n')
	
	stream = Stream(data)
	while True:

		#read '('	
		while True:
			char = stream.get()
			if char == '(' or stream.eof():
				break

		if stream.eof():
			break

		root = Node()
		root.read(stream)
		

		#insert the structure into standard PTB
		sline = slines[supto].strip()
		factors = []
		while sline != "---":
			print "inserting:",sline
			label,start,end = sline.split()
			start = int(start)
			end = int(end)
			diff = end-start
			factors.append((diff,start,end,label))
			
			supto+=1
			sline = slines[supto].strip()
		supto +=1
		
		#sort by diff, so that the inner (smallest) nodes are inserted first
		factors.sort()
		
		#root.show()
		for diff,start,end,label in factors:
			root.insert(start,end,label)
			
		
		#output
		newf.write(root.ptb_show()+'\n')


	newf.close()
	print "FILE CLOSED:", fname		
	
	
print "all done"
