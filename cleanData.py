import csv
from math import radians, cos, sin, asin, sqrt
import datetime
import re 

def haversine(lon1, lat1, lon2, lat2):
    
    #Calculate the great circle distance between two points 
    #on the earth (specified in decimal degrees)
    
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 2.090226E7 #feet
    return c * r

#dataDirectory = "C:\\Users\\Daniel Hatcher\\Desktop\\STA591\\"
dataDirectory = "/Users/hatcher/Desktop/STA591/"

#Load light dataset
lightsFileName = "PGLInstallBeforeNov17.csv"
lightsFileString = dataDirectory + lightsFileName

addresses = []
names = []
installDates = []
lightLats = []
lightLongs = []
lightTracts = []
lightIsGas = []
lightIsLiquor = []
lightIsFast = []

with open(lightsFileString) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        date = row['Date']
        s = date.split('/')
        if len(s) == 3:
            installDates.append(datetime.date(int(s[2])+2000,int(s[0]),int(s[1])))
            names.append(row['Name'])
            addresses.append(row['Address'])
            lightLats.append(float(row['Latitude']))
            lightLongs.append(float(row['Longitude']))
            lightTracts.append(row['CensusTract'])
            lightIsGas.append(row['ISGAS'])
            lightIsLiquor.append(row['ISLIQUOR'])
            lightIsFast.append(row['ISFAST'])
csvfile.close()

#Load DPD dataset
DPDFileName = "DPD_Stations.csv"
DPDFileString = dataDirectory + DPDFileName

DPDLats = []
DPDLongs = []

with open(DPDFileString) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        DPDLats.append(float(row['Latitude']))
        DPDLongs.append(float(row['Longitude']))
csvfile.close()

#Find nearest DPD station

nearestStation = []

for i in range(0,len(addresses)):
    currentMin = 1E9
    for j in range(0,len(DPDLats)):
        distance = haversine(lightLongs[i],lightLats[i],DPDLongs[j],DPDLats[j])
        if distance < currentMin:
            currentMin = distance
    nearestStation.append(currentMin)           
   
#Load Pre-2017 crime dataset

crimeDates = []
crimeLats = []
crimeLongs = []
crimeCodes = []

Pre2017FileName = "ViolentCrimeNoRapeJan15_Dec16.csv"
Pre2017FileString = dataDirectory + Pre2017FileName

with open(Pre2017FileString) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        location = row['LOCATION'].replace(' ','')
        latLongRE = re.compile('^(\()([-+]?)([\d]{1,2})(((\.)(\d+)(,)))(\s*)(([-+]?)([\d]{1,3})((\.)(\d+))?(\)))$')
        for i in range(len(location)):
            coords = re.match(latLongRE,location[i:])
            if coords is not None:
                    latLong = coords.group()
                    latLong = latLong[1:-1]
                    s=latLong.split(',')
                    crimeLats.append(float(s[0]))
                    crimeLongs.append(float(s[1]))
                    date = row['INCIDENTDATE']
                    crimeDates.append(datetime.date(int(date[6:10]),\
                        int(date[0:2]),int(date[3:5])))
                    crimeCodes.append(row['STATEOFFENSEFILECLASS'])
                    break
csvfile.close() 
    
#Load Post-2017 crime dataset
post2017FileName = "ViolentCrimeNoRapeDec16_Nov18.csv"
post2017FileString = dataDirectory + post2017FileName

with open(post2017FileString) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            crimeLats.append(float(row['Latitude']))
            crimeLongs.append(float(row['Longitude']))
            date = row['Incident Date & Time']                      
            crimeDates.append(datetime.date(int(date[6:10]),\
                        int(date[0:2]),int(date[3:5])))  
            crimeCodes.append(row['Arrest Charge'])
        except:
            continue
csvfile.close()

#Crime codes
burglaryCodes = ['22001','22002','22003']
larcenyCodes = ['23001','23002','23003','23004','23005','23006','23007']


#Crime variables 
murderBefore = [0.0]*len(addresses)
robberyBefore = [0.0]*len(addresses)
aggAssBefore = [0.0]*len(addresses)
burglaryBefore = [0.0]*len(addresses)
larcenyBefore = [0.0]*len(addresses)
vTheftBefore = [0.0]*len(addresses)
arsonBefore = [0.0]*len(addresses)

before = [0.0]*len(addresses)
after = [0.0]*len(addresses)

#Determine if crime within view of a light
limit = 2*330 #Median block length
oneyear = datetime.timedelta(days=365)
for i in range(0,len(addresses)):
    for j in range(0,len(crimeDates)):
        distance = haversine(crimeLongs[j],crimeLats[j],lightLongs[i],lightLats[i])
        if distance <= limit:
            if crimeDates[j] < installDates[i]:
                before[i] += 1.0
                if crimeCodes[j] == '9001':
                    murderBefore[i] += 1.0
                elif crimeCodes[j] == '12000':
                    robberyBefore[i] += 1.0
                elif crimeCodes[j] == '13002':
                    aggAssBefore[i] += 1.0
                elif crimeCodes[j] in burglaryCodes:
                    burglaryBefore[i] += 1.0
                elif crimeCodes[j] in larcenyCodes:
                    larcenyBefore[i] += 1.0
                elif crimeCodes[j] == '24001':
                    vTheftBefore[i] += 1.0
                elif crimeCodes[j] == '20000':
                    arsonBefore[i] += 1.0
            elif crimeDates[j] >= installDates[i] and crimeDates[j] <= installDates[i]+oneyear:
                after[i] += 1.0
    print(float(i)/float(len(addresses)))
                    
#Write output CSV
outFile = 'CrimeRatesByLight.csv'
with open(outFile,'w') as csvfile:
    fieldnames = ['Address','Name','InstallDate','Latitude','Longitude','Tract',\
                  'DistToStation','Before','PctMurder','PctRobbery',\
                  'PctAggAlt','PctBurg','PctLarc','PctVTheft','PctArson','After',\
                  'ISGAS','ISLIQUOR','ISFAST','PctReduction']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames)    
    writer.writeheader()
    for i in range(0,len(addresses)):
        #Ignore crimeless lights
        if before[i] == 0.0 and after[i] == 0.0:
            continue
        writer.writerow({\
            'Address':addresses[i],\
            'Name':names[i],\
            'InstallDate':installDates[i],\
            'Latitude':lightLats[i],\
            'Longitude':lightLongs[i],\
            'Tract':lightTracts[i],\
            'ISGAS':lightIsGas[i],\
            'ISLIQUOR':lightIsLiquor[i],\
            'ISFAST':lightIsFast[i],\
            'DistToStation':nearestStation[i],\
            'Before':before[i],\
            'PctMurder':murderBefore[i]/before[i],\
            'PctRobbery':robberyBefore[i]/before[i],\
            'PctAggAlt':aggAssBefore[i]/before[i],\
            'PctBurg':burglaryBefore[i]/before[i],\
            'PctLarc':larcenyBefore[i]/before[i],\
            'PctVTheft':vTheftBefore[i]/before[i],\
            'PctArson':arsonBefore[i]/before[i],\
            'After':after[i],\
            'PctReduction':(1.0-(after[i]/before[i]))*100.0})
    
    