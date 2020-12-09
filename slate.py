from flask import Flask, render_template, request
from forms import SignUpForm, LoginForm, ChangePassword, CreateStory, UploadStory, Comment, EditName, EditEmail, EditBio, EditPic, EditPassword, AuthorSearch, ArticleSearch
from flask_mysqldb import MySQL
from flask_uploads import configure_uploads, IMAGES, UploadSet
import uuid
import datetime
from flask import session, redirect, url_for
import os
import re
#from pymysql.cursors import DictCursor

app = Flask(__name__)

app.config['SECRET_KEY']='ashirshahparadnan'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'slate'
# app.config['MySQL_CURSORCLASS'] = 'DictCursor'

app.config['UPLOADED_IMAGES_DEST'] = 'static/author_data/images'
#app.config['UPLOADED_BLOGS_DEST'] = 'static/author_data/blogs'


images = UploadSet('images', IMAGES)
configure_uploads(app, images)

# blogs = UploadSet('blogs',DOCUMENTS)
# configure_uploads(app, blogs)

db = MySQL(app)

def update_flags():
    cursor = db.connection.cursor()
    select_stmt = "SELECT * FROM flags"
    cursor.execute(select_stmt)
    themes = cursor.fetchall()
    
    with open("themes.txt", 'w') as f:  
        for theme in themes:
            write_this = str(theme[0]) + "\t" +  str(theme[1]) + "\n"
            f.write(write_this)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def homepage():
    update_flags()
    return render_template("home.html")

@app.route("/signup", methods=["POST", "GET"])
def signup():
    """View function for Showing Details of Each Author.""" 
    form = SignUpForm()
    if form.validate_on_submit():
        '''GENERATE unique filename'''
        try:
            unique_name = str(uuid.uuid4())+'.jpeg'
            filepath = 'author_data/images/' + unique_name
            '''INSERT to database'''
            insert_stmt = "INSERT INTO author (Name, Password, Biography, Picture, Email) VALUES (%s,%s,%s,%s,%s)"
            data = (form.full_name.data,form.password.data,form.bio.data,filepath,form.email.data)
            cursor = db.connection.cursor()
            cursor.execute(insert_stmt,data)
            db.connection.commit()
        except:

            return render_template("signup.html", form = form, message = "Email ID already taken")

        _ = images.save(form.image.data,name=unique_name)

        return render_template("signup.html", message = "Successfully signed up")
    return render_template("signup.html", form = form)

