from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_mysqldb import MySQL
from flask_session import Session
from otp import genotp
from cmail import sendmail
import random
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
import os
app=Flask(__name__)
app.secret_key="27@Messanger"
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Admin'
app.config['MYSQL_DB']='Project'
Session(app)
mysql=MySQL(app)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/index/<id>')
def chat(id):
    cursor=mysql.connection.cursor()
    #cursor=mysql.get_db().cursor()
    cursor.execute('SELECT following from friends where followers=%s',[id])
    data=cursor.fetchall()

    return render_template('chat.html',id=id,data=data)


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=="POST":
        id=request.form['id']
        first_name=request.form['first_name']
        last_name=request.form['last_name']
        email=request.form['email']
        password=request.form['password']
        bio=request.form['bio']
        #cursor=mysql.get_db().cursor()
        cursor=mysql.connection.cursor()
        cursor.execute("select id from users")
        data=cursor.fetchall()
        if (id,) in data:
            flash('already id exists')
            return render_template('Signup.html')
        else:
            cursor.execute("select email from users")
            edata=cursor.fetchall()
            otp=genotp()
            subject='Thanks for registering to the application'
            body=f'Use this otp to register {otp}'
            sendmail(email,subject,body)
            return render_template('otp.html',otp=otp,id=id,first_name=first_name,last_name=last_name,email=email,password=password,bio=bio)
        # cursor.execute('insert into users(id,Frist_Name,Last_Name,Email,Password) values(%s,%s,%s,%s,%s)',[id,First_Name,Last_Name,Email,Password])
        # #mysql.get_db().commit()
        # mysql.connection.commit()
        # cursor.close()
        # flash('details registered') 
        # return redirect(url_for('index'))
    return render_template('Signup.html')
