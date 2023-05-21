from flask import Flask, request, render_template, jsonify,send_file
from flask_cors import CORS
from flask_cors import cross_origin
import subprocess
import pymysql
import bcrypt
import datetime
import time 
from functools import wraps
import os
import uuid
import csv
import json
from matching import map_sys
from read_data import read_data
import json
# app = Flask(__name__)
app = Flask(__name__, static_folder='static', static_url_path='/static/dist')
app.config.from_object(__name__)
CORS(app,resources={r"/*"  :{"origins":"*"}})
app.config["SECRET_KEY"] = "thisisasecretkey"
app.secret_key = "hdiu21y3y4yhr3294"
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESS_FOLDER'] = 'process'
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

if not os.path.exists(app.config["PROCESS_FOLDER"]):
    os.makedirs(app.config["PROCESS_FOLDER"])
pymysql.install_as_MySQLdb()
con = pymysql.connect(
    host='mysql',
    port=3306,
    user='root',
    password='123456',
    db='mapping_system',
)
cursor=con.cursor()


@app.route("/")
def index():
    return "Hello World!"

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    cursor.execute('SELECT password FROM users WHERE username=%s', username)
    result = cursor.fetchone()

    if not result:
        # User not found
        return jsonify({'message': 'User Not Found'}), 403

    # Check password hash with bcrypt
    if bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
        cursor.execute('SELECT id,username,firstname,lastname,email FROM users WHERE username=%s', username)
        result = cursor.fetchone()
        return jsonify({'message': 'Login successful','userinfo':{'userid':result[0], 'username':result[1],'firstname':result[2],'lastname':result[3],'email':result[4]}}), 200
    else:
        # Passwords do not match
        return jsonify({'message': 'Invalid credentials'}), 403

@app.route("/upload",methods=["POST"])
def upload():
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    user_id = request.headers.get('Authorization').split(' ')[1]
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], user_id)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    uuid_str = str(uuid.uuid4())
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], user_id, uuid_str+'.txt'))
    return jsonify({'message': 'File uploaded successfully','file_id':uuid_str}), 200



@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    cursor.execute('SELECT * FROM users WHERE username=%s OR email=%s', (username, email))
    result = cursor.fetchone()
    if result:
        return jsonify({'message': 'User or Email already exists'}), 403
    else:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO users(username, password, email,firstname,lastname) VALUES(%s, %s, %s, %s, %s)', (username, hashed, email, '', ''))
        con.commit()
        return jsonify({'message': 'User created successfully'}), 200


@app.route("/process",methods=["POST"])
def process():
    data = request.get_json()
    userid = data.get("userid")['userid']
    username = data.get("userid")['username']
    fileid = data.get("file_id")
    comment = data.get("comment")
    for i in fileid:
        cursor.execute('INSERT INTO Mappings(id,user_id,username,Commt,Editdate,Status) VALUES(%s, %s,%s, %s,%s,%s)', (i, userid, username, comment, time.strftime('%Y-%m-%d %H:%M:%S'),'Pending'))
        con.commit()
    save_path = os.path.join(app.config["PROCESS_FOLDER"], userid)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    # pending_check = False
    for i in fileid:
        map = map_sys('uploads/'+userid+'/'+i+'.txt', 'process/'+userid+'/'+i)
        map.mapping()
        # cmd = 'python snomed_ct.py ' + str(i) + ' ' + 'uploads/'+userid+'/'+i+'.txt'  
      # cmd = 'mpiexec -n 12 python snomed_ct.py ' + str(i) + ' ' + 'uploads/'+userid+'/'+i+'.txt'
        # result = subprocess.run(cmd)
        # os.system(cmd)
        # map = map_sys('uploads/'+userid+'/'+i+'.txt', 'process/'+userid+'/'+i,str(i))
        # map.mapping()
        cursor.execute('UPDATE Mappings SET Status=%s WHERE id=%s', ('Completed', i))
        con.commit()
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], userid, i+'.txt'))
    return jsonify({'message': 'File processed successfully'}), 200

@app.route("/getmaps",methods=["GET"])
def getmap():
    userid = request.headers.get('Getmapping').split(' ')[1]
    cursor.execute("SELECT * FROM Mappings")
    result = cursor.fetchall()
    temp = []
    if result:
        for i in result:
            temp.append({'mapid':i[0],'userid':i[1],'username':i[2],'comment':i[3],'editdate':i[4].strftime('%Y-%m-%d %H:%M:%S'),'status':i[5]})
        return jsonify({'message': 'Map found','map':temp}), 200
    else:
        return jsonify({'message': 'Map not found'}), 403
    
@app.route("/deletemap/<string:mapping_id>/<user_id>",methods=["DELETE"])
def deleteMap(mapping_id,user_id):
    # return jsonify({'message': mapping_id}), 200
    cursor.execute("DELETE FROM Mappings WHERE id = %s", mapping_id)
    con.commit()
    file_path = os.path.join(app.config["PROCESS_FOLDER"], user_id,mapping_id+'.json')
    os.remove(file_path)
    file_path = os.path.join(app.config["PROCESS_FOLDER"], user_id,mapping_id+'.csv')
    os.remove(file_path)
    return jsonify({'message': 'Map deleted successfully'}), 200


@app.route("/getmapresult/<user_id>/<string:mapping_id>",methods=["GET"])
def getmapresult(user_id,mapping_id):
    path = os.path.join(app.config["PROCESS_FOLDER"], user_id, mapping_id+'.json')
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    # path = os.path.join(app.config["PROCESS_FOLDER"], user_id, mapping_id+'.csv')
    # with open(path, mode='r') as csv_file:
    #     csv_reader = csv.DictReader(csv_file)
    #     data = json.dumps([row for row in csv_reader])
    return data, 200

@app.route("/editmapping",methods=["POST"])
def editmapping():
    data = request.get_json()
    editinfo = data.get("editinfo")
    index = editinfo['index']
    userid = data.get("userid")
    mapid = data.get("mapid")
    path = os.path.join(app.config["PROCESS_FOLDER"], userid, mapid+'.json')

    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    data[index]['distance'] = editinfo['distance']
    data[index]["out_put_data"] = editinfo["out_put_data"]
    data[index]["result_from"] = editinfo["result_from"]
    data[index]["history"] = editinfo["history"]
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)
    # Edit data
    path = os.path.join(app.config["PROCESS_FOLDER"], userid, mapid+'.csv')
    newrow = [editinfo['raw_data'], editinfo['out_put_data'], editinfo['result_from']]
    # Edit the process csv file
    with open(path, mode='r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        rows[index+1] = newrow
    with open(path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    with open('modify.csv', mode='r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        found = False
        for row in rows:
            if newrow[0] in row:
                row[1] = newrow[1]
                found = True
                break
        if not found:
            rows.append(newrow[0:2])
    with open('modify.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    return jsonify({'message': 'Map edited successfully'}), 200
@app.route("/deletemapping",methods=["POST"])
def deletemapping():
    data = request.get_json()
    index = data.get("mapinfo")["index"]
    userid = data.get("userid")
    mapid = data.get("mapid")
    path = os.path.join(app.config["PROCESS_FOLDER"], userid, mapid+'.csv')
    with open(path, mode='r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        del rows[index+1]
    with open(path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return jsonify({'message': 'Map deleted successfully'}), 200

@app.route("/download", methods=["POST"])
def download_file():
    file_id = request.json['file_id']
    userid = request.json['userid']
    path = os.path.join(app.config["PROCESS_FOLDER"], userid, file_id+'.csv')
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')