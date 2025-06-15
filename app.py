from flask import request, render_template, Flask, redirect, url_for, session
from flask_session import Session
import os
from datetime import datetime
from sqlite3 import connect
from hashlib import sha256

current_directory = os.getcwd()
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app) 

def collect_flairs():
    
    # connect to the database to retrieve a flairs
    connection = connect('database.db')
    statement = 'SELECT * FROM flairs'
    flairs = [x for x in connection.execute(statement)]
    connection.close()     
    
    return flairs

def check_admin():
    # for security:
    rank_= session.get('rank')
    if rank_ != "ADMIN":
        # restrict access only for admins
        return redirect(url_for('root'))

def separate_date(string):

    # this is a function to convert a datestamp into redable date
    string = str(string)
    date = string[-2:]
    month = int(string[-4:-2]) - 1
    year = string[::-1][4:][::-1]
    months = ['January', 'February', 'March',
              'April', 'May', 'June'
              'July', 'August', 'September',
              'October', 'November', 'December']
    return [year, months[month], date]



@app.route('/')
def root():

    # connect to the database to retrieve posts
    connection = connect('database.db')
    post_info = [x for x in connection.execute('SELECT * FROM posts')][::-1]
    connection.close()
    flairs = collect_flairs()   

    # validate to show three posts
    # print(post_info[0])
    post1, post2, post3 = None, None, None
    if len(post_info) >= 3:
        post1, post2, post3 = post_info[0], post_info[1], post_info[2]
    elif len(post_info) == 2:
        post1, post2 = post_info[0], post_info[1]
    elif len(post_info) == 1:
        post1 = post_info[0]
    # print(session.get('user_id'))
    # return the render template for the main page
    return render_template('index.html', post1=post1, post2=post2, 
                           post3=post3, user = session.get('user_id'),
                           rank = session.get('rank'), flairs = flairs)



@app.route('/find_post', methods = ['POST'])
def find_post(): 
    search_item = request.form['search']
    return redirect(url_for('find', search_item = search_item))



@app.route('/find/<search_item>')
def find(search_item):
    flairs = collect_flairs()   
    # connect to the database to retrieve posts
    connection = connect('database.db')
    post_info = [x for x in connection.execute('SELECT * FROM posts')][::-1]
    connection.close()

    indexes = []
    for post in post_info:
        # print(search_item.lower(), post[1].lower())
        if search_item.lower() in post[1].lower():
            indexes += [post]
    return render_template('find_post.html', indexes = indexes,
                            timestamp = separate_date(post_info[0][3]),
                            search_item = search_item,
                            flairs = flairs,
                            rank = session.get('rank'),
                            user = session.get('user_id'))



@app.route('/find_flair/<search_item>')
def find_flair(search_item):
    flairs = collect_flairs()  
    # connect to the database to retrieve posts
    connection = connect('database.db')
    post_info = [x for x in connection.execute('SELECT * FROM posts where post_flair = ?', (search_item,))][::-1]
    connection.close()

    return render_template('find_flair.html', indexes = post_info,
                            search_item = search_item,
                            flairs = flairs,
                            rank = session.get('rank'),
                            user = session.get('user_id'))



@app.route('/post/<int:Number>')
def show(Number):

    flairs = collect_flairs()  
    # connect to the database to retrieve a particular post
    connection = connect('database.db')
    statement = 'SELECT * FROM posts WHERE post_number = ?'
    post_info = [x for x in connection.execute(statement, (Number,))]
    connection.close()

    timestamp = separate_date(post_info[0][3]) # create the timestamp

    files = ""

    # this is to render the images (and videos I suppose)
    if post_info[0][5] != "":
        files = post_info[0][5].strip().split(';')
        files.pop()

    # return the render template for showing a particular post
    return render_template('show.html', post_info = post_info, 
                           files = files, timestamp = timestamp, user_id = session.get('user_id'),
                           flairs = flairs, rank = session.get('rank'),
                           user = session.get('user_id'), qty = len(files))



