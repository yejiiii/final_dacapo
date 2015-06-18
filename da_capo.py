# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, make_response, url_for, session, g, redirect, Response
from flask.ext.mysql import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import json
import datetime
from datetime import timedelta
import os, smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from random import randint

def send_gmail(to, subject, text):
    msg=MIMEMultipart()
    msg['From']=gmail_user
    msg['To']=to
    msg['Subject']=subject
    msg.attach(MIMEText(text))
    part=MIMEBase('application','octet-stream')
    Encoders.encode_base64(part)

    mailServer=smtplib.SMTP("smtp.gmail.com",587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user,gmail_pwd)
    mailServer.sendmail(gmail_user, to, msg.as_string())
    mailServer.close()


# configuration
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASK EXAMPLE_SETTINGS', silent=True)

mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
#app.config['MYSQL_DATABASE_PASSWORD'] = 'alsu12345'
app.config['MYSQL_DATABASE_PASSWORD'] = 'dlguswn12'
app.config['MYSQL_DATABASE_DB'] = 'da_capo'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)



def connect_db():
    return mysql.connect()


def init_db():
    """Creates the database tables."""
    db = connect_db()

    with app.open_resource('dacapo_wb.sql', mode='r') as f:
        sql_statements = " ".join(f.readlines())
        for sql in sql_statements.split(";"):
            if not sql:
                cursor = db.cursor()
                cursor.execute(sql)
                cursor.close()
    db.close()


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    g.db.execute(query, args)

    data = g.db.fetchall()
    rv = [dict((g.db.description[idx][0], value)
               for idx, value in enumerate(row)) for row in data]
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    print ("Start Application")
    db_connect = connect_db()
    db_connect.autocommit(1)

    g.db = db_connect.cursor()
    print type(g.db)

    g.user = None
    if 'user_id' in session:
        g.user = query_db('select StudentID ,UserName, UserEmail from User where StudentID = %s',
                          [session['user_id']], one=True)


@app.route('/')
def login():
    if g.user:
        return redirect(url_for('information'))

    return render_template('login.html')


@app.route('/logout_process')
def logout_process():
    if g.user:
        session.pop('user_id', None)

    return render_template('login.html')

@app.route('/check_login',  methods=["POST"])
def login_check():
    if request.method == "POST":
        id = request.form['id']
        password = request.form['password']

        user = query_db('''select * from User where StudentID = %s''', [id], one=True)

        if user == None:
            error = 'Invalid UserName'
            return render_template('login.html', error=error)
        if check_password_hash(user['UserPassword'], request.form['password']):
            session['user_id'] = user['StudentID']
            return redirect(url_for('information'))
        else:
            error = 'Invalid password'
            return render_template('login.html', error=error)


    # user = query_db('''select * from user where email = %s''', [request.form['email']], one=True)
    #
    # if user is None:
    #     error = 'Invalid username'
    # elif not check_password_hash(user['password'], request.form['password']):
    #     error = 'Invalid password'
    # else:
    #     session['user_id'] = user['email']
    #     return redirect(url_for('server_list'))

    # return  render_template('login.html', error=error)

    return id + " "  + password

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/registerUser', methods=["POST"])
def insert_new_user():
    if request.method == "POST":
        id = request.form['id']
        name = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        student = query_db('''select * from Students where StudentID = %s ''', [id], one=True)

        if not request.form['id']:
            error = 'please input id'
            return render_template('register.html', error=error)
        elif not request.form['username']:
            error = 'please input name'
            return render_template('register.html', error=error)
        elif not request.form['email']:
            error = 'please input email'
            return render_template('register.html', error=error)
        elif not request.form['password']:
            error = 'please input password'
            return render_template('register.html', error=error)
        elif request.form['password'] != request.form['password2']:
            error = 'please check that you have entered it correctly'
            return render_template('register.html', error=error)
        elif student['StudentName'] != request.form['username']:
            error = 'Invalid your studentID and Name'
            return render_template('register.html', error=error)
        else:
            g.db.execute('''insert into User (StudentID, UserName, UserPassword, UserEmail) values (%s, %s, %s, %s)''', [id, name, password,email])
            return redirect(url_for('next_register'))

@app.route('/confirm_register')
def next_register():
    return render_template('confirm_register.html')

@app.route('/information')
def information():
    return render_template('information.html')

