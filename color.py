#!/usr/bin/env python

# color.py - changes the console output colors
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
__author__      = 'Shafreen, RaviU'

import copy
import logging

CODE={
    'ENDC':0,  # RESET COLOR
    'BOLD':1,
    'UNDERLINE':4,
    'BLINK':5,
    'INVERT':7,
    'CONCEALD':8,
    'STRIKE':9,
    'GREY30':90,
    'GREY40':2,
    'GREY65':37,
    'GREY70':97,
    'GREY20_BG':40,
    'GREY33_BG':100,
    'GREY80_BG':47,
    'GREY93_BG':107,
    'DARK_RED':31,
    'RED':91,
    'RED_BG':41,
    'LIGHT_RED_BG':101,
    'DARK_YELLOW':33,
    'YELLOW':93,
    'YELLOW_BG':43,
    'LIGHT_YELLOW_BG':103,
    'DARK_BLUE':34,
    'BLUE':94,
    'BLUE_BG':44,
    'LIGHT_BLUE_BG':104,
    'DARK_MAGENTA':35,
    'PURPLE':95,
    'MAGENTA_BG':45,
    'LIGHT_PURPLE_BG':105,
    'DARK_CYAN':36,
    'AUQA':96,
    'CYAN_BG':46,
    'LIGHT_AUQA_BG':106,
    'DARK_GREEN':32,
    'GREEN':92,
    'GREEN_BG':42,
    'LIGHT_GREEN_BG':102,
    'BLACK':30,
}

def termcode(num):
    return '\033[%sm'%num

def colorstr(astr,color):
    return termcode(CODE[color])+astr+termcode(CODE['ENDC'])

class ColoredFormatter(logging.Formatter):
    LEVELCOLOR = {
        'DEBUG': 'BLUE',
        'INFO': 'GREEN',
        'WARNING': 'PURPLE',
        'ERROR': 'RED',
        'CRITICAL': 'RED_BG',
        }

    def __init__(self, msg):
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        record = copy.copy(record)
        levelname = record.levelname
        if levelname in self.LEVELCOLOR:
            record.levelname = colorstr(levelname,self.LEVELCOLOR[levelname])
            record.name = colorstr(record.name,'BOLD')
            record.msg = colorstr(record.msg,self.LEVELCOLOR[levelname])
        return logging.Formatter.format(self, record)
