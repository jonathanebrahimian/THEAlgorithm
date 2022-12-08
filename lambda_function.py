

import requests
import json
import os
import requests
from collections import defaultdict
import json
import re

'''
Regex explanations:
contracts: finds all contract declarations
  captures whether the contract is abstract and the contract name  
functions: finds all function declarations that may have modifiers
  captures the function name
'''
REGEX = dict({
  'contracts': '(?m)^^[ \t]*(abstract )?contract\s*([_A-z0-9]+)\s*(is [_A-z0-9, ]*)?\s*{',
  'functions': '(?m)^[ \t]*function ([_A-z0-9]+)\([^\)]*\)\s*([^{;]+){',
  'modifiers': '(?m)^[ \t]*modifier ([_A-z0-9]+)\([_A-z0-9]*\) {'
})

def lambda_handler(event, context):
  address = event['queryStringParameters']['token']
  print("This is the address",address)
  contract_name,source_split,source = get_contract_source(address)
  # TODO implement
  return {
    'statusCode': 200,
    'body': parse2(contract_name,source_split,source)
  }

def get_contract_source(address):
  api_key = os.environ.get('API_KEY')
  response = requests.get(f"""https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}""")
  data = response.json()
  # print(data)
  contract_name = data['result'][0]['ContractName']
  source = data['result'][0]['SourceCode']
  # print(source)
  
  if source[:2] == "{{":
    source = source[1:-1]
    source = json.loads(source)
    source = source['sources']
    concat = [source[key]['content'] for key in source]
    source = "\n".join(concat)
  
  try:
    source = json.loads(source)
    concat = [source[key]['content'] for key in source]
    source = "\n".join(concat)
  except Exception as e:
    # raise e
    pass
  # with open(f"{token}.txt", "w") as text_file:
  #   text_file.write(source)
  source_split = source.split('\n')
  print(len(source_split))

  return contract_name,source_split,source

def parse2(contract_name,source_split,source):
  #find contract names
  
  # '''
  contracts = re.finditer(REGEX['contracts'], source)
  # Custom contract "Constructor" for consistency
  new_contract = lambda curr_contract: {
    'name': curr_contract.group(2),
    'main': contract_name == curr_contract.group(2),
    'modifiers': []
  }
  # print([x for x in contracts])
  # print([x.group(2) for x in contracts])

  modifiers = re.finditer(REGEX['modifiers'], source)
  # Custom modifier "Constructor" for consistency
  new_modifier = lambda curr_modifier: {
    'functions': [],
    'name': curr_modifier.group(1)
  }
  # print([x for x in modifiers])
  # print([x.group(1) for x in modifiers])

  functions = re.finditer(REGEX['functions'], source)
  # Custom modifier "Constructor" for consistency
  new_function = lambda curr_function, source_code: {
    'name': curr_function.group(1),
    'source_code': source_code
  }
  # print([x for x in functions])
  # print([(x.group(1), x.group(2)) for x in functions])
  # '''
  
  data = {}
  data['contracts'] = []

  next_contract = None
  modifiers_list = []

  # This is a variable used to bypass any modifier processing parts of THE
  # algorithm if there are no modifiers
  has_modifiers = True

  try:
    next_contract = next(contracts)
  except StopIteration:
    #  No contracts were found, so return the empty list
    return data
  
  try:
    curr_modifier = next(modifiers)
  except StopIteration:
    #  No modifiers found, and this shouldn't break the code
    has_modifiers = False
  
  '''
  Right now, both next_contract and curr_modifier point to valid contracts and
  modifiers.
  
  CASE 1:
  If the next contract is before the current modifier, we want to get
  a new next contract, and change the next contract to the current one.
  
  CASE 2:
  Otherwise, we want to save the current modifier to that contract and get the
  next modifier.
  '''

  try:
    # Iterators throw a StopIteration exception when they are done
    while has_modifiers:
      # CASE 1
      if next_contract.start() < curr_modifier.start():
        # Update current contract
        curr_contract = next_contract

        # Save contract information
        data['contracts'].append(new_contract(curr_contract))

        # Get the next contract, or throw StopIteration if iterator is done
        next_contract = next(contracts)
        continue

      # CASE 2
      # Save modifier information
      data['contracts'][-1]['modifiers'].append(new_modifier(curr_modifier))
      modifiers_list.append({
        'name': curr_modifier.group(1),
        'contract': len(data['contracts']) - 1,
        'modifier': len(data['contracts'][-1]['modifiers']) - 1
      })

      # Get the next modifier, or throw StopIteration if iterator is done
      curr_modifier = next(modifiers)

  except StopIteration:
    pass

  '''
  Now, in case we ran out of modifiers, we iterate through the rest of the
  contracts and save them out.
  '''
  try:
    while True:
      # Update current contract
      curr_contract = next_contract

      # Save contract information
      data['contracts'].append(new_contract(curr_contract))

      # Get the next contract, or throw StopIteration if iterator is done
      next_contract = next(contracts)
  
  except StopIteration:
    pass

  '''
  Now, we are certainly out of contracts. We move all the rest of the modifiers,
  if there are any, into the last contract.
  '''
  try:
    while has_modifiers:
      # Save modifier information
      data['contracts'][-1]['modifiers'].append(new_modifier(curr_modifier))
      modifiers_list.append({
        'name': curr_modifier.group(1),
        'contract': len(data['contracts']) - 1,
        'modifier': len(data['contracts'][-1]['modifiers']) - 1
      })

      # Get the next modifier, or throw StopIteration if iterator is done
      curr_modifier = next(modifiers)

  except StopIteration:
    pass

  '''
  Now, we need to iterate through all the functions with an associated modifier,
  extract the source code with the function name, and return it
  '''
  try:
    while True:
      curr_function = next(functions)
      name, possible_modifiers = curr_function.group(1), curr_function.group(2)
      
      source_code = extract_source_code(source, curr_function.start())
      for modifier in modifiers_list:
        if modifier['name'] in possible_modifiers:
          data['contracts'][modifier['contract']]['modifiers'][modifier['modifier']]['functions'].append(
            new_function(curr_function, source_code)
          )

  except StopIteration:
    pass 

  return data

