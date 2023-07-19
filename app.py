import boto3
import sys, getopt 
import pandas as pd
import difflib 
import openai
import json 
import os 
import re
from io import StringIO
from tabulate import tabulate 

def gsearch(query):
    try:
        from GoogleNews import GoogleNews
    except ImportError:
        print("No module named 'GoogleNews' found")
 
    # Google Search and return 10 links
    googlenews = GoogleNews()
    googlenews.set_lang('en')
    googlenews.set_period('1d')
    googlenews.search(query)
    return(googlenews.results (sort=True))

def convert_results_table(search_res_json, ename):
    title = []
    media= []
    date_time = []
    desc = []
    link  = []
    enamelist = []
    try: 
        for news_item in search_res_json:
            title1 = news_item['title']
            media1 = news_item['media']
            date_time1 = news_item['datetime']
            desc1 = news_item['desc']
            link1 = news_item['link']
            ename1 = ename
            
            title.append(title1)
            media.append(media1)
            date_time.append(date_time1)
            desc.append(desc1)
            link.append(link1)
            enamelist.append(ename1)
    except: 
        print('Parsing error. Moving on \n')

    results_df = pd.DataFrame({'ename':enamelist, 'title' : title, 'media': media, 'date_time': date_time, \
                              'desc': desc, 'media': media, 'link': link})
    return(results_df)

def generate_chatgpt_prompt(ename, recs):
    file = open('prompt-1.txt', mode = 'r')
    ptxt = file.readlines()
    file.close()
    all_lines = ''.join(map(str,ptxt))
    #print(all_lines)
    #recs_s = recs.to_string(header=True,index=False,index_names=False).split('\n')
    # Adding a comma in between each value of list
    #recs_s = [','.join(ele.split()) for ele in recs_s]
    recs_s = recs.to_csv(index=False)
    #print(recs_s)
    prompt_text = all_lines.replace("<<ename>>", ename)
    prompt_text = prompt_text.replace("<<json>>", str(recs_s))
    #print(prompt_text)
    return(prompt_text)

def get_chatgpt_resp(question): 
    openai.api_key = os.environ['OPENAI_API_KEY']
    response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                    {"role":"system","content":"You are a chatbot"},
                    {"role":"system","content":question}]
    )
    result = ''
    for choice in response.choices:
        result+=choice.message.content
    
    ch_rep_sio = StringIO(result)
    ch_rep_df = pd.read_csv(ch_rep_sio, sep=',')

    #print(ch_rep_df.head())
    # assign column names 
    columns = ['id', 'credit_risk', 'signal']
    ch_rep_df.columns = columns
    ch_rep_df.columns = ch_rep_df.columns.str.strip()

    ch_rep_df['credit_risk'] = ch_rep_df['credit_risk'].str.strip()
    ch_rep_df['signal'] = ch_rep_df['signal'].str.strip()


    return (ch_rep_df)

def process_ename(ename, recs):
    prompt_txt = generate_chatgpt_prompt(ename, recs)
    ch_rep_df = get_chatgpt_resp(prompt_txt)
    print(ch_rep_df)
    ch_rep_adv_df = ch_rep_df.loc[ch_rep_df['credit_risk']=='Yes',]
    print(ch_rep_adv_df)
    print ("\t Found {} news items with adverse news for {}".format(ch_rep_adv_df.shape[0], ename))
    if ch_rep_adv_df.shape[0] > 0: 
        title = pd.merge(ch_rep_adv_df, recs, on='id' )
        print(tabulate(title[['title', 'signal']], headers='keys', tablefmt='psql'))
        

def main(argv):
    scrapeon = False 
    saveon = False 
    try:
        opts, args = getopt.getopt(argv,"e:sv", ['entityfile=','scrapeon', 'saveon'])
    except getopt.GetoptError:
            print ('Usage: python app.py --entityfile=<entity file path>')
            sys.exit(2)
    for opt, arg in opts:
        if opt in ('-e', '--entityfile'):
            efile = arg
        elif opt in ('-s', '--scrapeon'):
            scrapeon = True 
        elif opt in ('-v','--saveon'):
            saveon = True
        
    file = open(efile, mode = 'r')
    enames = file.readlines()
    enames_l = enames[0].split(',')
    file.close()
    
    if scrapeon:
        # Google search for the entity name and get the first 20 query links 
        results = pd.DataFrame()
        print ("#######################")
        print ("1. News Scraping")
        print ("#######################")
        print("Starting news scraping.")
   
        for ename in enames_l:
            search_result = gsearch(ename)
            results_df = convert_results_table(search_result, ename)
            print ("\t Entity: {}. Found {} items.".format(ename, results_df.shape[0]))
            results = pd.concat([results, results_df])
       
        print("Finished news scraping. Found {} news items for {} unique entities".format(results.shape[0], results.ename.nunique()))
        if saveon: 
            from datetime import datetime
            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            str_current_datetime = str(current_datetime)
            file_name = 'results'+str_current_datetime+'.csv'
            results.to_csv(file_name)

        print ("#######################")
        print ("2. Removing Duplicates")
        print ("#######################")
    else: 
        results = pd.read_csv('results2023-07-19.csv', index_col=[0])

    results['id'] = results.index

    print("Starting duplicate removal.")
    # Get Similarity grid by title 
    #df = results.loc[results['ename'] == 'Samsung Electronics']
    #df['sim'] = [difflib.get_close_matches(x, df['title'], cutoff=0.7)  for x in df['title']]
    #sim_df = df.explode('sim')
    #sim_df.to_csv('sim.csv')
    #print(pd.crosstab(sim_df.title, sim_df.sim))
    print("Finished duplicate removal. Removed 0 records")
    
    print ("#######################")
    print ("3. Starting GPT classification")
    print ("#######################")
    # Prepare the prompt 
    adv_items = []
    for ename in results.ename.unique(): 
        recs = results.loc[results['ename'] == ename, ['id', 'ename', 'title']]
       # if ename == 'Samsung Electronics': 
#            json_records = results.loc[results['ename'] == ename, ]\
#                .groupby(['ename']).apply(lambda x: x[['id', 'title']]\
#                                        .to_dict('records'))\
#                                            .reset_index().rename(columns={0:'news_items'}).to_json(orient ='records') 
        #if ename == ' VanMoof': 
        process_ename(ename, recs)

    # Send the news items with a credit risk signal to SNS Topic 

if __name__ == "__main__":
    main(sys.argv[1:])

