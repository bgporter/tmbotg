## tmbotg - a twitter bot

A little project that randomly tweets out fragments of lyrics from They Might Be Giants 
songs. 


<blockquote class="twitter-tweet" lang="en"><p>Minimum Wage!  HYAH!</p>&mdash; tmbotg (@tmbotg) <a href="https://twitter.com/tmbotg/statuses/421454171020492800">January 10, 2014</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

### Colophon & Thanks

- Obviously, thanks to They Might Be Giants, both for writing this stuff in the first place, and (as importantly for this project) not being all cease-and-desisty to this kind of fan project. This project is not officially affiliated with the band.
- All the editors/contributors to 'TMBW: The They Might Be Giants Knowledge Base' (http://www.tmbw.net) for maintaining full lyrics in a format that was relatively easy for me to extract.

**Python modules**

- [Requests](http://docs.python-requests.org/en/latest/) is the only reasonable way to deal with HTTP in Python.
- Similarly, [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) needs to be your first choice when you need to parse HTML, even the most horrible HTML
- [Twython](https://github.com/ryanmcgrath/twython) for handling the Twitter API. Clean and sensible.

### GetLyrics.py

Utility using Requests and BeautifulSoup to scrape the lyrics database that's at http://tmbw.net, storing the lyrics as one file per track.

### tmbotg.py

Twitter bot app (written using Twython) that assumes it will be called once a minute by a cron job. Approximately once an hour (depending on configuration data), it should generate a new tweet.

**TODO:** 

- [ ] add logging
- [ ] Add a mode that generates (daily?) stats (#posts, #followers, #favs, #retweets)
- [ ] wrap the update_status call in a try block so we can catch (and log) TwythonError exceptions (e.g. on a duplicate status update)
- [ ] add the ability to process mentions that contain a '?' by replying to that user with a chunk of lyrics.
- [x] Track the time of the most recent tweet & refuse to twwet again for some period of time after that (rate-limit to not feel spammy. Max once an hour? )

