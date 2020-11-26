from flask import Flask, render_template
from forms import SignUpForm, LoginForm, ChangePassword, CreateStory
from flask_mysqldb import MySQL
from flask_uploads import configure_uploads, IMAGES, UploadSet
import uuid
import datetime
from flask import session, redirect, url_for
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


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def homepage():
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
    name1 = session['user']
    pic_path = session['pic']
    bio1 = session['bio']
    return render_template("author.html",name=name1,pic=pic_path,bio=bio1) #send author object here)

@app.route("/cm/<cm_id>")
def cm(cm_id):
    name1 = session['user']
    pic_path = session['pic']
    bio1 = session['bio']
    return render_template("cm.html",name=name1,pic=pic_path,bio=bio1) #send content moderator object here)

@app.route("/create/<auth_id>",methods=["POST","GET"])
def create(auth_id):
    form = CreateStory()
    if form.validate_on_submit():
        timestamp=datetime.datetime.now()
        insert_stmt= "INSERT INTO blogs (Heading, Time_Published, Theme, Auth_ID, Flag_ID, Content) VALUES (%s,%s,%s,%s,%s,%s)"
        #blog_name = str(form.title.data)+'.docx'
        #filepath = 'author_data/blogs/' + blog_name
        flag_id=1 # have to query database for flag id
        data = (form.title.data,timestamp,form.theme.data,auth_id,flag_id,form.content.data)
        cursor = db.connection.cursor()
        cursor.execute(insert_stmt,data)
        db.connection.commit()
        return render_template("create_blog.html", message = "Succesfully submitted!")
    return render_template("create_blog.html",form=form)




if __name__ == "__main__":
    app.run(debug =False,host="0.0.0.0",port=5000)
