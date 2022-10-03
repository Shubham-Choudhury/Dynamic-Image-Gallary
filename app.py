import sqlite3
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super-secret-key'

DATABASE = 'database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "static/uploads")

db = SQLAlchemy(app)


class Posts(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text)
    content = db.Column(db.Text)

    def __init__(self, image, content):
        self.image = image
        self.content = content

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    username = db.Column(db.Text)
    password = db.Column(db.Text)

    def __init__(self,name, username, password):
        self.name = name
        self.username = username
        self.password = password



@app.route('/')
def index():
    posts = Posts.query.all()
    return render_template('index.html', posts=posts)

@app.route('/add-post', methods=['GET', 'POST'])
def add():
    if('user' in session and sessionUser(session['user'])):
        if request.method == 'POST':
            content = request.form.get('content')
            image = request.files['image']
            image_name = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
            post = Posts(image_name, content)
            db.session.add(post)
            db.session.commit()
            return redirect('/admin')

        return render_template('add-post.html')
    return redirect('/login')

@app.route('/admin')
def admin():
    if('user' in session and sessionUser(session['user'])):
        posts = Posts.query.all()
        return render_template('dashboard.html', posts=posts)
    return redirect('/login')


@app.route('/edit-post/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if('user' in session and sessionUser(session['user'])):
        post = Posts.query.filter_by(id=id).first()
        if request.method == 'POST':
            my_post = Posts.query.get(id)
            my_post.content = request.form['content']
            db.session.commit()
            return redirect('/admin')

        return render_template('update-post.html', post=post)
    return redirect('/login')

@app.route('/delete/<int:id>')
def delete(id):
    if('user' in session and sessionUser(session['user'])):
        post = Posts.query.get(id)
        image = post.image
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image))
        db.session.delete(post)
        db.session.commit()
        return redirect('/admin')

    return redirect('/login')

@app.route('/signin/admin', methods=['POST', 'GET'])
def signin():
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    password = generate_password_hash(password)
    user = Users(name, email, password)
    db.session.add(user)
    db.session.commit()
    return redirect('/admin')

def sessionUser(session_user):
    # print(session_user)
    result = Users.query.with_entities(Users.username).all()
    for i in range(len(result)):
        if(session_user in result[i][0]):
            return True
    return False

@app.route('/login', methods=['POST', 'GET'])
def login():
    if('user' in session and sessionUser(session['user'])):
        return redirect('/admin')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(username=email).first()

        if user:
            if check_password_hash(user.password, password):
                session['user'] = email
                return redirect('/admin')
            else:
                return redirect('/login')
        else:
            return redirect('/login')
    return render_template('login.html')

@app.route("/logout")
def logout():
    if('user' in session and sessionUser(session['user'])):  
        session.pop('user')
        return redirect('/')
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
