import os
from collections import Counter
import nltk
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
import string
import datetime
import dateutil.parser
import operator
import numpy as np
import matplotlib.pyplot as plt


# -------------------------------
# Directories
# -------------------------------

# NOTE: All folder paths and folder names end WITHOUT a /
# external directories
inputDir = 'input'
outputDir = 'output'

# internal folder names: multiple folders with these names will be created
# Split message: contains step 1 of output
splitMsgFolderName = 'split_msg'
# Timestamp folder: contains timestamp info
timestampFolderName = 'timestamps'
# Without stop words folder: contains step 2 of output
withoutStopWordsFolderName = 'without_stop_words'
# Analysis folder: contains final output
analysisFolderName = 'Individual analysis'
# Frequency plot folder: contains frequency plot images
frequencyPlotFolderName = 'frequency_plot'


# -------------------------------
# Script parameters
# -------------------------------

# -------------------------------
# Predefined constants
# -------------------------------

ALPHANUM = string.ascii_letters + string.digits
NULLDATETIME = datetime.datetime(1019,12,14,22,17)
TIMESTAMPFORMAT = "%Y-%m-%d %H:%M"

# -------------------------------
# Pre-processing
# -------------------------------

if not (os.path.exists(inputDir)):
    os.makedirs(inputDir)
if not (os.path.exists(outputDir)):
    os.makedirs(outputDir)

# ===============================
# Class definitions
# ===============================

class GlobalStats:
    def __init__(self):
        return

    def Calcs(self, contacts, outputFolderPath):
        fout = open(outputFolderPath,mode = "w",encoding="utf8")
        sumTM = 0
        NamesandMsgs = {}
        avgwords = {}
        fout.write("The list of people in this chat are \n")
        for name in contacts:
            fout.write("\n {} ".format(name))
            NamesandMsgs[name] = contacts[name].TotalMessages
            avgwords[name] = contacts[name].AvgWords
        print(NamesandMsgs.items())
        TopNamesAndMsgs = dict(sorted(NamesandMsgs.items(), key=operator.itemgetter(1), reverse=True)[:5])
        TopAvgWords = dict(sorted(avgwords.items(), key=operator.itemgetter(1), reverse=True)[:5])
        sumTM = sum(NamesandMsgs.values())
        fout.write("\n\nThe total messages sent in this chat are {}".format(sumTM))
        fout.write("\n\nThe top message senders in this chat are : ")
        for key,value in TopNamesAndMsgs.items():
            fout.write("\n{} : {}".format(key,value))
        fout.write("\n\nThe top users who write the most number of words per message are : ")
        for key,value in TopAvgWords.items():
            fout.write("\n{} : {}".format(key,value))
        fout.close()


