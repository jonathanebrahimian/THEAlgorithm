from dotenv import load_dotenv
import os
load_dotenv()
from lambda_function import lambda_handler

# lambda_handler(None,None)
event = {
   'queryStringParameters':{
      'token':'0x0eb638648207d00b9025684d13b1cb53806debe4'
   }
}
print(lambda_handler(event, None))