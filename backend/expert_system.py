"""
backend python
expert_system.py
"""
import sys
from contextlib import closing
import sqlite3
from sqlite3 import connect, OperationalError, DatabaseError
from collections import defaultdict
import ast
import openai
from backend.config import DATABASE_PATH, PROMPT_PATH, PROMPT_PATH_LINK, API_KEYS, MAX_TRIALS


class SearchResult:
    """Represents a search result.
    """

    def __init__(self, title, description=""):
        self.title = title
        self.description = description


class RelatedSearch:
    """Represents a related search.
    """
    def __init__(self, keyword, description):
        self.keyword = keyword
        self.description = description


def process_search_query(query):
    """Generate a list of search results and related searches based on the user's query
    """
    symptom, filters = get_filter_term_by_api(query)
    if not filters:
        return [], [], []
    objects = get_filter_objects_1(filters)
    diseases, other_symptoms_list, idx_and_othersymptoms = process_objects(
        objects, symptom)
    symptom_descriptions = get_symptom_descriptions(other_symptoms_list)
    search_results = [SearchResult(disease.replace(
        "_", " ").capitalize()) for disease in diseases]
    related_searches = [RelatedSearch(other_symptom.replace("_", " ").capitalize(
    ), symptom_descriptions[other_symptom]) for other_symptom in other_symptoms_list]
    return search_results, related_searches, idx_and_othersymptoms


def generate_recommendations(selected_results, idx_and_othersymptoms):
    """Generate a list of recommendations based on the user's selected search results
    """
    selected_results = [result.replace(" ", "_").lower()
                        for result in selected_results]
    final_diseases = get_filter_objects_2(
        selected_results, idx_and_othersymptoms)
    final_diseases_description = get_disease_description(final_diseases)
    recommendations = [SearchResult(disease.replace("_", " ").capitalize(
    ), final_diseases_description[disease]) for disease in final_diseases]

    # Calculate the total severity
    conn = sqlite3.connect('database/database.sqlite')
    cursor = conn.cursor()

    recommendations_with_severity = []
    for recommendation in recommendations:
        total_severity = 0
        for symptom in selected_results:
            cursor.execute("SELECT weight FROM 'Symptom-severity' WHERE symptom = ?", (symptom,))
            weight = cursor.fetchone()
            if weight:
                total_severity += weight[0]

        recommendations_with_severity.append({
            'title': recommendation.title,
            'description': recommendation.description,
            'severity': total_severity,
        })

    recommendations_with_severity_and_precautions_and_links = []
    for recommendation in recommendations_with_severity:
        links = get_links(recommendation['title'])
        cursor.execute("SELECT * FROM symptom_precaution WHERE Disease = ?", (recommendation['title'],))
        precautions = cursor.fetchone()
        if precautions:
            precautions_list = list([precaution.capitalize() for precaution in precautions[1:] if precaution != ''])
        else:
            precautions_list = []

        recommendations_with_severity_and_precautions_and_links.append({
            'title': recommendation['title'],
            'description': recommendation['description'],
            'severity': recommendation['severity'],
            'precautions': precautions_list,
            'links': links
        })

    conn.close()

    return recommendations_with_severity_and_precautions_and_links

def random_symptoms():
    """Get 6 random symptoms for home page
    """
    symptoms = []
    conn = sqlite3.connect('database/database.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT Symptom FROM 'Symptom-severity' ORDER BY RANDOM() LIMIT 6")
    results = cursor.fetchall()
    symptoms = [result[0] for result in results]
    symptoms = [symptom.replace("_", " ").capitalize() for symptom in symptoms]
    conn.close()
    return symptoms


def get_disease_description(final_diseases):
    """Return disease descriptions for final diagnosis
    """
    with connect(DATABASE_PATH) as connection:
        with closing(connection.cursor()) as cursor:
            try:
                if len(final_diseases) == 1:
                    cursor.execute(f"""
                    SELECT Disease, Description
                    FROM symptom_Description
                    WHERE Disease = '{tuple(final_diseases)[0]}';
                    """)
                else:
                    cursor.execute(f"""
                    SELECT Disease, Description
                    FROM symptom_Description
                    WHERE Disease IN {tuple(final_diseases)};
                    """)
                rows = cursor.fetchall()
                final_diseases_description = dict(rows)
            except OperationalError as e_r:
                print(e_r)
                sys.exit(1)
            except DatabaseError as e_r:
                print(e_r)
                sys.exit(1)
    return final_diseases_description


def get_symptom_descriptions(symptoms):
    """Gets the description of the symptoms for the related searches
    """

    with connect(DATABASE_PATH) as connection:
        with closing(connection.cursor()) as cursor:
            try:
                if len(symptoms) == 1:
                    cursor.execute(f"""
                    SELECT Symptom, description
                    FROM "Symptom-severity"
                    WHERE Symptom = '{tuple(symptoms)[0]}';
                    """)
                else:
                    cursor.execute(f"""
                    SELECT Symptom, description
                    FROM "Symptom-severity"
                    WHERE Symptom IN {tuple(symptoms)};
                    """)
                rows = cursor.fetchall()
                symptom_descriptions = defaultdict(str, rows)
            except OperationalError as e_r:
                print(e_r)
                sys.exit(1)
            except DatabaseError as e_r:
                print(e_r)
                sys.exit(1)
    return symptom_descriptions

def get_feedback(conn, name, email, message):
    """ insert feedback"""
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)', (name, email, message))
    conn.commit()

