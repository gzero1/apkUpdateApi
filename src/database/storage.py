import mysql.connector

connectionConfig = {
    "host": "192.168.0.16",
    "user": "UpdaterApi",
    "password": "gbm290102",
    "database": "g01_updater",
    "auth_plugin": 'mysql_native_password'
}

mydb = mysql.connector.connect(
    **connectionConfig
)

def query(queryString, params, ifFech = True):
    if (mydb.is_connected()):
        mycursor = mydb.cursor()
    else:
        mydb.connect(**connectionConfig)
        mycursor = mydb.cursor()
    mycursor.execute(queryString, params)
    
    if (ifFech):
        return mycursor.fetchall()
    else:
        mydb.commit()
        return 'Executed'

