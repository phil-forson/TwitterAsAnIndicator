import MetaTrader5 as mt5
import pandas as pd
import time
import warnings
from datetime import datetime
import ta
warnings.filterwarnings("ignore")
from sys import exit


mt5.initialize()


class MT5:

   def get_rates(symbol, n, timeframe=mt5.TIMEFRAME_H1):

        #initializing the metatrader 5 app
        mt5.initialize()
        #getting the current date
        time_now = datetime.now()
        #mt5 function to copy rates
        rates = mt5.copy_rates_from(symbol, timeframe, time_now, n)

        #converting the rates to a dataframe
        rates_df = pd.DataFrame(rates)

        rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
        #adding the time column to the rates dataframe
        rates_df['time'] = pd.to_datetime(rates_df['time'], format='%Y-%m-%d')

        #setting the time as the index
        rates_df = rates_df.set_index('time')

        #return the dataframe
        return rates_df

    #create an orders function
   def orders(symbol, lot, buy=True, id_position="No Id"):

        #initialize the metatrader if it is not already initialized
       if mt5.initialize() == False:
           mt5.initialize()


       filling_mode = mt5.symbol_info(symbol).filling_mode - 1

       ask_price = mt5.symbol_info_tick(symbol).ask

       bid_price = mt5.symbol_info_tick(symbol).bid


       point = mt5.symbol_info(symbol).point

       deviation = 20  
       if id_position == None:

           if buy:
               type_trade = mt5.ORDER_TYPE_BUY
               sl = ask_price*(1-0.004)
               tp = ask_price*(1+0.009)
               price = ask_price

           else:
               type_trade = mt5.ORDER_TYPE_SELL
               sl = bid_price*(1+0.004)
               tp = bid_price*(1-0.009)
               price = bid_price

           # Open the trade
           request = {
               "action": mt5.TRADE_ACTION_DEAL,
               "symbol": symbol,
               "volume": lot,
               "type": type_trade,
               "price": price,
               "deviation": deviation,
               "sl": sl,
               "tp": tp,
               "magic": 234000,
               "comment": "group 8",
               "type_time": mt5.ORDER_TIME_GTC,
               "type_filling": filling_mode,
           }

           result = mt5.order_send(request)
           result_comment = result.comment

       else:

           if buy:
               type_trade = mt5.ORDER_TYPE_SELL
               price = bid_price


           else:
               type_trade = mt5.ORDER_TYPE_BUY
               price = ask_price

           request = {
               "action": mt5.TRADE_ACTION_DEAL,
               "symbol": symbol,
               "volume": lot,
               "type": type_trade,
               "position": id_position,
               "price": price,
               "deviation": deviation,
               "magic": 234000,
               "comment": "group 8",
               "type_time": mt5.ORDER_TIME_GTC,
               "type_filling": filling_mode,
           }

           result = mt5.order_send(request)
           result_comment = result.comment
       return result.comment

   def resumetrade():
      mt5.initialize()

      # Define the name of the columns that we will create
      columns = ["ticket", "position", "symbol", "volume"]


      current_orders = mt5.positions_get()

      summary = pd.DataFrame()


      for order in current_orders:
           order_df = pd.DataFrame([order.ticket,
                                          order.type,
                                          order.symbol,
                                          order.volume],
                                         index=columns).transpose()
           summary = pd.concat((summary, order_df), axis=0)
      return summary


   def run(symbol, long, short, lot):

        # Initialize the connection if there is not
        if mt5.initialize() == False:
            mt5.initialize()

        # Display the date and the currency pair
        print("------------------------------------------------------------------")
        print("Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("SYMBOL:", symbol)

        # Initialize the meta trader app
        current_positions = MT5.resumetrade()
        # Print Buy and Sell 
        print(f"BUY: {long} \t  SELL: {short}")

        #
        try:
            position = current_positions.loc[current_positions["symbol"]==symbol].values[0][1]

            order_no = current_positions.loc[current_positions["symbol"]==symbol].values[0][0]
        except:
            position= None
            order_no = None

        if position == 0:
            trade_type = "BUY {}".format(symbol)
        elif position == 1:
            trade_type = "SELL {}".format(symbol)
        else:
            trade_type = "NO POSITION"
        print(f"CURRENT POSITION OF {symbol}: {trade_type} \t ID OF {symbol}: {order_no}")

        if long==True and position==0:
            long=False

        elif long==False and position==0:
            res = MT5.orders(symbol, lot, buy=True, id_position=order_no)
            print(f"CLOSE LONG TRADE: {res}")

        elif short==True and position ==1:
            short=False

        elif short == False and position == 1:
            res = MT5.orders(symbol, lot, buy=False, id_position=order_no)
            print(f"CLOSE SHORT TRADE: {res}")

        else:
            pass

        if long==True:

            res = MT5.orders(symbol, lot, buy=True, id_position=None)
            print(f"OPEN LONG TRADE: {res}")

        if short==True:
            res = MT5.orders(symbol, lot, buy=False, id_position=None)
            print(f"OPEN SHORT TRADE: {res}")

        print("=====================================================")


   def our_strategy(pair):
        
        # Features Engineering Process
        df = MT5.get_rates(pair, 70)
        
        # Creating the 30 simple moving average
        df["SMA 30"] = df["close"].rolling(30).mean()

        # Creating the 60 simple moving average
        df["SMA 60"] = df["close"].rolling(60).mean()

        # Creating the  RSI Indication
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=20).rsi()
        
        #shifting the rsi down by one column
        df["previous day rsi"] = df["rsi"].shift(1)

        # print(df[["close","SMA 30","SMA 60"]].head(35))


        first_buy_indication = df["SMA 30"].iloc[-1] > df["SMA 60"].iloc[-1]
        second_buy_indication = df["rsi"].iloc[-1] < df["previous day rsi"].iloc[-1]

        first_sell_indication = df["SMA 30"].iloc[-1] < df["SMA 60"].iloc[-1]
        second_sell_indication = df["rsi"].iloc[-1] > df["previous day rsi"].iloc[-1]
        
        buy = first_buy_indication and second_buy_indication
        sell = first_sell_indication and second_sell_indication

        return buy,sell
    
   def run_on_mt5(pair, lot):

        live = True
        
        if live:
            account_info = mt5.account_info()
            print("==================================================================")
            print("==================================================================")
        start = datetime.now().strftime("%H:%M:%S")
        print("time is now")
        while True:
            # Verfication for launch
            if datetime.now().weekday() not in (5,6):
                is_time = datetime.now().strftime("%H:%M:%S") == start #"23:59:59"
                print("start")
            else:
                is_time = False

            
            # Launch the algorithm
            if is_time:
                
                # Open the trades
                print(is_time)
                    # Create the signals
                buy, sell = MT5.our_strategy(pair)


                    # Run the algorithm
                if live:
                    MT5.run(pair, buy, sell,lot)
                        # if buy != sell:
                        #     exit(0)

                else:
                    print(f"CURRENCY PAIR: {pair}\t"
                        f"Buy: {buy}\t"
                        f"Sell: {sell}")

            time.sleep(1)

            return account_info.balance, account_info.profit, account_info.equity

