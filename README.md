## tmbotg - a twitter bot

A little project that randomly tweets out fragments of lyrics from They Might Be Giants 
songs. 

### GetLyrics.py

Utility using requests and BeautifulSoup to scrape the lyrics database that's at http://tmbw.net, storing the lyrics as one file per track.

### tmbotg.py

Twitter bot app (written using Twython) that assumes it will be called once a minute by a cron job. Approximately once an hour, it should generate a new tweet.

**TODO:** add the ability to process mentions that contain a '?' by replying to that user with a chunk of lyrics.
