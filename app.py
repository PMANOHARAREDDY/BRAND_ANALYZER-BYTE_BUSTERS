import functools
import os
import pathlib
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, abort, request, render_template, url_for, session, redirect, flash, jsonify
import praw
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector as sql
from bs4 import BeautifulSoup
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from flask_caching import Cache

# Allowing HTTPs to serve on the localhost
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
# Google API Credentials
google_client_id = "617388834874-khcmv9f11defv7tstbt1bga3cj5fa61r.apps.googleusercontent.com"

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow  = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri = "http://127.0.0.1:5000/block2"
    )

conn = sql.connect(host = "127.0.0.1", user = "root" ,password = "Pavitra@01", database = "brand_sentineo")
app = Flask(__name__)

app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379'
cache = Cache(app)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key")
c = conn.cursor()

# global Variables
global role
global email_id

@app.route('/manohar')
def manohar():
    client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ],
        redirect_uri="http://127.0.0.1:5000/block2"
    )
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route('/block2')
def block2():
    if session.get("state") != request.args.get("state"):
        abort(401)

    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="http://127.0.0.1:5000/block2"
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Decode and verify the ID token
    request_adapter = GoogleRequest()
    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        request_adapter,
        google_client_id  
    )

    session["google_id"] = id_info.get("sub")
    session["email"] = id_info.get("email")
    global email_id
    email_id = session["email"]
    c.execute('SELECT role FROM access WHERE email_id = %s', (session["email"],))
    result = c.fetchone()
    global role
    if result:
        role = result[0]
    else:
        role = 'cus'
    return render_template('dashboard.html')


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

# Tumbler API Credentials
tumbler_api_key = 'aeFN2SHfTT0Wz4frlZNRKHFa9Zxo6tfgrRpjxJhXmwOCZvOR6R'
tumbler_api_secret = '94eE6MYEn9JdWXcDKK75VzQOMeTOhn4ne0PftoKXvdinOfHReb'


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

# Function for the Tumbler API Data Analysis
def tumbler_analysis(key):
    url = f'https://api.tumblr.com/v2/tagged?tag={key}&api_key={tumbler_api_key}'
    response = requests.get(url)
    posts = response.json().get('response', [])
    text_bodies = []
    for post in posts:
        if post.get('type') == 'text' and 'body' in post:
            text_bodies.append(post['body'])
    clean_bodies = []
    for html_body in text_bodies:
        soup = BeautifulSoup(html_body, 'html.parser')
        for tag in soup(['figure', 'img']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        clean_bodies.append(text)
    sentiment = analyzer.polarity_scores(clean_bodies[0])['compound']
    return sentiment

# Home Page
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard', methods = ["post","get"])
def dashboard():
    mail = request.form.get('emailID')
    passwd = request.form.get('pass')
    user = request.form.get('user')
    c.execute('select email_id, pass, role from access')
    rows = c.fetchall()
    user_state = False
    registration_state = False
    for i in rows:
        if i[0] == mail and check_password_hash(i[1], passwd) and i[2] == user:
            user_state = True
            registration_state = True
            break 
        elif i[0] == mail and i[2] == user:
            registration_state = True   
    if user_state == True:
        global role
        global email_id
        role = user
        email_id = mail
        if role!='admin':
            flash("Login successful!", "success")
            return render_template('dashboard.html')
        else:
            flash("Login successful!", "success")
            return redirect(url_for('admin_dashboard'))
    else:
        if registration_state == True:
            flash("!!! Invalid Password !!", "danger")
        else:
            flash("!!! you are not registered, want to register???","danger")
        return redirect(url_for('home'))

def make_cache_key():
    return f"dashboard_{request.form.get('keyword', '')}"

# DashBoard 
@app.route('/dashboard2', methods = ["POST"])
@cache.cached(timeout=10, make_cache_key=make_cache_key)
def dashboard2():
    key = request.form.get('keyword')
    
    reddit_posts = reddit_analyis(key)
    EventRegistry_posts = EventRegistry_analysis(key)
    news_articles = news_Analysis(key)
    tumblr_blogs = tumbler_analysis(key)
    # reddit_posts = 0.663
    # EventRegistry_posts = 0.5
    # news_articles = 0
    # tumblr_blogs = 0.36

    if role == 'cus':   
        query = "insert into search (email_id, product) values('{}','{}')".format(email_id,key)
        c.execute(query)
        conn.commit()
        return render_template('Customer_dashboard.html', event = EventRegistry_posts,reddit = reddit_posts, news = news_articles, tumblr = tumblr_blogs)
    elif role == 'com':
        return render_template('brand_dashboard.html', event = EventRegistry_posts,reddit = reddit_posts, news = news_articles, tumblr = tumblr_blogs)
    else:
        return "State Bypassed"

@app.route('/register', methods = ["POST","GET"])
def register():
    if request.method == "POST" and request.form.get('pass1')==request.form.get('pass2'):
        user = request.form.get('role')
        mail = request.form.get('emailID')
        passwd = request.form.get('pass1')
        if mail[-10:] != "@gmail.com":
            flash("Not a valid gmail account.... use only public domain '@gmail.com'","danger")
            return render_template('register.html')
        if not (len(passwd) >= 8 and any(c.isupper() for c in passwd) and any(c.islower() for c in passwd) and any(c.isdigit() for c in passwd) and any(c in "!@#$%^&*()-_+=" for c in passwd)):
            flash("atleast eight characters, One Lowercase, One Uppercase, One digit, One special character is required","danger")
            return render_template('register.html')
        c.execute('select * from access')
        rows = c.fetchall()
        user_state = False
        for i in rows:
            if i[0]==mail and i[2] == user:
                user_state = True
        if user_state == True:
            return render_template('register.html')
        passwd = generate_password_hash(passwd)
        url = "insert into access values('{}','{}','{}')".format(mail, passwd, user)
        c.execute(url)
        conn.commit()
        flash("Registration Successful","success")
        return redirect(url_for('home'))
    elif request.method == "POST" and request.form.get('pass1')!=request.form.get('pass2'):
        flash("Passwords are not similiar..... try again!!!","danger")
        return render_template('register.html')
    else:
        return render_template('register.html')

@app.route('/admin_Dashboard')
def admin_dashboard():
    c.execute('select * from search')
    rows = c.fetchall()
    return render_template('admin_dashboard.html',trace = rows)

