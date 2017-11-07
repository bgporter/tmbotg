#! /usr/bin/env/python

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



from datetime import datetime
from datetime import date
from glob import glob
from pprint import pprint
from random import choice
from random import random
from time import time
from twython import Twython
from twython import TwythonStreamer
from twython.exceptions import TwythonError


import os.path

from jsonSettings import JsonSettings as Settings
import jsonSettings


# if we're started without a config file, we create a default/empty
# file that the user can fill in and then restart the app.
kDefaultConfigDict = {
   "appKey"             : "!!! Your app's 'Consumer Key'",
   "appSecret"          : "!!! Your app's 'Consumer Secret'",
   "accessToken"        : "!!! your access token",
   "accessTokenSecret"  : "!!! your access token secret",
   "lyricFilePath"      : "*.lyric",
   "tweetProbability"   : 24.0 / 1440,
   "minimumSpacing"     : 60*60,
   "minimumDaySpacing"  : 30,
   "logFilePath"        : "%Y-%m.txt"
}

kSettingsFileErrorMsg = '''\
There was no settings file found at {0}, so I just created an empty/default
file for you. Please edit it, adding the correct/desired values for each
setting as is appropriate.
'''




class LyricsFileError(Exception):
   def __init__(self, msg):
      self.msg = msg

   def __str__(self):
      return self.msg


class BotStreamer(TwythonStreamer):

   def SetOutputPath(self, path):
      self.path = path

   def on_success(self, data):
      # for now, all we're interested in handling are quoted tweets.
      if 'event' in data:
         if data['event'] == 'quoted_tweet':
            # get the id of the tweet that quotes us:
            tweetId = data['target_object']['id_str']
            # create a file that the other (periodic) cron-job bot process will handle.
            # As very rudimentary IPC, we use the id of the tweet that quotes us as
            # a filename. If we want to do more using the streaming API, we might want to write
            # more interesting data into the file to be parsed out later.
            # Example -- we may want to extend the replies to questions so that we also
            # reply to questions in quote tweets as well.
            with open(os.path.join(self.path, "{0}.fav".format(tweetId)), "wt") as f:
               f.write("{0}".format(tweetId))


   def on_error(self, status_code, data):
      print "ERROR: {0}".format(status_code)
      self.disconnect()



def ParseFilename(filePath):
   ''' we name files like "Album-Title_Track-Title.lyric". This function breaks
      a string in that format apart and returns a tuple ("Album-Title", "Track-Title")
   '''
   path, fileName = os.path.split(filePath)
   base, ext = os.path.splitext(fileName)
   return tuple(base.split("_"))


def TrimTweetToFit(listOfStrings, maxLength):
   '''
      Given a list of strings (one string per line), trim that list (usually from
      the back, but occasionally from the front to keep things interesting) until
      it's less than or equal to the maxLength parameter.
   '''
   length = 0
   for line in listOfStrings:
      length += len(line) + 1
   length = length - 1

   if length <= maxLength:
      return "\n".join(listOfStrings)
   else:
      if 1 == len(listOfStrings):
         # we can't trim any more because there's only one line left. Give up.
         return ""
      else:
         # decoding this next line: create a list that weights the probability of
         # whether we trim lines from the end or the front (more frequently from the end)
         popIndex = choice([-1] * 8 + [0] * 2)
         listOfStrings.pop(popIndex)
         return TrimTweetToFit(listOfStrings, maxLength)


class NoLyricError(Exception):
   pass




