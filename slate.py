from flask import Flask, render_template, request
from forms import SignUpForm, LoginForm, ChangePassword, CreateStory, UploadStory
from flask_mysqldb import MySQL
from flask_uploads import configure_uploads, IMAGES, UploadSet
import uuid
import datetime
from flask import session, redirect, url_for
import os
#from pymysql.cursors import DictCursor

app = Flask(__name__)

app.config['SECRET_KEY']='ashirshahparadnan'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'tigris52'
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
    print(data)

    headings = []

    for i in data:
        temp = [i[0], i[1]]
        headings.append(temp)

    auth_id = str(auth_id)

    msg = ''
    exist_stmt = "SELECT EXISTS(SELECT * FROM follow WHERE Author_ID = %s AND Follower_ID = %s )"
    data = (auth_id, session['user_id'])
    cursor = db.connection.cursor()
    cursor.execute(exist_stmt, data)
    exists = cursor.fetchall()
    exists = int(exists[0][0])
    if exists:
        msg = 'Followed'

    return render_template("author.html", name = name, 
                                        bio = bio, 
                                        pic = pic_path,
                                        auth_id = auth_id,
                                        headings = headings,
                                        message = msg)

#need to make this
@app.route("/blog/<blog_id>/<update>")
def blog_display(blog_id,update):
    cursor = db.connection.cursor()
    select_stmt = "SELECT Heading, Time_Published, Theme, Flag_ID, Auth_ID, Content FROM blogs WHERE Blog_ID=%s"
    blog_id = int(blog_id)
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
                        auth_id = auth_id, 
                        flag = flag_name, 
                        content = content,
                        blog_id = blog_id,
                        views = views,
                        applauds = applauds)

@app.route("/blog2/<blog_id>")
def blog_display2(blog_id):
    cursor = db.connection.cursor()
    select_stmt = "SELECT Heading, Time_Published, Theme, Flag_ID, Auth_ID, Content FROM blogs WHERE Blog_ID=%s"
    blog_id = int(blog_id)
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
    auth_id = int(flag_id)
    cursor = db.connection.cursor()
    cursor.execute(select_stmt, [flag_id])
    data = cursor.fetchall()

    flag_name = data[0][0]


    blog_id = int(blog_id)
    
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
                        auth_id = auth_id, 
                        flag = flag_name, 
                        content = content,
                        blog_id = blog_id,
                        views = views,
                        applauds = applauds)

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

        select_stmt = "SELECT Blog_ID FROM blogs WHERE Heading = %s AND Auth_ID=%s "
        cursor = db.connection.cursor()
        data_h = (form.title.data,auth_id)
        cursor.execute(select_stmt, data_h)
        data = cursor.fetchall()
        blog_id = int(data[0][0])


        insert_interactions = "INSERT INTO interactions (Blog_ID,Applauds, Views, Reports) VALUES (%s,%s,%s,%s)"
        data_interactions = (blog_id,0,0,0)
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

        select_stmt = "SELECT Blog_ID FROM blogs WHERE Heading = %s AND Auth_ID=%s"
        cursor = db.connection.cursor()
        data_h = (form.title.data,auth_id)
        cursor.execute(select_stmt, data_h)
        data = cursor.fetchall()
        print("data",data)
        blog_id = int(data[0][0])


        insert_interactions = "INSERT INTO interactions (Blog_ID,Applauds, Views, Reports) VALUES (%s,%s,%s,%s)"
        data_interactions = (blog_id,0,0,0)
        cursor.execute(insert_interactions,data_interactions)
        db.connection.commit()

        return render_template("create_blog.html", message = "Succesfully submitted!")
    return render_template("create_blog.html",form=form)

@app.route("/report/<blog_id>")
def report(blog_id):
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
    

    





if __name__ == "__main__":
    app.run(debug =False,host="0.0.0.0",port=5000)
