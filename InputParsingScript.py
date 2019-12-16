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
analysisFolderName = 'individual_analysis'
# Frequency plot folder: contains frequency plot images
frequencyPlotFolderName = 'frequency_plot'

# file names: file names are given with extensions
globalAnalysisOutputFileName = 'Overall Chat Statistics.txt'
globalBarGraphFileName = 'bar_graph_day_of_year.png'

# -------------------------------
# Script parameters
# -------------------------------

floatDigitsAfterDecimal = 2

# -------------------------------
# Predefined constants
# -------------------------------

ALPHANUM = string.ascii_letters + string.digits
NULLDATETIME = datetime.datetime(1019,12,14,22,17)
TIMESTAMPFORMAT = "%Y-%m-%d %H:%M"
FORBIDDENFILECHARACTERS = '\\/?*"<>|'

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

# Class contains common methods used by both the below classes. Functions such as ValidatePath and ValidateIO are shared as both classes have need of file validation
class CommonValidationMethods:
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
    # if not self.ValidateIO(inputFilePath, outputFilePath):
    #       return
    def ValidateIO(self, inputFilePath, outputFilePath):
        # Verifying existence of input file path
        (inputFileDirectory, inputFileName) = os.path.split(inputFilePath)
        if inputFileDirectory:
            if not self.ValidatePath(inputFileDirectory):
                print('Path {} is empty. Analysis aborted'.format(inputFileDirectory))
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


