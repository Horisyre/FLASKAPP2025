from flask import Flask, render_template, request, redirect, url_for, session
from dateutil.relativedelta import relativedelta 
import datetime
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import re 
import MySQLdb.cursors
from flask_mysqldb import MySQL
from config import Config
from MySQLdb.cursors import DictCursor
from forms import loginForm, Customerform, CroSubmitForm, CroAlterForm, completionForm, completeform, CroAlertForm
from globalFunc import get_time_now,get_date,switch_repair
import bcrypt

app = Flask(__name__ ,static_url_path='/static')
app.config.from_object(Config)
mysql = MySQL(app)

@app.route("/",methods=['GET','POST'])
def login():
    session['Logs']=[]
    msg=''
    form= loginForm()
    if form.validate_on_submit(): 
        usernumber=form.usernumber.data
        userpassword=form.userpassword.data
        try:
            tech_num= int(usernumber)

            with mysql.connection.cursor(DictCursor) as cursor:
                cursor.execute('SELECT password_hash FROM PSSWORDS WHERE Tech_number = %s',  (tech_num,))
                TechyData=cursor.fetchone()
                
                if TechyData==None:
                    raise ValueError("Username does not exist")
                stored_hash=TechyData["password_hash"]
                
                if bcrypt.checkpw(userpassword.encode('utf-8'), stored_hash.encode('utf-8')):
                    session['loggedin']=True
                    session['Tech_number']=tech_num
                    time= get_time_now()
                    session['Logs'].append(f"Technician {session['Tech_number']}, logged in @ {time}")
                    return redirect(url_for('home'))

                raise ValueError("Incorrect Password")

        except ValueError as v:
            msg=f"{v} "
            app.logger.warning(msg)
            return render_template('login.html', msg=msg,form=form)
        
        except Exception as e:
            msg="Error found in username or password"
            app.logger.warning(msg)
            return render_template('login.html', msg=msg,form=form)
    
    
    return render_template('login.html', msg=msg,form=form)




#to do
"""@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('if',None)
    session.pop('username', None)
    time=get_time_now()
    session['Logs'].append(f"{session['Tech_number']}, logged out @ {time}")
    return redirect(url_for('login'))  """  


@app.route("/home")
def home():
    try:
        date=get_date()
        with mysql.connection.cursor() as cursor:
            customersDue=False
            tech_no=int(session['Tech_number'])
            QUERY=("""SELECT * FROM Customers 
                    JOIN Workshop ON Customers.Cro_id = Workshop.Cro_id 
                    WHERE Tech_number=%s 
                        AND(
                            (Status = 'busy' AND Checked_in < %s)
                            OR 
                            (Status= 'pending' AND Checked_in < %s)
                        )""")
            cursor.execute(QUERY,(tech_no, date, date))
            alerts=cursor.fetchall()
            if alerts:
                customersDue=True
            TotalJobsCreated=0
            cursor.execute("SELECT COUNT(*) FROM Customers WHERE  Tech_number=%s",(tech_no,))
            TotalJobsCreated=cursor.fetchone()
            TotalJobsCreated=TotalJobsCreated[0]
            
            QUERY2=("""SELECT COUNT(*) FROM Customers 
                    JOIN Workshop ON Customers.Cro_id = Workshop.Cro_id 
                    WHERE Tech_number=%s 
                        AND(
                            (Status = 'busy' )
                            OR 
                            (Status= 'pending' )
                        )""")
            cursor.execute(QUERY2,(tech_no,))
            JobsUpcoming=0
            JobsUpcoming=cursor.fetchone()
            JobsUpcoming=JobsUpcoming[0]
            
            QUERY3=("""SELECT COUNT(*) FROM Customers 
                    JOIN Workshop ON Customers.Cro_id = Workshop.Cro_id 
                    WHERE Tech_number=%s 
                    AND Status = 'done' 
                    """)
            cursor.execute(QUERY3,(tech_no,))
            TotalJobsCompleted=0
            TotalJobsCompleted=cursor.fetchone()
            TotalJobsCompleted=TotalJobsCompleted[0]

            QUERY4 = """SELECT e.RowNumber 
                    FROM(
                        SELECT Tech_number, 
                            ROW_NUMBER() OVER(ORDER BY COUNT(*) DESC) AS RowNumber
                        FROM Customers 
                        JOIN Workshop ON Customers.Cro_id = Workshop.Cro_id 
                        WHERE Status = 'done'
                        GROUP BY Tech_number
                    ) AS e
                    WHERE Tech_number=%s"""
            cursor.execute(QUERY4,(tech_no,))
            Rank=cursor.fetchone()
            if Rank==None:
                Rank="NOT RANKED YET"
            else:
                Rank=Rank[0]
            return render_template('home.html', customersDue=customersDue,TotalJobsCreated=TotalJobsCreated,JobsUpcoming=JobsUpcoming,
            TotalJobsCompleted=TotalJobsCompleted,Rank=Rank)   
    except Exception  as e:
        #here willl log an error to app.loggr
        return "An internal error occurred", 500
    return render_template('home.html')