@app.route("/login", methods=["POST","GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        exist_stmt_auth = "SELECT EXISTS(SELECT * FROM author WHERE Email = %s)"
        exist_stmt_CM = "SELECT EXISTS(SELECT * FROM `content moderator` WHERE Email = %s)"
        ''' if not in database, return error '''
        data = (form.email.data)
        login_as = form.login_as.data
        cursor = db.connection.cursor()
        if (login_as == "Author"):
            cursor.execute(exist_stmt_auth, [form.email.data])
        elif (login_as == "Content Moderator"):
            cursor.execute(exist_stmt_CM, [form.email.data])
        
        # RETURNS TUPLE OF TUPLE FOR SOME REASON
        exists = cursor.fetchall()
        exists = int(exists[0][0])

        if not exists:
            return render_template("login.html", form = form, message = "Incorrect Email or Password")
        # db.connection.commit()
        # user = next((user for user in users if user["email"] == form.email.data and user["password"] == form.password.data), None)
        # if user is None:
        #     return render_template("login.html", form = form, message = "Wrong Credentials. Please Try Again.")
        else:
            user_id = form.email.data
            if (login_as == "Author"):
                statement = "SELECT Name, Password, Auth_ID, Biography, Picture FROM author WHERE Email=%s"
            elif (login_as == "Content Moderator"):
                statement = "SELECT Name, Password, CM_ID, Biography, Picture FROM `content moderator` WHERE Email=%s"
            cursor.execute(statement,[user_id])
            data = cursor.fetchall()
            username = str(data[0][0])
            password = str(data[0][1])
            user_id = str(data[0][2])
            bio = str(data[0][3])
            pic = str(data[0][4])

            if (password != form.password.data):
                return render_template("login.html", form = form, message = "Incorrect Email or Password")
            #add tuple in session['user'] for author and CM
            session['user'] = username
            session['user_id'] = user_id
            session['pic'] = pic
            session['bio'] = bio
            if (login_as == "Author"):
                session['login_as'] = "Author"
            elif ( login_as == "Content Moderator" ):
                session['login_as'] = "Content Moderator"
            return render_template("login.html", message = "Successfully Logged In!")
            #have to send author.html the author details that just logged in.

    return render_template("login.html", form = form)

@app.route("/change_password", methods=["POST","GET"])
def change_password():
    form = ChangePassword()
    if form.validate_on_submit():
        exist_stmt_auth = "SELECT EXISTS(SELECT * FROM author WHERE Email=%s)"
        cursor = db.connection.cursor()
        cursor.execute(exist_stmt_auth, [form.email.data])
        exists = cursor.fetchall()
        exists = int(exists[0][0])

        if not exists:
            return render_template("change_password.html", form = form, message = "Email not found!")
        else:
            print("****************")
            print("EMAIL =",form.email.data,"PASSWORD =", form.password.data)
            print("****************")
            reset_pswd = "UPDATE author SET Password=%s WHERE Email=%s"
            cursor = db.connection.cursor()
            cursor.execute(reset_pswd, [form.password.data,form.email.data])
            db.connection.commit()
            _ = cursor.fetchall()
            return render_template("change_password.html", form = form, message = "Password changed successfully!")
    return render_template("change_password.html", form = form)


@app.route("/logout")
def logout():
    if 'user' in session:
        session.pop('user')
        session.pop('user_id')
        session.pop('pic')
        session.pop('bio')

    return redirect(url_for('homepage'))

@app.route("/author/<auth_id>")
def author(auth_id):
    cursor = db.connection.cursor()

    select_stmt = "SELECT Name, Picture, Biography FROM author WHERE Auth_ID=%s"
    auth_id = int(auth_id)
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [auth_id])
    data = cursor.fetchall()

    name = data[0][0]
    pic_path = data[0][1]
    bio = data[0][2]

    select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Auth_ID=%s"
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [auth_id])
    data = cursor.fetchall()

    headings = []

    for i in data:
        temp = [i[0], i[1]]
        headings.append(temp)

    auth_id = str(auth_id)

    msg = ''
    if ( 'user_id' in session):
        exist_stmt = "SELECT EXISTS(SELECT * FROM follow WHERE Author_ID = %s AND Follower_ID = %s )"
        data = (auth_id, session['user_id'])
        cursor = db.connection.cursor()
        cursor.execute(exist_stmt, data)
        exists = cursor.fetchall()
        exists = int(exists[0][0])
        if exists:
            msg = 'Followed'

    return render_template("Author.html", name = name, 
                                        bio = bio, 
                                        pic = pic_path,
                                        auth_id = auth_id,
                                        headings = headings,
                                        message = msg)

