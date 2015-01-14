
# Copyright (c) 2013 Brett g Porter
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''
   jsonSettings.py -- wrapper around a text file containing json key/value pairs
   that we can access as either a dict
   settings['key']
   or an object
   settings.key


'''

import json

class SettingsFileError(Exception):
   def __init__(self, msg):
      self.msg = msg

   def __str__(self):
      return self.msg


class JsonSettings(object):
   '''
      A class to persist our app's settings in a json file. We can access any 
      of the of the values in the settings either as
      mySettings.attribute 
      or 
      mySettings['attribute']

      We separate
   '''
   def __init__(self, settingsFile, defaultDict=None):
      if defaultDict is None:
         defaultDict = {"newFile": "PLEASE EDIT THIS FILE"}
      try:
         self._settingsFile = settingsFile
         with open(settingsFile, "rt") as f:
            self._settings = json.loads(f.read())
            self._isDirty = False
      except IOError:
         # can't open the settings file. Warn the user & create a blank file.
         # They'll need to edit that file and re-start this program.
         self._settings = defaultDict.copy()
         self._isDirty = True
         self.Write()
         raise SettingsFileError(kSettingsFileErrorMsg.format(settingsFile))

   def Write(self):
      try:
         if self._isDirty: 
            with open(self._settingsFile, "wt") as f:
               f.write(json.dumps(self._settings, indent=3, 
                  separators=(',', ': ') ))
            self._isDirty = False
      except IOError, e:
         print "Error writing settings file: {0}".format(str(e))
         raise SettingsFileError()

   def __getitem__(self, key):
      ''' get an item from settings as if this were a dict. 
         If there's nothing at that key, returns None instead of 
         throwing an exception.
      '''
      return self._settings.get(key, None)

   def __getattr__(self, key):
      ''' ...or, get a thing as an attribute using dot notation 
         If there's nothing at that key, returns None instead of 
         throwing an exception.
         '''
      return self._settings.get(key, None)

   def __setattr__(self, key, val):
      if not key.startswith('_'):
         self._settings[key] = val
         self._isDirty = True
      else:
         # we need to prevent recursion!
         super(JsonSettings, self).__setattr__(key, val)   

   def __setitem__(self, key, val):
      self._settings[key] = val
      self._isDirty = True