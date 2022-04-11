from flask import *
from flask_moment import Moment
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from os import path
import random
app = Flask(__name__)
import pymongo
from bson.objectid import ObjectId
if os.environ.get("MONGO_URI")==None:
###means it's on this computer
    connection_file = open("connection_string.txt", 'r')
    content = connection_file.read().strip()
    connection_string = content
    connection_file.close()
else:
###means it's on heroku
    connection_string=os.environ.get("MONGO_URI")

client = pymongo.MongoClient(connection_string)
#db = client["social-media"]
if os.environ.get("DATABASE_NAME")==None:
    db = client["gunnhacks"]
else:
    db = client[os.environ.get("DATABASE_NAME")]
if os.environ.get("SECRET_KEY")==None:
    secret_file=open("secretkey.txt",'r')
    key=secret_file.read().strip()
    secret_file.close()
else:
    key=os.environ.get("SECRET_KEY")

app.secret_key = key
app.upload_folder = 'static/user-uploads'
moment = Moment(app)

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        first_name = request.form['first-name']
        last_name = request.form['last-name']
        email = request.form['email']
        password = request.form['password']
        info = {'first-name': first_name, 'last-name': last_name, 'email': email, 'password': password}
        info['groups'] = []
        info['friends'] = []
        db.register.insert_one(info)
        flash('Account created succesfully!', 'success')
        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user-info' in session:
        return redirect('/dashboard')
    if request.method == 'GET':
        return render_template('login.html')
    else:
        doc = {'email': request.form['login-email'], 'password': request.form['login-password']}
        found = db.register.find_one(doc)
        if found is None:
            flash('The email and password you entered did not match our records. Please double-check and try again.',
                  'danger')
            return redirect('/login')
        else:
            flash('Login Successful!', 'success')
            session['user-info'] = {'firstName': found['first-name'], 'lastName': found['last-name'],
                                    'email': found['email'], 'logintime': datetime.utcnow(), 'groups': found['groups'],
                                    'friends': found['friends']}
            return redirect('/dashboard')


@app.route('/dashboard', methods=['GET', 'POST'])
def default_dashboard():
    found = db.post.find_one()
    if found is None:
        stories = list(db.story.find().sort('time', -1))
        return render_template('dashboard.html', posts=[], stories=stories, selected='')
    return redirect('/dashboard/' + str(found['_id']))


@app.route('/dashboard/<post_id>', methods=['GET', 'POST'])
def dashboard(post_id):
    if request.method == 'GET':
        if 'user-info' not in session:
            flash('You need to be logged in to view this route', 'danger')
            return redirect('/login')
        posts = list(db.post.find().sort('time', -1))
        stories = list(db.story.find().sort('time', -1))
        print(stories)
        if len(post_id) != 24:
            return abort(404)
        found = db.post.find_one({'_id': ObjectId(post_id)})
        usernames = db.register.find({},{'first-name':1,'_id':1})
        found['_id']=str(found['_id'])
        session['selected_post']=found
        all_stories=[]
        return render_template('dashboard.html', posts=posts, stories=stories, usernames=usernames)
    else:
        information = {'user_email': session['user-info']['email'], 'time': datetime.utcnow(),
                       'user_entry': request.form['content']}
        db.entry.insert_one(information)
        return redirect('/dashboard')


@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    if request.method == 'GET':
        data = list(db.entry.find().sort('time', -1))
        print(request.args.get('search_bar'))
        search = request.args.get('search_bar')
        search = search.strip(" ")
        found_people = db.register.find({'first-name': search})
        return render_template('search_results.html', found_people=found_people, data=data, sizeofdata=len(data))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        firstname=request.args.get("firstname")
        all_posts_by_selected_user = db.post.find({'user_name': firstname})
        all_posts_by_selected_user_list=[]
        total_num_of_comments=0
        for each_post in all_posts_by_selected_user:
            all_posts_by_selected_user_list.append(each_post)
            total_num_of_comments+=len(each_post['comments'])
        total_num_of_posts=len(all_posts_by_selected_user_list)
        record=db.register.find_one({'first-name':firstname})
        comments = db.register.find_one({'first-name': firstname})
        return render_template('profile.html', record=record,total_num_of_comments=total_num_of_comments,total_num_of_posts=total_num_of_posts)