@app.route('/timetable_504')
def timetable_504():
    date=datetime.date.today()
    json_data = query_db('''select StudentID from Students WHERE StudentID = %s''', [session['user_id']])
    # return json.dumps(json_data)
    if not g.user:
        return redirect(url_for('login'))
    else:
        Start_time=["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"
                ,"18:00","19:00","20:00","21:00","22:00"];
        End_time=["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"
            ,"18:00","19:00","20:00","21:00","22:00","23:00"];

        number = 1;
        counter = [[0 for i in range(5)]for j in range(14)];
        for i in range(5):
            for j in range(14):
                counter[j][i]=number;
                number=number+1;
        # flask.jsonify(**json_data)
        data=json.dumps(json_data)
        room = '504'
        resp = make_response(render_template('timetable_504.html',date=date, room=room,data=data,Start_time=Start_time,End_time=End_time, counter=counter))
        resp.set_cookie('room', value=room)
        return resp

        #if request.method == "POST":
        #username = request.form['username']
        #id = request.form['userid']

        #resp = make_response(render_template('cookie.html',  username=username, userid=id))
        #resp.set_cookie('username', value=username)
        #resp.set_cookie('userid', value=id)

        #return resp

@app.route('/timetable_519')
def timetable_519():
    date=datetime.date.today()
    json_data = query_db('''select StudentID from Students WHERE StudentID = %s''', [session['user_id']])
    # return json.dumps(json_data)
    if not g.user:
        return redirect(url_for('login'))
    else:
        Start_time=["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"
                    ,"18:00","19:00","20:00","21:00","22:00"];
        End_time=["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"
                ,"18:00","19:00","20:00","21:00","22:00","23:00"];

        number = 1;
        counter = [[0 for i in range(5)]for j in range(14)];
        for i in range(5):
            for j in range(14):
                counter[j][i]=number;
                number=number+1;
        # flask.jsonify(**json_data)
        data=json.dumps(json_data)

        seat1=request.cookies.get('seat1')
        seat2=request.cookies.get('seat2')
        room = '519'
        resp = make_response(render_template('timetable_519.html',date=date,room=room,data=data,Start_time=Start_time,End_time=End_time,
                                             counter=counter,seat1=seat1,seat2=seat2))
        resp.set_cookie('room', value=room)
        return resp

@app.route('/master_reservation')
def master_reservation():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('master_reservation.html')

@app.route('/checkinformation')
def checkinformation():
    if not g.user:
        return redirect(url_for('login'))
    if "room" in request.cookies:
        room = request.cookies.get("room")
    return render_template('checkinformation.html')

@app.route('/selectlist')
def selectlist():
    if not g.user:
        return redirect(url_for('login'))
    #id=session['user_id']
    #reservation = query_db('''select * from Reservation where StudentID = %s''', [id], one=False)
    #r_date= reservation[Date]
    #StudentMember = query_db('''select * from ReservationMember where LeaderNumber = %s AND Date = %s''', [id, r_date], one=False)
    #print (reservation)

    return render_template('selectlist.html')

@app.route('/inputlist')
def inputlist():
    id=session['user_id']
    json_data=query_db('''select * from Reservation where StudentID = %s''', [id], one=False)
    #r_date= reservation[Date]
    #StudentMember = query_db('''select * from ReservationMember where LeaderNumber = %s AND Date = %s''', [id, r_date], one=False)
    return json.dumps(json_data)


@app.route('/finish')
def finish_reservation():
    if not g.user:
        return redirect(url_for('login'))
    reservation_date=request.cookies.get('reservation_date')
    id=session['user_id']
    reservation = query_db('''select * from Reservation where StudentID = %s AND Date = %s''', [id, reservation_date], one=True)
    reservationmember = query_db('''select MemberName from ReservationMember where LeaderNumber = %s AND Date = %s''', [id, reservation_date])

    member=''
    for i in reservationmember:
        member +=  i['MemberName'] + "\n"

    time= reservation['Time']
    object = reservation['Object']

    room=reservation['RoomNumber']
    status=reservation['Status']
    date=reservation['Date']
    return render_template('finish_reservation.html', room=room,object=object, member=member, time=time, status=status, date=date)



        #if 'username' in request.cookies:
            #username = request.cookies.get('username')
            #id = request.cookies.get('userid')

        #return render_template('cookie.html', username=username, userid=id)

@app.route('/student_member')
def student_member():
    if not g.user:
        return redirect(url_for('login'))
    else:
        id=session['user_id']
        Start_time=["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"
                ,"18:00","19:00","20:00","21:00","22:00"];
        End_time=["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00"
            ,"18:00","19:00","20:00","21:00","22:00","23:00"];
        count = 0
        while 1:
            if (not (request.args.get('time'+unicode(count), ''))):
                print count
                break
            count=count+1

        starting=[0 for i in range(count)]
        ending=[0 for i in range(count)]

        seat1 = request.args.get('seat0', '')
        seat2 = request.args.get('seat1', '')

        day1 = request.args.get('day0', '')
        date = datetime.date.today()
        date_week = date.isoweekday()
        i = int(day1)-(date_week)
        reservation_date=str(date+timedelta(days=i))
        print reservation_date

        print "day"
        print day1
        print seat1
        print seat2
        for i in range(count):
            starting[i]=Start_time[int(request.args.get('time'+unicode(i), ''))]
            ending[i]=End_time[int(request.args.get('time'+unicode(i), ''))]

        memory=''
        for i in range(count):
            memory=memory+starting[i]+'~'+ending[i]

        resp = make_response(render_template('student_member.html', memory=memory, reservation_date=reservation_date))
        resp.set_cookie('memory', value=memory)
        resp.set_cookie('reservation_date', value=reservation_date)
        resp.set_cookie('seat1', value=seat1)
        resp.set_cookie('seat2', value=seat2)
        return resp
        memory=request.cookies.get('memory')


    return render_template('student_member.html',memory=memory, reservation_date=reservation_date)

