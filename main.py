from flask import *
from flask_moment import Moment
from datetime import datetime
from werkzeug.utils import secure_filename
from os import path
import random

app = Flask(__name__)
import pymongo
from bson.objectid import ObjectId

connection = "mongodb+srv://tvisha_r:Tvisha2006@cluster0.kwpmn.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
client = pymongo.MongoClient(connection)
#db = client["social-media"]
db = client["gunnhacks"]
app.debug = True
app.secret_key = 'sdfsdfs'
app.upload_folder = '/Users/tvisharanjan/PycharmProjects/social-media/static/user-uploads'
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
        print(session)
        if 'user-info' not in session:
            flash('You need to be logged in to view this route', 'danger')
            return redirect('/login')
        posts = list(db.post.find().sort('time', -1))
        print(posts)
        stories = list(db.story.find().sort('time', -1))
        if len(post_id) != 24:
            return abort(404)
        found = db.post.find_one({'_id': ObjectId(post_id)})
        found['_id']=str(found['_id'])
        session['selected_post']=found

        return render_template('dashboard.html', posts=posts, stories=stories)
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
        return render_template('profile.html')




@app.route('/create_story', methods=['POST'])
def create_story():
    if request.method == 'POST':
        new = {'user': session['user-info']['firstName'], 'time_posted': datetime.utcnow(),
               'story': [{'type': 'text', 'content': 'Hello!'}, {'type': 'img',
                                                                 'content': 'https://images.unsplash.com/photo-1502759683299-cdcd6974244f?ixid=MnwxMjA3fDB8MHxzZWFyY2h8NXx8d2FsbHBhcGVyc3xlbnwwfHwwfHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60'}]}
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
    found = db.post.find_one({'_id': ObjectId(post_id)})
    user_comment = {'comment_name': session['user-info']['firstName'],
                    'comment_time': datetime.utcnow(),
                    'comment_text': request.form['comment']}

    db.post.update_one({'_id': ObjectId(post_id)}, {'$push': {'comments':user_comment}})

    return redirect('/dashboard' + '/' + post_id)


@app.route('/delete/<id>', methods=['GET', 'POST'])
def delete(id):
    if request.method == 'GET':
        document = db.entry.find_one({'_id': ObjectId(id)})
        db.entry.delete_one(document)
        return redirect('/dashboard')

@app.route('/change_profile_pic', methods=['GET', 'POST'])
def change_profile_pic():
    if request.method == 'GET':

        return render_template('settings.html')


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
