#!/usr/bin/env python

# main.py - Initialise environment and run management modules
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

__version__     = '0.0.1'
__author__      = 'RaviU, Shafreen'

import os
import sys
import re
import time
import subprocess 
import logging
import color

import settings

class Main:

    path = '';
    repo_location = '.'
    context = {}
    settings
            
    def __init__(self, settings, path):

	# Configuring the logging. This logging is used accross all the components
	logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(levelname)s: %(message)s', filename ='{0}/log/so2py.log'.format(os.path.abspath('.')), filemode = 'w',)

	# Setting the output console too
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(logging.DEBUG)
	ch.setFormatter(color.ColoredFormatter('%(asctime)s: %(levelname)s: %(message)s'))
	logging.getLogger().addHandler(ch)

        print "Running Managment Tools v%s" % __version__ 

        if settings.repo_location == '' or settings.repo_location == None or settings.repo_location == '#UPDATE_REPO_LOCATION':
            self.repoloc_wizard()
	    settings = reload(settings)
	
        sys.path.append(os.path.realpath(__file__)+'/modules/')
        self.context = {'path': path, 'success': True, 'settings': settings}
	self.path = path
	self.settings = settings
        self.repo_locationrepo_location = settings.repo_location
	self.context['repo_location'] = settings.repo_location

	try:
      		self.run(settings.run_order)
		
		if 'changed_paths' in self.context: 
			changed_paths = self.context['changed_paths'] 
			for path in changed_paths:
				logging.info('change done @ {0}'.format(path))

		tree_dic = self.context['tree_dic'] 
		if tree_dic: 
			print color.colorstr("| Associativity tree view of updated artifacts", 'DARK_BLUE')
			self.print_tree(self.context['component_artifact_id'], tree_dic, ' ')

		if self.get_user_opinion() == 'n':
			self.revert_changes()
			logging.info('successfully reverted all the changes because user entered - n')			

		logging.info('management tool executed without any errors')
	except:
		self.revert_changes()
		raise			
    
    def run(self, run_order):
        for component in run_order:                         
            _module = __import__('modules.%s' % component, globals(), locals(), [component], -1)
            component_class = getattr(_module, component)
            component_object = component_class(self.context)

            print 'Running %s' % component + ' component v%s' % component_object.get_version()

            self.context = component_object.run()
            if not self.context['success']:
                print "Failed to complete %s" % component + " run" 

	    self.verify_map()

    def revert_changes(self):
	# Need to revert all changes done
	if 'changed_paths' in self.context:
		changed_paths = self.context['changed_paths'] 
		svn_revert_command = 'svn revert --recursive {0}'
		for path in changed_paths:
			if os.system(svn_revert_command.format(path)) == 0:
				logging.info('successfully reverted changes @ {0}'.format(path))
			else:
				logging.error('failed to revert changes @ {0}'.format(path))
	

    def verify_map(self):
	if 'path' not in self.context:
		self.context['path'] = self.path
	if 'repo_location' not in self.context:
		self.context['repo_location'] = self.repo_location

	if 'settings' not in self.context:
		self.context['settings'] = self.settings
               
    def get_direcotry(self):
	continue_loop = True
	prompt = "Looks like you're running us for the first time. Please enter file path to Carbon Platform code: "
	while(continue_loop):
		repo_loc = raw_input(prompt)
		if(os.path.isdir(repo_loc)):
			continue_loop = False
		else:
			prompt = "The file path you entered is not a valid directory. Please enter file path to Carbon Platform code: "
	return repo_loc

    def get_user_opinion(self):
        continue_loop = True
        prompt = "Do you want to keep the changes ? [y/n] : "
        while(continue_loop):
                opi = raw_input(prompt)
                if opi.lower() == 'y' or opi.lower() == 'n':
                        continue_loop = False
			return opi
                else:
                        prompt = "The option you entered is not a valid option. Please enter a valid option : "
        return repo_loc

    def repoloc_wizard(self):
        repo_loc = self.get_direcotry()	
        repo_loc = repo_loc.replace('\\', '\\\\').replace(' ', '\\ ').replace('/', '\/')
        sed_string = 'sed -r -i \"s/repo_location = \'\' \#UPDATE_REPO_LOCATION/repo_location = %r' % repo_loc + '/g\" %s' % os.path.abspath('.') + '/settings.py'
        subprocess.call(sed_string, shell=True) 

    def print_tree(self, artifact_id, dic, padding):   

	    print color.colorstr(padding[:-1] + '+-' + artifact_id, 'BLUE') 

	    padding = padding + ' '
	    files = []

	    try:
		files = dic[artifact_id]
	    except:
		files = []	

	    count = 0
	    for file in files:
		count += 1
		print color.colorstr(padding + '|', 'BLUE')
		path = file
		if files:
		    if count == len(files):
		        self.print_tree(path, dic, padding + ' ')
		    else:
		        self.print_tree(path, dic, padding + '|')
		else:
		    print color.colorstr(padding + '+-' + file, 'BLUE')

path = sys.argv[1] 
main = Main(settings, path)
