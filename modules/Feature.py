#!/usr/bin/env python

# Feature.py - Does all the things related to features
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

import os
import logging
import sys
import urllib, urllib2
from lxml import etree as ET
import xml.dom.minidom as mini

__author__  ='Shafreen, RaviU'
__version__ ='1.0.0'

class Feature:

	context = {}

	def __init__(self, context):
		self.context = context

	def find_dependent_features(self, component_artifact_id, dependent_projects):

		current_path = os.path.abspath('.')
	    
	        for root, subFolders, files in os.walk(self.context['repo_location'] + "/features"):
			if '.svn' in subFolders:
				subFolders.remove('.svn')

			if 'target' in subFolders:
				subFolders.remove('target')

			if 'src' in subFolders:
				subFolders.remove('src')

			if 'resources' in subFolders:
				subFolders.remove('resources')

			if 'nested-categories' in subFolders:
				subFolders.remove('nested-categories')

			if 'repository' in subFolders:
				subFolders.remove('repository')

			for file_name in files:
				if file_name == 'pom.xml':
					os.chdir(root)
					feature_pom = ET.parse('pom.xml')
					element = feature_pom.xpath("/p:project/p:dependencies/p:dependency/p:artifactId[re:match(text(), '{0}$')]".format(component_artifact_id),\
						                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
					if element:
						dependent_projects.add(root)

		os.chdir(current_path)

	def refactor_depenedent_result(self, dependent_projects):
		''' Take care of older versions in the result set.'''
	    
		project_dic = {}
		project_path_set = set([])
	    
		for project in dependent_projects:
			project_tuple = project.rpartition('/')

			if project_tuple[0] in project_dic:
				existing_version = project_dic[project_tuple[0]]
				new_version = project_tuple[2]

				existing_version_int = existing_version.replace('.', '')
				new_version_int = new_version.replace('.', '')
				if int(new_version_int) > int(existing_version_int):
					project_dic[project_tuple[0]] = new_version
			else:
				project_dic[project_tuple[0]] = project_tuple[2]

		for key in project_dic.keys():
			project_path_set.add(key + "/" + project_dic[key])
		
		return project_path_set

	def get_pom_gav_coordinates(self, context, file_path):
		repo_loc = context['repo_location']

		os.chdir(file_path)
		feature_pom = ET.parse('pom.xml')
		feature_artifact_id = feature_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		feature_version = feature_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		feature_parent_version = feature_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		feature_group_id = feature_pom.xpath('/p:project/p:parent/p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		feature_packaging = feature_pom.xpath('/p:project/p:packaging', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		if not feature_version:
			feature_version = feature_parent_version

		# Need to add these info to context as subsequent components need them
		#context['component_artifact_id'] = feature_artifact_id[0].text
		#context['component_artifact_version'] = feature_version[0].text

		return {"g": feature_group_id[0].text, "a": feature_artifact_id[0].text, "v": feature_version[0].text, "p": feature_packaging[0].text}

	def is_released_feature_nexus(self, context, file_path):
		gav = self.get_pom_gav_coordinates(context, file_path)
		gav['r'] = self.context['settings'].nexus_repo_name
		
		params = urllib.urlencode(gav)
		url = self.context['settings'].nexus_url + '/nexus/service/local/artifact/maven/resolve?%s' % params
		print url

		try:
			response = urllib2.urlopen(url).read()
			response_et = ET.fromstring(response)
			if gav['v'] == response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text:
				print response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text + " is released"							
				return True
			else:
				return False

		except urllib2.HTTPError as e:
			if e.code == 404:
				# This mean it is not a released version. because if u try to resolve a gav wich is not released this url throws 404
				return False
		except:
			raise Exception()

	def create_new_feature(self, file_path):
		''' If the feature is released this operation will create a new feature and returen the path to the new feature. '''
	    
		os.chdir(file_path)

		feature_version = self.get_pom_gav_coordinates(self.context, file_path)['v']

		# Build the component to see if it builds before doing anything
		if os.system('mvn clean install -Dmaven.test.skip=true') == 0:
			logging.info('feature builds successfully with new changes.')
		else:
			logging.error('could not build feature with the new changes.')
			raise Exception()

		# Get the new version of the coponent using the old version
		#feature_versions = feature_version.rpartition('.')
		#micro_version = feature_versions[2]
		#int_micro_version = int(micro_version)
		#int_micro_version += 1 

		#new_feature_version = feature_versions[0] + feature_versions[1] + str(int_micro_version)

		new_feature_version = self.get_imidiate_new_version(self.context, file_path)
		print new_feature_version

		# Go back to the root of the project
		os.chdir('..')

		if os.system('svn up --force .') == 0:
			logging.info('successfully upated the local svn copy @ {0}.'.format(file_path))
		else:
			logging.error('failed to update the local svn copy @ {0}'.format(file_path))
			raise Exception()			

		if not os.path.exists(new_feature_version):
			svn_mkdir_command = 'svn copy {0} {1}'.format(feature_version, new_feature_version)

			if os.system(svn_mkdir_command) == 0:
				os.chdir(new_feature_version)
				feature_pom = ET.parse('pom.xml')

				# Need this in case we have to revert the changes
				changed_paths = self.context['changed_paths'] 
				changed_paths.add(os.path.abspath('.'))

				feature_version = feature_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

				if feature_version: 
					feature_version[0].text = new_feature_version                
					feature_pom.write('pom.xml')
				else:
					feature_artifactId = feature_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
					cmd = 'sed -i \'s/<artifactId>{0}<\\/artifactId>/<artifactId>{0}<\\/artifactId>\\n    <version>{1}<\\/version>/\' pom.xml'.format(feature_artifactId[0].text, new_feature_version)
					if os.system(cmd) != 0:
						logging.error('failed to updated the chunk feature pom file with the new componenet.')
						raise Exception()             

				logging.info('successfully created a new component version -> {0}@{1}'.format(new_feature_version, os.path.abspath('.')))
	
				# Return the path to the new feature
				return os.path.abspath('.')
				    
			else:
				logging.error('failed to create a new component version -> {0}'.format(new_feature_version))
				raise Exception()
		else:
			# See if it is under version control
			os.chdir(new_feature_version)

			if os.system('svn info') == 0:
				logging.info('updating the existing compnent version {0} @ {1}'.format(new_feature_version, os.path.abspath('.')))
				return os.path.abspath('.')
			else:
				logging.error('seems you have not done the changes to latest existing version @{0}'.format(os.path.abspath('.')))
				raise Exception()	


	def update_feature_pom(self, feature_path, component_artifact_id, component_artifact_version):
	    	    
		os.chdir(feature_path)

		if os.system('svn up') == 0:
			logging.info('successfully upated the local svn copy @ {0}.'.format(feature_path))
		else:
			logging.error('failed to update the local svn copy @ {0}'.format(feature_path))
			raise Exception()

		feature_pom = ET.parse('pom.xml')

		feature_artifact_id = feature_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		feature_version = feature_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		feature_parent_version = feature_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		if not feature_version:
			feature_version = feature_parent_version
	    
		feature_component_dependency = feature_pom.xpath("/p:project/p:dependencies/p:dependency/p:artifactId[re:match(text(), '{0}$')]".format(component_artifact_id),\
				                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

		# Update dependency
		dependency_element = feature_component_dependency[0].getparent()
		dependency_version_element = dependency_element.find('p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		if dependency_version_element is not None:
			dependency_version_element.text = component_artifact_version
		else:
			new_version_element = ET.fromstring('<version>{0}</version>'.format(component_artifact_version))
			dependency_element.append(new_version_element)

		# Update p2 plugin stuff
		dependency_artifcatId_element = dependency_element.find('p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		dependency_groupId_element = dependency_element.find('p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		new_dependency_gav = '{0}:{1}:{2}'.format(dependency_groupId_element.text, dependency_artifcatId_element.text, component_artifact_version)

		# includedFeatures
		p2_feature_dependency = feature_pom.xpath("//p:includedFeatures/p:includedFeatureDef[re:match(text(), '{0}$')]".format(dependency_artifcatId_element.text),\
				                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
		if p2_feature_dependency:
			#p2_feature_dependency[0].text = p2_feature_dependency[0].text + ":" + component_artifact_version
			p2_feature_dependency[0].text = p2_feature_dependency 
		else:
			p2_feature_dependency = feature_pom.xpath("//p:includedFeatures/p:includedFeatureDef[re:match(text(), '{0}:\d.\d.\d\s*$ || {0}:.*$')]".format(dependency_artifcatId_element.text),\
				                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
			if p2_feature_dependency:            
				#p2_feature_dependency[0].text = p2_feature_dependency[0].text.rpartition(':')[0] + ':' + component_artifact_version
				p2_feature_dependency[0].text = new_dependency_gav
			else: 	    
				# bundles 
				p2_feature_dependency = feature_pom.xpath("//p:bundleDef[re:match(text(), '{0}$')]".format(dependency_artifcatId_element.text),\
						                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
				if p2_feature_dependency:
					#p2_feature_dependency[0].text = p2_feature_dependency[0].text + ":" + component_artifact_version
					p2_feature_dependency[0].text = new_dependency_gav
				else:
					p2_feature_dependency = feature_pom.xpath("//p:bundleDef[re:match(text(), '{0}:\d.\d.\d\s*$ || {0}:.*$')]".format(dependency_artifcatId_element.text),\
							    namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
					if p2_feature_dependency:
						#p2_feature_dependency[0].text = p2_feature_dependency[0].text.rpartition(':')[0] + ':' + component_artifact_version
						p2_feature_dependency[0].text =  new_dependency_gav
					#else:
					#	raise Exception()
		            
		feature_pom.write('pom.xml')

		self.new_prettify()

		# Need this in case we have to revert the changes
		changed_paths = self.context['changed_paths'] 
		changed_paths.add(os.path.abspath('.'))

		logging.info('successfully update the feature with the new component version {0}@{1}'.format(component_artifact_version, os.path.abspath('.')))

		return [feature_artifact_id[0].text, feature_version[0].text]

	def upate_chunk_component(self, context, new_file_path):
		os.chdir(context['repo_location'] + "/product-releases")

		# Get the latest chunk release
		chunks = os.listdir(".")
		chunks.sort(key=os.path.getmtime, reverse=True)

		os.chdir("./{0}/features".format(chunks[0]))
		relative_path = new_file_path.replace(context['repo_location'], "../../..")

		chunk_feature_pom = ET.parse('pom.xml')

		# Make sure we don't add duplicates 
		element = chunk_feature_pom.xpath("//p:module[re:match(text(), '{0}')]".format(relative_path),\
						                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

		if not element:
			modules = chunk_feature_pom.xpath("//p:modules/node()", namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
			parent_module = modules[0].getparent()
			new_module_element = ET.fromstring('<module>{0}</module>'.format(relative_path))
			parent_module.append(new_module_element)
			chunk_feature_pom.write('pom.xml')

			self.new_prettify()	

			changed_paths = context['changed_paths'] 
			changed_paths.add(os.path.abspath('.'))	

        def master_method(self, component_artifact_id, component_artifact_version):
		
		# Find dependent featurs of the component
		dependent_projects = set([])
		self.find_dependent_features(component_artifact_id, dependent_projects)

		# Refacator dependent feature to remove older versions. *Only* should contain the latest released versions
		feacatored_dependet_set = self.refactor_depenedent_result(dependent_projects)

	        # For each dependet feature add/update the component id and version if there is any
	        for feature_path in feacatored_dependet_set:

			print feature_path
			# See if the feature is released
			#feature_version = self.is_released_feature_nexus(self.context, feature_path)

			# Create new feature if it is released and return the path to new feature		
			#if feature_version:
			#	feature_path = self.create_new_feature(feature_path)

			feature_path = self.create_new_feature(feature_path)

			# Update the feature
			feature_id_version = self.update_feature_pom(feature_path, component_artifact_id, component_artifact_version)

			self.upate_chunk_component(self.context, feature_path)

			# Recursively call the master method
			self.master_method(feature_id_version[0], feature_id_version[1])

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
		''' This the root method of the component. This method initiate the execution of the feature. Therefore by looking at this method
			one can determine the execution flow and what it does.'''

		component_artifact_id = self.context['component_artifact_id']
		component_artifact_version = self.context['component_artifact_version']

		self.master_method(component_artifact_id, component_artifact_version)

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

