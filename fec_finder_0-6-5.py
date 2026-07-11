import requests
import csv
import argparse
import sys
import zipfile
import datetime
import linecache
import fecapikey as apiKey
import time
import os
import ast
# For debugging
# import traceback

## code to fetch from fec website
def writeFECData(candID, office, emailNum, phoneNum, webNum):
    params = {'api_key': apiKey.fecApiKey, 'committee_type': office, 'designation': 'P'}
    candComms = requests.get("https://api.open.fec.gov/v1/candidate/" + candID + "/committees/", params = params) 
    if 'results' in candComms.json():
        commArr = candComms.json()['results']
    else:
        print("Error for candidate " + candID + " " + firstName + " " + lastName)
        print(candComms.json())
        return [emailNum, phoneNum, webNum]
    if len(commArr) == 0:
        print("No principal committee found")
        return [emailNum, phoneNum, webNum]
    email, phone, website = [], [], []
    #numPrincipal = 1
    localemailnum, localphonenum, localwebsitenum = 0, 0, 0
    for comm in commArr:
        if comm['email']:
            if ';' in comm['email']:
                emails = comm['email'].split(';')
                for emailelement in emails:
                    if emailelement.lower().strip() not in email:
                        email.append(emailelement.lower().strip())
                        localemailnum += 1
            else:
                if comm['email'].lower().strip() not in email:
                    email.append(comm['email'].lower().strip())
                    localemailnum += 1
        if comm['custodian_phone']:
            if ';' in comm['custodian_phone']:
                phones = comm['custodian_phone'].split(';')
                for phoneelement in phones:
                    if phoneelement.strip() not in phone:
                        phone.append(phoneelement.strip())
                        localphonenum += 1
            else:
                if comm['custodian_phone'].strip() not in phone:
                    phone.append(comm['custodian_phone'].strip())
                    localphonenum += 1
        if comm['website']:
            if ';' in comm['website']:
                websites = comm['website'].split(';')
                for websiteelement in websites:
                    if websiteelement.lower().strip() not in website:
                        website.append(websiteelement.lower().strip())
                        localwebsitenum += 1
            else:    
                if comm['website'].lower().strip() not in website:
                    website.append(comm['website'].lower().strip())
                    localwebsitenum += 1
        if localemailnum > emailNum:
            emailNum = localemailnum
        if localphonenum > phoneNum:
            phoneNum = localphonenum
        if localwebsitenum > webNum:
            webNum = localwebsitenum
        """ if numPrincipal > 1:
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
            if comm['custodian_phone']:
                phone = comm['custodian_phone']
            if comm['website']:
                website = comm['website'].lower()
        numPrincipal += 1 """
    if office == 'H':
        office = "House"
    elif office == 'S':
        office = "Senate"
    else:
        office = "Error: " + office

    candData = [firstName, lastName, middlePrefixSuffix, office, state, district, party, email, phone, 
                                                website]
    writer.writerow(candData)
    time.sleep(.75)
    return [emailNum, phoneNum, webNum]

def expandContactColumns(emailNum, phoneNum, webNum):
    newcolumns = ["First Name", "Last Name", "Middle+Prefix+Suffix", "Office", "State", "District", "Party"]
    for i in range(emailNum):
        newcolumns.append("Email " + str(i+1))
    for i in range(phoneNum):
        newcolumns.append("Phone " + str(i+1))
    for i in range(webNum):
        newcolumns.append("Website " + str(i+1))
    writer = csv.writer(open("FEC_finder_candidates.csv", 'w', encoding="utf-8", newline = ""))
    writer.writerow(newcolumns)
    isFirst = True
    with open("FEC_finder_candidates_unsort.csv", 'r', encoding="utf-8", newline = "") as f:
        reader = csv.reader(f)
        for row in reader:
            print("in reader")
            if isFirst:
                isFirst = False
                continue
            emailCounter, phoneCounter, webCounter = 0, 0, 0
            newRow = [row[0], row[1], row[2], row[3], row[4], row[5], row[6]]
            emailRow = ast.literal_eval(row[7])
            print(emailRow)
            phoneRow = ast.literal_eval(row[8])
            print(phoneRow)
            webRow = ast.literal_eval(row[9])
            print(webRow)
            if len(emailRow) > 0:
                for i in range(0, len(emailRow)):
                    newRow.append(emailRow[i])
                    emailCounter += 1
            if emailCounter < emailNum:
                for i in range(emailCounter, emailNum):
                    newRow.append("")
            if len(phoneRow) > 0:
                for j in range(0, len(phoneRow)):
                    newRow.append(phoneRow[j])
                    phoneCounter += 1
            if phoneCounter < phoneNum:
                for i in range(phoneCounter, phoneNum):
                    newRow.append("")
            if len(webRow) > 0:
                for k in range(0, len(webRow)):
                    newRow.append(webRow[k])
                    webCounter += 1
            writer.writerow(newRow)
    os.remove("FEC_finder_candidates_unsort.csv")


# Set up Argument Parser instance to check which states to scrape
parser = argparse.ArgumentParser(prog="FEC Scraper", 
                                 description = """Scrape Congressional and Senate 
                                                filing data from FEC website""")
