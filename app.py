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
news_api_key = '83224eca-05ce-402d-b67b-fec066a110f8'


analyzer = SentimentIntensityAnalyzer()




if __name__ == "__main__":
    app.run(debug = True)