@app.route('/otp/<otp>/<id>/<first_name>/<last_name>/<email>/<password>/<bio>',methods=['GET','POST'])
def otp(otp,id,first_name,last_name,email,password,bio):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            # lst=[id,First_Name,Last_Name,Email,Password]
            # query='insert into users values(%s,%s,%s,%s,%s)'
            cursor.execute('insert into users(id,first_name,last_name,email,password,bio) values(%s,%s,%s,%s,%s,%s)',(id,first_name,last_name,email,password,bio))
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            
            return redirect(url_for('login'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,id=id,first_name=first_name,last_name=last_name,email=email,password=password,bio=bio)



@app.route('/login', methods =['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('chat',id=session['user']))
    if request.method=="POST":
        user=request.form['id']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        #cursor=mysql.get_db().cursor()
        cursor.execute('select id from users')
        users=cursor.fetchall()            
        cursor.execute('select password from users where id=%s',[user])
        data=cursor.fetchone()
        #mysql.get_db().commit()
        mysql.connection.commit()
        cursor.close()
        if (user,) in users:
            if password==data[0]:
                session["user"]=user
                return redirect(url_for('chat',id=user))
            else:
                flash('Invalid Password')
                return render_template('login.html')
        else:
            flash('Invalid id')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))

@app.route('/addcontact',methods=['GET','POST'])
def addcontact():
    #cursor=mysql.get_db().cursor()
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT id  from users where id!=%s',[session.get('user')])
    data=cursor.fetchall()
    cursor.execute('select following from friends where followers=%s',[session.get('user')])
    new_data=cursor.fetchall()
    data=tuple([i for i in data if i  not in new_data])
    print(data)
    if request.method=="POST":
        Enter_Username=request.form['option']
        #cursor=mysql.get_db().cursor()
        cursor=mysql.connection.cursor()
        cursor.execute('insert into friends values(%s,%s)',[session.get('user'),Enter_Username])
        #mysql.get_db().commit()
        mysql.connection.commit()
        return redirect(url_for('chat',id=session.get('user')))
    return render_template('Addcontact.html',data=data)


@app.route('/profile',methods=["GET","POST"])
def profilepage():
    cursor=mysql.connection.cursor()
    cursor.execute('select first_name,last_name,email,bio from users where id=%s',[session.get('user')])
    data=cursor.fetchone()
    cursor.close()
    path=os.path.dirname(os.path.abspath(__file__))
    static_path=os.path.join(path,'static')
    fdata=os.listdir(static_path)
    print(session.get('user'))
    if request.method=='POST':
        file=request.files['file']
        ext=file.filename.split('.')
        if ext!='.jpg':
            flash('Upload only .jpg')
        filename=session.get('user')+'.jpg'
        file.save(os.path.join(static_path,filename))
        fdata=os.listdir(static_path)
    return render_template('Profile1.html',data=data,fdata=fdata)
@app.route('/settings',methods=['GET','POST'])
def settings():
    if request.method=='POST':
        email = request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('update users set email=%s where id=%s',[email,session.get('user')])
        mysql.connection.commit()
        cursor.close()
        flash('Email submitted successfully')
    return render_template('setting.html')
@app.route('/back')
def back():
    return redirect(url_for('login'))
@app.route('/message/<id>',methods=['GET','POST'])
def message(id):
    if session.get('user'):
        #cursor=mysql.get_db().cursor()
        cursor=mysql.connection.cursor()
        cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(session.get('user'),id))
        sender=cursor.fetchall()
        cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(id,session.get('user')))
        reciever=cursor.fetchall()
        cursor.execute('select filename from files where follower=%s and following=%s',(session.get('user'),id))
        sender_files=cursor.fetchall()
        cursor.execute('select filename from files where follower=%s and following=%s',(id,session.get('user')))
        reciever_files=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            if 'file' in request.files:
                file=request.files['file']
                filename=file.filename
                #cursor=mysql.get_db().cursor()
                cursor=mysql.connection.cursor()
                cursor.execute('INSERT INTO files (follower,following,filename,file) values(%s,%s,%s,%s)',(session.get('user'),id,filename,file.read()))
                #mysql.get_db().commit()
                mysql.connection.commit()
                cursor.execute('select filename from files where follower=%s and following=%s',(session.get('user'),id))
                sender_files=cursor.fetchall()
                cursor.execute('select filename from files where follower=%s and following=%s',(id,session.get('user')))
                reciever_files=cursor.fetchall()
                return render_template('Messenger.html',id=id,sender=sender,reciever=reciever,sender_files=sender_files,reciever_files=reciever_files)
            message=request.form['Message']
            # cursor=mysql.get_db().cursor()
            cursor=mysql.connection.cursor()
            cursor.execute('INSERT INTO messenger(followers,following,message) values(%s,%s,%s)',(session['user'],id,message))
            #mysql.get_db().commit()
            mysql.connection.commit()
            cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(session.get('user'),id))
            sender=cursor.fetchall()
            cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(id,session.get('user')))
            reciever=cursor.fetchall()
        return render_template('Messenger.html',id=id,sender=sender,reciever=reciever,sender_files=sender_files,reciever_files=reciever_files)
    return redirect(url_for('login'))

@app.route('/download/<filename>')
def download(filename):
    #cursor=mysql.get_db().cursor()
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT file from files where filename=%s',[filename])
    data=cursor.fetchone()[0]
    return send_file(BytesIO(data),download_name=filename,as_attachment=True)
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        id=request.form['id']
        cursor=mysql.connection.cursor()
        cursor.execute('select id from users')
        data=cursor.fetchall()
        print(data)
        if (id,) in data:
            cursor.execute('select email from users where id=%s',[id])
            data=cursor.fetchone()[0]
            print(data)
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the passwword using- {request.host+url_for("createpassword",token=token(id,1000))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid id'
    return render_template('forgot.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        id=s.loads(token)['id']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update users set password=%s where id=%s',[npass,id])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'
        
app.run(use_reloader=True,debug=True)


