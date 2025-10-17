#EasyIBKR 

A helper module which makes automating trades using IBKR and Python MUCH easier through helper functions 
which sort through the confusing syntax elements.

Note: This build is based on ib_insync, though this may be updated to the newer maintained async version


HOW TO USE:

first, run the connect() function. By default it uses the params TWS API sets for you (make sure to set up your TWS to work with API!!), however you can change this by calling the function with params;

connect(ip,port,clientId)

-------Getting Information-------

getLiquidity() -> returns your account summary 
getValue() -> returns your total account value (cash + positions)

getCurrentBasics(ticker) -> returns a list of [bid,ask,last,open] for the specified ticker 

getHistoricals(ticker,duration,size,toShow,endDateTime) 
duration is how far back to go 
size is the bar size 
toShow is what point in the bar to show (open,close,high,low,midpoint) 
endDateTime is the last date to get data for, by default it goes until the latest it can 


-------Placing Trades--------

placeLimit(ticker,quantity,short,limit)
short -> a boolean, if True then places a short trade, if False, long 
limit -> limit price 

placeBracket(ticker,qty,short,limit,stopLoss,takeProfit) 
same as Limit but we can specify stopLoss and takeProfit limit prices, orders are One-Cancels-Order 


## Installation

```Bash
pip install easyIBKR 

