"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file creates your application.
"""

from app import app, db
from flask import render_template, request, jsonify, send_file, url_for, send_from_directory
import os
from app.models import Users, Follows, Posts, Users, Likes
from app.forms import RegisterUserForm, LoginForm, PostForm
from werkzeug.utils import secure_filename, check_password_hash, generate_password_hash
from flask_wtf.csrf import generate_csrf
from datetime import timedelta
import datetime
import jwt
from functools import wraps


###
# Routing for your application.
###

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth = request.headers.get('Authorization', None) # or request.cookies.get('token', None)

    if not auth:
      return jsonify({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'}), 401

    parts = auth.split()

    if parts[0].lower() != 'bearer':
      return jsonify({'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}), 401
    elif len(parts) == 1:
      return jsonify({'code': 'invalid_header', 'description': 'Token not found'}), 401
    elif len(parts) > 2:
      return jsonify({'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}), 401

    token = parts[1]
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        return jsonify({'code': 'token_expired', 'description': 'token is expired'}), 401
    except jwt.DecodeError:
        return jsonify({'code': 'token_invalid_signature', 'description': 'Token signature is invalid'}), 401

    g.current_user = user = payload
    return f(*args, **kwargs)

  return decorated


@app.route('/')
def index():
    return jsonify(message="This is the beginning of our API")


@app.route('/api/v1/register', methods=['POST'])
def register():
    form = RegisterUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        location = form.location.data
        biography = form.biography.data
        profile_photo = form.profile_photo.data

        filename = secure_filename(profile_photo.filename)
        profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        joined_on = datetime.datetime.now()

        user = Users(username, password, firstname, lastname, email, location, biography,  filename, joined_on)
        db.session.add(user)
        db.session.commit()

        users = db.session.execute(db.select(Users)).scalars()
        users_data = []
        for user in users:
            users_data.append({
                "message": "User successfully registered",
                "firstname": user.firstname,
                "lastname": user.lastname,
                "username": user.username,
                "password": user.password,
                "email": user.email,
                "location":user.location,
                "biography": user.biography,
                "profile_photo": user.profile_photo,
                "joined_on": user.joined_on
            })

        return jsonify(data=users_data)
    else:
        return form_errors(form)


@app.route("/api/v1/users/<user_id>/posts", methods=["POST"])
@authorize
def create_post(user_id):
    form = PostForm()
    id = user_id
    user = Users.query.filter_by(id=id).first()
    if(not user):
        return jsonify({
            "message": "user do not exist"
        })
    
    if request.method == "POST" and form.validate_on_submit():
        caption = request.form['caption']
        f = form.photo.data
        filename = secure_filename(f.filename)
        img_url = os.path.join(app.config['UPLOAD_FOLDER'],filename)
        f.save(img_url)

        post = Posts(
            photo=filename,
            caption=caption,
            user=user
        )

        db.session.add(post)
        db.session.commit()

        return jsonify({
            "message": "post created"
        })
    else:
        return "server error"
        
        
@app.route('/api/v1/users/<int:user_id>/posts', methods=['GET'])
@requires_auth
def posts(user_id):
    posts = db.session.execute(db.select(Post).filter_by(user_id=id)).scalar()
    posts_data = []
    for post in posts:
        posts_data.append({
            "id": post.id,
            "user_id": post.user_id,
            "photo": post.photo,
            "description": post.description,
            "created_on": post.created_on
        })

    return jsonify(data=posts_data)


@app.route("/api/v1/posts", methods=["GET"])
def all_posts():
    posts = Posts.query.all()
    arr = []
    for post in posts:
        obj = {
            "id": post.id,
            "user_id": post.user_id,
            "photo": "/api/v1/photo/" + post.photo,
            "caption": post.caption,
            "created_at": post.created_at,
            "likes": len(post.likes)
        }
        arr.append(obj)
    return jsonify({
        "posts": arr
    })
@app.route("/api/v1/posts/<postId>/like", methods=["POST"])
def like(postId):
    try:
        token = request.headers["Authorization"].split(" ")[1]
        decoded_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
    except:
        return jsonify({
            "error": "token not present!"
        }), 404
    userId = decoded_data['id']
    currentuser = Users.query.filter_by(id=userId).first()
    post = Posts.query.filter_by(id=postId).first()
    like = Likes(posts=post, user=currentuser)
    db.session.add(like)
    db.session.commit()

    return jsonify({
        "message": "You liked the post",
        "likes": len(post.likes)
    })

@app.route('/api/v1/csrf-token', methods=['GET'])
def get_csrf():
    return jsonify({'csrf_token': generate_csrf()})


@app.route('/api/v1/jwt-token', methods=['GET'])
def get_jwt():
    timestamp = datetime.now()
    payload = {
        "sub": 1,
        "iat": timestamp,
        "exp": timestamp + timedelta(minutes=30)
    }

    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify(token=token)
    
# # Login route # 
# @app.route("/api/v1/auth/login", methods=["POST"])
# def login():
#     form = LoginForm()
#     if request.method == "POST" and form.validate_on_submit():
#         username = request.form['username']
#         password = request.form['password']
#         user = Users.query.filter_by(username=username).first()
#         if(not user):
#             return jsonify({
#                 "error": "User do not exist!"
#             })
#         if(not(check_password_hash(user.password, password))):
#             return jsonify({
#                 "error": "Invalid credentials!"
#             })
#         data = {}
#         data['id'] = user.id
#         data['username'] = user.username
#         token = jwt.encode(data, app.config["SECRET_KEY"], algorithm="HS256")
#         return jsonify({
#             "message": "User successfully logged in",
#             "token": token
#         })

# Logout route #        
@app.route("/api/v1/auth/logout", methods=["POST"])
def logout():
    return jsonify({
        "message": "User logged out"
    })


# Here we define a function to collect form errors from Flask-WTF
# which we can later use
@app.route("/api/v1/photo/<filename>", methods=['GET'])
def get_image(filename):
    return send_from_directory(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER']), filename)
    
# ------------ following a target user --------------------- #
@app.route("/api/users/<userId>/follow", methods=["POST"])
@authorize
def follow(userId):
    currentuser = Users.query.filter_by(id=userId).first()
    if(not currentuser):
        return jsonify({
            "error": "user does not exist"
        })
    
    data = request.get_json()
    print(data)
    target_id = data['follow_id']
    print(target_id)
    targetuser = Users.query.filter_by(id=target_id).first()

    follow = Follows(follower=targetuser, currentuser=currentuser)
    db.session.add(follow)
    db.session.commit()

    return jsonify({
        "message": "You are now following " + targetuser.username
    })

# ------------ number of followers --------------------- #
@app.route("/api/users/<userId>/follow", methods=["GET"])
@authorize
def followers(userId):
    currentuser = Users.query.filter_by(id=userId).first()

    if(not currentuser):
        return jsonify({
            "error": "user does not exist"
        })
    
    return jsonify({
        "followers": len(currentuser.following)
    })

def form_errors(form):
    errors = []
    for field, error in form.errors.items():
        errors.append({
            "field": field,
            "message": error[0]
        })

    return jsonify(errors=errors)

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404