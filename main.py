import requests
import eyed3
import sys

def main() -> bool:
    if len(sys.argv) == 1:
        printHelp()
        return False
    authorName = sys.argv[1]
    print(authorName)
    return False

def printHelp():
    print("USAGE: main.py FOLDERPATH")

if __name__  == "__main__":
    main()