parser.add_argument('year', type=int, nargs=1)
scaleGroup = parser.add_mutually_exclusive_group(required=True)
scaleGroup.add_argument('-requestLimit', type=int)
scaleGroup.add_argument('-full', action='store_true')
parser.add_argument('-local', action='store_true')
parser.add_argument('-offset', type=int, default=0)
parser.add_argument('-numRuns', type=int, default=0)
#parser.add_argument('-officeRequest', nargs=(1,2), type=list, default=['H', 'S'])
stateGroup = parser.add_mutually_exclusive_group()
# Add arguments for which states to scrape, or all states, and whether abbreviated
# Use of mutual exclusive group ensures only one of these arguments is used
stateGroup.add_argument('-statesName', nargs = '+', help = "Scrape specific states by full name")
stateGroup.add_argument('-statesAbbr', nargs = '+', help = "Scrape specific states by abbreviation") 
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

statelist = []
if args.statesName:
    # Create a dictionary to convert state abbreviations to full names
    statesConversion = {"Alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "district of columbia": "DC",
    "american Samoa": "AS",
    "guam": "GU",
    "northern mariana islands": "MP",
    "puerto rico": "PR",
    "united states minor outlying islands": "UM",
    "u.s. virgin islands": "VI"}
    for usState in args.statesName:
        statelist.append(statesConversion[usState.lower()])

elif args.statesAbbr:
    statelist = [state.upper() for state in args.statesAbbr]

# if args.officeRequest:
#     officeList = [office.upper() for office in args.officeRequest]
#     for office in officeList:
#         if office != 'H' and office != 'S':
#             print("Invalid office request. Please enter 'H' for House, 'S' for Senate, or both.")
#             print("Exiting")
#             sys.exit()
# else:
officeList = ['H', 'S']

filename = year+".zip"
# Send a GET request to the URL and create a BeautifulSoup object
if args.local != True:
    zip = requests.get("https://www.fec.gov/files/bulk-downloads/" + year 
                            + "/webl" + year[2:] + ".zip") 
    with open(filename, 'wb') as f:
        f.write(zip.content)

columns = ["First Name", "Last Name", "Middle+Prefix+Suffix", "Office", "State", "District", "Party", 
           "Email", "Phone", "Website"]
candData = []
prefile = open("FEC_finder_candidates_unsort.csv", 'w', encoding="utf-8", newline = "")
writer = csv.writer(prefile)
writer.writerow(columns)

# control variables
# keep get requests below 1000 per hour
requestNum = 0
# track how many email phone and web columns are needed
emailNum, phoneNum, webNum = 0, 0, 0

if not args.full and args.offset and not args.numRuns:
    print('1')
    for i in range(args.offset+1, args.requestLimit + args.offset+1):
        if requestNum == args.requestLimit:
            print("Request limit reached. Exiting")
            break
        with zipfile.ZipFile(filename, 'r') as archive:
            lineStr = linecache.getline(archive.namelist()[0], i)
        lineArr = lineStr.split('|')
        office = lineArr[0][:1]
        if (office != 'H' and office != 'S') or (office not in officeList):
            continue
        state = lineArr[18]
        if statelist:
            if state not in statelist:
                continue
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
        if len(extraNames) > 2:
            for i in range(2, len(extraNames)):
                middlePrefixSuffix += extraNames[i] + " "
        print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
        returnList = writeFECData(candID, office, emailNum, phoneNum, webNum)
        emailNum = returnList[0]
        phoneNum = returnList[1]
        webNum = returnList[2]
        requestNum += 1

elif not args.full and args.numRuns:
    print('2')
    if args.offset:
        offset = args.offset
    else:
        offset = 0
    for i in range((args.numRuns-1)*offset+1, (args.numRuns-1)*offset+args.requestLimit+1):
        if requestNum == args.requestLimit:
            print("Request limit reached. Exiting")
            break
        with zipfile.ZipFile(filename, 'r') as archive:
            lineStr = linecache.getline(archive.namelist()[0], i)
        #lineStr = linecache.getline(candText, i).decode("ascii")
        lineArr = lineStr.split('|')
        office = lineArr[0][:1]
        if (office != 'H' and office != 'S') or (office not in officeList):
            continue
        state = lineArr[18]
        if statelist:
            if state not in statelist:
                continue
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
        if len(extraNames) > 2:
            for i in range(2, len(extraNames)):
                middlePrefixSuffix += extraNames[i] + " "
        print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
        returnList = writeFECData(candID, office, emailNum, phoneNum, webNum)
        emailNum = returnList[0]
        phoneNum = returnList[1]
        webNum = returnList[2]
        requestNum += 1

else:  
    print('3') 
    linecount = 1 
    archive = zipfile.ZipFile(filename, 'r')
    candTextName = "webl"+year[2:]+".txt"
    candText = archive.open(candTextName)
    for line in candText:
        if linecount < args.offset:
            linecount += 1
            continue
        if requestNum == args.requestLimit:
            print("Request limit reached. Exiting")
            break
        lineStr = line.decode("ascii")
        lineArr = lineStr.split('|')
        office = lineArr[0][:1]
        if (office != 'H' and office != 'S') or (office not in officeList):
            continue
        state = lineArr[18]
        if statelist:
            if state not in statelist:
                continue
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
        if len(extraNames) > 2:
            for i in range(2, len(extraNames)):
                middlePrefixSuffix += extraNames[i] + " "
        print(lastName + ", " + firstName + " -- " + middlePrefixSuffix + ", " + party)
        returnList = writeFECData(candID, office, emailNum, phoneNum, webNum)
        emailNum = returnList[0]
        phoneNum = returnList[1]
        webNum = returnList[2]
        requestNum += 1

prefile.close()
expandContactColumns(emailNum, phoneNum, webNum)