class TmBot(object):
   '''
      The class that actually runs the bot.
   '''

   def __init__(self, argDict=None):
      if not argDict:
         argDict = { 'debug' : False, "force": False, 'stream': False, 'botPath' : "."}
      # update this object's internal dict with the dict of args that was passed
      # in so we can access those values as attributes.
      self.__dict__.update(argDict)

      # we build a list of dicts containing status (and whatever other args
      # we may need to pass to the update_status function as we exit, most
      # probably 'in_reply-to_status_id' when we're replying to someone.)
      self.tweets = []

      self.history = Settings(self.GetPath("tmbotg_history.json"))
      self.settings = Settings(self.GetPath("tmbotg.json"), kDefaultConfigDict)
      s = self.settings
      if self.stream:
         self.twitter = BotStreamer(s.appKey, s.appSecret, s.accessToken, s.accessTokenSecret)
         self.twitter.SetOutputPath(self.botPath)
      else:
         self.twitter = Twython(s.appKey, s.appSecret, s.accessToken, s.accessTokenSecret)

   def GetPath(self, path):
      '''
         Put all the relative path calculations in one place. If we're given a path
         that has a leading slash, we treat it as absolute and do nothing. Otherwise,
         we treat it as a relative path based on the botPath setting in our config file.
      '''
      if not path.startswith(os.sep):
         path = os.path.join(self.botPath, path)
      return path

   def Log(self, eventType, dataList):
      '''
         Create an entry in the log file. Each entry will look like:
         timestamp\tevent\tdata1\tdata2 <etc>\n
         where:
         timestamp = integer seconds since the UNIX epoch
         event = string identifying the event
         data1..n = individual data fields, as appropriate for each event type.
         To avoid maintenance issues w/r/t enormous log files, the log filename
         that's stored in the settings file is passed through datetime.strftime()
         so we can expand any format codes found there against the current date/time
         and create e.g. a monthly log file.
      '''
      now = int(time())
      today = datetime.fromtimestamp(now)
      fileName = self.settings.logFilePath
      if not fileName:
         fileName = "%Y-%m.txt"
         self.settings.logFilePath = fileName
      path = self.GetPath(fileName)
      path = today.strftime(path)
      with open(path, "a+t") as f:
         f.write("{0}\t{1}\t".format(now, eventType))
         f.write("\t".join(dataList))
         f.write("\n")

   def SendTweets(self):
      ''' send each of the status updates that are collected in self.tweets
      '''
      for msg in self.tweets:
         if self.debug:
            print msg['status'].encode("UTF-8")
         else:
            try:
               self.twitter.update_status(**msg)
            except TwythonError, e:
               Log("EXCEPTION", [str(e), msg['status'].encode("UTF-8")])


   def CheckDaySpacing(self, album, title):
      ''' There are a few tunes that seem to come up *way* too often. We'll maintain
         a new history file that just tracks the last time that any given (album, track) tuple
         is used (and maybe this should just be title?). If we're okay to use this song, return
         true.
      '''
      key = "{0}_{1}".format(album, title)
      retval = True
      lastUsed = self.history[key]
      if lastUsed:
         minimumSpace = self.settings.minimumDaySpacing
         if not minimumSpace:
            minimumSpace = 30
            self.settings.minimumDaySpacing = minimumSpace
         today = date.today()
         last = date.fromordinal(lastUsed)
         # how many days has it been since we last tweeted this album/track?
         daysAgo = (today - last).days
         retval =  daysAgo > minimumSpace
         if not retval:
            self.Log("TooSoon", [album, title, "used {0} days ago".format(daysAgo)])
      return retval


   def LogHistory(self, album, title):
      today = date.today()
      key = "{0}_{1}".format(album, title)
      self.history[key] = today.toordinal()

   def CreateUpdate(self):
      '''
         Called everytime the bot is Run().
         If a random number is less than the probability that we should generate
         a tweet (or if we're told to force one), we look into the lyrics database
         and (we hope) append a status update to the list of tweets.

         1/11/14: Added a configurable 'minimumSpacing' variable to prevent us from
         posting an update too frequently. Starting at an hour ()

      '''
      doUpdate = False
      last = self.settings.lastUpdate or 0
      now = int(time())
      lastTweetAge = now - last

      maxSpace = self.settings.maximumSpacing
      if not maxSpace:
         # default to creating a tweet at *least* every 4 hours.
         maxSpace = 4 * 60 * 60
         self.settings.maximumSpacing = maxSpace

      if lastTweetAge > maxSpace:
         # been too long since the last tweet. Make a new one for our fans!
         doUpdate = True

      elif random() < self.settings.tweetProbability:
         # Make sure that we're not tweeting too frequently. Default is to enforce
         # a 1-hour gap between tweets (configurable using the 'minimumSpacing' key
         # in the config file, providing a number of minutes we must remain silent.)
         requiredSpace = self.settings.minimumSpacing
         if not requiredSpace:
            # no entry in the file -- let's create one. Default = 1 hour.
            requiredSpace = 60*60
            self.settings.minimumSpacing = requiredSpace

         if lastTweetAge > requiredSpace:
            # Our last tweet was a while ago, let's make another one.
            doUpdate = True

      if doUpdate or self.force:
         try:
            # Occasionally force some short(er) updates so they're not all
            # paragraph-length.. (these values arbitrarily chosen)
            maxLen = choice([210, 120, 120, 120, 120, 100, 100, 100, 80, 80, 40])
            album, track, msg = self.GetLyric(maxLen)
            self.tweets.append({'status' : msg})
            self.settings.lastUpdate = int(time())
            # we'll log album name, track name, number of lines, number of characters
            self.Log("Tweet", [album, track, str(1 + msg.count("\n")), str(len(msg))])
         except NoLyricError:
            self.Log("NoLyric", [])
            pass

   def HandleMentions(self):
      '''
         Get all the tweets that mention us since the last time we ran and process each
         one.
         Any time we're mentioned in someone's tweet, we favorite it. If they ask
         us a question, we reply to them.
      '''
      mentions = self.twitter.get_mentions_timeline(since_id=self.settings.lastMentionId)
      if mentions:
         # Remember the most recent tweet id, which will be the one at index zero.
         self.settings.lastMentionId = mentions[0]['id_str']
         for mention in mentions:
            who = mention['user']['screen_name']
            text = mention['text']
            theId = mention['id_str']

            # we favorite every mention that we see
            if self.debug:
               print "Faving tweet {0} by {1}:\n {2}".format(theId, who, text.encode("utf-8"))
            else:
               try:
                  self.twitter.create_favorite(id=theId)
               except TwythonError, e:
                  Log("EXCEPTION", [str(e), msg['status'].encode("UTF-8")])


            eventType = 'Mention'
            # if they asked us a question, reply to them.
            if "?" in text:
               # create a reply to them.
               maxReplyLen = 120 - len(who)
               album, track, msg = self.GetLyric(maxReplyLen)
               # get just the first line
               msg = msg.split('\n')[0]
               # In order to post a reply, you need to be sure to include their username
               # in the body of the tweet.
               replyMsg = "@{0} {1}".format(who, msg)
               self.tweets.append({'status': replyMsg, "in_reply_to_status_id" : theId})
               eventType = "Reply"

            self.Log(eventType, [who])



   def HandleQuotes(self):
      ''' The streaming version of the bot may have detected some quoted tweets
         that we want to respond to. Look for files with the .fav extension, and
         if we find any, handle them.
      '''
      faves = glob(self.GetPath("*.fav"))
      for fileName in faves:
         with open(fileName, "rt") as f:
            tweetId = f.readline().strip()
            if self.debug:
               print "Faving quoted tweet {0}".format(tweetId)
            else:
               try:
                  self.twitter.create_favorite(id=tweetId)
               except TwythonError as e:
                  self.Log("EXCEPTION", str(e))
         os.remove(fileName)


   def Run(self):
      if self.stream:
         if self.debug:
            print "About to stream from user account."
         try:
            # The call to user() will sit forever waiting for events on
            # our user account to stream down. Those events will be handled
            # for us by the BotStreamer object that we created ab
            self.twitter.user()
         except KeyboardInterrupt:
            # disconnect cleanly from the server.
            self.twitter.disconnect()
      else:
         self.CreateUpdate()
         self.HandleMentions()
         self.HandleQuotes()
         self.SendTweets()

         # if anything we dpsid changed the settings, make sure those changes get written out.
         self.settings.lastExecuted = str(datetime.now())
         self.settings.Write()
         self.history.Write()


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

      files = glob(self.GetPath(self.settings.lyricFilePath))
      if not files:
         # there aren't any lyrics files to use -- tell them to  GetLyrics
         raise LyricsFileError("Please run GetLyrics.py to fetch lyric data first.")

      fName = choice(files)
      album, track = ParseFilename(fName)
      # Check to see if it's been long enough since we tweeted from this song:
      if not self.CheckDaySpacing(album, track):
         return self.GetLyric(maxLen, count-1)
      stanza = ""
      with open(fName, "rt") as f:
         data = f.read().decode("utf-8")
         stanzas = data.split("\n\n")
         stanza = choice(stanzas).strip().split('\n')
         stanza = TrimTweetToFit(stanza, maxLen)

      if stanza:
         self.LogHistory(album, track)
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

   parser.add_argument("--stream", action="store_true",
      help="run in streaming mode")
   args = parser.parse_args()
   # convert the object returned from parse_args() to a plain old dict
   argDict = vars(args)


   # Find the path where this source file is being loaded from -- we use
   # this when resolving relative paths (e.g., to the data/ directory)
   botPath = os.path.split(__file__)[0]
   argDict['botPath'] = botPath

   try:
      bot = TmBot(argDict)
      bot.Run()
   except (jsonSettings.SettingsFileError, LyricsFileError) as e:
      # !!! TODO: Write this into a log file (also)
      bot.Log("ERROR", [str(e)])
      print str(e)
