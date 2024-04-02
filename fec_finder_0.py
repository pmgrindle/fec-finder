import requests
import csv
import argparse
import sys
import zipfile
import datetime
import linecache
import fecapikey as apiKey
# For debugging
# import traceback

## code to fetch from fec website
def writeFECData(candID, office):
    params = {'api_key': apiKey.fecApiKey, 'committee_type': office, 'designation': 'P'}
    candComms = requests.get("https://api.open.fec.gov/v1/candidate/" + candID + "/committees/", params = params) 
    commArr = candComms.json()['results']
    email, phone, website, extraEmails, extraPhones, extraWebsites = "", "", "", "", "", ""
    numPrincipal = 1
    for comm in commArr:
        if numPrincipal > 1:
            if numPrincipal == len(commArr):
                if comm['email']:
                    extraEmails += comm['email'].lower()
                if comm['custodian_phone']:
                    extraPhones += comm['custodian_phone']
                if comm['website']:
                    extraWebsites += comm['website'].lower()
            else:
                if comm['email']:
                    extraEmails += comm['email'].lower() + ", "
                if comm['custodian_phone']:
                    extraPhones += comm['custodian_phone'] + ", "
                if comm['website']:
                    extraWebsites += comm['website'].lower() + ", "
        else:
            if comm['email']:
                email = comm['email'].lower()
            email = comm['email'].lower()
            if comm['custodian_phone']:
                phone = comm['custodian_phone']
            if comm['website']:
                website = comm['website'].lower()
        numPrincipal += 1
    if office == 'H':
        office = "House"
    elif office == 'S':
        office = "Senate"
    else:
        office = "Error: " + office

    candData = [firstName, lastName, middlePrefixSuffix, office, state, district, party, email, phone, 
                                                website, extraEmails, extraPhones, extraWebsites]
    writer.writerow(candData)

# Set up Argument Parser instance to check which states to scrape
parser = argparse.ArgumentParser(prog="FEC Scraper", 
                                 description = """Scrape Congressional and Senate 
                                                filing data from FEC website""")
parser.add_argument('year', type=int, nargs=1)
scaleGroup = parser.add_mutually_exclusive_group(required=True)
scaleGroup.add_argument('-requestLimit', type=int)
scaleGroup.add_argument('-full', action='store_true')
parser.add_argument('-local', action='store_true')
lowTierGroup = parser.add_mutually_exclusive_group()
lowTierGroup.add_argument('-offset', type=int, default=0)
lowTierGroup.add_argument('-numRuns', type=int, default=0)
#group = parser.add_mutually_exclusive_group(required=True)
# Add arguments for which states to scrape, or all states, and whether abbreviated
# Use of mutual exclusive group ensures only one of these arguments is used
#group.add_argument('-all', action = "store_true", help = "Scrape all states")
#group.add_argument('-statesName', nargs = '+', help = "Scrape specific states by full name")
#group.add_argument('-statesAbbr', nargs = '+', help = "Scrape specific states by abbreviation") 
args = parser.parse_args()

preyear = str(args.year)
year = preyear[1:len(preyear)-1]
if len(year) != 4 or year.isdigit() == False or int(year) % 2 != 0:
    print("Invalid year. Please input a 4 digit year. Each cycle is the even number over 2 years. Ex: 2018 is for 2017-2018.") 
    print("Exiting")
    sys.exit()

if int(year) < 1996 or int(year) > datetime.date.today().year:
    print("Invalid year. Please input an even year between 1996 and " + str(datetime.date.today().year))
    print("Exiting")
    sys.exit()

if args.full:
    args.requestLimit = 7200
else:
    if args.requestLimit < 1:
        print("Request limit must be greater than 0.")
        print("Exiting")
        sys.exit()

    elif args.requestLimit > 1000:
        print("Request limit must be less than 1000 per hour.")
        print("Exiting")
        sys.exit()  

    else:
        print("Warning, you have entered " + str(args.requestLimit) + " requests. You get 1000 per hour, unless you have an upgraded API key for 7200 per hour.")
        decision = input("Are you sure you want this many requests (y/n) : ")
        if decision.lower() != 'y' and decision.lower() != 'yes':
            print("Exiting")
            sys.exit()



filename = year+".zip"
# Send a GET request to the URL and create a BeautifulSoup object
if args.local != True:
    zip = requests.get("https://www.fec.gov/files/bulk-downloads/" + year 
                            + "/webl" + year[2:] + ".zip") 
    with open(filename, 'wb') as f:
        f.write(zip.content)

columns = ["First Name", "Last Name", "Middle+Prefix+Suffix", "Office", "State", "District", "Party", 
           "Email", "Phone", "Website", "Extra Emails", "Extra Phones", "Extra Websites"]
candData = []
writer = csv.writer(open("FEC_finder_candidates.csv", 'w', encoding="utf-8", newline = ""))
writer.writerow(columns)

# control variables to keep get requests below 1000 per hour
requestNum = 0

if not args.full and args.offset:
    print('1')
    for i in range(args.offset+1, args.requestLimit + args.offset):
        if requestNum == args.requestLimit:
            print("Request limit reached. Exiting")
            sys.exit()
        with zipfile.ZipFile(filename, 'r') as archive:
            lineStr = linecache.getline(archive.namelist()[0], i)
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
        lastName = fullName.split(',')[0][0] + fullName.split(',')[0][1:].lower()
        extraNames = fullName.split(',')[1].split(' ')
        firstName = extraNames[1][0] + extraNames[1][1:].lower()
        middlePrefixSuffix = ""
        print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
        if len(extraNames) > 2:
            for i in range(2, len(extraNames)):
                middlePrefixSuffix += extraNames[i] + " "
        writeFECData(candID, office)
        requestNum += 1

elif not args.full and args.numRuns:
    print('2')
    for i in range((args.numRun-1)*500+1, 500*args.numRuns):
        if requestNum == 500:
            print("Request limit reached. Exiting")
            sys.exit()
        with zipfile.ZipFile(filename, 'r') as archive:
            lineStr = linecache.getline(archive.namelist()[0], i)
        #lineStr = linecache.getline(candText, i).decode("ascii")
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
        lastName = fullName.split(',')[0][0] + fullName.split(',')[0][1:].lower()
        extraNames = fullName.split(',')[1].split(' ')
        firstName = extraNames[1][0] + extraNames[1][1:].lower()
        middlePrefixSuffix = ""
        print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
        if len(extraNames) > 2:
            for i in range(2, len(extraNames)):
                middlePrefixSuffix += extraNames[i] + " "
        writeFECData(candID, office)
        requestNum += 1

else:  
    print('3')  
    archive = zipfile.ZipFile(filename, 'r')
    candTextName = "webl"+year[2:]+".txt"
    candText = archive.open(candTextName)
    for line in candText:
        if requestNum == args.requestLimit:
            print("Request limit reached. Exiting")
            sys.exit()
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
        lastName = fullName.split(',')[0][0] + fullName.split(',')[0][1:].lower()
        extraNames = fullName.split(',')[1].split(' ')
        firstName = extraNames[1][0] + extraNames[1][1:].lower()
        middlePrefixSuffix = ""
        print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
        if len(extraNames) > 2:
            for i in range(2, len(extraNames)):
                middlePrefixSuffix += extraNames[i] + " "
        writeFECData(candID, office)
        requestNum += 1

    



