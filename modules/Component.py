#!/usr/bin/env python

# Component.py - Does all the things related to components
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import os
import subprocess
import urllib, urllib2
import logging
from lxml import etree as ET
import xml.dom.minidom as mini

__author__  ='Shafreen, RaviU'
__version__ ='1.0.0'

class Component:

	context = {}

	def __init__(self, context):
		self.context = context

	def get_pom_gav_coordinates(self, context, file_path):
		repo_loc = context['repo_location']

		os.chdir(file_path)
		component_pom = ET.parse('pom.xml')
		component_artifact_id = component_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		component_version = component_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		component_parent_version = component_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		component_group_id = component_pom.xpath('/p:project/p:parent/p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		if not component_version:
			component_version = component_parent_version
		
		return {"g": component_group_id[0].text, "a": component_artifact_id[0].text, "v": component_version[0].text}

	#def is_released_component_nexus(self, context):
	#	gav = self.get_pom_gav_coordinates(context)
	#	gav['r'] = self.context['settings'].nexus_repo_name
		
	#	params = urllib.urlencode(gav)
	#	url = self.context['settings'].nexus_url + '/nexus/service/local/artifact/maven/resolve?%s' % params
	#	print url
	#			
	#	try:
	#		response = urllib2.urlopen(url).read()
	#		response_et = ET.fromstring(response)
	#		if gav['v'] == response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text:
	#			print response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text + " is released"						
	#			return gav['v']
	#			#return True
	#		else:
	#			return None

	#	except urllib2.HTTPError as e:
	#		if e.code == 404:
				# This mean it is not a released version. because if u try to resolve a gav wich is not released this url throws 404
	#			return None
	#	except:
	#		raise Exception()

	def create_new_component(self, context):
		''' If the component is released this operation will create a new component '''

		file_path = context['path']
		os.chdir(file_path)

		component_version = self.get_pom_gav_coordinates(self.context, file_path)['v']
		new_component_version = self.get_imidiate_new_version(self.context, file_path)

		print component_version, new_component_version

		# Go back to the root of the project
		os.chdir('..')		
		if os.system('svn up --force .') == 0:
			logging.info('successfully upated the local svn copy @ {0}.'.format(file_path))
		else:
			logging.error('failed to update the local svn copy @ {0}'.format(file_path))
			raise Exception()	

		# Make sure we have done changes to the latest existing version
		if not os.path.exists(new_component_version):
			svn_mkdir_command = 'svn copy {0} {1}'.format(component_version, new_component_version)

			if os.system(svn_mkdir_command) == 0:
								
				os.chdir(new_component_version)

				# This makes sure changing the project version won't impact any other reference to project version.
				old_version = self.get_pom_gav_coordinates(self.context, os.path.abspath('.'))['v']
				if old_version: 
					if os.system('sed -i \'s/${{project.version}}/{0}/g\' pom.xml'.format(old_version)) == 0:
						logging.info('successfully replaced ${{project.version}} with it is actual value @ {0}'.format(os.path.abspath('.')))
					else:
						logging.error('failed to replace ${{project.version}} with it is actual value @ {0}'.format(os.path.abspath('.')))
						raise Exception()
				else:
					logging.error('couldn not find the original version of component @ {0}'.fromat(os.path.abspath('.')))
					raise Exception()
				
				component_pom = ET.parse('pom.xml')

				# Need this in case we have to revert the changes				
				changed_paths = self.context['changed_paths'] 
				changed_paths.add(os.path.abspath('.'))				
				
				# now the pom file is ready be changed.
				component_version = component_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})							
				if component_version:
					component_version[0].text = new_component_version
					component_pom.write('pom.xml')
				else:
					component_artifactId = component_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
					cmd = 'sed -i \'s/<artifactId>{0}<\\/artifactId>/<artifactId>{0}<\\/artifactId>\\n    <version>{1}<\\/version>/\' pom.xml'.format(component_artifactId[0].text, new_component_version)
					
					if os.system(cmd) == 0:
						logging.info('successfully updated the chunk component pom file with the new componenet.')
					else:
						logging.error('failed to updated the chunk component pom file with the new componenet.')
						raise Exception()  

				# Need to add these info to context as subsequent components need them
				context['component_artifact_version'] = new_component_version 				

				# Build and install the new component to see if it builds before doing anything
				if os.system('mvn clean install -Dmaven.test.skip=true') == 0:
					logging.info('component builds successfully with new changes.')
				else:
					logging.error('could not build component with the new changes.')
					raise Exception()

				self.new_prettify()

				logging.info('successfully created a new component version {0}'.format(new_component_version))
									
				return os.path.abspath('.')

			else:				
				logging.error('failed to create a new component version {0}'.format(new_component_version))
				raise Exception()
		else:
			if component_version == new_component_version:
				
				os.chdir(new_component_version)

				# See if it is under version control
				if os.system('svn info') == 0:
					logging.info('updating the existing component version {0} @ {1}'.format(new_component_version, os.path.abspath('.')))					
				else:
					logging.error('seems component version is not version controle @ {0}'.format(os.path.abspath('.')))
					raise Exception()

				# Build and install the new component to see if it builds before doing anything
				if os.system('mvn clean install -Dmaven.test.skip=true') == 0:
					logging.info('component builds successfully with new changes.')
					return os.path.abspath('.')  
				else:
					logging.error('could not build component with the new changes.')
					raise Exception()
			else:
				logging.error('seems you have not done the changes to the latest existing version @ {0}'.format(os.path.abspath('.')))
				raise Exception()

	def upate_chunk_component(self, context, new_file_path):
		os.chdir(context['repo_location'] + "/product-releases")

		# Get the latest chunk release
		chunks = os.listdir(".")
		chunks.sort(key=os.path.getmtime, reverse=True)

		os.chdir("./{0}/components".format(chunks[0]))
		relative_path = new_file_path.replace(context['repo_location'], "../../..")

		chunk_component_pom = ET.parse('pom.xml')		
		
		# Make sure we don't add duplicates 
		element = chunk_component_pom.xpath("//p:module[re:match(text(), '{0}')]".format(relative_path),\
						                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})	

		if not element:
			modules = chunk_component_pom.xpath("//p:modules/node()", namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
			parent_module = modules[0].getparent()
			new_module_element = ET.fromstring('<module>{0}</module>'.format(relative_path))
			parent_module.append(new_module_element)
			chunk_component_pom.write('pom.xml')

			self.new_prettify()	

			changed_paths = context['changed_paths'] 
			changed_paths.add(os.path.abspath('.'))	

	def get_imidiate_new_version(self, context, file_path):
		gav = self.get_pom_gav_coordinates(context, file_path)
		gav['r'] = self.context['settings'].nexus_repo_name
		gav['v'] = 'LATEST'
	
		params = urllib.urlencode(gav)
		url = self.context['settings'].nexus_url + '/nexus/service/local/artifact/maven/resolve?%s' % params
		print url

		try:
			response = urllib2.urlopen(url).read()
			response_et = ET.fromstring(response)
			version = response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text
			
			feature_versions = version.rpartition('.')
			micro_version = feature_versions[2]
			int_micro_version = int(micro_version)
			int_micro_version += 1 

			imidiate_new_version = feature_versions[0] + feature_versions[1] + str(int_micro_version)

			return imidiate_new_version
		except:
			logging.error('could not create the latest imidiate version for {0}'.format(url))
			raise Exception()
	    
	def run(self):
		''' This the root method of the component. This method initiate the execution of the component. Therefore by looking at this method
			one cad determin the execution flow and what it does.'''

		changed_paths = set([])
		self.context['changed_paths'] = changed_paths 

		# Need to add these info to context as subsequent components need them. here we set the *DEFAULT* values.
		gav_default_codinates = self.get_pom_gav_coordinates(self.context, self.context['path'])
		self.context['component_artifact_id'] = gav_default_codinates['a']
		self.context['component_artifact_version'] = gav_default_codinates['v']

		# 2) This approach allows us to shape the svn according to nexus.
		path_to_new_component = self.create_new_component(self.context)

		# Update latest chunk with the new component
		if path_to_new_component:
			self.upate_chunk_component(self.context, path_to_new_component)

		return self.context

	def get_version(self):
		return __version__

	def new_prettify(self):
		reparsed = mini.parseString(mini.parse('pom.xml').toxml())
		pretty_string =  '\n'.join([line for line in reparsed.toprettyxml(indent=' '*4).split('\n') if line.strip()])

		try:
			f = open('pom.xml', 'w') # open for 'w'riting
			f.write(pretty_string) # write text to file
		finally:
			f.close()
