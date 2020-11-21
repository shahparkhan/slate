from flask import Flask, render_template
from forms import SignUpForm, LoginForm
from flask_mysqldb import MySQL
from flask_uploads import configure_uploads, IMAGES, UploadSet
import uuid
from flask import session, redirect, url_for
#from pymysql.cursors import DictCursor

app = Flask(__name__)

app.config['SECRET_KEY']='ashirshahparadnan'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'slate'
# app.config['MySQL_CURSORCLASS'] = 'DictCursor'

app.config['UPLOADED_IMAGES_DEST'] = 'author_data/images'
images = UploadSet('images', IMAGES)
configure_uploads(app, images)

db = MySQL(app)

def generate_author_id(author_name):
    pass





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

        filename = images.save(form.image.data,name=unique_name)

        return render_template("signup.html", message = "Successfully signed up")
    return render_template("signup.html", form = form)

@app.route("/login", methods=["POST","GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        exist_stmt = "SELECT EXISTS(SELECT * FROM author WHERE Email = %s)"
        ''' if not in database, return error '''
        data = (form.email.data)
        cursor = db.connection.cursor()
        cursor.execute(exist_stmt, [form.email.data])
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
            statement = "SELECT Name, Password FROM author WHERE Email=%s"
            cursor.execute(statement,[user_id])
            data = cursor.fetchall()
            username = str(data[0][0])
            password = str(data[0][1])

            if (password != form.password.data):
                return render_template("login.html", form = form, message = "Incorrect Email or Password")

            session['user'] = username
            return render_template("login.html", message = "Successfully Logged In!")
    return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect(url_for('homepage', _scheme='https', _external=True))


if __name__ == "__main__":
    app.run(debug =False,host="0.0.0.0",port=5000)
