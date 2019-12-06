import os
from collections import Counter
#-------------------------------
#Directories
#-------------------------------
inputDir = 'input'
fileDir = 'temp'
analysisDir = 'analysis'
#-------------------------------
#Script parameters
#-------------------------------

#Whether to check if every line in the script is an authentic message based on the time in log
shouldValidateLineDates = True

#-------------------------------
#Pre-processing
#-------------------------------
if not(os.path.exists(inputDir)):
    os.makedirs(inputDir)
if not(os.path.exists(fileDir)):
    os.makedirs(fileDir)
if not(os.path.exists(analysisDir)):
    os.makedirs(analysisDir)

#===============================
#Utility functions
#===============================

#Check if the message starts with a date in the proper format
#TODO Make it check whether the date is practically feasible, not important
def ValidateLineDate(linestr):
    #The first 20 characters of the message correspond to the timestamp
    linestr = linestr[0:20]
    flag = True
    if (linestr[2] != '/' or linestr[5] != '/'):
        flag = False
    if (linestr[10] != ','):
        flag = False
    if (linestr[11] != ' ' or linestr[17] != ' ' or linestr[19] != ' '):
        flag = False
    if (linestr[14] != ':'):
        flag = False
    if (linestr[18] != '-'):
        flag = False
    for i in range(20):
        if (i not in (2,5,10,11,14,17,18,19)):
            if (not(linestr[i].isdigit())):
                flag = False
    return flag

#Check whehter the message was sent by someone. Meaning it is of the format "person_name: Message".
def ValidateLineName(linestr):
    #The first 20 characters of the message correspond to the timestamp
    linestr = linestr[20:]
    name_length = 0
    flag = False
    #Searches for a semicolon to indicate where the message starts
    while(name_length < len(linestr)):
        if (linestr[name_length] == ':'):
            flag = True
            break
        name_length+=1
    if (flag == False):
        return(False, 'null', 'null')
    if (flag == True):
        #Returns whether name was detected, the name and the rest of the string
        return(True, linestr[:name_length], linestr[name_length+2:])

#Function should print the top 5 word count
def AnalyseMsgsFromFile(filename):
    print('Analysing file {}'.format(filename))
    fout = open(analysisDir+'/Analysis_{}'.format(filename),mode='w', encoding='utf8')
    # text file will be opened
    with open(fileDir+'/'+filename, 'r', encoding='utf8') as g:
        coun = Counter(g.read().split())
        for word,count in coun.most_common(5):
            fout.write('%s: %d\n' % (word, count))
    print('Analysis complete. Output stored in {}'.format(analysisDir+'/Analysis_{}'.format(filename)))

#Function should check whether the message sent was just a media message
def IsIgnorableMsg(message):
    if (message == "<Media omitted>\n"):
        return True
    return False


#===============================
#Main control loop
#===============================
for fname in os.listdir(inputDir):
    if fname.endswith('.txt'):
        #text file will be opened
        f = open(inputDir+'/{}'.format(fname), mode='r', encoding='utf8')

        #fout is a dictionary of all file pointers mapped to the name of the messager
        fout = {}
        
        print('Processing {}'.format(fname))

        #Total lines parsed
        totalMsg = 0
        #Of which how many had passed the timestamp validation
        validDates = 0
        #Of which how many had been actually sent by a person
        validMsg = 0
        line = f.readline()
        while(line):
            totalMsg+=1
            isDateValid = ValidateLineDate(line)
            (isNameValid, name, message) = ValidateLineName(line)
            #First checks if the message starts with a timestamp
            if (isDateValid):
                validDates += 1
                #Then checks if it has a valid name of sender
                if (isNameValid):
                    validMsg += 1
                    #In that case, write the message into the corresponding text file of that sender
                    #If such a text file doesn't exist, create one
                    if name not in fout:
                        fout[name] = open(fileDir+'/{}_{}'.format(name, fname), mode='w', encoding='utf8')
                    if (not(IsIgnorableMsg(message))):
                        fout[name].write(message)
            line = f.readline()
        print('Processing finished. {} lines parsed. {} valid timestamps discovered. {} valid messages found.'.format(totalMsg, validDates, validMsg))
        f.close()
        for name in fout:
            fout[name].close()
        
        #Analyses each file created as part of the processing

        for name in fout:
            AnalyseMsgsFromFile(name+'_'+fname)