@app.route('/create_story', methods=['POST'])
def create_story():
    if request.method == 'POST':

        file = request.files["story-image"]
        filename = secure_filename(file.filename)
        name_of_file = filename.split(".")
        updated_filename = name_of_file[0] + session['user-info']['firstName'] + str(datetime.utcnow()) + "." + \
                           name_of_file[1]
        file.save(path.join(app.upload_folder, updated_filename))
        information = {'user_name': session['user-info']['firstName'], 'user_email': session['user-info']['email'],
                       'time': datetime.utcnow(),
                       'user_entry': request.form['story-text-content'], "story_image": updated_filename}
        db.story.insert_one(information)
        return redirect('/dashboard')


@app.route('/create_post', methods=['POST'])
def create_post():
    if request.method == 'POST':
        new = {'user': session['user-info']['firstName'], 'time_posted': datetime.utcnow(),
               'story': [{'type': 'text', 'content': 'Hello!'}, {'type': 'img',
                                                                 'content': 'https://images.unsplash.com/photo-1502759683299-cdcd6974244f?ixid=MnwxMjA3fDB8MHxzZWFyY2h8NXx8d2FsbHBhcGVyc3xlbnwwfHwwfHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60'}]}

        file = request.files["post-image"]
        filename = secure_filename(file.filename)
        name_of_file = filename.split(".")
        updated_filename = name_of_file[0] + session['user-info']['firstName'] + str(datetime.utcnow()) + "." + \
                           name_of_file[1]
        file.save(path.join(app.upload_folder, updated_filename))
        information = {'user_name': session['user-info']['firstName'], 'user_email': session['user-info']['email'],
                       'time': datetime.utcnow(),
                       'user_entry': request.form['post-text-content'],
                       'user_caption': request.form['post-text-caption'], "post_image": updated_filename,
                       "liked_by": [],
                       'comments': []}
        db.post.insert_one(information)
        return redirect('/dashboard')


@app.route('/like_post/<like>', methods=['GET', 'POST'])
def like_post(like):
    if request.method == 'GET':
        # information = {'user_name': session['user-info']['firstName'],'user_email': session['user-info']['email']}
        # db.post.insert_one(information)
        found = db.post.find_one({'_id': ObjectId(like)})
        likes = list(found['liked_by'])
        if session['user-info']['email'] in likes:
            likes.remove(session['user-info']['email'])
        else:
            likes.append(session['user-info']['email'])
        db.post.update_one(found, {'$set': {'liked_by': likes}})

        print(found)
        # if found is not None:
        #
        #     db.post.insert_one(information)
        return redirect('/dashboard')



@app.route('/comments/<post_id>', methods=['POST'])
def comments(post_id):
    # found = db.post.find_one({'_id': ObjectId(post_id)})
    user_comment = {'comment_name': session['user-info']['firstName'],
                    'comment_time': datetime.utcnow(),
                    'comment_text': request.form['comment']}

    db.post.update_one({'_id': ObjectId(post_id)}, {'$push': {'comments':user_comment}})
    print(user_comment)
    return redirect('/dashboard' + '/' + post_id)


@app.route('/delete/<id>', methods=['GET', 'POST'])
def delete(id):
    if request.method == 'GET':
        document = db.entry.find_one({'_id': ObjectId(id)})
        db.entry.delete_one(document)
        return redirect('/dashboard')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':

        return render_template('settings.html')
    else:
        firstName=request.form['first_name']
        lastName = request.form['last_name']
        bio = request.form['bio']
        profile_pic = request.files["profile-pic"]
        filename = secure_filename(profile_pic.filename)
        name_of_file = filename.split(".")
        updated_filename = name_of_file[0] + session['user-info']['firstName'] + str(datetime.utcnow()) + "." + \
                           name_of_file[1]
        profile_pic.save(path.join(app.upload_folder, updated_filename))
        db.register.update_one({'email':session['user-info']['email']}, {'$set': {'first-name': firstName,'last-name': lastName,'bio':bio,"profile_pic":updated_filename}},upsert=True)
        found = db.register.find_one({'email':session['user-info']['email']})
        session['user-info'] = {'firstName': found['first-name'], 'lastName': found['last-name'],
                                'email': found['email'], 'logintime': datetime.utcnow(), 'bio':found['bio'], "profile_pic":found['profile_pic']}
        print("hello")
        print(session['user-info'])
        return redirect('/dashboard')

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'GET':

        return render_template('test.html')

@app.route('/user/<name>', methods=['GET', 'POST'])
def user_name(name):
    return name


@app.route('/logout')
def logout():
    session.pop('user-info')
    return redirect('/login')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html')


if __name__ == '__main__':
    app.run(debug=True)
