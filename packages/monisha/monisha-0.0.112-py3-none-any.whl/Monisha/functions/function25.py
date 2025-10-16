import requests
from bs4 import BeautifulSoup
from ..scripts import Apis, Scripted
#=======================================================================

class Money:

    def convert(money, FROM="USD", TO="INR"):
        moni = float(money)
        page = requests.get(Apis.DATA01.format(FROM, TO))
        soup = BeautifulSoup(page.text, 'html.parser')
        dat1 = soup.find(class_="ccOutputTrail").previous_sibling
        dat2 = soup.find(class_="ccOutputTrail").get_text(strip=True)
        rate = float(Scripted.DATA12.format(dat1, dat2))
        return round(moni * rate, 2)

#=======================================================================
