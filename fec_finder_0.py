import requests
import csv
import argparse
import sys
import zipfile
import datetime
import cmd
# For debugging
# import traceback

# Set up Argument Parser instance to check which states to scrape
parser = argparse.ArgumentParser(prog="FEC Scraper", 
                                 description = """Scrape Congressional and Senate 
                                                filing data from FEC website""")
parser.add_argument('year', type=int, nargs=1)
parser.add_argument('requestLimit', type=int)
parser.add_argument('-local', action='store_true')
#group = parser.add_mutually_exclusive_group(required=True)
# Add arguments for which states to scrape, or all states, and whether abbreviated
# Use of mutual exclusive group ensures only one of these arguments is used
#group.add_argument('-all', action = "store_true", help = "Scrape all states")
#group.add_argument('-statesName', nargs = '+', help = "Scrape specific states by full name")
#group.add_argument('-statesAbbr', nargs = '+', help = "Scrape specific states by abbreviation") 
args = parser.parse_args()

preyear = str(args.year)
year = preyear[1:len(preyear)-1]
if len(year) != 4 or year.isdigit() == False or year % 2 != 0:
    print("Invalid year. Please input a 4 digit year. Each cycle is the even number over 2 years. Ex: 2018 is for 2017-2018.") 
    print("Exiting")
    sys.exit()

if year < 1996 or year > datetime.date.today().year:
    print("Invalid year. Please input an even year between 1996 and " + str(datetime.date.today().year))
    print("Exiting")
    sys.exit()

if args.requestLimit < 1:
    print("Request limit must be greater than 0.")
    print("Exiting")
    sys.exit()

if args.requestLimit > 1000:
    print("Request limit must be less than 1000 per hour.")
    print("Exiting")
    sys.exit()  

if args.requestLimit >= 500:
    print("Warning, you have requested " + str(args.requestLimit) + " requests. You get 1000 per hour.")
    decision = cmd.raw_input("Are you sure you want this many requests (y/n) : ")
    if decision.lower() != 'y' or decision.lower() != 'yes':
        print("Exiting")
        sys.exit()


filename = year+".zip"
# Send a GET request to the URL and create a BeautifulSoup object
if args.local != True:
    zip = requests.get("https://www.fec.gov/files/bulk-downloads/" + year 
                            + "/webl" + year[2:] + ".zip") 
    with open(filename, 'wb') as f:
        f.write(zip.content)

archive = zipfile.ZipFile(filename, 'r')
candTextName = "webl"+year[2:]+".txt"
candText = archive.open(candTextName)

columns = ["First Name", "Last Name", "Middle+Prefix+Suffix", "State", "District", "Party", 
           "Email", "Phone", "Website", "Extra Emails", "Extra Phones", "Extra Websites"]
candData = []
writer = csv.writer(open("FEC_finder_candiates.csv", 'w', encoding="utf-8", newline = ""))
writer.writerow(columns)

# control variables to keep get requests below 1000 per hour
requestNum = 0

for line in candText:
    if requestNum == args.requestLimit:
        print("Request limit reached. Exiting")
        break
    lineStr = line.decode("ascii")
    lineArr = lineStr.split('|')
    office = lineArr[0][:1]
    if office != 'H' and office != 'S':
        continue
    state = lineArr[18]
    district = ""
    if office == 'H':
        district = lineArr[19]
    candID = lineArr[0]
    party = lineArr[4]
    fullName = lineArr[1]
    lastName = fullName.split(',')[0]
    extraNames = fullName.split(',')[1].split(' ')
    firstName = extraNames[1]
    middlePrefixSuffix = ""
    print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
    if len(extraNames) > 2:
        for i in range(2, len(extraNames)):
            middlePrefixSuffix = middlePrefixSuffix + extraNames[i] + " "
    
    ## code to fetch from fec website
    params = {'api_key': 'DEMO_KEY', 'committee_type': office, 'designation': 'P'}
    candComms = requests.get("https://api.open.fec.gov/v1/candidate/" + candID + "/committees/", params = params) 
    requestNum += 1
    commArr = candComms.json()['results']
    email, phone, website, extraEmails, extraPhones, extraWebsites = "", "", "", "", "", ""
    numPrincipal = 1
    for comm in commArr:
        if numPrincipal > 1:
            if numPrincipal == len(commArr):
                extraEmails += comm['email']
                extraPhones += comm['phone']
                extraWebsites += comm['website']
            else:
                extraEmails += comm['email'] + ", "
                extraPhones += comm['phone'] + ", "
                extraWebsites += comm['website'] + ", "
        else:
            email = comm['email']
            phone = comm['phone']
            website = comm['website']
        numPrincipal += 1
    
    candData = [firstName, lastName, middlePrefixSuffix, state, district, party, email, phone, 
                                                website, extraEmails, extraPhones, extraWebsites]
    writer.writerow(candData)



