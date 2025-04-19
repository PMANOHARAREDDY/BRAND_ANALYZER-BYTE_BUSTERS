import os
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, request, render_template, url_for, session, redirect, flash, jsonify
import praw
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Reddit API Credentials
reddit = praw.Reddit(
    client_id = '-mi82_n8q6dN9o4RiUGoKQ',
    client_secret = 'hkf_DBqNC0yqsfTEnhC6i-PBfYZqHA',
    user_agent = 'Product_Sentineo'
)

# News API Credentials
news_api_key = 'f1c1b88c5f55436596e8df23d2a7649b'

# Event Registry Credentials
event_registry_api_key = '354393d0-e38d-4735-9b99-fd99a8edc17f'

analyzer = SentimentIntensityAnalyzer()

# Funtion for Reddit API Data Analysis
def reddit_analyis(key):
    posts = []
    for post in reddit.subreddit("technology").search(key,limit = 100):
        upvotes = max(post.score, 0)
        downvotes = int((1 - post.upvote_ratio) * (upvotes + abs(post.score))) if post.score < 0 else int((1 - post.upvote_ratio) * (upvotes + abs(post.score)))
        posts.append({
            "id":post.id,
            "title":post.title,
            "selftext" : post.selftext,
            "created utc":post.created_utc,
            "score":post.score,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "sentiment": 0.2*(analyzer.polarity_scores(post.title)['compound']) + (0.5*upvotes)/(upvotes+downvotes) - 0.3*(downvotes)/(upvotes+downvotes)
        })
        df = pd.DataFrame(posts)
        result = df['sentiment'].mean()
    return result

# Function for News API data Analysis
def news_Analysis(key):
    url = f'https://newsapi.org/v2/everything?q={key}&apiKey={news_api_key}&pageSize=100'
    response = requests.get(url)
    articles = response.json().get('articles', [])
    posts = []
    for article in articles:
        title = article['title']
        description = article['description'] or ''
        content = article['content'] or ''
        complete_data = f'{title}{description}{content}'
        sentiment = analyzer.polarity_scores(complete_data)['compound']
        posts.append({
            "title":title,
            "description":description,
            "content":content,
            "sentiment":sentiment
        })
        df = pd.DataFrame(posts)
        result = df['sentiment'].mean()
    return result

# Funtion for EVENT Registry API Data Analysis
def EventRegistry_analysis(key):
    url = f'https://eventregistry.org/api/v1/article/getArticles?query=%7B%22%24query%22%3A%7B%22keyword%22%3A%22{key}%22%2C%22lang%22%3A%22eng%22%7D%2C%22%24filter%22%3A%7B%22forceMaxDataTimeWindow%22%3A%2231%22%7D%7D&resultType=articles&articlesSortBy=date&articlesPage=1&articlesCount=1&apiKey={event_registry_api_key}'
    response = requests.get(url)
    obj = response.json().get('articles', [])
    posts = []
    posts.append(obj["results"][0]['body'])
    sentiment = analyzer.polarity_scores(posts[0])['compound']
    return sentiment

# Home Page
@app.route('/')
def home():
    return render_template('dashboard.html')

# DashBoard 
@app.route('/dashboard', methods = ["POST"])
def dashboard():
    key = request.form.get('keyword')
    reddit_posts = reddit_analyis(key)
    EventRegistry_posts = EventRegistry_analysis(key)
    news_articles = news_Analysis(key)
    # return "News articles Data : "+str(news_articles)
    # return "Reddit Data : "+ str(reddit_posts)
    # return "Event Registry Data " : str(EventRegistry_posts)
    return jsonify({"reddit posts":str(reddit_posts) , "Event Registry Articles":str(EventRegistry_posts), "News Articles":str(news_articles)})

if __name__ == "__main__":
    app.run(debug = True)