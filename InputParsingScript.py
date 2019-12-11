import os
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
import string

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
# Without stop words folder: contains step 2 of output
withoutStopWordsFolderName = 'without_stop_words'
# Analysis folder: contains final output
analysisFolderName = 'analysis'

# -------------------------------
# Script parameters
# -------------------------------

# -------------------------------
# Predefined constants
# -------------------------------

ALPHANUM = string.ascii_letters + string.digits

# -------------------------------
# Pre-processing
# -------------------------------

if not (os.path.exists(inputDir)):
    os.makedirs(inputDir)
if not (os.path.exists(outputDir)):
    os.makedirs(outputDir)

# ===============================
# Utility functions
# ===============================

# Check if a directory exists, if not, create it
def ValidatePath(path):
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
def ValidateIO(inputFilePath, outputFilePath):
    # Verifying existence of input file path
    (inputFileHead, inputFileName) = os.path.split(inputFilePath)
    if inputFileHead:
        if not ValidatePath(inputFileHead):
            print('Path {} is empty. Analysis aborted'.format(inputFileHead))
            return False
        if inputFilePath == outputFilePath:
            print('Output and input paths are identical. Analysis aborted')
            return False

    # Verifying existence of output folder containing the output file
    ValidatePath(os.path.split(outputFilePath)[0])
    return True

# Variation of ValidateIO used if output folder instead of output file is specified
def ValidateIOf(inputFilePath, outputFolderPath):
    (inputFileHead, inputFileName) = os.path.split(inputFilePath)
    if inputFileHead:
        if not ValidatePath(inputFileHead):
            print('Path {} is empty. Analysis aborted'.format(inputFileHead))
            return False
    # Verifying existence of output folder containing the output file
    ValidatePath(outputFolderPath)
    return True

# Check if the message starts with a date in the proper format
def ValidateLineDate(linestr):
    # The first 20 characters of the message correspond to the timestamp
    linestr = linestr[0:20]
    if len(linestr) < 20:
        return False
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
    return flag

# Check whether the message was sent by someone. Meaning it is of the format "person_name: Message".
def ValidateLineName(linestr):
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
def FindWordCountFromFile(inputFilePath, outputFilePath):
    print('Analysing file: {}'.format(inputFilePath))

    if not ValidateIO(inputFilePath, outputFilePath):
        return

    # Input from fin, output in fout
    fout = open(outputFilePath, mode='w', encoding='utf8')
    with open(inputFilePath, 'r', encoding='utf8') as fin:
        coun = Counter(fin.read().split())
        for word, count in coun.most_common(5):
            fout.write('%s: %d\n' % (word, count))
    fout.close()
    print('Analysis complete. Output stored in {}'.format(outputFilePath))

# Function should check whether the message sent was one of the few system generated messages:
# Media Messages, Deleted Messages, Group Invites
def IsIgnorableMsg(message):
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
def RemoveStopWords(inputFilePath, outputFilePath):
    # Stop Words: commonly used words like for, is, and that need to be filtered out
    stop_Words = set(stopwords.words('english'))
    # TweetTokenizer tokenizes string but preserves ' and - in words
    tknr = TweetTokenizer()

    if not ValidateIO(inputFilePath, outputFilePath):
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
def SplitMessageFilesBySender(inputFilePath, outputFolderPath):
    # fout is a dictionary of all file pointers mapped to the name of the message
    fout = {}

    if not ValidateIOf(inputFilePath, outputFolderPath):
        return
    
    # text file will be opened
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
        isDateValid = ValidateLineDate(line)
        (isNameValid, name, message) = ValidateLineName(line)
        # First checks if the message starts with a timestamp
        if (isDateValid):
            validDates += 1
            # Then checks if it has a valid name of sender
            if (isNameValid):
                validMsg += 1
                isContinuation = True
                lastMsgSenderName = name

                # In that case, write the message into the corresponding text file of that sender
                # If such a text file doesn't exist, create one
                if name not in fout:
                    fout[name] = open('{}/{}.txt'.format(outputFolderPath, name), mode='w', encoding='utf8')
                if (not (IsIgnorableMsg(message))):
                    fout[name].write(message)
            # If a valid timestamp exist but a valid name does not, then whatever message comes next cannot be a continuation
            else:
                isContinuation = False
        # If a valid timestamp doesn't exist, it means that the message is a continuation line of previously sent message
        else:
            if isContinuation:
                fout[lastMsgSenderName].write(line)
        line = f.readline()
    print('Processing finished. {} lines parsed. {} valid timestamps discovered. {} valid messages found.'.format(totalMsg, validDates, validMsg))
    f.close()
    for name in fout:
        fout[name].close()
    return fout


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
        ValidatePath(splitMessageOutputFolderPath)

        withoutStopWordsOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt, withoutStopWordsFolderName)
        ValidatePath(withoutStopWordsOutputFolderPath)

        analysisOutputFolderPath = outputDir + '/{}/{}'.format(inputFileNameWithoutExt, analysisFolderName)
        ValidatePath(analysisOutputFolderPath)

        # Processing Steps
        # fout is a dictionary of all file pointers mapped to the name of the message
        fout = SplitMessageFilesBySender(inputTextFilePath, splitMessageOutputFolderPath)

        # Analysis Steps
        # loops through each individual contact name in the group
        for contact_name in fout:
            # Input Folder ---> Output Folder

            # Split Messages ---> Without Stop Words
            RemoveStopWords('{}/{}.txt'.format(splitMessageOutputFolderPath, contact_name), '{}/{}.txt'.format(withoutStopWordsOutputFolderPath, contact_name))

            # Without Stop Words ---> Analysis
            FindWordCountFromFile('{}/{}.txt'.format(withoutStopWordsOutputFolderPath, contact_name), '{}/{}.txt'.format(analysisOutputFolderPath, contact_name))
