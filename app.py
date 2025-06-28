from flask import Flask , redirect , flash , request , render_template , jsonify , url_for , session
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import timedelta

app = Flask(__name__)

app.secret_key = "HMI"
clint = MongoClient("mongodb+srv://sriram65raja:1324sriram@cluster0.dejys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
HMI = clint['ai']
EMPLOYEE_REGISTER = HMI["EMPLOYEE_REGISTER"]
CLINET_DATILS = HMI["CLINET_DATILS"]
ACCEPTED_LIST = HMI['ACCEPTED_LIST']

app.permanent_session_lifetime = timedelta(days=50)

@app.route("/")
def Home():
    if session.get("email"):
        role = session.get("role")
        return redirect(f"/dash/{role}")
    return render_template("index.html")



@app.route("/hmi-manage/employee" , methods=["GET" , "POST"])
def hmi():
    if (request.method == "POST"):
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        role = request.form.get("role")
        
        try:
            if(EMPLOYEE_REGISTER.find_one({"Employee_email":email})):
                return "Email with This Employee already Exits"
            
            data = {
                "Employee_name":name,
                "Employee_email":email,
                "Employee_phone_no":phone,
                "Employee_Role":role
            }
            
            EMPLOYEE_REGISTER.insert_one(data)
            return redirect("/hmi-manage/employee")
        
        except:
            return "Error on Creating the Emplyee due to Server Heavy Load or Network Error , You can Also Try After Some Times.....!"
    
    Employee = EMPLOYEE_REGISTER.find({})
    
    return render_template("hmi.html" , E=Employee)


@app.route("/hmi-manage/home")
def hmi_home():
    Cleints = CLINET_DATILS.find({})
    return render_template("hmi-home.html" , c=Cleints)

@app.route("/del/employee/<id>"  , methods=['POST'])
def Delete_user(id):
    EMPLOYEE_REGISTER.find_one_and_delete({"_id":ObjectId(id)})
    return render_template("hmi.html")


@app.route("/login" , methods=["GET" , "POST"])
def login():
    if(request.method == "POST"):
        phone_no = request.form.get('phone')
        try:
            User = EMPLOYEE_REGISTER.find_one({"Employee_phone_no":phone_no})
            if User:
                session["email"] = User["Employee_email"]
                session["role"] = User["Employee_Role"]
                if session.get("role") == "ClinetEmployee":
                    return redirect(url_for('dash' , role="ClinetEmployee"))
                else:
                    return redirect(url_for('dash' , role="Developer"))
                
            else:
                return "User Not Found"
        except Exception as e:
            print(e)
            return "Server Error"
    
    return render_template("login.html")
            
@app.route("/dash/<role>")
def dash(role):
    email = session.get("email")
    if not session.get("email"):
        return redirect("/login")
    if role == "ClinetEmployee":
       return render_template("ce.html" , email= email)
    else:
       return render_template("dev.html" , email = email)
   


@app.route("/get-clint-deatils" , methods=["POST"])
def GetClinet():
    cname = request.form.get("cname")
    cemail = request.form.get("cemail")
    cphone = request.form.get("cphone")
    csell = request.form.get("csell")
    
    email = session.get("email")
    
    User = EMPLOYEE_REGISTER.find_one({"Employee_email":email})
    
    if User:
        name_emp = User["Employee_name"]
    
    try:
        data={
            "cname":cname,
            "cemail":cemail,
            "cphone":cphone,
            "csell":csell,
            "Emplyee_name":name_emp,
            "Accepted":False
        }    
        
        c = CLINET_DATILS.insert_one(data)
    
        session["Sumbited_id"] = str(c.inserted_id)
        return redirect("/qr-code")
    except:
        return "Server Error"

    

@app.route("/qr-code")
def qr_code():
    return render_template("qr.html")
   

@app.route("/show-accpted")
def show_accpted():
    show_acc = ACCEPTED_LIST.find({}).sort("_id" , -1)
    return render_template("show-ac.html" , s=show_acc)
   
@app.route("/accept/<id>" , methods=["POST"])
def Accept(id):
    CLINET_DATILS.find_one_and_update({"_id":ObjectId(id)} , {"$set" :{
        "Accepted":True
    }})
    
    Clint = CLINET_DATILS.find_one({"_id":ObjectId(id)})
    ACCEPTED_LIST.insert_one(Clint)
    
    CLINET_DATILS.delete_one({"_id":ObjectId(id)})
    
    return redirect("/hmi-manage/home")

@app.route("/reject/<id>" , methods=["POST"])
def Reject(id):
     CLINET_DATILS.find_one_and_update({"_id":ObjectId(id)} , {"$set" :{
        "Accepted":"Rejected"
    }})
     
     Clint = CLINET_DATILS.find_one({"_id":ObjectId(id)})
     ACCEPTED_LIST.insert_one(Clint)
     CLINET_DATILS.delete_one({"_id":ObjectId(id)})
     
     return redirect("/hmi-manage/home")
    

@app.route("/get-accepted-data")
def Get_Accepted():
    sumb_id = session.get("Sumbited_id")
    
    c = ACCEPTED_LIST.find_one({"_id": ObjectId(sumb_id)})
    
    if c:
        c["_id"] = str(c["_id"])
        return jsonify(c)
    else:
        return jsonify({"error": "No data found"}), 404



@app.route('/delete-all', methods=['GET'])
def delete_all_records():
    result = ACCEPTED_LIST.delete_many({})
    return jsonify({
        "message": "All records deleted",
        "deleted_count": result.deleted_count
    })
    
    
       

if __name__ == "__main__":
    app.run(debug=True , port=1212)
