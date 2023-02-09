import csv
import requests
# from botocore.vendored import requests
from bs4 import BeautifulSoup
import json

#lambda function
def lambda_handler(event, context):
  # queryParams = event["queryStringParameters"]  
  # #   print(queryParams)

  # if 'eventId' in queryParams and 'clubId' in queryParams:
  #   url = "https://system.gotsport.com/org_event/events/{}/schedules?club={}".format(queryParams['eventId'],queryParams['clubId'])
  # else:
  #   print("'eventId' or 'clubId' are missing in query params. Needs to be like this '?eventId=18280/&clubId=3694'", queryParams)      
  #   url = "https://system.gotsport.com/org_event/events/18280/schedules?club=3694"    
  #   print("Using default URL", url)

  url = "https://system.gotsport.com/org_event/events/18280/clubs" 
  details = getCoachDetails(url)
  exportToCVS(details)
  return details
  
def getCoachDetails(url):
  url = "https://system.gotsport.com/org_event/events/18280/clubs" 
  contacts = []
  
  html =  getHtml(url)
  clubs = parseClubsListingHtml(html)

  for club in clubs:
    teamsByClubHtml = getHtml(club['link'])
    clubContacts = parseContactDetailsFromClubHtml(teamsByClubHtml)
    for c in clubContacts:
      c['club_name'] = club['club_name']
    # print('clubContacts', clubContacts)
    contacts.extend(clubContacts)

  # print('LAST CLUB --', contacts[-1])
  return contacts
    

# return a list of club names and links to their teams page
# https://system.gotsport.com/org_event/events/18280/clubs
def parseClubsListingHtml(html):
  clubs = []
  tableOfClubs = html.find_all("table", {"class": "table table-bordered table-condensed table-hover"})[0]

#loop club links
  table_body = tableOfClubs.find('tbody')
  rows = table_body.find_all('tr')
  for row in rows:        
    # cols = row.find_all('td')
    aTag = row.find('a')
    clubLink = 'https://system.gotsport.com' + aTag.get('href')
    clubs.append({'club_name':aTag.text, 'link': clubLink})
  
  return clubs

## parse html, to get team details then jump 2 deep to get coaches' details
# https://system.gotsport.com/org_event/events/18280/clubs/18604
def parseContactDetailsFromClubHtml(html):
  contacts = []
  tableOfTeams = html.find_all("table")[0]
  rows = tableOfTeams.find_all('tr')
  rows.pop(0) # remove headers
  for teamRow in rows:  
    teamCols = teamRow.find_all('td')
    # https://system.gotsport.com/org_event/events/18280/schedules?team=932206
    teamUrl = 'https://system.gotsport.com' + teamCols[0].find('a').get('href')
    teamCols = [ele.text.strip() for ele in teamCols]
    # swap schedule to contacts 
    # https://system.gotsport.com/org_event/events/18280/contacts?team=932206
    teamContactsUrl = teamUrl.replace('schedules', 'contacts')
    # print('teamContactUrl', teamContactUrl)
    contactHtml =  getHtml(teamContactsUrl)

    # ////
    tableOfPeople = contactHtml.find("table")
    rowsOfPeople = tableOfPeople.find_all('tr')    
    # rowsOfPeople.pop(0)
    for personRow in rowsOfPeople:
      # print('personRow', personRow)
      personCols = personRow.find_all('td')
      personCols = [ele.text.strip() for ele in personCols]
      
      # print('personCols', personCols)
      details = {'team':teamCols[0], 'url': teamUrl, 'gender':teamCols[1], 
                 'age':teamCols[2],'division': teamCols[3], 'bracket':teamCols[4], 
                'person_name':personCols[1], 'email':personCols[2], 'cell':personCols[3]}
      # print('details', details)
      contacts.append(details)

    # print("-------- All Contacts by club--------\n", contacts)
  return contacts
  
def getHtml(url):
  try:
    print("Calling url:", url)
    webpage = requests.get(url)
    # print(webpage)
    
    if webpage.status_code == 200:
      webpage_bs = BeautifulSoup(webpage.text, 'html.parser')
      # webpage_bs = BeautifulSoup(webpage.content, 'html.parser')
      # print("Success")
      # print(webpage_bs.prettify())
      # print("Success getting HTML")
      return webpage_bs
    else:
      # print(webpage.status_code+" "+url)
      raise Exception("API Failure - " + webpage.status_code+ " "+url)
  except Exception as e:
    print("request does not work : ", url)
    print("Exception : ", e)
    raise Exception("API Exception - " + url + " " + e)

def exportToCVS(details):
  with open("contactList.csv","w",newline="") as f:  
      title = "club_name,team,url,gender,age,division,bracket,person_name,email,cell".split(",") # quick hack
      cw = csv.DictWriter(f,title,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
      cw.writeheader()
      cw.writerows(details)