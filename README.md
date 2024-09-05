# REDDIT DATA
---

This is just a quick and dirty test to see if I can extract trends for different tickers on r/pennystocks.


## DATA

The data is as follows:
- `comments.jsonl` is every comment made in r/pennystocks between Jan1 2024 to May1 2024
- `posts.jsonl` is every post made in r/pennystocks between Jan1 2024 to May1 2024
  - [These were downloaded via this nice tool](https://arctic-shift.photon-reddit.com/download-tool): 
- `NASDAQ|NYSE|OTCtickers.csv` were downloaded from the  NYSE (I think) website circa Aug 2024.


## Problems:

1. OTC/NYSE/NASDAQ exchanges have tickers that are english words. This casues huge problems when extracting frequencies in comments/posts.
2. Volume. While the subreddit is somewhat large, there  simply arent enough comments about tickers to provide enough insight into trending ones.

## Solutions
1. You can easily hand-pull out single tickers by constructing a `Ticker` object. This works well enough
2. There's likely some work you can do by looking at posts with a ticker name and the numer of comments it has (i.e a post about XYZ has 100 comments, it's probably fair to assume that it's a busy ticker).