def extract_source_code(source, start):
  stack = 0
  in_function = False
  in_comment = False
  in_multiline_comment = False
  fn_length = 0

  prev_char, curr_char = '', ''
  while True:
    # Keep track of last 2 characters for comments
    prev_char = curr_char

    # Look at the next character
    fn_length += 1
    curr_char = source[start+fn_length]

    # Break out of/return because of // comments
    if in_comment:
      if curr_char == '\n':
        in_comment = False
      continue

    # Break out of/return because of /* comments */
    if in_multiline_comment:
      if prev_char == '*' and curr_char == '/':
        in_multiline_comment = False
      continue

    # Check for going deeper a level
    if curr_char == '{':
      stack += 1
      in_function = True
    
    # Check for returning from a level
    elif curr_char == '}':
      stack -= 1
    
    # Check for starting a // comment
    elif prev_char == '/' and curr_char == '/':
      in_comment = True
    
    # Check for starting a /* comment */
    elif prev_char == '/' and curr_char == '*':
      in_multiline_comment = True
    
    # If we have escaped the function and we have visited, we are done
    if stack == 0 and in_function:
      break
  
  return source[start:start+fn_length+1].split('\n')

def parse(contract_name,source_split):
  contract_def = 'contract ' + contract_name

  # find extended contracts
  extendables = []
  for i, line in enumerate(source_split):
    line_split = line.split(' ')
    if len(line_split) >= 2 and line_split[0] == 'contract':
      extendables.append(line_split[1].strip())
    elif len(line_split) >= 3 and line_split[0] == 'abstract' and line_split[1] == 'contract':
      extendables.append(line_split[2].strip())
  # print(extendables)


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
    # print(line_n,line)
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

  stack = -9999
  lines = []
  functions = defaultdict(set)
  src = {}
  visibilities = ['private', 'internal', 'external', 'public']
  for line_n, line in enumerate(source_split):
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
  
  dataframe_data = []
  for key in modifier_src:
    dataframe_data.append(
      {
      'code':"".join(modifier_src[key]),
      'function_name':key
    }
    )
  
  return data