class IndivStats:

    def __init__(self,name = 'null',AvgWords = 0,TotalMessages = 0,WordCount = 0):
        self.AvgWords = AvgWords
        self.TotalMessages = TotalMessages
        self.WordCount = WordCount
        self.name = name

    def IncrementMsgCount(self, amt):
        self.TotalMessages += amt

    def IncrementWordCount(self, amt):
        self.WordCount += amt

    def Calculations(self,inputFilePath,outputFilePath):
        fin = open(inputFilePath,mode='r',encoding="utf8")
        fout = open(outputFilePath,mode = 'a',encoding = "utf8")
        self.WordCount = 0
        count = 0
        line = fin.readline()
        while(line):
            (x,nam,message) = self.ValidateLineName(line)
            words = message.split()
            self.WordCount += len(words)
            if x and self.name == nam:
                count += 1
            line = fin.readline()
        self.TotalMessages = count
        self.AvgWords = round(self.WordCount / self.TotalMessages)
        fout.write("\n\nThe Total number of words sent by {} is {}".format(self.name,self.WordCount))
        fout.write("\n\nThe Total number of messages sent by {} is {}".format(self.name, self.TotalMessages))
        fout.write("\n\nThe Average number of words sent by {} per message is {}".format(self.name, self.AvgWords))
        fin.close()
        fout.close()
        return self.WordCount,self.TotalMessages,self.AvgWords

    # ===============================
    # Utility functions
    # ===============================

    # Function returns day of year as int. The day of year is always found for a leap year.
    def DayOfYear(self, timeStamp):
        timeStamp = datetime.datetime(2000, timeStamp.month, timeStamp.day)
        yday = (timeStamp - datetime.datetime(timeStamp.year, 1, 1)).days + 1
        return yday

    # ===============================
    # Utility functions
    # ===============================

    # Check if a directory exists, if not, create it
    def ValidatePath(self, path):
        if not (os.path.exists(path)):
            os.makedirs(path)
            return False
        # True implies path exists
        return True

    # Function used to check if input and output file paths are feasible.
    # If this function returns false, it means something is wrong with the IO specifications
    # To use: insert below code snippet
    # if not ValidateIO(inputFilePath, outputFilePath):
    #       return
    def ValidateIO(self, inputFilePath, outputFilePath):
        # Verifying existence of input file path
        (inputFileHead, inputFileName) = os.path.split(inputFilePath)
        if inputFileHead:
            if not self.ValidatePath(inputFileHead):
                print('Path {} is empty. Analysis aborted'.format(inputFileHead))
                return False
            if inputFilePath == outputFilePath:
                print('Output and input paths are identical. Analysis aborted')
                return False

        # Verifying existence of output folder containing the output file
        self.ValidatePath(os.path.split(outputFilePath)[0])
        return True

    # Variation of ValidateIO used if output folder instead of output file is specified
    def ValidateIOf(self,inputFilePath, outputFolderPath):
        (inputFileHead, inputFileName) = os.path.split(inputFilePath)
        if inputFileHead:
            if not self.ValidatePath(inputFileHead):
                print('Path {} is empty. Analysis aborted'.format(inputFileHead))
                return False
        # Verifying existence of output folder containing the output file
        self.ValidatePath(outputFolderPath)
        return True

    # Check if the message starts with a date in the proper format, also returns datetime if a valid one was found
    def ValidateLineDate(self,linestr):
        # The first 20 characters of the message correspond to the timestamp
        linestr = linestr[0:20]
        rcrdDateTime = NULLDATETIME
        if len(linestr) < 20:
            return (False, rcrdDateTime)
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
            if (i not in (2, 5, 10, 11, 14, 17, 18, 19)):
                if (not (linestr[i].isdigit())):
                    flag = False
        if (flag == True):
            # parse function reads the timestamp in string form and converts it into a datetime data type
            rcrdDateTime = dateutil.parser.parse(linestr[0:17], dayfirst=True)
        # Returns whether timestamp is valid along with timestamp
        return (flag, rcrdDateTime)

    # Check whether the message was sent by someone. Meaning it is of the format "person_name: Message".
    def ValidateLineName(self,linestr):
        # The first 20 characters of the message correspond to the timestamp
        linestr = linestr[20:]
        name_length = 0
        flag = False
        # Searches for a semicolon to indicate where the message starts
        while (name_length < len(linestr)):
            if (linestr[name_length] == ':'):
                flag = True
                break
            name_length += 1
        if (flag == False):
            return (False, 'null', 'null')
        if (flag == True):
            # this means that a name was found. Now we have to check whether it is a false name due to misinterpretation
            name = linestr[:name_length]
            # misinterpretation in group creation
            if (' created group "' in name):
                return (False, 'null', 'null')
            # misinterpretation in group subject change
            if (' changed the subject from "' in name):
                return (False, 'null', 'null')
            # Returns whether name was detected, the name and the rest of the string
            return (True, linestr[:name_length], linestr[name_length + 2:])

    # Function should print the top 5 word count
    def FindWordCountFromFile(self,inputFilePath, outputFilePath):
        print('Analysing file: {}'.format(inputFilePath))

        if not self.ValidateIO(inputFilePath, outputFilePath):
            return

        # Input from fin, output in fout
        fout = open(outputFilePath, mode='w', encoding='utf8')
        fout.write("The top 5 words used by the user are :\n\n")
        with open(inputFilePath, 'r', encoding='utf8') as fin:
            coun = Counter(fin.read().split())
            for word, count in coun.most_common(5):
                fout.write('%s : %d\n' % (word, count))
        fout.close()
        print('Analysis complete. Output stored in {}'.format(outputFilePath))

    # Function should check whether the message sent was one of the few system generated messages:
    # Media Messages, Deleted Messages, Group Invites
    def IsIgnorableMsg(self,message):
        if (message == "<Media omitted>\n"):
            return True
        if (message == "This message was deleted\n"):
            return True

        # NOTE: The below message contains a hidden character \u200e at the start of the message. So message length was increased from 42 to 43
        if (message[:43] == "‎Open this link to join my WhatsApp Group: "):
            return True
        if (message[:44] == "Follow this link to join my WhatsApp group: "):
            return True
        return False

    # Function should remove all stopwords that are present in the list of stopwords
    def RemoveStopWords(self,inputFilePath, outputFilePath):
        # Stop Words: commonly used words like for, is, and that need to be filtered out
        stop_Words = set(stopwords.words('english'))
        # TweetTokenizer tokenizes string but preserves ' and - in words
        tknr = TweetTokenizer()

        if not self.ValidateIO(inputFilePath, outputFilePath):
            return

        fin = open(inputFilePath, mode='r', encoding='utf8')
        fout = open(outputFilePath, mode='w', encoding="utf8")

        line = fin.readline()
        while line:
            wordlist = tknr.tokenize(line)
            for word in wordlist:
                word = word.lower()
                # If the word contains an apostrophe, it is a contraction. The first word in the contraction is only considered
                # Any words following the apostrophe are always stop words. So we can ignore them
                if ("'" in word):
                    word = nltk.word_tokenize(word)[0]
                if not word in stop_Words:
                    flag = False
                    for letter in word:
                        # The word is counted as a valid word if and only if it has at least one alphanum in it
                        if letter in (ALPHANUM):
                            flag = True
                            break
                    if flag == True:
                        fout.write(" " + word)
            fout.write('\n')
            line = fin.readline()

        fin.close()
        fout.close()

    # Reads a group, and creates a text file for each person who sent messages in the group
    def SplitMessageNametagTimestamp(self,inputFilePath, msgOutputFolderPath, timestampOutputFolderPath):
        # splitmsgfout is a dictionary of all splitmsg output file pointers mapped to the name of the message
        splitmsgfout = {}
        # timestampfout is a dictionary of all timestamp output file pointers mapped to the name of the message
        timestampfout = {}
        # contacts is a dictionary of all the class objects of IndivStats for the particular chat
        contacts = {}

        if not self.ValidateIOf(inputFilePath, msgOutputFolderPath):
            return
        self.ValidatePath(timestampOutputFolderPath)

        # input text file will be opened
        f = open(inputFilePath, mode='r', encoding='utf8')
        print('Processing: {}'.format(inputFilePath))

        # Total lines parsed
        totalMsg = 0
        # Of which how many had passed the timestamp validation
        validDates = 0
        # Of which how many had been actually sent by a person
        validMsg = 0
        line = f.readline()
        # variable that checks whether the current message is a continuation of a previous message
        isContinuation = False
        lastMsgSenderName = 'null'
        while (line):
            totalMsg += 1
            (isDateValid, currentMsgDateTime) = self.ValidateLineDate(line)
            (isNameValid, name, message) = self.ValidateLineName(line)
            # First checks if the message starts with a timestamp
            if (isDateValid):
                validDates += 1
                # Then checks if it has a valid name of sender
                if (isNameValid):
                    isContinuation = True
                    lastMsgSenderName = name

                    # In that case, write the message into the corresponding text file of that sender
                    # If such a text file doesn't exist, initialise the name into the dictionaries and create text file
                    if name not in splitmsgfout:
                        # initialise splitmsg output file
                        splitmsgfout[name] = open('{}/{}.txt'.format(msgOutputFolderPath, name), mode='w',
                                                  encoding='utf8')
                        # initialse timestamp output file
                        timestampfout[name] = open('{}/{}.txt'.format(timestampOutputFolderPath, name), mode='w',
                                                   encoding='utf8')
                        # initialise contact class object
                        contacts[name] = IndivStats(name, 0, 0, 0)

                    # This is the final check that determines if the message is a valid message, sent by a contact. Deleted messages and invites are ignored here.
                    if (not (self.IsIgnorableMsg(message))):
                        validMsg += 1
                        # Message contents are added to splitmsg file
                        splitmsgfout[name].write(message)
                        # Timestamp is added to timestamp file
                        timestampfout[name].write(currentMsgDateTime.strftime(TIMESTAMPFORMAT))
                        timestampfout[name].write('\n')


                # If a valid timestamp exist but a valid name does not, then whatever message comes next cannot be a continuation
                else:
                    isContinuation = False
            # If a valid timestamp doesn't exist, it means that the message is a continuation line of previously sent message
            else:
                if isContinuation:
                    splitmsgfout[lastMsgSenderName].write(line)
            line = f.readline()
        print('Processing finished. {} lines parsed. {} valid timestamps discovered. {} valid messages found.'.format(
            totalMsg, validDates, validMsg))
        f.close()
        for name in splitmsgfout:
            splitmsgfout[name].close()
            timestampfout[name].close()
        return splitmsgfout,timestampfout,contacts

        # Reads a text file containing timestamps, and plots a bar graph based on frequency of occurence of timestamps
        # Output is saved to an image file
        # NOTE: currently the function counts frequency on a per day basis. TODO: Add more frequency options

    def FrequencyPlotFromFile(self,inputFilePath, outputFilePath, frequency='day'):
        # File validation
        if not self.ValidateIO(inputFilePath, outputFilePath):
            return

        # Frequencies of messages sent on a per day basis
        freqDistTableYearly = np.zeros(366, int)

        # Counting frequencies
        with open(inputFilePath, 'r', encoding='utf8') as fin:
            line = fin.readline()
            while line:
                # Timestamps are correctly parsed if they are in the standard format for timestamps
                currentTimeStamp = dateutil.parser.parse(line)
                # Converted timestamp to an integer value from 1 to 366 depending on day of year, useful for plotting
                yDay = self.DayOfYear(currentTimeStamp)
                freqDistTableYearly[yDay - 1] += 1
                line = fin.readline()

        # this is for plotting purpose
        index = np.arange(1, 367)
        plt.bar(index, freqDistTableYearly)
        plt.xlabel('Day of Year', fontsize=5)
        plt.ylabel('No of Messages', fontsize=5)
        # plt.xticks(index, index, fontsize=5, rotation=30)
        plt.title('Yearly frequency of messaging')
        plt.savefig(outputFilePath, dpi=200)
        plt.close()



