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

def reddit_analyis(key):
    posts = []
    for post in reddit.subreddit("technology").search(key,limit = 100):
        posts.append({
            "id":post.id,
            "title":post.title,
            "selftext" : post.selftext,
            "created utc":post.created_utc,
            "score":post.score,
        })
    return posts

def news_Analysis(key):
    url = f'https://newsapi.org/v2/everything?q={key}&apiKey={news_api_key}&pageSize=100'
    response = requests.get(url)
    articles = response.json().get('articles', [])
    return articles

def EventRegistry_analysis(key):
    url = f'https://eventregistry.org/api/v1/article/getArticles?query=%7B%22%24query%22%3A%7B%22keyword%22%3A%22{key}%22%2C%22lang%22%3A%22eng%22%7D%2C%22%24filter%22%3A%7B%22forceMaxDataTimeWindow%22%3A%2231%22%7D%7D&resultType=articles&articlesSortBy=date&articlesPage=1&articlesCount=50&apiKey={event_registry_api_key}'
    response = requests.get(url)
    articles = response.json().get('articles', [])
    return articles

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/dashboard', methods = ["POST"])
def dashboard():
    key = request.form.get('keyword')
    reddit_posts = reddit_analyis(key)
    EventRegistry_posts = EventRegistry_analysis(key)
    news_articles = news_Analysis(key)

    return jsonify({"reddit posts":reddit_posts , "Event Registry Articles":EventRegistry_posts, "News Articles":news_articles})

if __name__ == "__main__":
    app.run(debug = True)