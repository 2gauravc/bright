import boto3
import sys, getopt 
import pandas as pd
def gsearch(query):
    try:
        from GoogleNews import GoogleNews
    except ImportError:
        print("No module named 'GoogleNews' found")
 
    # Google Search and return 10 links
    googlenews = GoogleNews()
    googlenews.set_lang('en')
    googlenews.set_period('60d')
    googlenews.search(query)
    return(googlenews.results (sort=True))

def convert_results_table(search_res_json):
    title = []
    media= []
    date_time = []
    desc = []
    link  = []
    try: 
        for news_item in search_res_json:
            title1 = news_item['title']
            media1 = news_item['media']
            date_time1 = news_item['datetime']
            desc1 = news_item['desc']
            link1 = news_item['link']
            
            title.append(title1)
            media.append(media1)
            date_time.append(date_time1)
            desc.append(desc1)
            link.append(link1)
    except: 
        print('Parsing error. Moving on \n')

    results_df = pd.DataFrame({'title' : title, 'media': media, 'date_time': date_time, \
                              'desc': desc, 'media': media, 'link': link})
    return(results_df)


def main(argv):
    try:
        opts, args = getopt.getopt(argv,"i:", ["entity="])
    except getopt.GetoptError:
            print ('Usage: python app.py --entity=<entity name>')
            sys.exit(2)
    for opt, arg in opts:
        if opt == '--entity':
            ename = arg
    # Google search for the person name and get the first 20 query links 
    search_result = gsearch(ename)
    results_df = convert_results_table(search_result)
    print(results_df.head())

if __name__ == "__main__":
    main(sys.argv[1:])

