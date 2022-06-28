import smtplib

fb_ph=8
fb_turb=4
message = "Turbidity (should be 1.5-4.5NTU) sensor value : "+str(fb_turb)+"\npH (should be 6.5-7.5)  sensor value : "+str(fb_turb)+" \n one of the above is out of range \n Please take measures immediately!!"
smtpUser="project.be.jnn@gmail.com"
smtpPass="SSVP@2021"
toAdd = "project.b3.jnn@gmail.com"
fromAdd = smtpUser
subject="water quality in your area"
header= "Take action Fast on your water"
body="values of ph and turbidity are: "

s=smtplib.SMTP("smtp.gmail.com",587)
s.ehlo()
s.starttls()
s.ehlo()

s.login(smtpUser,smtpPass)
s.sendmail(fromAdd,toAdd , message)
s.quit()