'''

'''
from firebase import firebase
from flask import Flask,render_template,request,redirect,url_for
from flask_cors import CORS, cross_origin

from sklearn.metrics import accuracy_score
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from csv import writer
from collections import defaultdict

import csv
import pandas as pd
import numpy as np
import yagmail
import seaborn as sns
import random


app = Flask(__name__,template_folder='template',static_folder='static')
app.config['SECRET_KEY'] = ''
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/login": {"origins": "http://localhost:5000"}})


@app.route("/")
def index():
    return render_template('index.html')

@app.route('/final',methods=['POST'])
def getres():
	#final two values
	value1='SAFE to drink'
	value2='UNSAFE to drink'

	#get value from the frontend form
	wid=request.form['d']
	ph=request.form['ph']
	cond=request.form['conductivity']
	turb=request.form['turbidity']
	place=request.form['place']
	lat=request.form['lat']
	lon=request.form['lon']
	email=request.form['email']
	#make a list for that form elements
	lst=[ph,cond,turb,0]

	#Connect firebase by giving real-time url
	fb = firebase.FirebaseApplication('https://water-quality-42101-default-rtdb.firebaseio.com/',None)

	#fetch the results from firebse root /
	result = fb.get('/water', None)

	lst1=list()
	lst2=list()
	
	if result is not None:
		#if firebase has data then traverse through each row
		for sid in result.keys():
			
			#fetch every row data and assign it to respective variables
			d=result[sid]
			fb_ph=d['ph']
			fb_cond=d['Conductivity']
			fb_turb=d['Turbidity']
			fb_pot=d['Potability']
		
			#append fetched data to lst1
			lst1=[fb_ph,fb_cond,fb_turb,fb_pot]
			#append the lst1 to lst2 as its numpy array
			lst2.append(lst1)
			
	#append the given input at the end of the lst2		
	lst2.append(lst)

	with open('checkwater.csv', 'w', newline='') as write_obj:
		#here we will convert lst lst2 to csv using writerows
		csv_writer = writer(write_obj)
		csv_writer.writerows(lst2)
	
	
	#read the updated csv
	dataset=pd.read_csv('checkwater.csv',error_bad_lines=False)

	#this will contains no of rows and no of columns
	(rows,cols)=dataset.shape
	
	#make dataframe such that X contains data of ph,turbidity,conductivity and y contains target value
	X=pd.DataFrame(dataset.iloc[:rows-1,:-1])
	y=pd.DataFrame(dataset.iloc[:rows-1,-1])
	
	#train the model
	X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.5, random_state=0)
	X_test=X_test.append(pd.DataFrame(dataset.iloc[rows-1:,:-1]))
	y_test=y_test.append(pd.DataFrame(dataset.iloc[rows-1:,:-1]))   


	#apply algorithm
	model=RandomForestClassifier()
	model.fit(X_train,y_train)
	
	#predict for test data
	y_pred=model.predict(X_test)
	y_pred=pd.DataFrame(y_pred,columns=['Predicted'])

	#containd total no of rows and cols in y_pred
	(r,c)=y_pred.shape
	n=y_pred.iloc[r-1,0]
	
	#take predicted data and place it in m 
	m=int(round(n))
	dataset.iloc[rows-1:,-1]=m
	dataset.to_csv("checkwater.csv", index=False)

	#m==0 is safe and m==1 is unsafe	
	if m==0:
		res=value1
	elif m==1:
		res=value2

	#save your email and password in password file and open it
	f=open("password.txt","r")
	lines=f.readlines()
	email_txt=lines[0]
	password_txt=lines[1]

	#send message to the email id given
	message = "Your Water is "+res+" with the following values:\n"+"Conductivity (<400mg/l) :  "+str(cond)+"\nTurbidity (1-4.5NTU)  :  "+str(turb)+"\npH (6.5-8.5)  :  "+str(ph)
	yag = yagmail.SMTP(email_txt,password_txt)
	yag.send(to=email, subject="Water Quality in Your Area",contents=message)

	#upload to water as new one will also be added when its predicts next input
	fb.post('/water',
                  {'ph':ph,
                   'Conductivity':cond,
    				'Turbidity':turb,
    				'Potability':m
                  })

	#upload predicted data to firebase if place is not present else show updated
	predicted_res=fb.get('/predicted',None)

	if predicted_res is not None:
		for i in predicted_res.keys():
			pre_data=predicted_res[i]

			if pre_data['Place']==place and pre_data['Latitude']==lat and pre_data['Longitude']==lon and pre_data['Water ID']==wid:
				fb.put("predicted/"+i,"ph",ph)
				fb.put("predicted/"+i,"Conductivity",cond)
				fb.put("predicted/"+i,"Turbidity",turb)
				fb.put("predicted/"+i,"Potability",m)
				fb.put("predicted/"+i,"Place",place.lower())
				fb.put("predicted/"+i,"Latitude",lat)
				fb.put("predicted/"+i,'Water ID',wid)
				fb.put("predicted/"+i,"Longitude",lon)
				fb.put("predicted/"+i,"Email",email)
				return ('<html><body><h1 style=color:red>water at your place is '+res+'</h1></body></html>')

	fb.post('/predicted',
                  {'ph':ph,
                   'Conductivity':cond,
    				'Turbidity':turb,
    				'Water ID':wid,
    				'Place':place.lower(),
    				'Latitude':lat,
    				'Longitude':lon,
    				'Email':email,
    				'Potability':m
                  })

	#print predicted data
	return ('<html><body><h1 style=color:red>water at your place is '+res+'</h1></body></html>')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    #If the method is post (user submits an request to validate credentials)
    if request.method == 'POST':
    	#we will take given uname and password store it in variable
        uname = request.form['username']
        pwd = request.form['password']

        #if username and password matches load admindash function else show error
        if uname != 'Admin' or pwd != 'admin':
            error = "Invalid Credentials. Please try again."
        else:
            return redirect(url_for("admindash",id="b3admin"))
            

    return render_template('login.html', error=error)

#to print bar data
@app.route('/<id>')
def admindash(id):
    fb = firebase.FirebaseApplication('https://water-quality-42101-default-rtdb.firebaseio.com/', None)
    result = fb.get('/predicted', None)

    #dic and count of safety for pie chart
    #using default dic as it does not raise key error 
    data = defaultdict(list)
    scnt = 0
    ncnt = 0
    lst = []

    #bardata dictionary
    bar_data = {'Place': 'percentage of safety'}
    if result is not None:
        # create data for bargraph and pie chart
        for i in result.keys():
            d = result[i]
            fb_pot = d['Potability']
            fb_place = d['Place']

            # append all place to list
            lst.append(fb_place)

            # if water is safe then count it and add place:no_of_safety to dictionary
            if fb_pot == 0:
            	#total safety for incrementing
                scnt += 1
                
                #for bar_data we check whethergiven key(place) exists if it does then we will increment
                #by 1 else we initialize to 1
                if fb_place in bar_data.keys():
                    bar_data[fb_place] += 1
                else:
                    bar_data[fb_place] = 1
            else:
            	#total non-safe count incremented
                ncnt += 1

    # to calculate percentage of safety
    for key, value in bar_data.items():
        if value != 'percentage of safety':
            bar_data[key] = (value / lst.count(key)) * 100
    # pie chart data
    data = {'Potability': 'Count', 'safe': scnt, 'not safe': ncnt}
    return render_template('admin.html', data=data, data2=bar_data)

if __name__ == "__main__":
    app.run(debug = True)
