from sre_constants import SUCCESS
from matplotlib.style import available
import streamlit as st
from assignment import *
import MetaTrader5 as mt5
from no_api import get_tweets
import nltk
import matplotlib.pyplot as plt
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('words')
from nltk.corpus import stopwords
from collections import Counter
from string import punctuation
from wordcloud import WordCloud, STOPWORDS
from nltk.corpus import words
from nltk.util import ngrams


header =st.header("The FXBullies Algo-Trading System")

Walkthrough = st.sidebar.header('Walkthrough') 

walkthrough1 = st.sidebar.text(' 1. You select the pair you want to\ntrade.\n2. You enter the lot-size you want \nto trade.\n3. Go algo if the algorithm says so\nif not stay tuned for trading\nopportunities')

supported_pairs =st.sidebar.header('Supported pairs')
supported_pairs_sub =st.sidebar.text('EURUSD\nUSDCAD\nGBPUSD\nNZDUSD\nUSDJPY')

Strategies =st.sidebar.header('Strategies')
Strategies_sub =st.sidebar.text('SUPPORT AND RESISTANCE\nMOVING AVERAGES\nRELATIVE STRENGTH INDEX')

Requirements =st.subheader('REQUIREMENTS')
requirements_subs ='You are required to have the latest version of MetaTrader5.\nYou can download on the [MetaTrader website](https://www.metatrader5.com/en/download)\nAfter setting up, you need to allow "Algo Trading" on your metatrader app \nby tapping on it'

st.markdown(requirements_subs,unsafe_allow_html=True)

##main body

available_pairs = ['Select from these pairs','EURUSD','USDCAD','USDJPY','NZDUSD','GBPUSD']
currency_pair_option = st.selectbox('What pair are we trading today', available_pairs)


stop_words = stopwords.words('english') +list(punctuation) + ["''","''","''","''","万円", "''"] + ["''"]
if currency_pair_option != 'Select from these pairs':
    df = get_tweets(currency_pair_option, 50)
    
    df['Clean Tweets'] = df.Tweets.apply(lambda x: ' '.join([w for w in str(x).lower().split() if w not in stop_words and w.isalpha()]))
    df.dropna()

    new_df = pd.DataFrame(df)
    new_df = new_df[['Date','User','Clean Tweets']]

    new_df = new_df.set_index('Date')
    st.header('A dataframe of the most recent tweets containing {}'.format(currency_pair_option))

    st.dataframe(new_df)

    ##most common words unigram
    unigram = Counter()

    for row in df['Clean Tweets'].str.split(' '):
        unigram.update(row)
        
    unigram_output = dict(unigram.most_common(20))


    tweets = df['Tweets'].to_numpy()

    fig = plt.figure(figsize=(15,8))

    plt.subplot(2,2,1)
    plt.barh(list(unigram_output.keys()), list(unigram_output.values()))
    plt.title('Top 10 words in tweets concerning the {} pair'.format(currency_pair_option))

    st.pyplot(fig)

    ##most common words bigram
    bigrams = Counter()

    for row in df['Clean Tweets'].str.lower():
        bigrams.update(ngrams(row.split(' '), 2))

    bigram_output = dict()
    for key, value in dict(bigrams.most_common(20)).items():
        bigram_output[' '.join(key)] = value

    def return_signal(dic):
        if 'closed buy' in dic and 'closed sell' in dic:
            if dic['closed buy']>dic['closed sell']:
                return 'sell'
            elif dic['closed sell'] > dic['closed buy']:
                return 'buy'
        elif 'closed buy' in dic and not 'closed sell' in dic:
            return 'sell'
        elif 'closed sell' in dic and not 'closed buy' in dic:
            return 'buy'
        else:
            return 'neutral'


    tweet_signal = return_signal(bigram_output)




    bigram_fig = plt.figure(figsize=(15,8))

    plt.subplot(2,2,1)
    plt.barh(list(bigram_output.keys()), list(bigram_output.values()))
    plt.title('Top 10 words in tweets concerning the {} pair'.format(currency_pair_option))

    st.pyplot(bigram_fig)

    if tweet_signal == 'buy':
        st.success("Higher Probability of buy because of limited sell orders")
    elif tweet_signal == 'sell':
        st.success("Higher Probability of sells because of limited buy orders")
    else:
        st.success("Low trades in action from twitter")

    ## wordcloud
    st.header("Wordcloud of {}".format(currency_pair_option))
    fig2 = plt.figure(figsize=(10,6))

    comment_words = ''
    Stopwords_list = set(STOPWORDS)
    for val in df['Clean Tweets'].loc[:20]:
        
        val = str(val)

        tokens = val.split()
        
        for i in range(len(tokens)):
            tokens[i] = tokens[i].lower()
        
        comment_words += " ".join(tokens)+" "
    
    wordcloud = WordCloud(width = 800, height = 800,
                    background_color ='white',
                    stopwords = Stopwords_list,
                    min_font_size = 10).generate(comment_words)
    
    # plot the WordCloud image                      
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad = 0)
    
    plt.show()

    st.pyplot(fig2)


    Algo_mode= st.header('Algo-mode')








    lot_size = st.text_input('What lot size are you willing to trade','0.01')

    rates_dataframe = MT5.get_rates(currency_pair_option,20)


    if available_pairs != 'Select from these pairs':
        st.subheader('Here is a dataframe of {} in an hour timeframe'.format(currency_pair_option))
        st.dataframe(rates_dataframe)
        custom_df = rates_dataframe['close']

        #Display line chart
        line_chart = plt.figure(figsize=(15,8))
        plt.style.use('dark_background')
        plt.plot(custom_df)
        
        st.pyplot(line_chart)

        buy,sell = MT5.our_strategy(currency_pair_option)

        if buy == False and sell == True:
            st.subheader('Looks like we are selling {}'.format(currency_pair_option))
        elif buy == True and sell == False:
            st.subheader('We are buying to the moooooon')
            
        else:
            st.subheader('The market is scary at the moment, we are still observing')
        l_size = float(lot_size)
        if buy == False and sell == False:
            st.warning('Cannot go algo mode 😞')
        else:
            if st.button('Algo Mode'):
                st.success('We have something special for you, open your meta trader app')
                
                balance, profit,equity = MT5.run_on_mt5(currency_pair_option, l_size)

                st.write("========================================================================================")
                st.write("Date: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if buy == True:
                    st.write("Order: BUY")
                else:
                    st.write("Order: SELL")
                st.write("Symbol: ", currency_pair_option)
                st.write("Balance: {}".format(balance))
                st.write("Equity: {}".format(equity))
                st.write("Profit: {}".format(profit))
                st.write("========================================================================================")
                
        




    