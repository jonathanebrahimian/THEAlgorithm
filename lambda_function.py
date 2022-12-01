

import requests
import json
import os
import requests
from collections import defaultdict
import json

# Hi!!!!
def lambda_handler(event, context):
   address = event['queryStringParameters']['token']
   print("This is the address")
   contract_name,source_split = get_contract_source(address)
    # TODO implement
   return {
      'statusCode': 200,
      'body': parse(contract_name,source_split)
   }

def get_contract_source(address):
   token = 'ape'
   api_key = os.environ.get('API_KEY')
   response = requests.get(f"""https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}""")
   data = response.json()
   contract_name = data['result'][0]['ContractName']
   source = data['result'][0]['SourceCode']
   # with open(f"{token}.txt", "w") as text_file:
   #    text_file.write(source)
   source_split = source.split('\n')
   return contract_name,source_split
   # len(source_split)




def parse(contract_name,source_split):
   contract_def = 'contract ' + contract_name

   # find extended contracts
   extendables = []
   for i,line in enumerate(source_split):
      # if 'contract ' + contract_name in line[:len(contract_def)+1]:
      #     # print(i+1,line)
      #     is_idx = line.find('is') + 2
      #     line = line.replace('{','')
      #     extendables = line[is_idx:].split(',')
      #     extendables = [extendable.strip() for extendable in extendables]
      line_split = line.split(' ')
      for word_i,x in enumerate(line_split):
         if word_i == 0 and x.strip() == 'contract' and word_i + 1 < len(line_split):
               extendables.append(line_split[word_i + 1].strip())
      # if line.strip()[:8] == 'contract':
      #     extendables
         
   print(extendables)


   modifiers = defaultdict(set)
   # find modifiers
   stack = 0
   curr_contract = None
   # modifiers = []
   for line_n,line in enumerate(source_split):
      stripped = line.strip()
      for extendable in extendables + [contract_name]:
         if 'contract ' + extendable in line:
               assert stack == 0
               curr_contract = extendable

      prev = ''
      for i,char in enumerate(stripped):
         if i == 0 and char == '*':
               continue
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
         modifiers[curr_contract].add(stripped[9:stripped.find('(')])

   # print(modifiers)

   functions = defaultdict(set)
   visibilities =['private', 'internal', 'external', 'public']
   for line_n,line in enumerate(source_split):
      stripped = line.strip()
      if 'function' == stripped[:8]:
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
               if mod in ['','view','returns','pure','virtual']:
                  continue
               functions[mod].add(func_name)



   # print("This contract extends the following contracts",extendables)
   # print('----------------------')
   # print("Modifiers per contract")
   # for key in modifiers:
   #    print("---Contract:",key,'---')
   #    for mod in modifiers[key]:
   #       print(mod)


   # # modifiers
   # print('----------------------')

   # print("The modifiers are used in these functions")
   # for key in functions:
   #    print("--- Modifier",key,'----')
   #    for func in functions[key]:
   #             print(func)
   data = {}
   data['contracts'] = defaultdict(list)
   for key in modifiers:
      modifiers_json = []
      for mod in modifiers[key]:
         modifiers_json.append({
            'name':mod,
            'functions':list(functions[mod])
         })

      data['contracts'][key].append(
         {
            'name':key,
            'modifiers':modifiers_json
         }
      )

   return data

# lambda_handler(None,None)