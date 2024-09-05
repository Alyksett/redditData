from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Dict, List, Optional
import pandas as pd
import datetime
import csv
import matplotlib.pyplot as plt

import re
def remove_emojis(data):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return re.sub(emoj, '', data)

type Content = Comment | Post

class Exchange(Enum):
    NYSE=1
    NASDAQ=2
    OTC=3
    
@dataclass
class Comment:
    content: str
    time: str
    value = 1
        
    def get_time(self):
        return datetime.datetime.fromtimestamp(self.time)
    def __repr__(self):
        return f'Content: {self.content:<100} Time: {self.time:<20}'
    def __hash__(self):
        return hash(self.content) ^ hash(self.time)
    
    def __lt__(self, l: Content, r: Content):
        return l.time < r.time
    def __gt__(self, l: Content, r: Content):
        return l.time > r.time
    
@dataclass
class Post:
    title: str
    body: str
    num_comments: int
    time: str
    value = 2
    
    def __repr__(self):
        return f'Title: {self.title:<20}\tComments: {self.num_comments}\tBody: {self.body[:20]:<20}\tTime: {self.time}'
    def __hash__(self):
        return hash(self.title) ^ hash(self.time) ^ hash(self.body)

@dataclass
class Ticker:
    ticker: str
    name: str
    exchange:Exchange
    references: list[Content]
    
    def __repr__(self):
        return f'Ticker: {self.ticker:<10}\tReferences: {len(self.references)}\tExchange: {self.exchange:<15}\tName: {self.name:<20}\n'
    
    def references_str(self):
        res = f"Number of references: {len(self.references)}\n"
        for r in self.references:
            if isinstance(r, Comment):
                res+=f"\t Comment body: {r.content}\n"
            if isinstance(r, Post):
                res+=f"\t Post Title: {r.title}\n"
                res+=f"\t Post Body: {r.body}\n"
        return res
            
    def __hash__(self):
        return hash(self.ticker) ^ hash(self.name)

class TickerContainer:
    def __init__(self, tickers: set[Ticker]):
        self.tickers: set[Ticker] = tickers
        self._tickers_dict: Dict[str, Ticker] = {ticker.ticker: ticker for ticker in tickers}
    
    def __getitem__(self, key: str) -> Optional[Ticker]:
        return self._tickers_dict.get(key)
    
    def __contains__(self, key: str) -> bool:
        return key in self._tickers_dict
    
def equal_interval_buckets(numbers, n):
    min_val = min(numbers)
    max_val = max(numbers)
    interval_size = (max_val - min_val) / n
    
    buckets = [[] for _ in range(n)]
    
    for num in numbers:
        index = int((num - min_val) / interval_size)
        if index == n:  # Ensure the last bucket includes the maximum value
            index = n - 1
        buckets[index].append(num)
    
    return buckets



def get_ticker(file:str, exchange: Exchange) -> set[Ticker]:
    res = set()
    with open(file) as file:
        reader = csv.reader(file)
        for row in reader:
            ticker=row[0]
            name=row[1]
            res.add(Ticker(ticker=ticker, name=name, exchange=exchange, references=[]))
    return res

    

def get_tickers() -> TickerContainer:
    OTC = get_ticker("OTCtickers.csv", exchange=Exchange.OTC)
    NYSE = get_ticker("NYSEtickers.csv", exchange=Exchange.NYSE)
    NASDAQ = get_ticker("NASDAQtickers.csv", exchange=Exchange.NASDAQ)
    return TickerContainer(OTC | NYSE | NASDAQ)


def get_comments() -> set[Comment]:
    df = pd.read_json('comments.jsonl', lines=True)
    res = set()
    for _, row in df.iterrows():
        body: str = row['body']
        body = ' '.join(body.split())
        if body == "[removed]":
            continue
        # remove auto mod comment
        if "Does this submission" in body:
            continue
        time = row['created']
        res.add(Comment(content=body, time=time))
    return res

def get_posts() -> set[Post]:
    df = pd.read_json('posts.jsonl', lines=True)
    res = set()
    for _, row in df.iterrows():
        title = row['title']
        title = ' '.join(title.split())
        self_text = row['selftext']
        self_text = ' '.join(self_text.split())
        time = row['created']
        num_comments = int(row['num_comments'])
        
        
        res.add(Post(title=remove_emojis(title), body=remove_emojis(self_text), num_comments=num_comments, time=time))
        
    return res

from collections import defaultdict

def generate_references(posts: set[Post], comments: set[Comment], tickers: set[Ticker]):
    symbol_post_index = defaultdict(list)
    symbol_comment_index = defaultdict(list)
    
    for p in posts:
        words_in_title = set(p.title.lower().split())
        words_in_body = set(p.body.lower().split())
        for word in words_in_title:
            symbol_post_index[word].append(p)
        for word in words_in_body:
            symbol_post_index[word].append(p)
            
    for c in comments:
        words_in_content = set(c.content.lower().split())
        for word in words_in_content:
            symbol_comment_index[word].append(c)
            
    for t in tickers:
        symbol = t.ticker.lower()
        if symbol in symbol_post_index:
            t.references.extend(symbol_post_index[symbol])
        if symbol in symbol_comment_index:
            t.references.extend(symbol_comment_index[symbol])
            
def _key(t: Content):
    return t.time

def sort_references(tickers: set[Ticker]):
    for t in tickers:
        t.references = sorted(t.references, reverse=True, key=_key)
    return tickers

def get_all_tickers():
    tickers = get_tickers()
    # ticker = Ticker(ticker="ATOS", name="", exchange=Exchange.NASDAQ, references=[])
    
    posts = get_posts()
    comments = get_comments()
    generate_references(posts=posts, comments=comments, tickers=tickers.tickers)
    referenced_tickers = list(filter(lambda x: len(x.references)>10 and len(x.references) < 70, tickers.tickers))
    print(referenced_tickers)
    

def get_single_ticker(symbol: str):
    ticker = Ticker(ticker=symbol, name="", exchange=Exchange.NASDAQ, references=[])
    
    posts = get_posts()
    comments = get_comments()
    generate_references(posts=posts, comments=comments, tickers={ticker})
    # referenced_tickers = list(filter(lambda x: len(x.references)>10 and len(x.references) < 70, tickers.tickers))
    # print(referenced_tickers)
    
    # r = sorted(ticker.references, reverse=True, key=_key)
    # print(ticker.references_str())
    N = 15
    times = equal_interval_buckets([t.time for t in ticker.references], N)
    print(times)
    
    plt.plot(list(range(N)), [len(c) for c in times])
    plt.show()

if __name__ == "__main__":
    get_single_ticker("VLCN")