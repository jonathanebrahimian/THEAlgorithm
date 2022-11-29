token = "688TQHB39UPFXBNCUM5YMMT9184KSRU8HP"

import requests
import json


response = requests.get("""https://api.etherscan.io/api
   ?module=contract
   &action=getsourcecode
   &address=0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413
   &apikey=YourApiKeyToken""")

