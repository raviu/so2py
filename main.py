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

__version__ = '0.0.1'

import os
import sys
import inspect
import re
import time

import settings

class Main:

    code_base_path = '.'
            
    def __init__(self, settings):
        print "Running Managment Tools v%s" % __version__ 
        sys.path.append(os.path.realpath(__file__)+'/modules/')
        self.code_base_path = settings.repo_location
        self.run(settings.run_order)
        
    
    def run(self, run_order):
        response = True       
        for component in run_order:                         
            print 'Loading %s' % component + ' component'
            _module = __import__('modules.%s' % component, globals(), locals(), [component], -1)
            component_class = getattr(_module, component)
            component_object = component_class(response)

            success = component_object.run()
            if not success:
                print "Failed to complete %s" % component + " run" 
               


main = Main(settings)