#need to make this
@app.route("/blog/<blog_id>/<update>", methods=["POST","GET"])
def blog_display(blog_id,update):

    form = Comment()
    cursor = db.connection.cursor()
    blog_id = int(blog_id)

    if form.validate_on_submit():
        time = datetime.datetime.now()
        insert_stmt = "INSERT INTO comments (Blog_ID, Auth_ID, Comment, Time_Posted, Author) VALUES (%s,%s,%s,%s,%s)"
        data = (blog_id,session['user_id'],form.comment.data, time, session['user'])
        cursor = db.connection.cursor()
        cursor.execute(insert_stmt,data)
        db.connection.commit()

    select_stmt = "SELECT Heading, Time_Published, Theme, Flag_ID, Auth_ID, Content FROM blogs WHERE Blog_ID=%s"
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [blog_id])
    data = cursor.fetchall()
    heading = data[0][0]
    time_published = data[0][1].strftime("%d-%b-%Y (%H:%M:%S)")
    theme = data[0][2]
    flag_id = data[0][3]
    auth_id = data[0][4]
    content = data[0][5]

    select_stmt = "SELECT Name FROM author WHERE Auth_ID=%s"
    auth_id = int(auth_id)
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [auth_id])
    data = cursor.fetchall()

    auth_name = data[0][0]

    select_stmt = "SELECT Flag FROM flags WHERE Flag_ID=%s"
    flag_id = int(flag_id)
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [flag_id])
    data = cursor.fetchall()

    flag_name = data[0][0]

    select_stmt = "SELECT Comment, Author, Time_Posted, Auth_ID FROM comments WHERE Blog_ID=%s"
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [blog_id])
    data = cursor.fetchall()
    temp_comments = list(data)
    comments = []

    for comment in temp_comments:
        temp_list = list(comment)
        temp_list[2] = temp_list[2].strftime("%d-%b-%Y (%H:%M:%S)")
        temp_tuple = tuple(temp_list)
        comments.append(temp_tuple)

    comments = tuple(comments)

    blog_id = int(blog_id)

    
    update = int(update)
    if (update == 1):
        update_views = "UPDATE interactions SET Views= Views + 1 WHERE Blog_ID=%s"
        cursor = db.connection.cursor()
        cursor.execute(update_views,[blog_id])
        db.connection.commit()

    select_stmt = "SELECT Applauds,Views FROM interactions WHERE Blog_ID=%s"
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [blog_id])
    data = cursor.fetchall()
    applauds = int(data[0][0])
    views = int(data[0][1])


    return render_template("blog.html", 
                        heading = heading, 
                        time_published = time_published, 
                        theme = theme, 
                        author = auth_name, 
                        flag = flag_name, 
                        content = content,
                        form = form,
                        comments = comments,
                        blog_id = blog_id,
                        views = views,
                        applauds = applauds,
                        auth_id = auth_id)


@app.route("/follow/<follower>/<following>")
def follow(follower, following):
    exist_stmt = "SELECT EXISTS(SELECT * FROM follow WHERE Author_ID = %s AND Follower_ID = %s )"
    data = (following, follower)
    cursor = db.connection.cursor()
    cursor.execute(exist_stmt, data)
    exists = cursor.fetchall()
    exists = int(exists[0][0])
    if not exists:
        insert_follow = "INSERT INTO follow (Author_ID, Follower_ID) VALUES (%s,%s)"
        data_follow = (following,follower)
        cursor = db.connection.cursor()
        cursor.execute(insert_follow,data_follow)
        db.connection.commit()
    return render_template("author.html", message = 'You are now following this author!')

@app.route("/unfollow/<follower>/<following>")
def unfollow(follower, following):
    delete_stmt = 'DELETE FROM follow WHERE Follower_id = %s AND Author_ID = %s'
    cursor = db.connection.cursor()
    data = (follower,following)
    cursor.execute(delete_stmt,data)
    db.connection.commit()
    return render_template("author.html", message = 'You are not following this author anymore.')


@app.route("/followers/<auth_id>")
def display_followers(auth_id):
    search_stmt = "SELECT Follower_ID FROM follow WHERE Author_ID=%s"
    cursor = db.connection.cursor()
    cursor.execute(search_stmt,[auth_id])
    data = cursor.fetchall()
    auth_ids = []
    for i in data:
        temp = i[0]
        auth_ids.append(temp)

    authors = []
    #now select the names of the authors who are your followers and display them
    select_author = "SELECT Name FROM author WHERE Auth_ID=%s"
    cursor = db.connection.cursor()
    for i in auth_ids:
        cursor.execute(select_author,[i])
        data = cursor.fetchall()
        authors.append([data[0][0],i])

    return render_template ("followers.html",authors = authors)




