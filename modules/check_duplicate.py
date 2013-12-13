#!/bin/python
# Finds Duplicate Jars in WSO2 Carbon Servers
import os
import argparse 

class JarDuplicateChecker:

	jar_dirs = [] 
	carbon_home = ''
	base_dir = ''

	def __init__(self, jarDirs = ['plugins', 'patches/patch0000', 'patches/patch0001'], path = os.getenv('CARBON_HOME', os.getcwd()), base = '/repository/components'):
		self.jar_dirs = jarDirs
		self.carbon_home = path 
		self.base_dir = base

	def findDuplicates(self):
		for _dir in self.jar_dirs:
			print '-- %s' % self.carbon_home + '/' + self.base_dir + '/' + _dir + '/' + ' --'
			file_map = {}
			original_names = {}
		        try:	
				for _file in os.listdir(self.carbon_home + '/' + self.base_dir + '/' + _dir + '/'):
					file_name = _file.split('_')[0]
					try:
						file_map[file_name] += 1
						original_names[file_name] += ', ' + _file
					except KeyError:
						file_map[file_name] = 1
						original_names[file_name] = _file
				
				found_duplicate = False	
				for k,v in file_map.iteritems():
					if file_map[k] > 1:
						print original_names[k]
						found_duplicate = True
				if not found_duplicate:
					print 'No duplicates found'			
				print '-- --\n'
			except OSError:
				print 'No such directory' 
				print '-- --\n'	

jdc = JarDuplicateChecker()
jdc.findDuplicates()
