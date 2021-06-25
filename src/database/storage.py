import mysql.connector


mydb = mysql.connector.connect(
    host = "192.168.0.16",
    user = "UpdaterApi",
    password = "gbm290102",
    database="g01_updater",
    auth_plugin='mysql_native_password'
)

def query(queryString, params, ifFech = True):
    mycursor = mydb.cursor()
    mycursor.execute(queryString, params)
    
    if (ifFech):
        return mycursor.fetchall()
    else:
        mydb.commit()
        return 'Executed'

