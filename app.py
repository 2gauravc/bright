import boto3
import sys, getopt 

def gsearch(query, num_results):
    try:
        from GoogleNews import GoogleNews
    except ImportError:
        print("No module named 'GoogleNews' found")
 
    # Google Search and return 10 links
    googlenews = GoogleNews()
    googlenews.set_lang('en')
    googlenews.set_period('7d')
    googlenews.search('APPLE')
    return(googlenews.results (sort=True))

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
    num_results=20
    search_links = gsearch(ename, num_results)
    print (search_links)


if __name__ == "__main__":
    main(sys.argv[1:])

