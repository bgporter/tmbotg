#! /usr/bin/env/python

# Copyright (c) 2015 Brett g Porter
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

''' Simple utility to grab lyrics from the 2015 Dial a Song releases, which 
   aren't collected on TMBW under a single collection at this point. Command
   line, accepts a string with the track name & pulls down the lyric file.

   Because I'll be using this by hand as the songs are released, I'm not expending
   much effort with try/except blocks, etc. If I mistype something at the command line,
   I'll figure things out then
'''

import sys
import urllib
from GetLyrics import ProcessTrack

kAlbum = "Dial a Song"
kUrlTemplate = "http://tmbw.net/wiki/Lyrics:{0}"


def Scrub(s):
   ''' spaces in the lyric URL pattern are replaced with underscores '''
   s = urllib.quote(s)
   return s.replace(' ', '_')

if __name__ == "__main__":
   title = sys.argv[1]
   url = kUrlTemplate.format(title)
   ProcessTrack(kAlbum, title, url)
