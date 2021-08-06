from MySQLdb import cursors
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField, form,validators
from passlib.hash import sha256_crypt
from functools import wraps


#Kullanıcı Giriş Kontrol Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Lütfen Giriş Yapın","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kullanıcı Kayıt Formu 
class RegisterForm(Form):
   name = StringField("İsim Soyisim:",validators=[validators.InputRequired(message=("Size Nasıl Hitap Etmeliyiz?")),validators.Length(min = 4,max = 25)])
   username = StringField("Kullanıcı Adı:",validators=[validators.InputRequired(message=("Kullanıcı Adı Sizi Diğer Kullanıcılardan Ayırmamızı Sağlar")),validators.Length(min = 5,max = 35)])
   email = StringField("Email Adresi:",validators=[validators.InputRequired(message=("Kayıt Yapmak İçin Emailinizi Girmelisiniz")),validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")])
   password = PasswordField("Parola:",validators=[validators.InputRequired(message = "Lütfen bir parola belirleyin"),validators.Length(min = 8,max = 16,message=("Şifreniz 8 ila 16 Karaketer Arasında Olmalıdır.")),validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")])
   confirm = PasswordField("Parola Doğrula")
#Kullanıcı Giriş Formu
class LoginForm(Form):
   username=StringField("Kullanıcı Adı:")
   password=PasswordField("Parola:")
app=Flask(__name__)
app.secret_key="bloglisa"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "bloglisa"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
#Makale Form
class ArticleForm(Form):
    title=StringField("Makale Başlığı:",validators=[validators.length(min=5,max=40)])
    content=TextAreaField("Makale İçeriği:",validators=[validators.length(min=20,message="Daha Uzun Bir İçerik Girmelisiniz")])


mysql=MySQL(app)



@app.route("/")
def index():
   return render_template("index.html")

#about
@app.route("/about")
def about():
    return render_template("about.html")

#dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor= mysql.connection.cursor()
    sorgu="Select * From articles where author = %s"
    resault = cursor.execute(sorgu,(session["username"],))
    if resault>0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else: 
        return render_template("dashboard.html")

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where id=%s"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")
# Login İşlemi
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

       cursor = mysql.connection.cursor()

       sorgu = "Select * From users where username = %s"

       result = cursor.execute(sorgu,(username,))

       if result > 0:
           data = cursor.fetchone()
           real_password = data["password"]
           if sha256_crypt.verify(password_entered,real_password):
               flash("Başarıyla Giriş Yaptınız {}".format(username),"success")

               session["logged_in"] = True
               session["username"] = username
               session["logged_in"]=True
               session["username"]= username

               return redirect(url_for("index"))
           else:
               flash("Kullanıcı Adınızı Veya Parolanızı Yanlış Girdiniz!!","danger")
               return redirect(url_for("login")) 

       else:
           flash("Kullanıcı Adınızı Veya Parolanızı Yanlış Girdiniz!!","danger")
           return redirect(url_for("login"))

    
    return render_template("login.html",form = form)
#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#articles
@app.route("/article/<string:id>")
def detail(id):
   return "Article Id: "+id
#Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="Select * From articles where id =%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
        if result==0:
            flash("Bu İşleme Yetkiniz Yok","danger")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form=form)
            
    else:
        #Post Request
        form=ArticleForm(request.form)

        newTitle = form.title.data
        newContent= form.content.data

        sorgu2="Update articles Set title=%s,content=%s where id=%s"
        cursor= mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makaleniz Başarıyla Güncellendi","success")
        return redirect(url_for("dashboard"))




#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))



#Makale Ekle
@app.route("/addarticle",methods=["GET","POST"])
def addarticle(): 
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate:
        title=form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu="Insert Into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)
#Makale Sayfası 
@app.route("/articles")
def articles():
    cursor= mysql.connection.cursor()
    sorgu="Select * From articles"
    result =cursor.execute(sorgu)
    if result>0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
         return render_template("articles.html")

#Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("index"))
   else:
       keyword = request.form.get("keyword")
       cursor = mysql.connection.cursor()
       sorgu = "Select * from articles where title like '%" + keyword +"%'"
       result = cursor.execute(sorgu)
       if result == 0:
           flash("Aranan kelimeye uygun makale bulunamadı...","warning")
           return redirect(url_for("articles"))
       else:
           articles = cursor.fetchall()

           return render_template("articles.html",articles = articles)
#Profil Sayfası
@app.route("/profil/")
@login_required
def Profil():
    return render_template ("profil.html")

if __name__=="__main__":
   app.run(debug=True)