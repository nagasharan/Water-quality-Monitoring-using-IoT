from firebase import firebase
import csv

with open('potability.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    
    for row in csv_reader:
        ph=row[0]
        cond=row[1]
        turb=row[2]
        pot=row[3]
        
        fb = firebase.FirebaseApplication('https://water-quality-42101-default-rtdb.firebaseio.com/',None)
        result = fb.post('/water', {'ph': ph,'Conductivity':cond,'Turbidity':turb,
                                    'Potability':pot})
