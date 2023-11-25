import sqlite3
import time
import hashlib

from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL

import secrets
foo = secrets.token_urlsafe(16)

DATABASE_NAME = "ble.db"
TABLE_NAME = "shortened_links"

app = Flask(__name__)
app.secret_key = foo
# Bootstrap-Flask requires this line
bootstrap = Bootstrap5(app)
# Flask-WTF requires this line
csrf = CSRFProtect(app)

class LinkForm(FlaskForm):
    link = StringField("", render_kw = {"placeholder" : "Enter link to shorten..."}, validators = [DataRequired(), URL()])
    submit = SubmitField("Submit")

def shorten_link(link):
    m = hashlib.sha256()
    m.update(bytes(link, encoding='utf-8'))
    digest = m.hexdigest()
    return digest[-6:]

def get_short_link_from_db(full_link):
    ts_created = time.time_ns()
    # check if the link has already been shortened
    with sqlite3.Connection(DATABASE_NAME) as conn:
        short_link = conn.cursor().execute(
            f"SELECT short_link FROM {TABLE_NAME} WHERE full_link = '{full_link}';"
        ).fetchone()
    
    if short_link:
        return short_link[0]
    
    # now shorten the link
    short_link = shorten_link(full_link)
    with sqlite3.Connection(DATABASE_NAME) as conn:
        conn.cursor().execute(
            f"INSERT INTO {TABLE_NAME} VALUES(?,?,?);", (full_link, short_link, ts_created)
        )
        conn.commit()

    return short_link

def get_full_link_from_db(short_link):
    with sqlite3.Connection(DATABASE_NAME) as conn:
        full_link = conn.cursor().execute(
            f"SELECT full_link FROM {TABLE_NAME} WHERE short_link = '{short_link}';"
        ).fetchone()
    
    return full_link[0] if full_link else ""


@app.route("/", methods=["GET", "POST"])
def index():
    short_link = ""
    link_form = LinkForm()

    if link_form.validate_on_submit():
        link = link_form.link.data
        print(f"Form submitted with link {link}!")
        short_link = get_short_link_from_db(link)
    
    return render_template("index.html", link_form=link_form, short_link = short_link, error = "")

@app.route("/<path:path>", methods=["GET"])
def access_shortlink(path):
    print("Accessing short link...")
    full_link = get_full_link_from_db(path)
    if full_link: 
        print(full_link)
        return redirect(full_link)
    
    return redirect("/")

@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug = True)