@app.route("/following/<auth_id>")
def display_following(auth_id):
    search_stmt = "SELECT Author_ID FROM follow WHERE Follower_ID=%s"
    cursor = db.connection.cursor()
    cursor.execute(search_stmt,[auth_id])
    data = cursor.fetchall()
    auth_ids = []
    for i in data:
        temp = i[0]
        auth_ids.append(temp)

    authors = []
    #now select the names of the authors who are you're following and display them
    select_author = "SELECT Name FROM author WHERE Auth_ID=%s"
    cursor = db.connection.cursor()
    for i in auth_ids:
        cursor.execute(select_author,[i])
        data = cursor.fetchall()
        authors.append([data[0][0],i])

    return render_template ("following.html",authors = authors)





@app.route("/cm/<cm_id>")
def cm(cm_id):
    name1 = session['user']
    pic_path = session['pic']
    bio1 = session['bio']
    return render_template("cm.html",name=name1,pic=pic_path,bio=bio1) #send content moderator object here)

@app.route("/upload_blog/<auth_id>", methods=['POST', 'GET'])
def upload_blog(auth_id):
    cursor = db.connection.cursor()
    form = UploadStory()
    if form.validate_on_submit():
        timestamp=datetime.datetime.now()
        f = request.files['doc']
        name = f.filename
        f.save(name)
        fin = open(name)
        filedata = fin.readlines()
        filedata = '\n'.join(filedata)
        fin.close()
        os.remove(name)

        insert_stmt= "INSERT INTO blogs (Heading, Time_Published, Theme, Auth_ID, Flag_ID, Content) VALUES (%s,%s,%s,%s,%s,%s)"
        flag_id = 1
        data = (form.title.data,timestamp,form.theme.data,auth_id,flag_id,filedata)
        cursor.execute(insert_stmt,data)
        db.connection.commit()

        select_stmt = "SELECT Blog_ID FROM blogs WHERE Auth_ID=%s AND Heading=%s"
        data = (int(auth_id), form.title.data)
        cursor.execute(select_stmt, data)
        d = cursor.fetchall()
        blog_id = int(d[0][0])

        insert_interactions = "INSERT INTO interactions (Blog_ID, Applauds, Views, Reports) VALUES (%s,%s,%s,%s)"
        data_interactions = (blog_id, 0,0,0)
        cursor.execute(insert_interactions,data_interactions)
        db.connection.commit()

        
        return render_template("upload_blog.html", message="Success!")
    return render_template("upload_blog.html", form=form)


@app.route("/create/<auth_id>",methods=["POST","GET"])
def create(auth_id):
    cursor = db.connection.cursor()
    form = CreateStory()
    if form.validate_on_submit():
        timestamp=datetime.datetime.now()
        insert_stmt= "INSERT INTO blogs (Heading, Time_Published, Theme, Auth_ID, Flag_ID, Content) VALUES (%s,%s,%s,%s,%s,%s)"
        #blog_name = str(form.title.data)+'.docx'
        #filepath = 'author_data/blogs/' + blog_name
        # have to query database for flag id
        flag_id = 1
        data = (form.title.data,timestamp,form.theme.data,auth_id,flag_id,form.content.data)
        cursor.execute(insert_stmt,data)
        db.connection.commit()

        select_stmt = "SELECT Blog_ID FROM blogs WHERE Auth_ID=%s AND Heading=%s"
        data = (int(auth_id), form.title.data)
        cursor.execute(select_stmt, data)
        d = cursor.fetchall()
        blog_id = int(d[0][0])

        insert_interactions = "INSERT INTO interactions (Blog_ID, Applauds, Views, Reports) VALUES (%s,%s,%s,%s)"
        data_interactions = (blog_id, 0,0,0)
        cursor.execute(insert_interactions,data_interactions)
        db.connection.commit()

        return render_template("create_blog.html", message = "Succesfully submitted!")
    return render_template("create_blog.html",form=form)

