# Scraper-covid-19
A scraper that scrapes Covid-19 table from [Ministry of Government and Family Welfare](https://www.mohfw.gov.in/) website every hour. If any changes occur, then an email is sent to the GMAIL account notifying the change with appropriate messages.  

The conda environment can be created using ```conda create --name <env> --file requirements.txt```.\
Other Requirements:
1. Chrome Web Driver- which can be downloaded from [here](https://chromedriver.chromium.org/downloads). It is to be placed in the same project folder.
2. A JSON file containing the EMAIL and PASSWORD of GMAIL account as follows
```json
   {
    "EMAIL": <gmail_address>,
    "PASSWORD": <password>
   }
```
To run the script
```
python scraper.py --file <path to JSON file containing Gmail Credentials>
```
