#! /usr/bin/env/python
# Copyright (c) 2013 Brett g Porter
# 


from glob import glob
from pprint import pprint
from random import choice
from random import random
from twython import Twython

import os.path
import json



# if we're started without a config file, we create a default/empty 
# file that the user can fill in and then restart the app.
kDefaultConfigDict = {
   "appKey"             : "!!! Your app's 'Consumer Key'",
   "appSecret"          : "!!! Your app's 'Consumer Secret'",
   "accessToken"        : "!!! your access token",
   "accessTokenSecret"  : "!!! your access token secret",
   "lyricFilePath"      : "*.lyric",
   "tweetProbability"   : 24.0 / 1440,
}

kSettingsFileErrorMsg = '''\
There was no settings file found at {0}, so I just created an empty/default
file for you. Please edit it, adding the correct/desired values for each
setting as is appropriate.
'''


class SettingsFileError(Exception):
   def __init__(self, msg):
      self.msg = msg

   def __str__(self):
      return self.msg

class Settings(object):
   '''
      class to persist our app's settings in a json file.
   '''
   def __init__(self, settingsFile):
      try:
         self._settingsFile = settingsFile
         with open(settingsFile, "rt") as f:
            self._settings = json.loads(f.read())
      except IOError:
         # can't open the settings file. Warn the user & create a blank file.
         self._settings = kDefaultConfigDict
         self.Write()
         raise SettingsFileError(kSettingsFileErrorMsg.format(settingsFile))

   def Write(self):
      try:
         with open(self._settingsFile, "wt") as f:
            f.write(json.dumps(self._settings, indent=3, 
               separators=(',', ': ') ))
      except IOError, e:
         print "Error writing settings file: {0}".format(str(e))
         raise SettingsFileError()

   def __getitem__(self, key):
      ''' get an item from settings as if this were a dict. '''
      return self._settings[key]

   def __getattr__(self, key):
      ''' ...or, get a thing as an attribute using dot notation '''
      return self._settings[key]

   def __setattr__(self, key, val):
      if not key.startswith('_'):
         self._settings[key] = val
      else:
         # we need to prevent recursion!
         super(Settings, self).__setattr__(key, val)   

         
 
def ParseFilename(filePath):
   ''' we name files like "Album-Title_Track-Title.lyric". This function breaks 
      a string in that format apart and returns a tuple ("Album-Title", "Track-Title")
   '''
   path, fileName = os.path.split(filePath)
   base, ext = os.path.splitext(fileName)
   return tuple(base.split("_"))


class NoLyricError(Exception):
   pass




class TmBot(object):
   '''
      The class that actually runs the bot.
   '''

   def __init__(self, argDict=None):
      if not argDict:
         argDict = { 'debug' : False, "force": False}
      self.__dict__.update(argDict)

      # we build a list of dicts containing status (and whatever other args 
      # we may need to pass to the update_status function as we exit, most 
      # probably 'in_reply-to_status_id' when we're replying to someone.)
      self.tweets = []

      self.settings = Settings("tmbotg.json")
      s = self.settings
      self.twitter = Twython(s.appKey, s.appSecret, s.accessToken, s.accessTokenSecret)

   def SendTweets(self):
      ''' send each of the status updates that are collected in self.tweets 
      '''
      for msg in self.tweets:
         if self.debug:
            print msg['status']
         else:
            self.twitter.update_status(**msg)

   def CreateUpdate(self):
      if (random() < self.settings.tweetProbability) or self.force:
         try:
            album, track, msg = self.GetLyric(120)
            self.tweets.append({'status' : msg})
         except NoLyricError:
            # we should log this.
            pass

   def HandleMentions(self):
      pass

   def Run(self):
      self.CreateUpdate()
      self.HandleMentions()
      self.SendTweets()


   def GetLyric(self, maxLen, count=10):
      ''' open a random lyric file, then grab a random stanza of lyrics from it, 
         then (if needed) trim it down into lines <= maxLen
         returns a tuple (album, track, stanza) (we may want to log the album/tracks
            that are being used...)

         If we don't immediately find a random chunk of text that meets the maxLen
         criteria, we call ourself recursively, decrementing the count parameter until 
         it hits zero, at which point we give up and raise an exception. Obviously, we 
         could look for a longer time, or come up with a search algorithm to find text 
         meets the current length criteria, or, or, or..., but I actually like the idea 
         that it's possible to occasionally just throw up our hands and give up. We'll 
         try again in a bit.
      '''
      if 0 == count:
         raise NoLyricError()

      files = glob(self.settings.lyricFilePath)
      fName = choice(files)
      album, track = ParseFilename(fName)
      stanza = ""
      with open(fName, "rt") as f:
         data = f.read().decode("utf-8")
         stanzas = data.split("\n\n")
         stanza = choice(stanzas).strip()
         while len(stanza) > maxLen:
            # Keep trimming off lines from the bottom until either:
            # 1. There's only a single line of text left and we can't trim any more
            # 2. We have text that's <= the current maxLen.
            trimmed = stanza.rsplit("\n", 1)[0]
            if stanza == trimmed:
               stanza = ""
               break
            stanza = trimmed
      if stanza:
         return (album, track, stanza)
      else:
         return self.GetLyric(maxLen, count-1)


if __name__ == "__main__":
   import argparse
   parser = argparse.ArgumentParser()
   parser.add_argument("--debug", action='store_true', 
      help="print to stdout instead of tweeting")
   parser.add_argument("--force", action='store_true', 
      help="force operation now instead of waiting for randomness")
   args = parser.parse_args()
   argDict = vars(args)

   try:
      bot = TmBot(argDict)
      bot.Run()
   except SettingsFileError as e:
      print str(e)