@app.route("/report/<blog_id>")
def report(blog_id):
    if 'user' not in session:
        return redirect(url_for('blog_display',blog_id= blog_id,update = 0))

    auth_id = int (session['user_id'])
    blog_id = int( blog_id )
    exist_stmt = "SELECT EXISTS(SELECT * FROM reports WHERE Auth_ID = %s AND Blog_ID = %s )"
    data = (auth_id, blog_id)
    cursor = db.connection.cursor()
    cursor.execute(exist_stmt, data)
    exists = cursor.fetchall()
    exists = int(exists[0][0])
    if not exists:
        insert_stmt = "INSERT INTO reports (Auth_ID, Blog_ID) VALUES (%s,%s)"
        data = (auth_id,blog_id)
        cursor = db.connection.cursor()
        cursor.execute(insert_stmt,data)
        db.connection.commit()

        update_stmt = "UPDATE interactions SET Reports = Reports + 1 WHERE Blog_ID = %s"
        cursor = db.connection.cursor()
        cursor.execute(update_stmt,[blog_id])
        db.connection.commit()

    return redirect(url_for('blog_display',blog_id= blog_id,update = 0))

@app.route("/applaud/<blog_id>")
def applaud(blog_id):

    if 'user' not in session:
        return redirect(url_for('blog_display',blog_id= blog_id,update = 0))

    auth_id = int (session['user_id'])
    blog_id = int( blog_id )
    exist_stmt = "SELECT EXISTS(SELECT * FROM applauds WHERE Auth_ID = %s AND Blog_ID = %s )"
    data = (auth_id, blog_id)
    cursor = db.connection.cursor()
    cursor.execute(exist_stmt, data)
    exists = cursor.fetchall()
    exists = int(exists[0][0])
    if not exists:
        insert_stmt = "INSERT INTO applauds (Auth_ID, Blog_ID) VALUES (%s,%s)"
        data = (auth_id,blog_id)
        cursor = db.connection.cursor()
        cursor.execute(insert_stmt,data)
        db.connection.commit()

        update_stmt = "UPDATE interactions SET Applauds = Applauds + 1 WHERE Blog_ID = %s"
        cursor = db.connection.cursor()
        cursor.execute(update_stmt,[blog_id])
        db.connection.commit()

    return redirect(url_for('blog_display',blog_id= blog_id,update = 0))


@app.route("/delete_blog/<blog_id>", methods=["POST","GET"])
def delete_blog(blog_id):
    cursor = db.connection.cursor()
    try:
        pic_path = session['pic']
        select_stmt = "SELECT Auth_ID FROM blogs WHERE Blog_ID=%s"
        delete_stmt = "DELETE FROM blogs WHERE Blog_ID = %s"
        cursor.execute(select_stmt, [blog_id])
        auth_id = int(cursor.fetchall()[0][0])
        # deleting blog
        cursor.execute(delete_stmt, [blog_id])
        db.connection.commit()
        # deletion done
        select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Auth_ID=%s"
        cursor.execute(select_stmt, [auth_id])

        data = cursor.fetchall()
        headings = []

        for i in data:
            temp = [i[0], i[1]]
            headings.append(temp)

        return redirect(url_for('author',auth_id= auth_id))
    except:
        return "Failed!"

@app.route('/delete_auth/<auth_id>', methods=["POST","GET"])
def delete_auth(auth_id):
    cursor = db.connection.cursor()
    try:
        delete_stmt = 'DELETE FROM author WHERE Auth_id = %s'
        cursor.execute(delete_stmt,[auth_id])
        db.connection.commit()
        return redirect(url_for('logout'))
    except:
        return "Failed!"

@app.route('/edit_profile/<auth_id>', methods=["POST","GET"])
def edit_profile(auth_id):
   return render_template("edit_profile.html")

@app.route('/edit_name/<auth_id>', methods=["POST","GET"])
def edit_name(auth_id):
    form = EditName()
    if form.validate_on_submit():
        try:
            name = form.name.data
            update_stmt = "UPDATE author SET Name=%s WHERE Auth_ID=%s"
            cursor = db.connection.cursor()
            cursor.execute(update_stmt,[name, auth_id])
            db.connection.commit()
            session['user'] = name
            return redirect(url_for('edit_profile',auth_id=auth_id))
        except:
            return "Failed!"
    return render_template("edit_name.html",form=form)