@app.route('/form')
def form():
    check_admin()
    flairs = collect_flairs()  
    # connect to the database to retrieve a flairs
    connection = connect('database.db')
    statement = 'SELECT * FROM flairs'
    flairs = [x for x in connection.execute(statement)]
    connection.close()        

    # redirect to main page
    return render_template('form.html', 
                            flairs = flairs,
                            rank = session.get('rank'),
                            user = session.get('user_id'))



@app.route('/edit_page/<int:Number>')
def edit_form(Number):
    check_admin()

    flairs = collect_flairs()  

    # connect to the database to retrieve a particular post
    connection = connect('database.db')
    statement = 'SELECT * FROM posts WHERE post_number = ?'
    post_info = [x for x in connection.execute(statement, (Number,))]
    connection.close()

    # return the render template for form edit
    return render_template('edit.html', post_info = post_info,
                            flairs = flairs,
                            rank = session.get('rank'),
                            user = session.get('user_id'))



@app.route('/show', methods = ['POST'])
def save():
    check_admin()

    # retrieve information from form
    title = request.form['title']
    flair = request.form['flair'] #changed
    connection = connect('database.db')
    if len([x for x in connection.execute('SELECT * FROM posts where post_flair = ?', (flair,))]) == 0:
        connection.execute("INSERT INTO flairs(flair) VALUES(?)", (flair,))
    description = request.form['description']
    f1 = request.files.getlist('file1')
    thumb = request.files['thumb']

    # connect to database to save a particular post without the image
    statement = '''INSERT INTO posts(title, description, date, post_flair) VALUES(?,?,?,?)''' #changed

    # changes dates and months to 2 digits if they are 1
    month_ = str(datetime.now().month) 
    month_ = '0' + month_ if len(month_) == 1 else month_
    date_= str(datetime.now().day)
    date_ = '0' + date_ if len(date_) == 1 else date_
    timestamp = int(str(datetime.now().year) + month_ + date_)
    connection.execute(statement, (title, description, timestamp, flair)) #changed

    # files are saved later because we want to separate files 
    # with the same names from multiple posts by adding post number

    # now its savin files time, we save the multiple files first 
    post_number = [x for x in connection.execute("SELECT rowid FROM posts")][-1][0]
    file_names = ''
    for i in f1:
        if i.filename != "":
            file_ = str(post_number) + "_" +i.filename
            #path = os.path.join('/home/eclipseyy/mysite/static', file_)
            path = os.path.join(f'{current_directory}/static', file_)
            file_names += file_ + ';'
            i.save(path)

    # then, we save the thumbnail
    if thumb.filename != "":
        thumbfile = str(post_number) + "_" + "thumbnail" + "_" +thumb.filename
        #path = os.path.join('/home/eclipseyy/mysite/static', file_)
        path = os.path.join(f'{current_directory}/static', thumbfile)
        thumb.save(path)
        statement = '''UPDATE posts SET files = ?, 
                    thumbnail = ? WHERE post_number = ?'''
        connection.execute( statement, (file_names, thumbfile, post_number))

    # commit to database the thumbnail and files
    else:
        statement = '''UPDATE posts SET files = ?, 
                    thumbnail = ? WHERE post_number = ?'''
        connection.execute( statement, (file_names, '', post_number))

    connection.commit()
    connection.close()

    # redirects to the main page
    return redirect(url_for('root'))




@app.route('/edit_/<int:Number>', methods = ['POST'])
def edit_(Number):

    # for security:
    rank_= session.get('rank')
    if rank_ != "ADMIN":
        # restrict access only for admins
        return redirect(url_for('root'))

    else:

        #retrieve information from form
        title = request.form['title']
        description = request.form['description']
        f1 = request.files.getlist('file1')
        # connect to database to save a particular post
        connection = connect('database.db')
        statement = '''UPDATE posts SET title = ?,
                    description = ? WHERE post_number = ?'''
        connection.execute(statement, (title, description, Number))
        connection.commit()

        # this is just saving the file, but we need 
        # to take note of the name of the old files
        file_names = ''
        statement = 'SELECT * FROM posts WHERE post_number = ?'
        old = [x for x in connection.execute(statement, (Number,))][0][5]
        for i in f1:
            if i.filename != "":
                file_ = str(Number) + "_" +i.filename
                path = os.path.join(f'{current_directory}\\static', file_)
                file_names += file_ + ';'
                i.save(path)

        # now, we delete the old files that we saved from earlier
        if file_names != "":
            if old != "":
                files = old.strip().split(';')
                files.pop()
                for x in files:
                    path = os.path.join(f'{current_directory}\\static', x)
                    try:
                        os.remove(path)
                    except:
                        pass
            statement = 'UPDATE posts SET files = ? WHERE post_number = ?'  
            connection.execute(statement, (file_names, Number))
            connection.commit()

        
        connection.close()

        # redirects to the edited post
        return redirect(url_for('show', Number = Number))


