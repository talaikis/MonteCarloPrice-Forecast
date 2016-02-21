import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as sc
import MySQLdb as mdb
import time
import seaborn as sns

scriptStart = time.time()

#connect to DB
def connect_to_DB():
    
    #Connect to the <a href="http://www.talaikis.com/mysql/">MySQL</a> instance
    db_host = '127.0.0.1'
    db_user = 'root'
    db_pass = '8h^=GP655@740u9'
    db_name = 'lean'

    con = mdb.connect(host = db_host, user = db_user, passwd = db_pass, db = db_name)
    
    return con

#disconnect from databse
def disconnect(con):
    # disconnect from server
    con.close()
    
#get data from <a href="http://www.talaikis.com/mysql/">MySQL</a>
def req_sql(sym, con, period):
    # Select all of the historic close data
    sql = """SELECT DATE_TIME, CLOSE FROM `"""+sym+"""` WHERE DATE_TIME >= (curdate() - interval """+str(period)+""" month) ORDER BY DATE_TIME ASC;"""

     #create a pandas dataframe
    df = pd.read_sql_query(sql, con=con, index_col='DATE_TIME')

    return df

#yeah, simply roll dice
def roll_Returns_dice(params):
    return sc.t.rvs(df=int(params[0]), loc=params[1], scale=params[2], size=100000)

#generate path
def bet_machine(starting_price, trades, params, trim, last, dta, plot_paths):
    
    value = starting_price
    global allReturns
    global allReturns1
    if len(allReturns) > 0:
        allReturns = []
    if len(allReturns1) > 0:
        allReturns1 = []
    global pathReturns
    global pathReturns1
    X = []
    Y = []
    positive_returns = []
    negative_returns = []
    i = 1
    
    #clean values
    returns = roll_Returns_dice(params)
    
    for r in returns:
        if r > 0 and r < trim[1]:
            positive_returns.append(r)
        if r < 0 and r > trim[0]:
            negative_returns.append(r)
    
    lossRate = 50
    
    #make date
    if last[1] < 10:
        m = "0"+str(last[1])
    else:
        m = str(last[1])
    if last[2] < 10:
        d = "0"+str(last[2])
    else:
        d = str(last[2])
    dte = str(last[0])+"-"+m+"-"+d
    dates = pd.date_range(dte, periods=trades)
    
    #make trading
    for i in range(0,  trades):
        #roll the next day
        ret = sc.norm.ppf(q=random.random(), loc=dta[0], scale=dta[1])        
        #calc return
        value = (1 + float(ret))*value
        Y.append(value)
        allReturns.append(ret)
        allReturns1.append(value)
        i += 1
        
    pathReturns.append(allReturns)
    pathReturns1.append(allReturns1)
    
    #default
    if plot_paths:
        plt.plot(dates, Y)

#script body
if __name__ == "__main__":
    
    #don't touch those
    x = 0
    allReturns = []
    pathReturns = []
    allReturns1 = []
    pathReturns1 = []
    xAx = []
    con = connect_to_DB()
    
    #inputs
    paths = 1000
    periods = 24 #months
    days = 252
    
    #get data, fit it, generate a similar sample and see if's similar
    data = req_sql("YAHOO_INDEX_GSPC", con, periods).pct_change().dropna()
    p = req_sql("YAHOO_INDEX_GSPC", con, periods).dropna()
    params = sc.t.fit(data.CLOSE)
    last_price = p.tail(1).CLOSE
    last_day = [int(p.tail(1).index.year), int(p.tail(1).index.month), int(p.tail(1).index.day)]
    d = [data.mean(), data.std(), data.var()]
    
    # make patths
    while x < paths:
        bet_machine(starting_price=last_price, trades=days, params=params, trim=[data.CLOSE.min(), data.CLOSE.max()], last=last_day, dta=d, plot_paths=False)
        print "Generated path no. %s" %x
        x += 1
    
    disconnect(con)
    
    #make date
    if last_day[1] < 10:
        m = "0"+str(last_day[1])
    else:
        m = str(last_day[1])
    if last_day[2] < 10:
        d = "0"+str(last_day[2])
    else:
        d = str(last_day[2])
    dte = str(last_day[0])+"-"+m+"-"+d
    dates = pd.date_range(dte, periods=days)
    
    #get average of all paths and percentiles 
    arr = np.array(pathReturns1)
    yAx_avg = []
    yAx_5 = []
    yAx_95 = []
    for trade in range(0, len(arr[0])):
        a = []
        for path in range(0, len(arr)):
            a.append(arr[path][trade])
        avg = np.mean(a)
        yAx_avg.append(avg)
        yAx_5.append(np.percentile(a=a, q=5))
        yAx_95.append(np.percentile(a=a, q=95))
    
    #plot history
    plt.plot(p.CLOSE)
    
    #plot mean and extreme percentiles
    plt.plot(dates, yAx_avg, lw=3, color='r')
    plt.plot(dates, yAx_5, lw=3, color='r')
    plt.plot(dates, yAx_95, lw=3, color='r')
    plt.grid(True)
    plt.ylabel('Price')
    plt.xlabel('Time')
    
    timeused = (time.time()-scriptStart)/60
    print("Done in ",timeused, " minutes")
    
    plt.show()