@app.route('/edit_email/<auth_id>', methods=["POST","GET"])
def edit_email(auth_id):
    form = EditEmail()
    if form.validate_on_submit():
        try:
            email = form.email.data
            update_stmt = "UPDATE author SET Email=%s WHERE Auth_ID=%s"
            search_stmt = "SELECT Email FROM author WHERE Auth_ID=%s"
            cursor = db.connection.cursor()
            cursor.execute(search_stmt,[auth_id])
            data = cursor.fetchall()[0][0]
            print("DATA", data)
            if data == email:
                print("Email same")
                return render_template("edit_email.html", form=form, message="Email can not be the same as previous email")
            cursor.execute(update_stmt,[email, auth_id])
            db.connection.commit()
            return render_template('edit_email.html',form=form, message="Success")
        except:
            print("Email already exists!")
            return render_template('edit_email.html',form=form, message="Email ID already taken")
    return render_template("edit_email.html", form=form, message= "test")

@app.route('/edit_password/<auth_id>', methods=["POST","GET"])
def edit_password(auth_id):
    form = EditPassword()
    if form.validate_on_submit():
        try:
            password = form.password.data
            print("password", password)
            update_stmt = "UPDATE author SET Password=%s WHERE Auth_ID=%s"
            cursor = db.connection.cursor()
            cursor.execute(update_stmt,[password, auth_id])
            db.connection.commit()
            return redirect(url_for('edit_profile', auth_id=auth_id))
        except:
            print("failed")
            return render_template('edit_password.html',form=form, message="Failed")
    return render_template("edit_password.html",form=form)



@app.route('/edit_bio/<auth_id>', methods=["POST","GET"])
def edit_bio(auth_id):
    form = EditBio()
    if form.validate_on_submit():
        bio = form.bio.data
        update_stmt = "UPDATE author SET Biography=%s WHERE Auth_ID=%s"
        cursor = db.connection.cursor()
        cursor.execute(update_stmt,[bio, auth_id])
        db.connection.commit()
        return redirect(url_for('edit_profile', auth_id=auth_id))
    return render_template("edit_bio.html",form=form)

@app.route('/edit_pic/<auth_id>', methods=["POST","GET"])
def edit_pic(auth_id):
    form = EditPic()
    cursor = db.connection.cursor()
    if form.validate_on_submit():
        '''DELETING OLD FILE'''
        search_stmt = "SELECT Picture FROM author WHERE Auth_ID=%s"
        cursor.execute(search_stmt,[auth_id])
        data = cursor.fetchall()[0][0]
        cwd = os.getcwd() + '/static/' + data
        print("FILE NAME", cwd)
        os.remove(cwd)


        '''GENERATE unique filename'''
        try:
            unique_name = str(uuid.uuid4())+'.jpeg'
            filepath = 'author_data/images/' + unique_name
            '''INSERT to database'''
            insert_stmt = "UPDATE author SET Picture=%s WHERE Auth_ID=%s"
            data = (filepath,auth_id)
           
            cursor.execute(insert_stmt,data)
            db.connection.commit()
        except:
            return render_template("edit_pic.html", form = form, message = "Could not upload Image")
        _ = images.save(form.image.data,name=unique_name)
        print("return success",filepath, unique_name)
        return render_template("edit_profile.html", message = "Success")
    return render_template("edit_pic.html", form = form)


