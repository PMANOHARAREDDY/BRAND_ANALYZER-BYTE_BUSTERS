import os
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, request, render_template, url_for, session, redirect, flash
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


analyzer = SentimentIntensityAnalyzer()


@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/dashboard', methods = ["POST"])
def dashboard():
    key = request.form.get('keyword')
    url = f'https://newsapi.org/v2/everything?q={key}&apiKey={news_api_key}&pageSize=100'
    response = requests.get(url)
    articles = response.json().get('articles', [])
    return articles

if __name__ == "__main__":
    app.run(debug = True)