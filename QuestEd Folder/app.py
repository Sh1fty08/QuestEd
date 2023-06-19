from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import current_user, LoginManager
import mysql.connector
import random
import sys
import time
import random

app = Flask(__name__)
app.secret_key = '12345'


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Calleja_0221",
    database="quested"
)

cursor = db.cursor()

#user fetcher
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM login_database WHERE idlogin_database=%s", (user_id,))
    return cursor.fetchone()
#user fetcher

#login
@app.route('/')
def root():
    return render_template('login.html', )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM login_database WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user is not None:
            session['username'] = user[1]
            return redirect('/home')
        else:
            return redirect('/login')
    return render_template('login1.html' )
#login 

#register
@app.route('/register1')
def register1():
    return render_template('register.html')   

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor.execute("SELECT * FROM login_database WHERE username=%s", (username,))
        if cursor.fetchone() is not None:
            return "Username already exists!"

        cursor.execute("INSERT INTO login_database (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
        db.commit()
        return redirect('/login')
    return render_template('register.html')
#register

#homepage      
@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        cursor.execute("SELECT * FROM login_database WHERE username=%s", (username,))
        user_data = cursor.fetchone()
        if user_data:
            username = user_data[1]
            email = user_data[2]
    
            return render_template('homepage.html', username=username, email=email)
        else:
            return "User not found in the database."
    else:

        return redirect(url_for('login'))
 #homepage 
      
#play pagge
@app.route('/playpage')
def play():
    return render_template('play.html') 
#play pagge

#leaderboards page
@app.route('/leaderboards/<category>')
def leaderboard(category):

    if category == 'english':
        cursor.execute("SELECT * FROM eleaderboards_database ORDER BY score DESC LIMIT 10")
    elif category == 'science':
        cursor.execute("SELECT * FROM sleaderboards_database  ORDER BY score DESC LIMIT 10")
    elif category == 'math':
        cursor.execute("SELECT * FROM mleaderboards_database  ORDER BY score DESC LIMIT 10")
    else:
        return "Invalid category"

    scores = cursor.fetchall()
    return render_template('leaderboards.html', scores=scores, category=category.capitalize())
#leaderboards page

#Single player page
@app.route('/single')
def single():
    return render_template('singleplayer.html')
#Single player page

#game
@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'POST':
        counter = int(request.form['counter'])
        user_answer = request.form['answers']
        score = int(request.form['score'])
        category = session.get('category')
        remaining_time = 60

        if not category:
            return redirect(url_for('play'))

        table_name = f"{category[0]}questions_database"
        questions = session.get('questions')
        question = questions[counter - 1]

        if question:
            correct_answer = question[2]

            start_time = session.get('start_time')
            current_time = time.time()
            elapsed_time = current_time - start_time
            remaining_time = 60 - int(elapsed_time)

            if user_answer.strip().lower() == correct_answer.strip().lower():
                score += remaining_time * 1000

        counter += 1
        session['counter'] = counter
        session['score'] = score

        if counter > 10:
            session.pop('counter', None)
            session.pop('score', None)
            session.pop('category', None)
            session.pop('start_time', None)

            insert_score(category, score)

            return redirect(url_for('result', score=score))

        question = questions[counter - 1]
        start_time = session.get('start_time')
        elapsed_time = time.time() - start_time
        remaining_time = max(60 - int(elapsed_time), 0)

        if remaining_time <= 0:
            session.pop('counter', None)
            session.pop('score', None)
            session.pop('category', None)
            session.pop('start_time', None)

            insert_score(category, score)

            return redirect(url_for('result', score=score))

        return render_template('game.html', question=question[1], counter=counter, score=score, category=category,
                               remaining_time=remaining_time)

    else:
        category = request.args.get('category')
        start_time = time.time()

        if not category:
            return redirect(url_for('play'))

        session['category'] = category
        session['start_time'] = time.time()
        session['counter'] = 1
        session['score'] = 0
        table_name = f"{category[0]}questions_database"
        questions = get_shuffled_questions(table_name)
        session['questions'] = questions
        question = questions[0]
        elapsed_time = time.time() - start_time
        remaining_time = max(60 - int(elapsed_time), 0)

        if question:
            return render_template('game.html', question=question[1], counter=1, score=0, category=category,
                                   remaining_time=remaining_time)
        else:
            return "No questions found in the database."
#game

def get_shuffled_questions(table_name):
    cursor.execute("SELECT * FROM {}".format(table_name))
    questions = cursor.fetchall()
    random.shuffle(questions)
    return questions
        
#score inserter
def insert_score(category, score):
    if 'username' in session:
        username = session['username']

        if category == 'english':
            leaderboard_table = 'eleaderboards_database'
        elif category == 'science':
            leaderboard_table = 'sleaderboards_database'
        elif category == 'math':
            leaderboard_table = 'mleaderboards_database'
        else:
            return "Invalid category"

        try:
            cursor.execute(f"INSERT INTO {leaderboard_table} (username, score) VALUES (%s, %s)", (username, score))
            db.commit()
            return True
        except mysql.connector.Error as error:
            return str(error)

    return "User not logged in" 
#score inserter

#result
@app.route('/result')
def result():
    score = request.args.get('score')

    return render_template('result.html', score=score)
#result

#editorial
@app.route('/user_game', methods=['GET', 'POST'])
def user_game():

    if request.method == 'POST':
        username = request.form['username']
        cursor.execute("SELECT * FROM editorial_database WHERE username=%s", (username,))   
        questions = cursor.fetchall()
        

        if questions:
            game_questions = []
            for question in questions:
                game_question = {
                    'username': question[1],
                    'question': question[2],
                    'answer': question[3]
                }
                game_questions.append(game_question)

            session['game_questions'] = game_questions
            session['counter'] = 1
            session['score'] = 0

            return redirect(url_for('play_user_game'))
        else:
            return "No questions found for the selected username."
        
    return render_template('user_game.html')
    

#editorial
@app.route('/play_user_game', methods=['GET', 'POST'])
def play_user_game():
    if 'game_questions' in session:
        game_questions = session['game_questions']
        counter = session.get('counter', 1)

        if request.method == 'POST':
            user_answer = request.form['answers']
            game_questions = session.get('game_questions')

            if game_questions:
                if counter <= len(game_questions):
                    correct_answer = game_questions[counter - 1]['answer']
                    score = session.get('score', 0)

                    if user_answer.strip().lower() == correct_answer.strip().lower():
                        score += 1  

                    counter += 1
                    session['counter'] = counter
                    session['score'] = score

                    if counter <= len(game_questions):
                        return redirect(url_for('play_user_game'))

                    session.pop('counter', None)
                    session.pop('score', None)
                    session.pop('game_questions', None)

                    final_score = score
                    return render_template('game_completed.html', final_score=final_score)

        if counter <= len(game_questions):
            current_question = game_questions[counter - 1]['question']
            return render_template('play_user_game.html', question=current_question, game_questions=game_questions,
                                   counter=counter)

    return redirect(url_for('user_game'))

@app.route('/editorial', methods=['GET', 'POST'])
def editorial():
    if request.method == 'POST':
        option = request.form['option']

        if option == 'create':
            return redirect(url_for('create_questionnaire'))
        elif option == 'play':
            return redirect(url_for('select_questionnaire'))

    return render_template('editorial.html')

@app.route('/create', methods=['GET', 'POST'])
def create_questionnaire():
    if request.method == 'POST':
        username = session.get('username')  
        question = request.form['question']
        answer = request.form['answer']

        cursor.execute("INSERT INTO editorial_database (username, question, answer) VALUES (%s, %s, %s)", (username, question, answer))
        db.commit()

        return redirect(url_for('create_questionnaire'))

    return render_template('create_questionnaire.html')

@app.route('/select', methods=['GET', 'POST'])
def select_questionnaire():
    if request.method == 'POST':
        username = request.form['username']
        cursor.execute("SELECT * FROM editorial_database WHERE username=%s", (username,))
        questions = cursor.fetchall()

        if questions:
            game_questions = []
            for question in questions:
                game_question = {
                    'username': question[1],
                    'question': question[2],
                    'answer': question[3]
                }
                game_questions.append(game_question)

            session['game_questions'] = game_questions
            session['counter'] = 1
            session['score'] = 0
            return redirect(url_for('play_user_game'))
        else:
            return "No questions found for the selected username."

    return render_template('select_questionnaire.html')
#editorial

#settings
# settings page
@app.route('/settings')
def settings():
    if 'username' in session:
        username = session['username']
        cursor.execute("SELECT * FROM editorial_database WHERE username=%s", (username,))
        questions = cursor.fetchall()
        return render_template('settings.html', questions=questions)
    else:
        return redirect(url_for('login'))

# delete question
@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'username' in session:
        username = session['username']
        cursor.execute("DELETE FROM editorial_database WHERE ideditorial_database=%s AND username=%s", (question_id, username))
        db.commit()
    return redirect(url_for('settings'))
#settings

#about page
@app.route('/about')
def about():
    return render_template('about.html')
#about page

#exit app
@app.route('/exit')
def exit_app():
    sys.exit(0) 
#exit app

if __name__ == '__main__':
    app.run()