####################################################################

def chat_gpt_api(message):
    success = False
    trial = 0
    openai.api_key = API_KEYS[trial]
    while not success:
        try:
            messages = []
            messages.append(
                {"role": "user", "content": message},
            )
            # use static prompt for now to save money...
            chat_completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages
            )
            answer = chat_completion.choices[0].message.content
            print(answer)
            success = True
        except openai.error.RateLimitError:
            trial += 1
            if trial >= MAX_TRIALS:
                answer = "Openai API error. Please try again later."
                break
            openai.api_key = API_KEYS[trial]

    return answer

def get_links(disease):
    with open(PROMPT_PATH_LINK, 'r', encoding="utf8") as file:
        prompt = file.read().format(disease)
    links = chat_gpt_api(prompt)
    links = '\t'.join(links.strip().split('\n'))

    ## use static prompt for now to save money...
    # links = '1. Dengue - WHO: https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue      2. Dengue - CDC: https://www.cdc.gov/dengue/index.html'
    print(links)
    return links


def get_filter_term_by_api(user_request):
    """return related symptoms
    """

    with open(PROMPT_PATH, 'r', encoding="utf8") as file:
        prompt = file.read().format(user_request)
    try:
        symptoms = ast.literal_eval(chat_gpt_api(prompt))
    except:
        print('No matching symptoms.')
        return [], ''
    if not symptoms:
        print('No matching symptoms.')
        return [], ''
    sql = """
    SELECT *
    FROM dataset
    WHERE
    """
    cache_symptoms = symptoms[:]
    while symptoms:
        sql += f"""(' ' || LOWER(Symptom_1) || ' ' || LOWER(Symptom_2) \
        || ' ' || LOWER(Symptom_3) || ' ' || LOWER(Symptom_4) || ' ' \
        || LOWER(Symptom_5) || ' ' || LOWER(Symptom_6) || ' ' || LOWER(Symptom_7) \
        || ' ' || LOWER(Symptom_8) || ' ' || LOWER(Symptom_9) || ' ' || LOWER(Symptom_10) \
        || ' ' || LOWER(Symptom_11) || ' ' || LOWER(Symptom_12) || ' ' || LOWER(Symptom_13) \
        || ' ' || LOWER(Symptom_14) || ' ' || LOWER(Symptom_15) || ' ' || LOWER(Symptom_16) 
        || ' ' || LOWER(Symptom_17) || ' ')
    LIKE '% {symptoms.pop()} %'"""
        if symptoms:
            sql += ' or '
    sql += ';'

    return cache_symptoms, sql


def get_filter_objects_1(filter_term):
    """
    Get objects from database by filter query.
    """
    try:
        with connect(DATABASE_PATH) as connection:
            # Check if empty database
            # validate_id(connection, args.id)
            symptoms = []
            with closing(connection.cursor()) as cursor:
                try:
                    cursor.execute(filter_term)
                    rows = cursor.fetchall()
                    symptoms.append(rows)

                # corrupted database
                except DatabaseError as ex:
                    print(f"Error executing the query: {ex}", file=sys.stderr)
                    sys.exit(1)
        return rows

    # database cannot be opened/connected
    except OperationalError as ex:
        print(f"Error connecting to the database: {ex}", file=sys.stderr)
        sys.exit(1)


def process_objects(rows, symptom):
    """
    return a list of diseases, a list of other symptoms, and a dictionary of idx and other symptoms
    """
    disease = set()
    other_symptoms_list = set()
    idx_and_othersymptoms = defaultdict(list)
    for row in rows:
        disease.add(row[1].strip())
        for ele in row[2:]:
            ele = ele.strip()
            if ele and ele != symptom:
                other_symptoms_list.add(ele)
                idx_and_othersymptoms[row[0]].append(ele)
    return disease, other_symptoms_list, idx_and_othersymptoms

# TODO: calculate the coverage of user feedback and the symptom lists
def cal_coverage(clicked_symptoms, idx_and_othersymptoms):
    """
    finding correct diagnosis based on all symptoms given
    """
    clicked_symptoms = set(clicked_symptoms)
    final_idx = []
    max_prop = 0
    for idx in idx_and_othersymptoms:
        othersymptoms = idx_and_othersymptoms[idx]
        prop = len(set(othersymptoms).intersection(
            clicked_symptoms))  # /len(set(othersymptoms))
        if prop == max_prop:
            final_idx.append(idx)
        elif prop > max_prop:
            max_prop = prop
            final_idx = [idx]
    return final_idx


def get_filter_objects_2(clicked_symptoms, idx_and_othersymptoms):
    """
    finding diagnosis based on all symptoms given
    """
    final_idx = cal_coverage(clicked_symptoms, idx_and_othersymptoms)

    try:
        with connect(DATABASE_PATH) as connection:
            # Check if empty database
            # validate_id(connection, args.id)
            diseases = set()
            with closing(connection.cursor()) as cursor:
                try:
                    for idx in final_idx:
                        cursor.execute(
                            f'select Disease from dataset where idx={idx};')
                        rows = cursor.fetchall()
                        diseases.add(rows[0][0].strip())

                # corrupted database
                except DatabaseError as ex:
                    print(f"Error executing the query: {ex}", file=sys.stderr)
                    sys.exit(1)
                return diseases

    # database cannot be opened/connected
    except OperationalError as ex:
        print(f"Error connecting to the database: {ex}", file=sys.stderr)
        sys.exit(1)
