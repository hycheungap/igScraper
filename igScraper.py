import datetime
import time
import requests
import json
import os
import pandas


#  All json file generated is for reference or further usage
def scrapePosts(tag, pages=None):
    arr = []
    end_cursor = ''  # empty for the 1st page
    totalPage = 0

    if pages is not None:
        page_count = pages  # for version, desire no. of pages
        for i in range(0, page_count):
            url = "https://www.instagram.com/explore/tags/{0}/?__a=1&max_id={1}".format(tag, end_cursor)
            try:
                r = requests.get(url)
                # time.sleep(2)  # ensure the data is downloaded
                data = r.json()
                end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info'][
                    'end_cursor']  # value for the next page
                edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges']  # list with posts
            except Exception as e:
                print('Exception:', e)
                continue
            for item in edges:
                arr.append(item['node'])
            totalPage += 1
    else:
        page_count = 0  # while version, until last pages
        while end_cursor != None:
            url = "https://www.instagram.com/explore/tags/{0}/?__a=1&max_id={1}".format(tag, end_cursor)
            try:
                r = requests.get(url)
                # time.sleep(2)  # ensure the data is downloaded
                data = r.json()
                end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info'][
                    'end_cursor']  # value for the next page
                edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges']  # list with posts
            except Exception as e:
                print('Exception:', e)
                continue
            for item in edges:
                arr.append(item['node'])
            totalPage += 1

    with open('posts.json', 'w') as outfile:
        json.dump(arr, outfile)  # save to json
    print('Total posts scraped:', len(arr), '  Total pages scraped:', page_count)


def scrapePostsDetail():
    with open('posts.json', 'r') as f:
        posts = json.loads(f.read())
    postsDetail = []
    for item in posts:
        shortcode = item['shortcode']
        url = "https://www.instagram.com/p/{0}/?__a=1".format(shortcode)
        try:
            r = requests.get(url)
            time.sleep(1)  # ensure the data is downloaded
            # data = json.loads(r.text)
            data = r.json()
            if data['graphql']['shortcode_media']['location'] is not None:
                shortcode_media = data['graphql']['shortcode_media']
                postsDetail.append(shortcode_media)
        except Exception as e:
            print('Exception:', e)
            continue
    with open('postsDetail.json', 'w') as outfile:
        json.dump(postsDetail, outfile)  # save to json
    print('Valid posts detail with location:', len(postsDetail))


def scrapeLocations():
    postDetails = []
    locations = []
    with open('postsDetail.json', 'r') as f:
        postDetails = json.loads(f.read())  # load json data from previous step
    for item in postDetails:
        locationId = item['location']['id']  # get location for a post
        url = 'https://www.instagram.com/explore/locations/{0}/?__a=1'.format(locationId)
        try:
            r = requests.get(url)
            time.sleep(2.5)  # ensure the data is downloaded
            # data = json.loads(r.text)
            data = r.json()
            location = data['graphql']['location']
            locations.append(location)
        except Exception as e:
            print('location = \'Exception\' Scrape locations Exception:', e)
            location = 'Exception'  # identify for exception when get the response
            continue
    with open('locations.json', 'w') as outfile:
        json.dump(locations, outfile)  # save to json
    print('Valid location:', len(locations))