# Class used for maintaining overall statistics of a group chat. IndivStat objects are created through this class which handle individual stat data
# GlobalStats inherits all the methods from CommonValidationMethods class.
class GlobalStats(CommonValidationMethods):
    def __init__(self, name):
        self.name = name
        self.contacts = {}
        self.inputFilePath = 'null'
        self.outputFolderPath = 'null'
        self.splitMessageOutputFolderPath = 'null'
        self.timestampOutputFolderPath = 'null'
        self.withoutStopWordsOutputFolderPath = 'null'
        self.individualAnalysisOutputFolderPath = 'null'
        self.globalAnalysisOutputFilePath = 'null'
        self.frequencyPlotOutputFolderPath = 'null'
        self.globalFrequencyPlotOutputFilePath = ' null'

    def SetFilePaths(self, inputFilePath):
        self.inputFilePath = inputFilePath
        self.outputFolderPath = outputDir +'/{}'.format(self.name)
        # Definition of local file directories, these are unique for a particular group chat
        self.splitMessageOutputFolderPath = outputDir + '/{}/{}'.format(self.name, splitMsgFolderName)
        self.ValidatePath(self.splitMessageOutputFolderPath)

        self.timestampOutputFolderPath = outputDir + '/{}/{}'.format(self.name, timestampFolderName)
        self.ValidatePath(self.timestampOutputFolderPath)

        self.withoutStopWordsOutputFolderPath = outputDir + '/{}/{}'.format(self.name, withoutStopWordsFolderName)
        self.ValidatePath(self.withoutStopWordsOutputFolderPath)

        self.individualAnalysisOutputFolderPath = outputDir + '/{}/{}'.format(self.name, analysisFolderName)
        self.ValidatePath(self.individualAnalysisOutputFolderPath)

        self.globalAnalysisOutputFilePath = outputDir + '/{}/{}'.format(self.name, globalAnalysisOutputFileName)
        self.ValidatePath(self.globalAnalysisOutputFilePath)

        self.frequencyPlotOutputFolderPath = outputDir + '/{}/{}'.format(self.name, frequencyPlotFolderName)
        self.ValidatePath(self.frequencyPlotOutputFolderPath)

        self.globalFrequencyPlotOutputFilePath = outputDir + '/{}/{}'.format(self.name, globalBarGraphFileName)
        
    def Calculations(self):
        # Processing Steps
        # The Contacts is a dictionary of all IndivStats mapped to their name
        # Split Messages folder and Timestamp folder are created by this operation
        self.contacts = self.SplitMessageNametagTimestamp()

        # Analysis Steps
        # loops through each individual contact name in the group
        for contactName in self.contacts:
            
            # Setting the output file paths, so the object can access its respective output files easily
            splitMessageOutputFilePath = '{}/{}.txt'.format(self.splitMessageOutputFolderPath, contactName)
            timestampOutputFilePath = '{}/{}.txt'.format(self.timestampOutputFolderPath, contactName)
            withoutStopWordsOutputFilePath = '{}/{}.txt'.format(self.withoutStopWordsOutputFolderPath, contactName)
            individualAnalysisOutputFilePath = '{}/{}.txt'.format(self.individualAnalysisOutputFolderPath, contactName)
            frequencyPlotOutputFilePath = '{}/{}.png'.format(self.frequencyPlotOutputFolderPath, contactName)
            self.contacts[contactName].SetFilePaths(splitMessageOutputFilePath, timestampOutputFilePath, withoutStopWordsOutputFilePath, individualAnalysisOutputFilePath, frequencyPlotOutputFilePath)

            # Calculations performed on the object, its Individual Analysis is performed and all relevant files are created
            self.contacts[contactName].Calculations()
        self.WriteOverallGroupChatOutput()

    # ===============================
    # Utility functions
    # ===============================

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

            # if the name contains characters than cannot be on a word file, this function removes them
            name = self.RemoveCharacters(name, FORBIDDENFILECHARACTERS)
            
            # Returns whether name was detected, the name and the rest of the string
            return (True, linestr[:name_length], linestr[name_length + 2:])


    # Function replaces all occurences of the input characters with a whitespace
    def RemoveCharacters(self,inputString, characters):
        transTable = str.maketrans(characters, ' '*len(characters))
        return inputString.translate(transTable)
    
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

    # Reads a group, and creates a text file for each person who sent messages in the group
    def SplitMessageNametagTimestamp(self):
        # splitmsgfout is a dictionary of all splitmsg output file pointers mapped to the name of the message
        splitmsgfout = {}
        # timestampfout is a dictionary of all timestamp output file pointers mapped to the name of the message
        timestampfout = {}
        # contacts is a dictionary of all the class objects of IndivStats for the particular chat
        contacts = {}

        if not self.ValidateIOf(self.inputFilePath, self.splitMessageOutputFolderPath):
            return
        self.ValidatePath(self.timestampOutputFolderPath)

        # input text file will be opened
        f = open(self.inputFilePath, mode='r', encoding='utf8')
        print('Processing: {}'.format(self.inputFilePath))

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
                        splitmsgfout[name] = open('{}/{}.txt'.format(self.splitMessageOutputFolderPath, name), mode='w',
                                                  encoding='utf8')
                        # initialse timestamp output file
                        timestampfout[name] = open('{}/{}.txt'.format(self.timestampOutputFolderPath, name), mode='w',
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
        return contacts

    def WriteOverallGroupChatOutput(self):
        
        fout = open(self.globalAnalysisOutputFilePath,mode = "w",encoding="utf8")
        
        # Initialising data variables
        totalMessagesSum = 0
        namesAndMsgs = {}
        avgWords = {}
        totalChatWordsCounter = Counter()
        groupFreqDistTableYearly = np.zeros(366, int)


        print("Performing overall analysis on group chat: {}".format(self.name))
        fout.write("The list of people in this chat are \n")
        for name in self.contacts:
            fout.write("\n{} ".format(name))
            namesAndMsgs[name] = self.contacts[name].totalMessages
            avgWords[name] = self.contacts[name].avgWords
            groupFreqDistTableYearly = np.add(groupFreqDistTableYearly,self.contacts[name].freqDistTableYearly)
            totalChatWordsCounter += self.contacts[name].allWordCounts
        # namesAndMsgs will contain a dict of contact names mapped to total messages sent by them. This function will find top 5 of those names based on messages sent
        topNamesAndMsgs = dict(sorted(namesAndMsgs.items(), key=operator.itemgetter(1), reverse=True)[:5])
        # avgWords will contain a dict of contact names mapped to average words per message. This function will find top 5 f those names based on average words per message.
        topAvgWords = dict(sorted(avgWords.items(), key=operator.itemgetter(1), reverse=True)[:5])
        # totalMessagesSum adds all the totalMessages values of each individual contact
        totalMessagesSum = sum(namesAndMsgs.values())
        # groupAverageMessages finds average messages sent in group per day
        groupAverageMessages = round(np.mean(groupFreqDistTableYearly), floatDigitsAfterDecimal)

        # All totals and averages have been calculated. Now to write the rest of the data into the output file
        fout.write("\n\nThe total messages sent in this chat are {}".format(totalMessagesSum))
        fout.write("\n\nThe top message senders in this chat are : ")
        for key,value in topNamesAndMsgs.items():
            fout.write("\n{} : {}".format(key,value))
        fout.write("\n\nThe top users who write the most number of words per message are : ")
        for key,value in topAvgWords.items():
            fout.write("\n{} : {}".format(key,value))
        fout.write("\n\nThe average number of messages sent per day over the year are {}".format(groupAverageMessages))
        fout.write("\n\nThe top 5 most used words in the chat are:")
        for word, count in totalChatWordsCounter.most_common(5):
                fout.write('\n%s : %d' % (word, count))
        fout.close()

        # this is for plotting purpose
        index = np.arange(1, 367)
        plt.bar(index, groupFreqDistTableYearly)
        plt.xlabel('Day of Year', fontsize=5)
        plt.ylabel('No of Messages', fontsize=5)
        # plt.xticks(index, index, fontsize=5, rotation=30)
        plt.title('Yearly frequency of messaging')
        plt.savefig(self.globalFrequencyPlotOutputFilePath, dpi=200)
        plt.close()

        print("Overall Analysis complete.")

# Class used for storing and maintaining data of individual contact members in a particular group chat.
# IndivStats inherits all the methods from CommonValidationMethods class.
class IndivStats(CommonValidationMethods):

    # Setting up the class variables
    def __init__(self,name = 'null',avgWords = 0,totalMessages = 0,wordCount = 0):
        self.avgWords = avgWords
        self.totalMessages = totalMessages
        self.wordCount = wordCount
        self.name = name
        self.allWordCounts = Counter()
        self.freqDistTableYearly = np.zeros(366, int)
        self.splitMessageOutputFilePath = 'null'
        self.timestampOutputFilePath = 'null'
        self.withoutStopWordsOutputFilePath = 'null'
        self.individualAnalysisOutputFilePath = 'null'
        self.frequencyPlotOutputFilePath = 'null'
        
        
    # Setting the output file paths, so the object can access its respective output files easily
    def SetFilePaths(self, splitMessageOutputFilePath, timestampOutputFilePath, withoutStopWordsOutputFilePath, individualAnalysisOutputFilePath, frequencyPlotOutputFilePath):
        self.splitMessageOutputFilePath = splitMessageOutputFilePath
        self.timestampOutputFilePath = timestampOutputFilePath
        self.withoutStopWordsOutputFilePath = withoutStopWordsOutputFilePath
        self.individualAnalysisOutputFilePath = individualAnalysisOutputFilePath
        self.frequencyPlotOutputFilePath = frequencyPlotOutputFilePath


    def Calculations(self):
        # Input Folder ---> Output Folder

        # Split Messages ---> Without Stop Words
        # This function is also used to calculate total number of words, as it handles all words sent by the contact
        self.wordCount = self.RemoveStopWords()

        # Without Stop Words ---> Individual Analysis
        self.FindWordCountFromFile()

        # Timestamps ---> Frequency Plots
        # This function is also used to calculate total number of messages, as it handles all timestamps of messages sent by the contact
        self.totalMessages = self.FrequencyPlotFromFile()
        
        self.avgWords = round((self.wordCount / self.totalMessages), floatDigitsAfterDecimal)

        # Adding the rest of the data to the Individual Analysis file
        fout = open(self.individualAnalysisOutputFilePath, mode = 'a',encoding = "utf8")
        fout.write("\n\nThe Total number of words sent by {} is {}".format(self.name,self.wordCount))
        fout.write("\n\nThe Total number of messages sent by {} is {}".format(self.name, self.totalMessages))
        fout.write("\n\nThe Average number of words sent by {} per message is {}".format(self.name, self.avgWords))
        fout.close()

    # ===============================
    # Utility functions
    # ===============================

    # Function returns day of year as int. The day of year is always found for a leap year.
    def DayOfYear(self, timeStamp):
        timeStamp = datetime.datetime(2000, timeStamp.month, timeStamp.day)
        yDay = (timeStamp - datetime.datetime(timeStamp.year, 1, 1)).days + 1
        return yDay

    # Function should print the top 5 word count
    def FindWordCountFromFile(self):
        print('Analysing file: {}'.format(self.withoutStopWordsOutputFilePath))

        if not self.ValidateIO(self.withoutStopWordsOutputFilePath, self.individualAnalysisOutputFilePath):
            return

        # Input from fin, output in fout
        fout = open(self.individualAnalysisOutputFilePath, mode='w', encoding='utf8')
        fout.write("The top 5 words used by the user are :\n\n")
        with open(self.withoutStopWordsOutputFilePath, 'r', encoding='utf8') as fin:
            self.allWordCounts = Counter(fin.read().split())
            for word, count in self.allWordCounts.most_common(5):
                fout.write('%s : %d\n' % (word, count))
        fout.close()
        print('Analysis complete. Output stored in {}'.format(self.individualAnalysisOutputFilePath))

 
    # Function should remove all stopwords that are present in the list of stopwords
    # Function also calculates the word count and returns it
    def RemoveStopWords(self):
        # Stop Words: commonly used words like for, is, and that need to be filtered out
        stop_Words = set(stopwords.words('english'))
        # TweetTokenizer tokenizes string but preserves ' and - in words
        tknr = TweetTokenizer()

        if not self.ValidateIO(self.splitMessageOutputFilePath, self.withoutStopWordsOutputFilePath):
            return -1

        fin = open(self.splitMessageOutputFilePath, mode='r', encoding='utf8')
        fout = open(self.withoutStopWordsOutputFilePath, mode='w', encoding="utf8")

        totalWordCount = 0

        line = fin.readline()
        while line:
            wordlist = tknr.tokenize(line)
            for word in wordlist:
                word = word.lower()
                # If the word contains an apostrophe, it is a contraction. The first word in the contraction is only considered
                # Any words following the apostrophe are always stop words. So we can ignore them
                if ("'" in word):
                    word = nltk.word_tokenize(word)[0]
                # A word is recognised. Now we must find whether it is a stop word
                totalWordCount += 1
                if not word in stop_Words:
                    wordHasAnAlphaNumFlag = False
                    for letter in word:
                        # The word is counted as a valid word if and only if it has at least one alphanum in it
                        if letter in (ALPHANUM):
                            wordHasAnAlphaNumFlag = True
                            break
                    if wordHasAnAlphaNumFlag == True:
                        fout.write(" " + word)
                    # Otherwise, we have incorrectly added it to the word count. So we decrement word count
                    else:
                        totalWordCount -= 1
            fout.write('\n')
            line = fin.readline()

        fin.close()
        fout.close()
        return totalWordCount

        # Reads a text file containing timestamps, and plots a bar graph based on frequency of occurence of timestamps
        # Output is saved to an image file
        # NOTE: currently the function counts frequency on a per day basis. TODO: Add more frequency options

    def FrequencyPlotFromFile(self, frequency='day'):
        # File validation
        if not self.ValidateIO(self.timestampOutputFilePath, self.frequencyPlotOutputFilePath):
            return -1

        # Frequencies of messages sent on a per day basis
        self.freqDistTableYearly = np.zeros(366, int)

        # Counting frequencies
        with open(self.timestampOutputFilePath, 'r', encoding='utf8') as fin:
            totalMessages = 0
            line = fin.readline()
            while line:
                totalMessages += 1
                # Timestamps are correctly parsed if they are in the standard format for timestamps
                currentTimeStamp = dateutil.parser.parse(line)
                # Converted timestamp to an integer value from 1 to 366 depending on day of year, useful for plotting
                yDay = self.DayOfYear(currentTimeStamp)
                self.freqDistTableYearly[yDay - 1] += 1
                line = fin.readline()

        # this is for plotting purpose
        index = np.arange(1, 367)
        plt.bar(index, self.freqDistTableYearly)
        plt.xlabel('Day of Year', fontsize=5)
        plt.ylabel('No of Messages', fontsize=5)
        # plt.xticks(index, index, fontsize=5, rotation=30)
        plt.title('Yearly frequency of messaging')
        plt.savefig(self.frequencyPlotOutputFilePath, dpi=200)
        plt.close()
        return totalMessages



# ===============================
# Main control loop
# ===============================


for inputFileName in os.listdir(inputDir):
    # groupChats is a dictionary with Group chat names mapped to their respective GroupStat class objects
    groupChats = {}
    if inputFileName.endswith('.txt'):
        # This means we have detected an input file. We will assume all input files are group chat files that are stored in txt format.
        # Input file variable names for easy access
        # The file name is treated as the group chat's name. So "WhatsApp Chat with xxx" will end up being the group name
        (groupChatName, inputFileExt) = os.path.splitext(inputFileName)
        inputTextFilePath = inputDir + '/{}'.format(inputFileName)

        # An object for the group chat is created. It is named after the file name
        groupChats[groupChatName] = GlobalStats(groupChatName)

        # Setting the input and output file paths, so the object can access its respective output files easily
        groupChats[groupChatName].SetFilePaths(inputTextFilePath)

        # The group chat object now has all the info it requires to begin analysing. This function will also call individual analysis of each contact
        # name using the IndivStats class, whose object is an attribute of this class.
        groupChats[groupChatName].Calculations()