def email_check(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

    if(re.search(regex,email)):  
        return True  
          
    else:  
        return False  
      

@app.route('/search_author', methods=["POST","GET"])
def search_author():
    form = AuthorSearch()
    cursor = db.connection.cursor()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data

        if ( (name == "") and (email == "") ):
            message = 'Please enter text in the fields and then hit search'
            return render_template("search_author.html", form = form, message = message)

        elif ( name == ""):
            if ( (email_check(email) == False) ):
                message = 'Either enter a valid email address, or leave the field empty'
                return render_template("search_author.html", form = form, message = message)

            else:
                search_stmt = "SELECT Name, Auth_ID FROM author WHERE Email = %s"
                cursor.execute(search_stmt,[email])
                data = cursor.fetchall()

                if len(data) == 0:
                    message = 'No search results found :('
                    return render_template("search_author.html", form = form, message = message)

                authors = []

                for i in data:
                    temp = [i[0], i[1]]
                    authors.append(temp)

                return render_template("results_author.html", authors = authors)            

        elif (email == ""):
            search_stmt = "SELECT Name, Auth_ID FROM author WHERE Name LIKE %s"
            like_stmt = '%' + name + '%'
            cursor.execute(search_stmt,[like_stmt])
            data = cursor.fetchall()

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_author.html", form = form, message = message)

            authors = []

            for i in data:
                temp = [i[0], i[1]]
                authors.append(temp)

            return render_template("results_author.html", authors = authors)

        else:
            search_stmt = "SELECT Name, Auth_ID FROM author WHERE Name = %s AND Email = %s"
            cursor.execute(search_stmt,[name, email])
            data = cursor.fetchall()

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_author.html", form = form, message = message)

            authors = []

            for i in data:
                temp = [i[0], i[1]]
                authors.append(temp)

            return render_template("results_author.html", authors = authors)

    return render_template("search_author.html", form = form)


@app.route('/search_article', methods=["POST","GET"])
def search_article():
    form = ArticleSearch()
    cursor = db.connection.cursor()

    if form.validate_on_submit():
        title = form.title.data
        author = form.author.data
        theme = form.theme.data

        print(title, "-", author, "-", theme)
        if ( (title == "") and (author == "") and (theme == "-") ):
            message = 'Please enter text in the fields and then hit search'
            return render_template("search_article.html", form = form, message = message)

        elif ( (title == "") and (author == "") ):

            select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Theme = %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [theme])
            data = cursor.fetchall()

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            items = []

            for i in data:
                temp = [i[0], i[1]]
                items.append(temp)

            message = "Theme: " + theme

            items = [[message, items]]

            return render_template("results_article.html", items = items)

        elif ( (author == "") and (theme == "-") ):

            like_stmt = '%' + title + '%'

            select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Heading LIKE %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [like_stmt])
            data = cursor.fetchall()

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            items = []

            for i in data:
                temp = [i[0], i[1]]
                items.append(temp)

            message = "Title: " + title

            items = [[message, items]]


            return render_template("results_article.html", items = items)

        elif ( (theme == "-") and (title == "") ):

            like_stmt = '%' + author + '%'

            select_stmt = "SELECT Auth_ID, Name FROM author WHERE Name LIKE %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [like_stmt])
            data = cursor.fetchall()

            print(data, data[0], data[0][0], data[0][1])

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            num_authors = len(data)


            items = []

            for i in range(num_authors):

                auth_id = int(data[i][0])
                auth_name = str(data[i][1])

                select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Auth_ID = %s"
                cursor = db.connection.cursor()
                cursor.execute(select_stmt, [auth_id])
                data1 = cursor.fetchall()

                if len(data1) == 0:
                    continue

                sub_items = []

                for i in data1:
                    temp = [i[0], i[1]]
                    sub_items.append(temp)

                message = "Author: " + auth_name

                items.append([message, sub_items])

            if len(items) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)
            
            return render_template("results_article.html", items = items)

        elif ( (theme == "-") ):

            like_stmt = '%' + author + '%'

            select_stmt = "SELECT Auth_ID, Name FROM author WHERE Name LIKE %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [like_stmt])
            data = cursor.fetchall()

            print(data, data[0], data[0][0], data[0][1])

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            num_authors = len(data)

            items = []

            for i in range(num_authors):

                auth_id = int(data[i][0])
                auth_name = str(data[i][1])

                like_stmt = '%' + title + '%'

                select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Auth_ID = %s AND Heading LIKE %s"
                cursor = db.connection.cursor()
                cursor.execute(select_stmt, [auth_id, like_stmt])
                data1 = cursor.fetchall()

                if len(data1) == 0:
                    continue

                sub_items = []

                for i in data1:
                    temp = [i[0], i[1]]
                    sub_items.append(temp)

                message = "Author: " + auth_name + "\nTitle: " + title

                items.append([message, sub_items])

            if len(items) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)
            
            return render_template("results_article.html", items = items)

        elif ( (title == "") ):

            like_stmt = '%' + author + '%'

            select_stmt = "SELECT Auth_ID, Name FROM author WHERE Name LIKE %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [like_stmt])
            data = cursor.fetchall()

            print(data, data[0], data[0][0], data[0][1])

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            num_authors = len(data)

            items = []

            for i in range(num_authors):

                auth_id = int(data[i][0])
                auth_name = str(data[i][1])

                select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Auth_ID = %s AND Theme = %s"
                cursor = db.connection.cursor()
                cursor.execute(select_stmt, [auth_id, theme])
                data1 = cursor.fetchall()

                if i == 2:
                    print(data1)

                if len(data1) == 0:
                    continue

                sub_items = []

                for i in data1:
                    temp = [i[0], i[1]]
                    sub_items.append(temp)

                message = "Author: " + auth_name + "\nTheme: " + theme

                items.append([message, sub_items])

            if len(items) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)
            
            return render_template("results_article.html", items = items)

        elif ( (author == "") ):

            like_stmt = "%" + title + "%"

            select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Theme = %s AND Heading LIKE %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [theme, like_stmt])
            data = cursor.fetchall()

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            items = []

            for i in data:
                temp = [i[0], i[1]]
                items.append(temp)

            message = "Theme: " + theme + "\nTitle: " + title

            items = [[message, items]]

            return render_template("results_article.html", items = items)

        else:

            like_stmt = '%' + author + '%'

            select_stmt = "SELECT Auth_ID, Name FROM author WHERE Name LIKE %s"
            cursor = db.connection.cursor()
            cursor.execute(select_stmt, [like_stmt])
            data = cursor.fetchall()

            print(data, data[0], data[0][0], data[0][1])

            if len(data) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)

            num_authors = len(data)

            items = []

            for i in range(num_authors):

                auth_id = int(data[i][0])
                auth_name = str(data[i][1])

                like_stmt = '%' + title + '%'

                select_stmt = "SELECT Heading, Blog_ID FROM blogs WHERE Auth_ID = %s AND Theme = %s AND Heading LIKE %s"
                cursor = db.connection.cursor()
                cursor.execute(select_stmt, [auth_id, theme, like_stmt])
                data1 = cursor.fetchall()

                if i == 2:
                    print(data1)

                if len(data1) == 0:
                    continue

                sub_items = []

                for i in data1:
                    temp = [i[0], i[1]]
                    sub_items.append(temp)

                message = "Author: " + auth_name + "\nTheme: " + theme + "\nTitle: " + title

                items.append([message, sub_items])

            if len(items) == 0:
                message = 'No search results found :('
                return render_template("search_article.html", form = form, message = message)
            
            return render_template("results_article.html", items = items)


    return render_template("search_article.html", form = form)

@app.route('/trending/<trend>', methods=["POST","GET"])
def trending(trend):

    cursor = db.connection.cursor()
    
    trend = str(trend)

    if trend == "views":
        select_stmt = "SELECT Heading, Blog_ID, Views FROM blogs NATURAL JOIN interactions ORDER BY Views DESC LIMIT 10"
        cursor.execute(select_stmt)
        data = cursor.fetchall()

        items = []

        for i in data:
            temp = [i[0], i[1], i[2]]
            items.append(temp)

        message = "Top 10 Views"
        trend = "Views"
        return render_template("trending.html", items = items, message = message, trend = trend)

    elif trend == "applauds":
        select_stmt = "SELECT Heading, Blog_ID, Applauds FROM blogs NATURAL JOIN interactions ORDER BY Applauds DESC LIMIT 10"
        cursor.execute(select_stmt)
        data = cursor.fetchall()

        items = []

        for i in data:
            temp = [i[0], i[1], i[2]]
            items.append(temp)

        message = "Top 10 Applauds"
        trend = "Applauds"

        return render_template("trending.html", items = items, message = message, trend = trend)

    else:

        return render_template("home.html")


if __name__ == "__main__":
    app.run()
