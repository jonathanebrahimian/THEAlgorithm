from dotenv import load_dotenv
import os
load_dotenv()
from lambda_function import lambda_handler
tokens = {
    'nil': '0x0eb638648207d00b9025684d13b1cb53806debe4',
    'teather': '0xdac17f958d2ee523a2206206994597c13d831ec7',
    'matic': '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0',
    'usd': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'shib': '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE',
    'uni': '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',
    'ape': '0x4d224452801aced8b2f0aebe155379bb5d594381'  # issue with APE
}
# lambda_handler(None,None)
event = {
   'queryStringParameters':{
      'token':tokens['nil']
   }
}
lambda_handler(event, None)