# ===============================
# Main control loop
# ===============================


for inputFileName in os.listdir(inputDir):
    if inputFileName.endswith('.txt'):

        # Input file variable names for easy access
        (inputFileNameWithoutExt, inputFileExt) = os.path.splitext(inputFileName)
        inputTextFilePath = inputDir + '/{}'.format(inputFileName)

        # Definition of local file directories, these are unique for a particular group chat
        splitMessageOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt, splitMsgFolderName)
        IndivStats().ValidatePath(splitMessageOutputFolderPath)

        timestampOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt, timestampFolderName)
        IndivStats().ValidatePath(timestampOutputFolderPath)

        withoutStopWordsOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt,
                                                                       withoutStopWordsFolderName)
        IndivStats().ValidatePath(withoutStopWordsOutputFolderPath)

        analysisOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt, analysisFolderName)
        IndivStats().ValidatePath(analysisOutputFolderPath)

        frequencyPlotOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt, frequencyPlotFolderName)
        IndivStats().ValidatePath(frequencyPlotOutputFolderPath)

        # Processing Steps
        # fout is a dictionary of all file pointers mapped to the name of the message
        # Split Messages folder and Timestamp folder are created by this operation
        splitMsgFout,timeStampFout,Contacts = IndivStats().SplitMessageNametagTimestamp(inputTextFilePath, splitMessageOutputFolderPath, timestampOutputFolderPath)

        # Analysis Steps
        # loops through each individual contact name in the group
        for contact_name in Contacts:
            # Input Folder ---> Output Folder

            # Split Messages ---> Without Stop Words
            IndivStats().RemoveStopWords('{}/{}.txt'.format(splitMessageOutputFolderPath, contact_name),'{}/{}.txt'.format(withoutStopWordsOutputFolderPath, contact_name))

            # Without Stop Words ---> Analysis
            IndivStats().FindWordCountFromFile('{}/{}.txt'.format(withoutStopWordsOutputFolderPath, contact_name),'{}/{}.txt'.format(analysisOutputFolderPath, contact_name))
            WordCount, TotMsg, AvgWords = IndivStats(contact_name,0,0,0).Calculations(inputTextFilePath,'{}/{}.txt'.format(analysisOutputFolderPath, contact_name))
            Contacts[contact_name].WordCount = WordCount
            Contacts[contact_name].TotalMessages = TotMsg
            Contacts[contact_name].AvgWords = AvgWords
            IndivStats().FrequencyPlotFromFile('{}/{}.txt'.format(timestampOutputFolderPath, contact_name),'{}/{}.png'.format(frequencyPlotOutputFolderPath, contact_name))

        GlobalStats().Calcs(Contacts,'{}/Overall Chat Statistics.txt'.format(analysisOutputFolderPath))