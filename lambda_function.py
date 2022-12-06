

import requests
import json
import os
import requests
from collections import defaultdict
import json


def lambda_handler(event, context):
   address = event['queryStringParameters']['token']
   print("This is the address",address)
   contract_name,source_split = get_contract_source(address)
   # TODO implement
   return {
      'statusCode': 200,
      'body': parse(contract_name,source_split)
   }

def get_contract_source(address):
   api_key = os.environ.get('API_KEY')
   response = requests.get(f"""https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}""")
   data = response.json()
   contract_name = data['result'][0]['ContractName']
   source = data['result'][0]['SourceCode']
   # with open(f"{token}.txt", "w") as text_file:
   #    text_file.write(source)
   source_split = source.split('\n')
   print(len(source_split))

   return contract_name,source_split


def parse(contract_name,source_split):
   contract_def = 'contract ' + contract_name

   # find extended contracts
   extendables = []
   for i, line in enumerate(source_split):
      # if 'contract ' + contract_name in line[:len(contract_def)+1]:
      #     # print(i+1,line)
      #     is_idx = line.find('is') + 2
      #     line = line.replace('{','')
      #     extendables = line[is_idx:].split(',')
      #     extendables = [extendable.strip() for extendable in extendables]
      line_split = line.split(' ')
      for word_i, x in enumerate(line_split):
         if word_i == 0 and x.strip() == 'contract' and word_i + 1 < len(line_split):
               extendables.append(line_split[word_i + 1].strip())
      # if line.strip()[:8] == 'contract':
      #     extendables



   modifiers = defaultdict(set)
   # find modifiers
   stack = 0
   curr_contract = None
   modifier_name = None
   modifier_src = {}
   # modifiers = []
   lines = []
   for line_n, line in enumerate(source_split):
      stripped = line.strip()
      for extendable in extendables + [contract_name]:
         if 'contract ' + extendable in line:
               assert stack == 0
               curr_contract = extendable

      prev = ''
      for i, char in enumerate(stripped):
         if i == 0 and char == '*':
               break
         if char == '/' and prev == '/':
               break
         if char == '{':
               stack += 1
         if char == '}':
               stack -= 1
         prev = char

      # stack += line.count('{')
      # stack -= line.count('}')
      if stack == 0:
         curr_contract = None

      if 'modifier' == stripped[:8]:
         assert curr_contract != None
         modifier_name = stripped[9:stripped.find('(')]
         modifiers[curr_contract].add(modifier_name)
      
      if modifier_name is not None:
         lines.append(line)
      
      if stack == 1 and modifier_name is not None:
         modifier_src[modifier_name] = lines
         modifier_name = None
         lines = []

   # print(modifiers)
   stack = -9999
   lines = []
   functions = defaultdict(set)
   src = {}
   visibilities = ['private', 'internal', 'external', 'public']
   for line_n, line in enumerate(source_split):
      # print(line_n,line,stack)
      stripped = line.strip()

      if 'function' == stripped[:8]:
         stack = 0
         func_name = stripped[9:stripped.find('(')]
         idx = -1
         vis_found = ''
         for visibility in visibilities:
               if stripped.find(visibility) > idx:
                  vis_found = visibility
                  idx = stripped.find(visibility)

         if idx == -1:
               continue

         mods = stripped[idx+len(vis_found):]
         mods = mods[:mods.find('(')].split(' ')
         for mod in mods:
               if mod in ['', 'view', 'returns', 'pure', 'virtual']:
                  continue
               functions[mod].add(func_name)

      prev = ''
      for i, char in enumerate(stripped):
         if i == 0 and char == '*':
               break
         if char == '/' and prev == '/':
               break
         if char == '{':
               stack += 1
         if char == '}':
               stack -= 1
         prev = char

      if stack >= 0:
         lines.append(line)
      if stack == 0:
         stack = -9999
         src[func_name] = lines
         lines = []
      
         

   for key in functions:
      functions[key] = list(functions[key])
      for i,func in enumerate(functions[key]):
         functions[key][i] = {
               'name':func,
               'source_code':src[func]
         }

   data = {}
   data['contracts'] = []
   data['test'] = 'This is a new line, for testing'
   for key in modifiers:
      modifiers_json = []
      for mod in modifiers[key]:
         modifiers_json.append({
         'name':mod,
         'functions':list(functions[mod])
         })
      main = contract_name == key
      
      data['contracts'].append(
         {
            'name':key,
            'modifiers':modifiers_json,
            'main':main
         }
      )
   
   import pandas as pd
   dataframe_data = []
   for key in modifier_src:
      dataframe_data.append(
         {
         'code':"".join(modifier_src[key]),
         'function_name':key
      }
      )
   
   # for key in src:
   #    if len(src[key]) == 1:
   #       continue
   #    dataframe_data.append({
   #       'code':"".join(src[key]),
   #       'function_name':key
   #    })

   df = pd.DataFrame(dataframe_data)

   df.to_csv("functions2.csv", index=False)
   return data
