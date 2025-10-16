# __license__ = 'MIT'
import math
import os
import sys
import time

def say(*messages):
    print(" ".join(str(m) for m in messages))

def ask(question):
    return input(question + " ")

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b if b != 0 else "Cannot divide by zero"

def square(n):
    return n * n

def cube(n):
    return n * n * n

def power(base, exp):
    return base ** exp

def sqrt(n):
    return math.sqrt(n)

def average(*numbers):
    return sum(numbers) / len(numbers)

def maximum(*numbers):
    return max(numbers)

def minimum(*numbers):
    return min(numbers)

def total(numbers):
    return sum(numbers)

def percentage(part, whole):
    return (part / whole) * 100

def isEven(n):
    return n % 2 == 0

def isOdd(n):
    return n % 2 == 1

def wait(seconds):
    time.sleep(seconds)

def showTime():
    say(time.strftime("%H:%M:%S"))

def showDate():
    say(time.strftime("%Y-%m-%d"))

def countdown(seconds):
    for i in range(seconds, 0, -1):
        say(i)
        time.sleep(1)
    say("Time's up!")

def repeat(times, func, *args):
    for _ in range(times):
        func(*args)

def ifTrue(condition, trueFunc, *trueArgs):
    if condition:
        trueFunc(*trueArgs)

def ifFalse(condition, falseFunc, *falseArgs):
    if not condition:
        falseFunc(*falseArgs)

def choose(option1, func1, option2, func2, *args):
    if option1:
        func1(*args)
    else:
        func2(*args)

def splitText(text, delimiter):
    return text.split(delimiter)

def joinText(items, connector):
    return connector.join(map(str, items))

def reverseText(text):
    return text[::-1]

def textLength(text):
    return len(text)

def makeUnique(items):
    return list(set(items))

def sortItems(items):
    return sorted(items)

def findInList(item, items):
    return item in items

def countInList(item, items):
    return items.count(item)

def writeFile(filename, content):
    with open(filename, 'w') as f:
        f.write(str(content))

def readFile(filename):
    with open(filename, 'r') as f:
        return f.read()

def appendFile(filename, content):
    with open(filename, 'a') as f:
        f.write(str(content))

def deleteFile(filename):
    if os.path.exists(filename):
        os.remove(filename)
        return True
    return False

def fileExists(filename):
    return os.path.exists(filename)

def listFiles(folder="."):
    return os.listdir(folder)

def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    input("Press Enter to continue...")

def exitApp():
    sys.exit()

def openWebsite(url):
    import webbrowser
    webbrowser.open(url)

def searchWeb(query):
    import webbrowser
    webbrowser.open(f"https://google.com/search?q={query}")

def saveData(key, value):
    if not hasattr(saveData, 'storage'):
        saveData.storage = {}
    saveData.storage[key] = value

def loadData(key):
    return getattr(saveData, 'storage', {}).get(key)

def roundNumber(n, decimals=0):
    return round(n, decimals)

def floorNumber(n):
    return math.floor(n)

def ceilingNumber(n):
    return math.ceil(n)

def absoluteValue(n):
    return abs(n)

def isPrime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def factorial(n):
    return math.factorial(n) if n >= 0 else "Invalid"

def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence

def createList(*items):
    return list(items)

def createDict(**pairs):
    return pairs

def getKeys(dictionary):
    return list(dictionary.keys())

def getValues(dictionary):
    return list(dictionary.values())

def addToDict(dictionary, key, value):
    dictionary[key] = value
    return dictionary

def removeFromDict(dictionary, key):
    if key in dictionary:
        del dictionary[key]
    return dictionary

def mergeDicts(dict1, dict2):
    return {**dict1, **dict2}

def toUpper(text):
    return text.upper()

def toLower(text):
    return text.lower()

def capitalizeText(text):
    return text.capitalize()

def titleText(text):
    return text.title()

def replaceText(text, old, new):
    return text.replace(old, new)

def trimText(text):
    return text.strip()

def startsWith(text, prefix):
    return text.startswith(prefix)

def endsWith(text, suffix):
    return text.endswith(suffix)

def findText(text, substring):
    return text.find(substring)

def countText(text, substring):
    return text.count(substring)

def convertCtoF(c):
    return (c * 9/5) + 32

def convertFtoC(f):
    return (f - 32) * 5/9

def convertKMtoMiles(km):
    return km * 0.621371

def convertMilesToKM(miles):
    return miles * 1.60934

def getCurrentFolder():
    return os.getcwd()

def changeFolder(path):
    os.chdir(path)

def createFolder(name):
    os.makedirs(name, exist_ok=True)

def isFile(path):
    return os.path.isfile(path)

def isFolder(path):
    return os.path.isdir(path)

def fileSize(filename):
    return os.path.getsize(filename)

def validateEmail(email):
    return '@' in email and '.' in email

def validateNumber(text):
    try:
        float(text)
        return True
    except:
        return False

def formatCurrency(amount):
    return f"${amount:.2f}"

def formatPercent(decimal):
    return f"{decimal * 100:.1f}%"

def formatNumber(n):
    return f"{n:,}"

def getSystemInfo():
    say(f"Python version: {sys.version}")
    say(f"Platform: {sys.platform}")

def timerStart():
    return time.time()

def timerStop(startTime):
    return time.time() - startTime

def measureTime(func, *args):
    start = time.time()
    result = func(*args)
    end = time.time()
    say(f"Time taken: {end - start:.2f} seconds")
    return result

def createCounter():
    counter = 0
    def count():
        nonlocal counter
        counter += 1
        return counter
    return count

def sayHello():
    say("Hello!")

def sayGoodbye():
    say("Goodbye!")

def calculateArea(shape, *dimensions):
    if shape == "circle":
        return math.pi * dimensions[0] ** 2
    elif shape == "square":
        return dimensions[0] ** 2
    elif shape == "rectangle":
        return dimensions[0] * dimensions[1]
    return 0

def calculatePerimeter(shape, *dimensions):
    if shape == "circle":
        return 2 * math.pi * dimensions[0]
    elif shape == "square":
        return 4 * dimensions[0]
    elif shape == "rectangle":
        return 2 * (dimensions[0] + dimensions[1])
    return 0