@app.route('/mem')
def mem():
    if 'room' in request.cookies:
        room=request.cookies.get('room')
    id=session['user_id']
    status='YES'
    g.db.execute('''insert into Reservation (StudentID, RoomNumber, Status) values (%s, %s, %s, %s)''', [id, room, status])

    return redirect(url_for('finish_reservation'))

@app.route('/member', methods=["POST"])
def member():
    if request.method == "POST":
        room=request.cookies.get('room')
        memory=request.cookies.get('memory')
        id=session['user_id']
        member= request.form.getlist('member_list')
        object = request.form.getlist('mymultiselect')
        reason= request.form.getlist('reason')
        reservation_date=request.cookies.get('reservation_date')

        for i in member:
            g.db.execute('''insert into ReservationMember (LeaderNumber, MemberName, Date) values (%s, %s, %s)''', [id, i, reservation_date])

        status='wait'
        g.db.execute('''insert into Reservation (StudentID, Object, RoomNumber, Status, Reason, Time, Date) values (%s, %s, %s, %s, %s, %s, %s)''', [id, object, room, status, reason, memory, reservation_date])

    return redirect(url_for('finish_reservation'))

@app.route('/input_member', methods=['GET'])
def input_member():
    data = request.args.get('term', '')
    print data
    json_data = query_db('''select * from Students WHERE StudentID like %s ''', [data+"%"])

    return Response(json.dumps(json_data),mimetype='application/json')

@app.route('/check_password')
def check_password():

    def send_gmail(to, subject, text):
        msg=MIMEMultipart()
        msg['From']=gmail_user
        msg['To']=to
        msg['Subject']=subject
        msg.attach(MIMEText(text))
        part=MIMEBase('application','octet-stream')
        Encoders.encode_base64(part)

        mailServer=smtplib.SMTP("smtp.gmail.com",587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(gmail_user,gmail_pwd)
        mailServer.sendmail(gmail_user, to, msg.as_string())
        mailServer.close()


    id = request.args.get('modal_id')
    email = request.args.get('modal_email')
    json_data = query_db('''select * from User WHERE StudentID = %s AND UserEmail = %s''', [id, email], one=True)
    # password = json_data['UserPassword']

    if json_data is not None:
        new_passwd = str(randint(1000000,9999999))
        print new_passwd
        hash_new = generate_password_hash(new_passwd)
        print hash_new
        g.db.execute('''UPDATE User SET UserPassword = %s WHERE StudentID = %s''', [hash_new, id])
        if __name__ == "__main__":
            title="비밀번호를 확인해주세요 -da_capo-"
            to=(email)
            gmail_user="l67378810@gmail.com"
            gmail_pwd="guswn6737"
            message= id+"password is"+new_passwd+"." +"\n" +"Please change password."
            send_gmail(to,title,message)

            data=json.dumps({'text': '메일이 발송되었습니다'})
    else:
        data=json.dumps({'text': '메일이 발송이 실패하였습니다'})

    return data

@app.route('/change_pwd')
def change_pwd():
    return render_template('checkpwd.html')

@app.route('/change', methods=["POST"])
def change():
    if request.method == "POST":
        id=session['user_id']

        passwd = generate_password_hash(request.form['passwd'])
        newpwd=request.form['newpwd']
        repwd=request.form['repwd']
        h_newpwd=generate_password_hash(newpwd)

        user = query_db('''select * from User where StudentID = %s''', [id], one=True)

        if not passwd:
            error = 'please input value'
            return render_template('checkpwd.html', error=error)
        elif not request.form['newpwd']:
            error = 'please input value'
            return render_template('checkpwd.html', error=error)
        elif not request.form['repwd']:
            error = 'please input value'
            return render_template('checkpwd.html', error=error)
        elif not passwd == user['UserPassword']:
            error = 'Invalid your password'
        elif newpwd != repwd:
            error = 'please retype new password correctly'
            return render_template('checkpwd.html', error=error)
        elif newpwd == repwd:
            g.db.execute('''UPDATE User SET UserPassword = %s WHERE StudentID = %s''', [h_newpwd, id])
            return redirect(url_for('logout_process'))



#date = datetime.date.today()
#date_week = date.isoweekday()
#if date_week==0:
#    g.db.execute('''TRUNCATE TABLE Reservation, ReservationMember''')

if __name__ == "__main__":
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)