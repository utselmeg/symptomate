"""This module contains the Flask app and routes.
"""

import secrets
import sqlite3
import html
from flask import Flask, request, render_template, redirect, url_for, flash
from backend.expert_system import process_search_query, generate_recommendations, random_symptoms, get_feedback

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

global SHARED_RESOURCES
SHARED_RESOURCES = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    """6 random symptoms on main page
    """
    random_sample = random_symptoms()
    if request.method == 'POST':
        return redirect(url_for('search'))
    else:
        return render_template('index.html', random_sample=random_sample)


@app.route('/search', methods=['POST'])
def search():
    """Process user input
    """
    global SHARED_RESOURCES

    user_input = request.form['user_input']
    search_results, related_searches, idx_and_othersymptoms = process_search_query(
        user_input)
    SHARED_RESOURCES['idx_and_othersymptoms'] = idx_and_othersymptoms
    return render_template('results.html', search_results=search_results
                           , related_searches=related_searches)


@app.route('/recommend', methods=['POST'])
def recommend():
    """Generates disease descriptions based on user input.
    """
    global SHARED_RESOURCES

    selected_results = request.form.getlist('related_search')
    idx_and_othersymptoms = SHARED_RESOURCES['idx_and_othersymptoms']
    recommendations_with_severity_and_precautions_and_links = generate_recommendations(
        selected_results, idx_and_othersymptoms)
    return render_template('recommendations.html', recommendations=recommendations_with_severity_and_precautions_and_links)



@app.route('/contactus')
def about():
    """Contact us page
    """
    return render_template('contact.html')


@app.route('/contatctus/submit', methods=['POST'])
def submit_form():
    """Submit form
    """
    form = request.form
    name = html.escape(form['name'])
    email = html.escape(form['email'])
    message = html.escape(form['message'])

    # validate form data

    print(request.form)
    # Create a SQLite3 connection
    # if form.validate_on_submit():
    conn = sqlite3.connect("database/database.sqlite", check_same_thread=False)
    # save to database
    get_feedback(conn, name, email, message)
    flash('Thank you for your feedback!')
    # # # send email
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # server.login()
    # server.sendmail('tselmeg.ulammandakh@yale.edu', email, f'Name: {name}\nEmail: {email}\nMessage: {message}')
    # server.quit()

    return render_template('contact.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