@app.route("/home/customerCreation",methods=['GET','POST']) 
def customerCreation():
    form=Customerform()
    with mysql.connection.cursor(DictCursor) as cursor:
        mydate=datetime.datetime.now()
        date =mydate.strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM Customers")
        NoRecords= cursor.fetchone()["COUNT(*)"] 
        if NoRecords==None:
            NoRecords=0
        CroNumber=NoRecords+1
        msg=""

    if form.validate_on_submit():
        Number = form.CustPhoneNo.data
        Name = form.CustomerName.data
        TechNo= form.TechNo.data
        Date =  form.date.data
        Email = form.CustomerEmail.data
        Device =  form.CustomerDevice.data
        CustAddress =  form.CustAddress.data
        fault= form.fault.data
        techy=session['Tech_number']
        time=get_time_now()

        try:
            with mysql.connection.cursor(DictCursor) as cursor:
                TechNo=int(TechNo)

                query0="SELECT * FROM Technicians WHERE Tech_number=%s"
                cursor.execute(query0,(TechNo,))
                technicianData=cursor.fetchone()
                if technicianData==None:
                    raise ValueError("Technician does not exist")

                session['Logs'].append(f"techy, number: {techy}, creating a customer @ {time}")
                session.modified = True
                query = """INSERT INTO Customers 
                            (Name, Device, Email, Tech_number, Phone_number, Fault, Physical_Address, Checked_in)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                        # Correct data as a tuple (must match placeholders order)
                data = (Name, Device, Email, TechNo, Number, fault, CustAddress, Date )
                    # Execute the query with data
                cursor.execute(query, data)
                last_inserted_id = int(cursor.lastrowid) #this form with the correct
                        
                workshop_query="""INSERT INTO Workshop (Cro_id, Status)
                        VALUES (%s, 'pending')"""
                cursor.execute(workshop_query, (last_inserted_id,))
                mysql.connection.commit()
                return redirect(url_for('home'))

        except Exception as e:
            #here willl log an error to app.loggr
            msg="invalid input in form"
            return render_template("customerCreation.html", mydate=date, CroNumber=CroNumber,form=form, msg=msg)
        except Exception as e:
            #here willl log an error to app.loggr
            msg="invalid input in form"
            return render_template("customerCreation.html", mydate=date, CroNumber=CroNumber,form=form, msg=msg)
    return render_template("customerCreation.html", mydate=date, CroNumber=CroNumber,form=form, msg=msg)


@app.route("/home/CustomerAlter",methods=['GET','POST'])
def CustomerAlter():
    # our form by defaul checks for a request.post for customer id for a sspeciifc submit button
    #log aan eerror if customer cro exists or not 
    form1=CroSubmitForm()
    form2=CroAlterForm()
    variable1=True
    msg=""
    return render_template( "CustomerAlter.html",form1=form1,form2=form2,variable1=variable1,msg=msg)
    
@app.route("/home/CustomerAlter/GETCRO",methods=['POST'])
def GETCRO():
    form1=CroSubmitForm()
    form2=CroAlterForm()
    variable1=True
    msg=""
    if form1.validate_on_submit():  
        variable1=False
        CRO_number=form1.CroNo.data
        
        try:
            CRO_id=int(CRO_number) 
            with mysql.connection.cursor(DictCursor) as cursor:
                cursor.execute("SELECT * FROM Customers WHERE Cro_id = %s",(CRO_number,)) #here we must pass paramter as tuple
                customer= cursor.fetchone()
                if customer:
                    number=customer["Phone_number"]
                    address=customer["Physical_Address"]
                    name=customer["Name"]
                    email=customer["Email"]
                    session['Logs'].append(f"fetching customer to alter details, cro number:{CRO_number}")
                    session['user']={
                        'username':name,
                        'usernumber':number,
                        'useradd':address,
                        'useremail':email
                    }
                    #here we will create a session for user session['user] this will be a dict cotaining [{custname:name},{custaddress:address},
                    # {custnumbe:number},{custemail:email}
                    return render_template('CustomerAlter.html',
                        CRO_num=CRO_number,default_CustAdd=address,
                        default_CustPhone=number,default_CustName=name,
                        default_CustEmail=email,form1=form1,form2=form2,variable1=variable1)
                elif customer==None:
                    variable1=True
                    msg="Customer does not exist"
        except Exception as e:
            #log the excpetion to python with ap.logger 
            return "An internal error occurred", 500
    else:
        msg="invalid input for CRO number "
    return render_template('CustomerAlter.html', form1=form1,form2=form2, msg=msg, variable1=variable1 )
            
@app.route("/home/CustomerAlter/ALTERCRO",methods=['GET','POST'])
def ALTERCRO():
    form2=CroAlterForm()
    msg=""
    if form2.validate_on_submit():
        Notmatch=[]
        CRO_number=form2.CRO_number.data
        CustAddress=form2.CustAddress.data
        CustPhoneNo=form2.CustPhoneNo.data
        CustomerName= form2.CustomerName.data
        CustomerEmail=form2.CustomerEmail.data
        Purchased_Items=form2.Purchased_Items_Cost
        Purchased_Items_Cost=form2.Purchased_Items
        custdetails=[ CustAddress,CustomerEmail,CustomerName,CustPhoneNo,Purchased_Items,Purchased_Items_Cost]
        for key,i in zip(session['user'],custdetails):
            session_info=session['user'][key]
            if session_info!=i:
                Notmatch.append(key)        
        #need to check if logs exists in session , since log can be removed in every session
        if 'Logs' in session:
            session['Logs'].append(f"changed customer information for cro number: {CRO_number}, attributes changed are, {', '.join(x for x in Notmatch)}")
            session.modified = True

        try:
            with mysql.connection.cursor() as cursor:  
                cursor.execute("UPDATE CUSTOMERS SET Name=%s,Email=%s, Phone_number=%s,Physical_Address=%s,Purchased_Items=%s,Purchased_Items_Cost=%s WHERE Cro_id =%s ",
                    (CustomerName, CustomerEmail,CustPhoneNo,CustAddress,Purchased_Items,Purchased_Items_Cost,CRO_number))
                mysql.connection.commit()
                return redirect(url_for('home'))
        except Exception as e:
            #log e to app.logger 
            variable1=False
            return render_template('CustomerAlter.html',
                        CRO_num=CRO_number,default_CustAdd=address,
                        default_CustPhone=number,default_CustName=name,
                        default_CustEmail=email,form1=form1,form2=form2,variable1=variable1,msg=msg)
    return render_template('CustomerAlter.html', form2=form2,variable1=variable1, msg=msg)

@app.route("/home/WorkLogs")
def WorkLogs():
    return render_template( "WorkLogs.html",logs=session['Logs'] )



@app.route("/home/CustomerAlter/CompleteCro",methods=['GET','POST'])
def CompleteCro():
    form1=completeform()
    form2=completionForm()
    variable1=True
    msg=""
    return render_template("CompleteCro.html",form1=form1,form2=form2,variable1=variable1)
    
@app.route("/home/CustomerAlter/CompleteCro/GettingCroForCompleting",methods=['POST'])
def GettingCroForCompleting():
    form1=completeform()
    form2=completionForm()
    variable1=True
    msg=""
    if form1.validate_on_submit():
        CRO_number=form1.CRO_number.data
        variable1=False
        try:
            CRO_number=int(CRO_number)
            with mysql.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Customers WHERE Cro_id=%s",(CRO_number,))
                customer= cursor.fetchone()
                if customer is None:#if custmomer cro_id does not exist
                    msg="Please check form input and try submit again "
                    variable1=True
                    return render_template("CompleteCro.html", msg=msg)
                TableColumns= [description[0] for description in cursor.description]
                return render_template("CompleteCro.html",customer=customer,TableColumns=TableColumns,CRO_NUM=CRO_number,form1=form1,
                form2=form2,variable1=variable1,msg=msg)
        except Exception as e:
            #log exception with error with app.logger 
            variable1=True
            msg= "Please re-submit Cro number"
            return render_template("CompleteCro.html", msg=msg,variable1=variable1)
    return render_template("CompleteCro.html",form1=form1,form2=form2,variable1=variable1 ,msg=msg)

@app.route("/home/CustomerAlter/CompleteCro/CompletingCro",methods=['GET','POST']) 
def CompletingCro():
    form1=completeform()
    form2=completionForm()
    variable1=False
    msg=""
    if form2.validate_on_submit():#not validating
        #here we need to get costs from workshop for repair costs and purchased then update total cost
        cro=request.form['CRO']
        Purchased_Items=form2.Purchased_Items.data
        diagnostics=form2.diagnostics.data
        RepairType=form2.RepairType.data 
        Purchased_Items_Cost=form2.Purchased_Items_Cost.data 
        date=get_date()
        try:
            time=get_time_now()
            date= get_date()
            with mysql.connection.cursor() as cursor:
                cursor.execute("SELECT Purchased_Items_Cost FROM Workshop WHERE Cro_id=%s",(cro,))
                Items_Cost=cursor.fetchone()
                Items_Cost=Items_Cost[0]
                if Items_Cost==None:
                    Items_Cost=0.00
                if Purchased_Items_Cost==None:
                    Purchased_Items_Cost=0.00
                Repair_Cost=switch_repair(RepairType)
                #handle reair cost if else, double check total_COst column name
                total_cost= 100+Items_Cost+ Repair_Cost
                completionQuery="""UPDATE Workshop SET  Diagnostic=%s, Status='done', Total_Cost=%s, Checked_out=%s, Repair_type=%s,
                    Repair_Cost=%s, Purchased_Items_Cost=%s Where Cro_id=%s"""
                cursor.execute(completionQuery,(diagnostics, total_cost, date, RepairType, Repair_Cost, Purchased_Items_Cost, cro,))
                mysql.connection.commit()
            session['Logs'].append(f"techician {session['Tech_number']} has completed CRO {cro} @ time: {time}")# not being updated
            session.modified=True
            return redirect(url_for("home"))
            #when we return re direct the other iframe in the webpage is not rendered hence should we return template?
        except Exception as e:
            msg="Something went wrong, please check input and try again"
            return render_template("CompleteCro.html",customer=customer,TableColumns=TableColumns,CRO_NUM=CRO_number,form1=form1,
                form2=form2,variable1=variable1,msg=msg)
    return render_template("CompleteCro.html",form2=form2,form1=form1,variable1=variable1, msg=msg)

@app.route("/Completed")
def Completed():
    return render_template( "Completed.html") 
    #cursor.description: This is an attribute of the database cursor object (cursor) that holds metadata about the columns of the query result.
    #the first column holds metadata pertaining to the table with regars to table name, hence the index allows us to access the firt column in the desciption attribute

@app.route('/Alerts.html') 
def Alerts():
    msg=""
    form=CroAlertForm()
    with mysql.connection.cursor() as cursor:
        if form.validate_on_submit():
            date=get_date()
            try:
                tech_no=int(form.Tech_number.data)
                QUERY=("""SELECT * FROM Customers 
                        JOIN Workshop ON Customers.Cro_id = Workshop.Cro_id 
                        WHERE Tech_number=%s 
                            AND(
                                (Status = 'busy' AND Checked_in < %s)
                                OR (Status= 'pending' AND Checked_in < %s)
                            )""")
                cursor.execute(QUERY,(tech_no,date,date))
                table_data=cursor.fetchall()
                if table_data is None:
                    table_data=None
                    columns=None
                    msg="No data found, please check form input and try again"
                    return render_template("Alerts.html", columns=columns,table_data=table_data, msg=msg)
                columns=[description[0] for description in cursor.description]
                return render_template("Alerts.html", columns=columns,table_data=table_data, msg=msg)
            except Exception as e:
                #app.loggger(e)
                msg="Please check form input and submit again"
    try:
        QUERY=("""SELECT * FROM Customers 
                JOIN Workshop ON Customers.Cro_id = Workshop.Cro_id 
                WHERE (Status = 'busy' AND Checked_in < %s)
                    OR (Status= 'pending' AND Checked_in < %s)""")

        cursor.execute(QUERY,(date, date,))
        table_data=cursor.fetchall()
        if not table_data:
            table_data=None
            columns=None
            msg= "no data found, please try again"
            return render_template("Alerts.html", columns=columns,table_data=table_data, msg=msg)
        columns=[description[0] for description in cursor.description]
        return render_template("Alerts.html", columns=columns,table_data=table_data,form=form, msg=msg)
    except Exception as e:
        #log e tp app.logger
        return "An internal error occurred", 500


@app.route('/help')
def help():
    return render_template("help.html")

@app.route('/prices.html')
def prices():
    return render_template("prices.html")

@app.route('/AllCompleted')
def AllCompleted():
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Workshop WHERE Status = 'done' ")
            ColumnData =cursor.fetchall()
            ColumnNames = [description[0] for description in cursor.description]
            return render_template("AllCompleted.html",ColumnData=ColumnData,ColumnNames=ColumnNames)
    except Exception as e:
         return "An internal error occurred", 500

@app.route('/CompletedForTechnician')
def CompletedForTechnician():
    try:
        with mysql.connection.cursor() as cursor:
            tech_num=session['Tech_number']
            query="""SELECT * FROM Workshop 
                JOIN Customers ON Workshop.Cro_id=Customers.Cro_id
                WHERE Status = 'done' 
                AND Tech_number=%s"""
            cursor.execute(query,(tech_num))
            ColumnData =cursor.fetchall()
            ColumnNames = [description[0] for description in cursor.description]
        return render_template("CompletedForTechnician.html",ColumnData=ColumnData,ColumnNames=ColumnNames)
    except Exception as e:
        #log e wwith app.logger
         return "An internal error occurred", 500


@app.route('/weeklyProfit')
def weeklyProfit():
    try:
        with mysql.connection.cursor() as cursor:
            today_date=get_date()
            today_date=datetime.datetime.strptime(today_date, "%Y-%m-%d")
            week_ago=today_date-datetime.timedelta(days=6)
            dates=[] #this will end becoming a array of  stirng ertainning to dates 
            costs=[] # a array of decimals
            for i in range(7):
                date=week_ago+datetime.timedelta(days=i)
                date=datetime.datetime.strftime(date, "%Y-%m-%d")
                query="SELECT Checked_out,SUM(Total_Cost) FROM workshop WHERE Checked_out = %s "
                cursor.execute(query,(date,))
                data=cursor.fetchall()
                for information in data:
                    if information[0]==None:
                        dates.append(str(date))
                        costs.append(float(0.00))
                    else:
                        dates.append(str(information[0])) 
                        costs.append(float(information[1]))
            #does my problem occur where dates are datetime objects and not strings?
            return render_template("weeklyProfit.html",dates=dates,costs=costs)
                    
            #optional, here we can use linear regression to predict future values, which mean we alter columns and add values to data
    except Exception as e:
        #log e to app.logger
         return "An internal error occurred", 500
    return redirect('home')

    
@app.route('/ToDoList.html')
def ToDoList():
    try:
        tech_no=session['Tech_number']
        with mysql.connection.cursor() as cursor:
            query= """
                SELECT Workshop.Cro_id, Customers.Name, Customers.Fault FROM Workshop
                JOIN Customers ON Workshop.Cro_id=Customers.Cro_id
                WHERE Tech_number= %s AND (Status='pending' OR Status='busy')
            """
            
            cursor.execute(query,(tech_no,))
            Cros_To_complete=cursor.fetchall()
            Cros_To_complete=[list(customer) for customer in Cros_To_complete]
            #conversions required due to having nested tuples in a tuple, tuples are immutable
            
            for customer in Cros_To_complete:
                if customer[2] is None:
                    customer[2]=""
            return render_template("ToDoList.html", Cros_To_complete=Cros_To_complete)
    except Exception as e:
        #log e to aapp.logger 
         return "An internal error occurred", 500


@app.route('/UserProfile')
def UserProfile():
    with mysql.connection.cursor() as cursor:
        today_date = datetime.datetime.today()
        first_of_month=today_date.replace(day=1)
        First_of_month = first_of_month.strftime("%Y-%m-%d")
        today_date =today_date.strftime("%Y-%m-%d")
        tech_no= session['Tech_number']

        try:
            query_1_0="""SELECT COUNT(*) FROM Workshop
                        JOIN Customers ON Workshop.Cro_id= Customers.Cro_id 
                        WHERE Status='done' AND  Checked_out< %s AND Checked_out> %s AND Tech_number=%s
                        """ 
            cursor.execute(query_1_0,(today_date, First_of_month, tech_no,))
            count_tech_no=(cursor.fetchone())
            count_tech_no=int(count_tech_no[0])

            query_1_1="""SELECT COUNT(*) FROM Workshop
                        JOIN Customers ON Workshop.Cro_id= Customers.Cro_id 
                        WHERE Status='done' AND  Checked_out< %s AND Checked_out> %s
                        """ 
            cursor.execute(query_1_1,(today_date, First_of_month,))
            count_all_tech=cursor.fetchone()
            count_all_tech=int(count_all_tech[0])
            if count_all_tech==0:
                AVERAGE_JOBS_MONTH=0
            else:
                AVERAGE_JOBS_MONTH= int(count_tech_no)/int(count_all_tech)

            query2="""SELECT COUNT(*) FROM Workshop
                        JOIN Customers ON Workshop.Cro_id= Customers.Cro_id 
                        WHERE Tech_number= %s AND  Checked_out< %s AND Checked_out> %s"""
            cursor.execute(query2,(tech_no,today_date,First_of_month,))
            JOBS_DONE_MONTH=cursor.fetchall()
            JOBS_DONE_MONTH=JOBS_DONE_MONTH[0]
            
            query3="""SELECT COUNT(*) FROM Workshop
                        JOIN Customers ON Workshop.Cro_id= Customers.Cro_id 
                        WHERE Tech_number= %s AND Status='pending' OR Status='busy'
                        """ 
            cursor.execute(query3,(tech_no,))
            JOBS_UNCOMPLETED=cursor.fetchall()
            JOBS_UNCOMPLETED=JOBS_UNCOMPLETED[0]
            
            KPA_PERFORMANCE=AVERAGE_JOBS_MONTH *5
            #get jobs done per month dvided by total jobs done per month, now multiply by 10 for a rank on 10   
        
            return render_template("UserProfile.html", AVERAGE_JOBS_MONTH=AVERAGE_JOBS_MONTH, JOBS_DONE_MONTH=JOBS_DONE_MONTH,
            JOBS_UNCOMPLETED=JOBS_UNCOMPLETED,KPA_PERFORMANCE=KPA_PERFORMANCE)
        except Exception as e:
            #app.logger(e)
            return "An internal error occurred", 500

@app.route('/monthlyProfit')#TO DO
def monthlyProfit():
    return "bad request",500
"""    try:
        with mysql.connection.cursor() as cursor:
            today_date=get_date()
            today_date=datetime.datetime.strptime(today_date, "%m")
            year_ago=today_date-datetime.timedelta(month=12)
            dates=[] #this will end becoming a array of  stirng ertainning to dates 
            costs=[] # a array of decimasl
            for i in range(7):
                date=week_ago+datetime.timedelta(days=i)
                date=datetime.datetime.strftime(date, "%Y-%m-%d")
                query="SELECT Checked_out,SUM(Total_Cost) FROM workshop WHERE Checked_out = %s "
                cursor.execute(query,(date,))
                data=cursor.fetchall()
                for information in data:
                    if information[0]==None:
                        dates.append(str(date))
                        costs.append(float(0.00))
                    else:
                        dates.append(str(information[0])) 
                        costs.append(float(information[1]))
            return render_template("monthlyProfit.html",dates=dates,costs=costs)
    except Exception as e:
        ##app.logger(e)
         return "An internal error occurred", 500"""
    

@app.route('/JobPieChart')#TO DO
def JobPieChart():
    return "An internal error occurred", 500
"""    with mysql.connection.cursor() as cursor:
        tech_no=session['Tech_number']
        try:
            query=SELECT Tech_number, Repair_type FROM Workshop
                JOIN Customers ON Workshop.Cro_id = Customers.Cro_id
                WHERE Tech_number= %s
                GROUP BY Repair_type
            cursor.execute(query,(tech_no,))
            data= cursor.fetchall()
            return render_template("JobPieChart.html",data=data)
        except Exception as e:
            app.logger(e)"""
            

@app.route('/PercentageJobsCompleted')
def PercentageJobsCompleted(): 
    #will be a pie chart representing number of jobs theyve complated compared to all jobs completeed
    try:
        tech_num=session['Tech_number']
        with mysql.connection.cursor() as cursor:
            query= """SELECT COUNT(*) FROM Workshop WHERE Status= 'done'"""
            cursor.execute(query)
            No_all_completed=cursor.fetchone()
            No_all_completed=No_all_completed[0]

            query2="""SELECT COUNT(*) FROM Workshop
                JOIN Customers ON Workshop.Cro_id= Customers.Cro_id 
                WHERE Status= 'done' AND Tech_number=%s"""
            cursor.execute(query2,(tech_num,))
            No_completed_tech=cursor.fetchone()
            No_completed_tech=No_completed_tech[0]
            data=[No_all_completed,No_completed_tech] #is [5,9]
        return render_template("PercentageJobsCompleted.html",data=data)
    except Exception as e:
        #app.logger(e)
         return "An internal error occurred", 500
    return redirect('home')

