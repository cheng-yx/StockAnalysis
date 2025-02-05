import praw
from textblob import TextBlob
import spacy
from collections import Counter
import datetime
import time
import re
import json

# Reddit API
reddit = praw.Reddit(
    client_id="",    
    client_secret="",  
    user_agent="Trading by Lonely_Challenge",  
    redirect_uri="http://localhost:",
)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Stop words
stop_words = set([
    "of", "is", "where", "which", "in", "on", "at", "for", "to", "and", "the", "a", "an", "with",
    "by", "this", "that", "from", "as", "it", "its", "was", "were", "has", "have", "be", "being", "been",
    "but", "or", "not", "so", "if", "out", "about", "more", "some", "such", "can", "will", "would", "should",
    "i","what","you","we","who","they","me","them","people","he","she","=","these","those","I", "the market",
    "US","something","a lot","everything","anyone","the stock","us","nothing","*","no one","stock","both",
    "the way","whatever","the end","him","year","market","-","all","All","time","’s", "the time",
])

# Stock code pattern
stock_code_pattern = re.compile(r"\b[A-Z]{1,5}\b")

# Time setting
end_time = datetime.datetime.utcnow()
start_time = end_time - datetime.timedelta(hours=36)

# Save keywords and sentences
all_sentences = []
keywords = []

# Search posts related to "investment"
subreddits = ["wallstreetbets", "investing", "stocks", "finance", "pennystock"]
for subreddit_name in subreddits:
    subreddit = reddit.subreddit(subreddit_name)

    for post in subreddit.hot(limit=100):
        post_time = datetime.datetime.utcfromtimestamp(post.created_utc)
        if start_time <= post_time <= end_time:
            combined_text = f"{post.title} {post.selftext or ''}"
            
            # Extract keywords
            doc = nlp(combined_text)
            for chunk in doc.noun_chunks:
                word = chunk.text.lower()
                if word not in stop_words:
                    keywords.append(word)

            # Extract stock codes
            stock_codes = [code for code in stock_code_pattern.findall(combined_text) if code != "I"]
            keywords.extend(stock_codes)

            # Split sentences and store
            sentences = [sent.text.strip() for sent in doc.sents]
            all_sentences.extend(sentences)

            # Analysis comments
            post.comments.replace_more(limit=0)
            top_comments = sorted(post.comments.list(), key=lambda x: x.score, reverse=True)[:20]
            for comment in top_comments:
                if comment.body:
                    doc = nlp(comment.body)

                    # Extract keywords from comments
                    for chunk in doc.noun_chunks:
                        word = chunk.text.lower()
                        if word not in stop_words:
                            keywords.append(word)

                    # Extract stock codes from comments
                    stock_codes = [code for code in stock_code_pattern.findall(comment.body) if code != "I"]
                    keywords.extend(stock_codes)

                    # Segment and store comment sentences
                    sentences = [sent.text.strip() for sent in doc.sents]
                    all_sentences.extend(sentences)

# Count keyword frequency
keyword_counter = Counter(keywords)
top_keywords = keyword_counter.most_common(100)

# Output the top 100 high-frequency keywords
print("\nTop 100 Keywords:")
for word, freq in top_keywords:
    print(f"{word}: {freq}")

# Save all_sentences to a JSON file
with open("all_sentences.json", "w", encoding="utf-8") as file:
    json.dump(all_sentences, file, ensure_ascii=False, indent=4)

print("\nAll sentences have been saved to 'all_sentences.json'.")