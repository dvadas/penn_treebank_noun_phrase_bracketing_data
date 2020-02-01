
class Stream:
	def __init__(self, data):
		self.data = data
		self.upto = 0
		self.len = len(data)
	def get(self): #read a single character
		if self.upto >= self.len:
			return "EOF"
		char = self.data[self.upto]
		self.upto += 1
		return char
	def readWord(self,chars = ""): #read up to whitespace, or a character in chars
		start = self.upto
		broke = False
		for i in range(start,self.len):
			if self.data[i].isspace():
				broke = True
				break
			if self.data[i] in chars:
				#include the char as well
				break
		end = i
		if not broke:
			end += 1
		word = self.data[start:end]
		self.upto = end
		return word
	def eof(self):
		return self.upto >= self.len
	def back(self):
		self.upto -= 1
		