@app.route('/delete/<int:Number>')
def delete(Number):

    # for security:
    rank_= session.get('rank')

    if rank_ != "ADMIN":
        # restrict access only for admins
        return redirect(url_for('root'))

    # connect to the database to retrieve posts
    connection = connect('database.db')
    statement = 'SELECT * FROM posts WHERE post_number = ?'
    post_info = [x for x in connection.execute(statement, (Number,))]

    # redirect if there's no file in the first place
    if post_info == []:
        return redirect(url_for('root'))
    
    # delete old flair
    
    statement = 'SELECT post_flair FROM posts WHERE post_number = ?'
    search_item = [x for x in connection.execute(statement, (Number,))][0][0]
    # print(search_item, len([x for x in connection.execute(f'SELECT * FROM posts where post_flair = "{search_item}"')]))
    if int(len([x for x in connection.execute(f'SELECT * FROM posts where post_flair = "{search_item}"')])) == 1:
        statement = f'DELETE FROM flairs WHERE flair = "{search_item}"'
        # print(statement)
        connection.execute(statement)

    # now, we delete the old files
    files = ""
    if post_info[0][5] != "":
        files = post_info[0][5].strip().split(';')
        files.pop()
        for x in files:
            path = os.path.join(f'{current_directory}\\static', x)
            try:
                os.remove(path)
            except:
                pass

    # then, we delete the thumbnail     
    if post_info[0][6] != "":
        path = os.path.join(f'{current_directory}\\static', post_info[0][6])
        try:
            os.remove(path)
        except:
            pass

    connection.execute('DELETE FROM posts WHERE post_number = ?', (Number, ))
    connection.commit()
    connection.close()

    # redirects to main page
    return redirect(url_for('root'))



@app.route('/login')
def login():
    flairs = collect_flairs()
    if session.get('user_id'):
        return redirect(url_for('root'))
    return render_template('login.html', 
                            flairs = flairs,
                            rank = session.get('rank'))



@app.route('/login_success', methods = ['POST'])
def login_success():
    username = request.form['USERNAME']
    password = request.form['PASSWORD']
    if username == "" or password == "":
        return redirect(url_for('login')) 
    new = sha256()
    new.update(password.encode())

    # connect to database to retrieve user name
    connection = connect('database.db')
    hashed = connection.execute('SELECT password FROM user_table WHERE username = ?', (username, ))
    try:
        relieved = [x for x in hashed][0][0]
        # print(f"{[x for x in hashed]}")
        if relieved == new.hexdigest():
            session['user_id'] = username
            session['rank'] = [x for x in connection.execute('SELECT rank FROM user_table WHERE username = ?', (username, ))][0][0]
            return redirect(url_for('root'))
        else:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('rank', None)
    return redirect(url_for('root'))



    
@app.route('/flair', methods = ['POST'])
def flair():
    flair = request.form['flair']

    # connect to the database to ad flair
    connection = connect('database.db')
    connection.execute('INSERT INTO flairs VALUES (?)', (flair, ))
    connection.commit()
    connection.close()
    
    return redirect(url_for('root'))         

# the next few lines are for error handling purposes
@app.errorhandler(404)
def error_handling(e):
    return render_template('404.html')

@app.errorhandler(405)
def error_handling(e):
    return render_template('405.html')

@app.errorhandler(500)
def error_handling(e):
    return render_template('500.html')



if __name__ == "__main__":
    app.run()
