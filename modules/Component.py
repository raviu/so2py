#!/usr/bin/env python
#Filename: component.py

import sys
import os
import subprocess
import urllib, urllib2
import logging
from lxml import etree as ET

__author__  ='Shafreen, RaviU'
__version__ ='1.0.0'

class Component:

	context = {}

	def __init__(self, context):
		self.context = context

		# This has to come from the main program
		logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(levelname)s: %(message)s', filename ='../log/component.log', filemode = 'w',)

		# Setting the output console too
		ch = logging.StreamHandler(sys.stdout)
		ch.setLevel(logging.INFO)
		ch.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
		logging.getLogger().addHandler(ch)

	def get_pom_gav_coordinates(self, context):
		file_path = context['path']
		repo_loc = context['repo_location']

		os.chdir(file_path)
		component_pom = ET.parse('pom.xml')
		component_artifact_id = component_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		component_version = component_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		component_parent_version = component_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
		component_group_id = component_pom.xpath('/p:project/p:parent/p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		return {"g": component_group_id[0].text, "a": component_artifact_id[0].text, "v": component_version[0].text}

	def is_released_component_nexus(self, context):
		gav = self.get_pom_gav_coordinates(context)
		gav['r'] = self.context['settings'].nexus_repo_name
		
		params = urllib.urlencode(gav)
		url = self.context['settings'].nexus_url + '/nexus/service/local/artifact/maven/resolve?%s' % params
		response = urllib2.urlopen(url).read()		
		try:
			response_et = ET.fromstring(response)
			if gav['v'] == response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text:
				print response_et.xpath('/artifact-resolution/data/version', namespaces={})[0].text + " is released"
				return True
			else:
				return False
		except:
			return False


	def is_released_component(self, context):
		''' finds if a particular component is released or not. Implemenation is based on chunk-system
			If the component is released it returns the component version.'''

		file_path = context['path']
		repo_loc = context['repo_location']

		try:
			os.chdir(file_path)
			component_pom = ET.parse('pom.xml')
			component_artifact_id = component_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
			component_version = component_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
			#component_parent_artifact_id = component_pom.xpath('/p:project/p:parent/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
			component_parent_version = component_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
			compoenet_parent_rpath = feature_pom.xpath('/p:project/p:parent/p:relativePath', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

			# This is becuase we really can't say parent artifactId is similar to its folder name
			if compoenet_parent_rpath:
				os.chdir(compoenet_parent_rpath[0].text.rpartition('/')[0])
				compoenet_parent_rpath = os.path.abspath('.')
			else:
				raise Exception()

			if not component_version:
				component_version = component_parent_version

			# Go to product releases ???
			os.chdir(repo_location + "/product-releases")

			# Get all the chunks available
			# proc = subprocess.Popen("ls", stdout=subprocess.PIPE, shell=True)
			# (out, err) = proc.communicate()
			# chunks = out.split()

			# Find in all chunks
			released_chunk = None
			for chunk in os.listdir("."):
				if os.path.isdir(chunk):
					os.chdir("./{0}/components".format(chunk))
					chunk_component_pom = ET.parse('pom.xml')
					module = chunk_component_pom.xpath("//p:modules/p:module[re:match(text(), '{0}/{1}')]".format(component_artifact_id[0].text, component_version[0].text), namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
					if module:
						released_chunk = chunk
						os.chdir("../..")
						break
					os.chdir("../..")

			# See if the parent pom is released
			if released_chunk is None:
				for chunk in os.listdir("."):
					os.chdir("./{0}/components".format(chunk))
					chunk_component_pom = ET.parse('pom.xml')

					component_parent_chunk_path = feature_parent_rpath.replace(repo_loc, '../../..')

					module = chunk_component_pom.xpath("//p:modules/p:module[re:match(text(), '{0}$')]".format(component_parent_chunk_path), namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

					if module:
						released_chunk = chunk
						os.chdir(module[0].text)

						chunk_parent_component_pom = ET.parse('pom.xml')
						module = chunk_parent_component_pom.xpath("//p:modules/p:module[re:match(text(), '{0}/{1}')]".format(component_artifact_id[0].text, component_version[0].text), namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

					os.chdir("../..")
					break

					os.chdir("../..")

			if module:
				#logging.info("{0}_{1} -> ".format(component_artifact_id[0].text, component_version[0].text) + released_chunk)
				return component_version[0].text
			else:
				#logging.info("{0}_{1} -> ".format(component_artifact_id[0].text, component_version[0].text) + "Not a released COMPONENT")
				return None
		except KeyboardInterrupt:
			pass
			#logging.error('You cancled the is_released_component is operation. You might have to manually reset the state of platform. !!!')
		except:
			pass
			#logging.error("Unexpected error:", sys.exc_info()[0])

	def create_new_component(self, context, component_version):
		''' If the component is released this operation will create a new component '''

		file_path = context['path']
		if component_version is not None:
			os.chdir(file_path)

			# Build the component to see if it builds before doing anything
			if os.system('mvn clean install -Dmaven.test.skip=true') == 0:
				logging.info('component builds successfully with new changes.')
			else:
				logging.error('could not build component with the new changes.')
				raise Exception()

			# Get the new version of the coponent using the old version
			component_versions = component_version.rpartition('.')
			micro_version = component_versions[2]
			int_micro_version = int(micro_version)
			int_micro_version += 1

			new_component_version = component_versions[0] + component_versions[1] + str(int_micro_version)

			# Go back to the root of the project
			os.chdir('..')
			if os.system('svn up') == 0:
				logging.info('successfully upated the local svn copy.')
			else:
				logging.error('failed to update the local svn copy.')
				raise Exception()

			# Make sure we have done changes to the latest existing version
			if not os.path.exists(new_component_version):
				svn_mkdir_command = 'svn copy {0} {1}'.format(component_version, new_component_version)

				if os.system(svn_mkdir_command) == 0:
					os.chdir(new_component_version)
					component_pom = ET.parse('pom.xml')

					# WHAT IF THERE IS NO VERSION ELEMENT ???
					component_version = component_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
					component_version[0].text = new_component_version
					component_pom.write('pom.xml')

					logging.info('successfully created a new component version -> {0}'.format(new_component_version))
					return os.path.abspath('.')

				else:
					logging.error('failed to create a new component version -> {0}'.format(new_component_version))
			else:
				logging.error('seems you have not done the changes to latest existing version !!!')

				return None

	def upate_chunk_component(self, context, new_file_path):
		os.chdir(context['repo_location'] + "/product-releases")

		# Get the latest chunk release
		chunks = os.listdir(".")
		chunks.sort(key=os.path.getmtime, reverse=True)

		os.chdir("./{0}/components".format(chunks[0]))
		relative_path = new_file_path.replace(context['repo_location'], "../../..")

		chunk_component_pom = ET.parse('pom.xml')
		modules = chunk_component_pom.xpath("//p:modules/node()", namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

		# 1) ---- best approach but pretty printing. But it only adds two spaces for indent :(
		#parent_module = modules[0].getparent()
		#new_module_element = ET.fromstring('<module>{0}</module>'.format(relative_path))
		#parent_module.append(new_module_element)

		# This for pretty printing. But it only adds two spaces for indent :(
		#parser = ET.XMLParser(remove_blank_text=True)
		#tree = ET.parse('pom_new.xml', parser)
		#tree.write('pom_new.xml', pretty_print=True)

		# 2) ---- OK. and does not ruing the pretty printing of the pom.xml
		esc_relative_path = relative_path.replace("/", "\\/")
		cmd = 'sed -i \'s/<\\/modules>/\\t<module>{0}<\/module>\\n\	<\\/modules>/g\' pom.xml'.format(esc_relative_path)

		if modules:
			if os.system(cmd) == 0:
				logging.info('successfully updated the chunk component pom file with the new componenet.')
			else:
				logging.error('failed to updated the chunk component pom file with the new componenet.')
				raise Exception()
		else:
			loggin.error('failed to find modules element in component pom file.')

	def run(self):
		# See if it is released
		component_version = self.is_released_component(self.context);

		# Create new component if it is released
		path_to_new_component = self.create_new_component(self.context, component_version)

		# Update latest chunk with the new component
		self.upate_chunk_component(self.context, path_to_new_component)

		return self.context

	def get_version(self):
		return __version__
