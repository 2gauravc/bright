import boto3
import sys, getopt 
import pandas as pd
import difflib 

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

def chatgpt_prompt(ename, res_df):
    file = open('prompt.txt', mode = 'r')
    ptxt = file.readlines()
    enames_l = enames[0].split(',')
    file.close()
    
    all_links = '\n'.join(map(str,search_links))
    prompt_text = "You are a expert KYC analyst. I need help to identify if there is any adverse news about {}\
       in the following links. \n {}. \n. In the reply include a 20 word summary of the text in each link and if you find any adverse\
           news (Yes or No)".format(pname, all_links)
    return(prompt_text)


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
        results = pd.read_csv('output/results.csv', index_col=[0])

    print("Starting duplicate removal.")
    # Get Similarity grid by title 
    #df = results.loc[results['ename'] == 'Samsung Electronics']
    #df['sim'] = [difflib.get_close_matches(x, df['title'], cutoff=0.7)  for x in df['title']]
    #sim_df = df.explode('sim')
    #sim_df.to_csv('sim.csv')
    #print(pd.crosstab(sim_df.title, sim_df.sim))
    print("Finished duplicate removal. Removed 0 records")
    
    # Generate the prompt 
    json_records = results[['ename','title', 'link']].to_json(orient ='records') 
    print(json_records)

    # Send the news items with a credit risk signal to SNS Topic 

if __name__ == "__main__":
    main(sys.argv[1:])