def generateCompletedPostsDetail():
    postsDetail = []
    locations = []
    print('Length of postsDetail equal to locations?', len(postsDetail) == len(locations))

    completedPostsDetail = []
    exceptionPostsDeatil = []
    with open('postsDetail.json', 'r') as f:
        postsDetail = json.loads(f.read())  # load json data from previous step
    with open('locations.json', 'r') as f:
        locations = json.loads(f.read())  # load json data from previous step
    for i in range(len(postsDetail)):
        shortcode = postsDetail[i]['shortcode']
        try:
            caption = postsDetail[i]['edge_media_to_caption']['edges'][0]['node']['text']
        except:
            caption = None
        location = postsDetail[i]['location']['name']
        locationId = postsDetail[i]['location']['id']
        try:
            country = locations[i]['directory']['country']['name']
        except:
            country = 'Exception'
        taken_at_timestamp = postsDetail[i]['taken_at_timestamp']
        date = datetime.datetime.fromtimestamp(taken_at_timestamp)
        post = {
            'shortcode': shortcode,
            'caption': caption,
            'location': location,
            'locationId': locationId,
            'country': country,
            'date': date.strftime('%d/%m/%Y')
        }
        if location == 'Exception' or country == 'Exception':  # store the exception post for later reprocess
            exceptionPostsDeatil.append(post)
            continue
        completedPostsDetail.append(post)
    with open('completedPostsDetail.json', 'w') as outfile:
        json.dump(completedPostsDetail, outfile)  # save to json
    with open('exceptionPostsDetail.json', 'w') as outfile:
        json.dump(exceptionPostsDeatil, outfile)  # save to json
    print('Completed posts detail', len(completedPostsDetail), ' Exception posts detail generated:',
          len(exceptionPostsDeatil))


def generalAnalysis():
    # Find frequency of posted countries/locations
    print('General analysis:')
    arr = []
    with open('completedPostsDetail.json', 'r') as f:
        completedPostsDetail = json.loads(f.read())  # load json data from previous step
    for item in completedPostsDetail:
        if item['country'] != None:
            place = item['country']
        else:
            place = item['location']
        arr.append(place)
    valueCount = pandas.Series(arr)
    with open('generalAnalysis.json', 'w') as outfile:
        json.dump(arr, outfile)  # save to json
    print(valueCount.value_counts())


def analysisOnSpecificPeriod(startM, endM):
    # Find frequency of posted countries/locations in a period
    startMonth = startM
    endMonth = endM
    startMonthName = datetime.date(1900, int(startMonth), 1).strftime('%B')
    endMonthName = datetime.date(1900, int(endMonth), 1).strftime('%B')
    print('\nAnalysis based in the period from', startMonthName, 'to', endMonthName)
    arr = []
    with open('completedPostsDetail.json', 'r') as f:
        completedPostsDetail = json.loads(f.read())
    for item in completedPostsDetail:
        postMonth = int(item['date'].split('/')[1])
        if postMonth >= int(startMonth) and postMonth <= int(endMonth):
            if item['country'] != None:
                place = item['country']
            else:
                place = item['location']
            arr.append(place)
    valueCount = pandas.Series(arr)
    with open('analysisOnSpecificPeriod.json', 'w') as outfile:
        json.dump(arr, outfile)  # save to json
    if len(arr) == 0:
        print('No data match')
    else:
        print(valueCount.value_counts())


# Program Start
####################################################################################
# Scrape data
startTime = datetime.datetime.now()  # Count for execution time
completedPosts = []
tag = 'trip'  # request search tag
targetPages = 1  # request pages waiting scrape

# If data is not scraped before, scrape data, else directly show the analysis
dataScraped = (os.path.exists('./posts.json') and
               os.path.exists('./postsDetail.json') and
               os.path.exists('./locations.json'))

print('Search tag:', tag)
if not dataScraped:
    # scrapePosts(tag)  # scrape all posts outer layer by tag
    scrapePosts(tag, targetPages)  # scrape some posts outer layer by tag and specific pages
    scrapePostsDetail()  # scrape posts detail
    scrapeLocations()  # scrape posts' location country
# Data ready!
completedPostsDetailGenerated = os.path.exists(
    './completedPostsDetail.json')  # Generate simplify and useful datafile for convenience
if not completedPostsDetailGenerated:
    generateCompletedPostsDetail()
# Start analysis
# Count the occurrence of each country / location from the data scraped
generalAnalysis()
analysisOnSpecificPeriod(5, 8)  # input month as integer

endTime = datetime.datetime.now()  # Count for execution time
print('\nExecution time:', endTime - startTime)
