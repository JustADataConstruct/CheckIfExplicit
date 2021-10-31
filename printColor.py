from colorama import Fore, Back, Style, init
import logging

def initPrint():
    init(autoreset=True)
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
    filename="explicit.log",level=logging.INFO,filemode="a")

def printInfo(text:str):
    t = text + "\n"
    print(t)
    logging.info(t)

def printSuccess(text:str):
    t = text + "\n"
    print(Fore.GREEN + t)
    logging.info(t)

def printWarning(text:str):
    t = text + "\n"
    print(Fore.YELLOW + t)
    logging.info(t)

def printError(text:str):
    t = text + "\n"
    print(Fore.RED + t)
    logging.info(t)