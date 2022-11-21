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

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import unquote
from os.path import join
import requests

kBaseUrl = "http://tmbw.net"

kOutputDir = "data"


def Log(s):
   print (s)

def Scrub(s):
   ''' Do whatever cleanup we need to do to turn a string (possibly with spaces
      in it) to a space-less name more usable as a file name 
   '''
   kIllegalChars = "!@#$%^&*()/\\{}[];:,?~`|"
   table = {}
   for ch in kIllegalChars:
    table[ch] = ''

   s = s.strip()
   s = s.translate(table)
   return s.replace(" ", '-')


def MakeFilename(album, track):
   ''' given an album/filename combo, return a filename that combines them'''
   return Scrub("{0}_{1}.lyric".format(album, track))

def GetSoup(urlFragment):
   ''' - join this fragment with the base url
       - retrieve the contents at the full url
       -  Parse with BeautifulSoup & return the resulting tree of objects.
   '''

   data = requests.get(urljoin(kBaseUrl, urlFragment))
   soup = BeautifulSoup(data.text)
   return soup


def ProcessDiscography(url):
   ''' load the page at 'url' and process everything in the table of albums 
      (with the id 'discog'), and in turn process each album.
   '''
   soup = GetSoup(url)
   table = soup.find(id="discog")
   rows = table("tr")
   # (skip the table header...)
   for row in rows[1:]:
      cells = row("td")
      link = cells[1].a
      name = link.text
      urlFragment = link['href']
      Log("Handling album '{0}'".format(name))
      ProcessAlbum(name, urlFragment)


def ProcessAlbum(albumName, url):
   ''' look for the table on an album page that contains the track
      listing for the album. This is a little more complicated because there
      may be multiple track listings associated with a single album (alternate release versions,
      etc.) so we can't rely on looking for a specific id. The tables that contain track
      data all have the class name 'ebena', so we'll look for tags with that class 
      and ignore any that end up not containing links to pages of lyrics.

      Hackier than I like, but we're scraping HTML and shouldn't be surprised.
   '''
   soup = GetSoup(url)
   tables = soup.find_all(attrs={"class": "ebena"})

   for table in tables:
      rows = table("tr")
      for row in rows:
         cells = row("td")
         # the "Purchase" table has fewer columns than the track info table. 
         if 5 == len(cells):
            try:
               trackName = cells[1].a.text
               lyricUrl = cells[3].a['href']
               ProcessTrack(albumName, trackName, lyricUrl)
            except Exception as e:
               print (str(e))



def ProcessTrack(albumName, trackName, url):
    '''
        url points at a lyrics page. The lyrics are inside a <div> that has the 
        class 'lyrics-table'.
    '''
    soup = GetSoup(url)
    lyrics = soup.find(attrs={"class": "lyrics-table"})
    stanzas = lyrics.find_all("p")
    fileName = join(kOutputDir, MakeFilename(albumName, trackName))
    Log("  {}".format(fileName))
    with open(fileName, "wt") as f:
        #   lyric = u"\n".join([stanza.text for stanza in stanzas]).encode("UTF-8")
        lyric = u"\n".join([stanza.text for stanza in stanzas])
        f.write(lyric)

if __name__ == "__main__":
   ProcessDiscography("wiki/Discography/Studio_Albums")
   ProcessDiscography("wiki/Discography/John_Linnell")
   ProcessDiscography("wiki/Discography/John_Flansburgh")
