import csv
import requests
# from botocore.vendored import requests
from bs4 import BeautifulSoup
import json
import re

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

  url = "https://system.gotsport.com/org_event/events/36230/clubs" 
  details = getCoachDetails(url)
  exportToCVS(details)
  return details
  
def getCoachDetails(url):
  # url = "https://system.gotsport.com/org_event/events/18280/clubs" 
  contacts = []
  
  html =  getHtml(url)
  clubs = parseClubsListingHtml(html)

  for club in clubs:
    teamsByClubHtml = getHtml(club['link'])
    clubContacts = parseContactDetailsFromClubHtml(teamsByClubHtml)
    for c in clubContacts:
      c['Company'] = club['club_name']
      c['Job title'] = re.sub(club['club_name']+ " ", "", c['Job title'], flags=re.I)
      c['Team Name'] = re.sub(club['club_name']+ " ", "", c['Team Name'], flags=re.I)
      
    # print('clubContacts', clubContacts)
    contacts.extend(clubContacts)

    # break

  # print('LAST CLUB --', contacts[-1])
  return contacts
    

# return a list of club names and links to their teams page
# https://system.gotsport.com/org_event/events/18280/clubs
def parseClubsListingHtml(html):
  clubs = []
  # print("-----------------------------------")
  # print("parseClubsListingHtml")
  # print(html)
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

    tableOfPeople = contactHtml.find("table")

    # Since we're generating the link for the contacts and not clicking the teampage from the club page
    # the team page actually might not a link to the coaches
    # When a team doesn't have coaches listed, redirected to -> https://system.gotsport.com/org_event/events/36230
    # kinda lazy but if the default page returned doesn't have a table it in. 

    # print("Is tableOfPeople None, team probably doesn't have coaches listed. ", teamUrl)
    if tableOfPeople is None:
      print("Team ", teamCols[0], " doesn't have a team contact listed. ", teamUrl)
      continue

    rowsOfPeople = tableOfPeople.find_all('tr')    
    # rowsOfPeople.pop(0)
    for personRow in rowsOfPeople:
      # print('personRow', personRow)
      personCols = personRow.find_all('td')
      personCols = [ele.text.strip() for ele in personCols]
      
      # print('personCols', personCols)
      # details = {'team':teamCols[0], 'url': teamUrl, 'gender':teamCols[1], 
      #            'age':teamCols[2],'division': teamCols[3], 'bracket':teamCols[4], 
      #           'person_name':personCols[1], 'email':personCols[2], 'cell':personCols[3]}
      
      f_name = personCols[1]
      l_name = ""

      if " " in personCols[1]:
        f_name = personCols[1][:personCols[1].find(" ")]
        l_name = personCols[1][personCols[1].find(" "):]

      notes = 'Age: ' + teamCols[2] + ' Division: ' + teamCols[3], ' Bracket: ' + teamCols[4]
      b_or_g =  "G" if teamCols[1][0].upper() == "F" else "B"

      #import for google 
      details = {
                "Team Name": teamCols[0],
                'Job title':teamCols[0] + " (" + teamCols[2] + " " + b_or_g + ")", 
                 "Custom Field 1 - Label": "Gender", "Custom Field 1 - Value": teamCols[1], 
                 "Custom Field 2 - Label": "Age", "Custom Field 2 - Value": teamCols[2], 
                 "Custom Field 3 - Label": "Division", "Custom Field 3 - Value": teamCols[3], 
                 "Custom Field 4 - Label": "Bracket", "Custom Field 4 - Value": teamCols[4], 

                 'First Name':f_name, 'Last Name':l_name,
                 "E-mail Address": personCols[2], 
                #  "E-mail 1 - Label": "Work", "E-mail 1 - Value": personCols[2],
                #  "E-mail 1 - Label": personCols[2], "E-mail 1 - Value": "Work",
                #  "Phone 1 - Label": "Phone", "Phone 1 - Value": personCols[3],
                #  "Phone 1 - Label": personCols[3], "Phone 1 - Value": "Phone",
                 "Phone": personCols[3], 
                #  "Website 1 - Label": "Schedule", "Website 1 - Value": teamUrl,
                 "Web Page": teamUrl,

                'person_name':personCols[1]}
                
      # print('details', details)
      contacts.append(details)

    # print("-------- All Contacts by club--------\n", contacts)
  return contacts
  
def getHtml(url):
  try:
    print("Calling url:", url)
    headers = { 'accept':'*/*',
      'accept-encoding':'gzip, deflate, br',
      'accept-language':'en-GB,en;q=0.9,en-US;q=0.8,hi;q=0.7,la;q=0.6',
      'cache-control':'no-cache',
      'dnt':'1',
      'pragma':'no-cache',
      'referer':'https',
      'sec-fetch-mode':'no-cors',
      'sec-fetch-site':'cross-site',
      'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    }
    webpage = requests.get(url=url, headers=headers)
    # print("Webpage")
    # print(webpage)
    
    if webpage.status_code == 200:
      webpage_bs = BeautifulSoup(webpage.text, 'html.parser')
      webpage_bs = BeautifulSoup(webpage.content, 'html.parser')
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
      # title = "Organization Name,Organization Department,team,url,gender,age,division,bracket,person_name,email,cell".split(",") # quick hack
      title = [
               "Company", # club name
               "Team Name", #team name
               "Job title",  # team name + Sex + Age
              #  "Website 1 - Label",  "Website 1 - Value", #URL
               "Web Page",
               "Custom Field 1 - Label", "Custom Field 1 - Value", #gender
               "Custom Field 2 - Label", "Custom Field 2 - Value",  # "age",
               "Custom Field 3 - Label", "Custom Field 3 - Value",  # "Division",
               "Custom Field 4 - Label", "Custom Field 4 - Value",  # "Bracket",
               "person_name", "First Name", "Last Name",
              #  "E-mail 1 - Label", "E-mail 1 - Value",  #"email"
               "E-mail Address",
               "Phone",
              #  "Phone 1 - Label", "Phone 1 - Value", # cell
               ]
      
      # for d in details:
      #   print(d)
      print("Exporting to csv!!")
      
      cw = csv.DictWriter(f,title,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
      cw.writeheader()
      cw.writerows(details)