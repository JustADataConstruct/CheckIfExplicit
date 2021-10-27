from colorama import Fore, Back, Style

def printInfo(text:str):
    print(text + "\n")

def printSuccess(text:str):
    print(Fore.GREEN + text + "\n")

def printWarning(text:str):
    print(Fore.YELLOW + text + "\n")

def printError(text:str):
    print(Fore.RED + text + "\n")