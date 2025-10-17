import requests as re
import pandas as pd
import json
import hidroconta.types as tp
import hidroconta.hist as hist
import hidroconta.endpoints as endpoints
import hidroconta.time as time
import datetime
import secrets
import string
# For python <3.9, replace list[] with List[] from 'from typing import List'

'''
Allows an easy access to Demeter API from Python and
implements pandas dataframes compatibility
'''

'''Session cookies stored'''
__stored_cookies = None
__verbose = False

POST_HDR = {"Content-Type": "application/json"}

# Exception to be thrown when Demeter API returns an error status code
class DemeterStatusCodeException(Exception):
    pass

def set_verbose(verbose: bool):
    __verbose = verbose

def set_server(server: endpoints.Server):
    endpoints.set_server(server)

def get_server():
    return endpoints.get_server()

def login(username: str, password: str, daat: str = None):
    global __stored_cookies

    payload = '{{"username":"{}", "password":"{}"}}'.format(username, password)

    header_list = {
    'Content-Type': 'application/json'
    }

    if(daat is not None):
        header_list['Authorization'] = 'Bearer ' + daat

    response = re.post(get_server() + endpoints.DEMETER_LOGIN ,data=payload, headers=header_list)

    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)

    cookies = response.cookies.get_dict()
    __stored_cookies = cookies
    return cookies

def generate_daat(description: str, username: str = '', send_to_me: bool = True):
    if send_to_me:
        send_to_me = 'true'
    else:
        send_to_me = 'false'
    
    payload = '{{"username":"{}", "description":"{}", "sendToMe":{}}}'.format(username, description, send_to_me)

    response = re.post(get_server() + endpoints.DEMETER_DAAT, data=payload, headers=POST_HDR)

    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)

def revoke_daat(username: str):
    payload = '{{"username":"{}"}}'.format(username)

    response = re.post(get_server() + endpoints.DEMETER_DAAT_REVOKE, data=payload, headers=POST_HDR)

    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)

def create_user(username: str, role: tp.Role, installations: list[str], description: str = None, access: tp.Access = tp.Access.COMMON):
    password = generate_secure_password()
    preferences = '{"email":null,"languageId":null,"mailLanguageId":null,"unitVolumeId":null,"unitFlowId":null,"notificationSend":false,"mailSendAlarms":false,"voiceSendAlarms":false,"phone":""}'
    write_all = access == tp.Access.ALL_WRITE
    access_all = access == tp.Access.ALL_READ or access == tp.Access.ALL_WRITE
    if write_all:
        write_all = "true" 
    else:
        write_all = "false"
    if access_all:
        access_all = "true"
    else:
        access_all = "false"
    
    payload = '{{"username": "{}", "password": "{}", "description": "{}", "preferences":{}, "rolename": "{}", "installations": {}, "writeToAll": {}, "accessToAll": {}}}'.format(username, password, description, preferences, role.name, installations, write_all, access_all)
    payload = payload.replace("'", '"')
    response = re.post(url=get_server() + endpoints.USERS, data=payload, headers=POST_HDR, cookies=__stored_cookies)
    if(response.status_code == 201):
        return response
    else:
        raise DemeterStatusCodeException(response.status_code, response.text)

def create_user_with_permission(file_route: str, role: tp.Role, description: str = None, access: tp.Access = tp.Access.COMMON):
    users = pd.read_csv(file_route)
    
    passwords = []
    users_ids = []
    for index, row in users.iterrows():
        password = generate_secure_password()
        username = row['username']
        codes = row['codes']
        installation = row['installation']
        codes = codes.split(';;')
        
        try:
            response = create_user(username=username, role=role, description=description, installations=[installation], access=access)
            pandas = pd.json_normalize(json.loads(response.text))
            user_id = pandas.loc[0, 'userId']
            users_ids.append(user_id)
            passwords.append(password)

            for code in codes:

                try:
                    grant_basic_permission(user_id=user_id, element_code=code)
                except DemeterStatusCodeException as error:
                    for i in range(len(users) - len(users_ids)):
                        users_ids.append('NAN')
                    for i in range(len(users) - len(passwords)):
                        passwords.append('NAN')
                    users['password'] = passwords
                    users['userId'] = users_ids
                    users.to_csv(file_route + '-copy.csv')
                    raise error
        except DemeterStatusCodeException as error:
            for i in range(len(users) - len(users_ids)):
                users_ids.append('NAN')
            for i in range(len(users) - len(passwords)):
                passwords.append('NAN')
            users['password'] = passwords
            users['userId'] = users_ids
            users.to_csv(file_route + '-copy.csv')
            raise DemeterStatusCodeException(error)
        
    for i in range(len(users) - len(users_ids)):
        users_ids.append('NAN')
    for i in range(len(users) - len(passwords)):
        passwords.append('NAN')

    users['password'] = passwords
    users['userId'] = users_ids
    users.to_csv(file_route + '-copy.csv')

def grant_basic_permission(user_id: int, element_code: str):
    searched = search(text=element_code, element_types=[tp.Element.IRIS, tp.Element.RTU, tp.Element.CENTAURUS], status=tp.Status.ENABLED, pandas = True)
    element_id = searched.loc[0, 'elementId']
    
    body = '{{"elementId":{},"userId":{},"write":false}}'.format(element_id, user_id)
    
    response = re.post(url=get_server + endpoints.PERMISSIONS, data=body, headers=POST_HDR, cookies=__stored_cookies)
    if(response.status_code != 201):
        raise DemeterStatusCodeException(response.status_code, response.text)

def generate_secure_password(length=12):
    if length < 12:
        raise ValueError("Password length must be at least 12 characters.")
    
    # Ensure one of each required character type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        '.'
    ]
    
    # Fill the rest of the password length with random choices from all characters
    remaining_length = length - 4
    all_characters = string.ascii_letters + string.digits + '.'
    password += [secrets.choice(all_characters) for _ in range(remaining_length)]
    
    # Shuffle the list to ensure randomness
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password) + '.'

def user_unlock(username: str):
    response = re.post(get_server() + endpoints.DEMETER_USER_UNLOCK + '/' + username, headers=POST_HDR)

    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)

def logout():
    response = re.post(get_server() + endpoints.DEMETER_LOGOUT, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
    
def __get_elements(element: str, element_id: int = None, pandas = False):
    if __verbose: 
        print('Endpoint called: ' + get_server() + endpoints.DEMETER_GET + element + ('' if element_id == None else ('/' + str(element_id))))
    response = re.get(get_server() + endpoints.DEMETER_GET + element + ('' if element_id == None else ('/' + str(element_id))), cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
    else:
        if pandas:
            data = json.loads(response.text)
            return pd.json_normalize(data)
        else:
            return response.text

def search(text:str = None, element_types:list[tp.Element] = None, status:tp.Status = tp.Status.ALL, pandas = False):

    payload = '{"status":"' + status + '"'
    if(text is not None):
        payload = payload + ',"searchText":"' + text + '"'
    if(element_types is None):
        element_types = [e for e in tp.Element.__dict__.values() if isinstance(e, str) and e != 'demeterapitypes']
    payload = payload + ',"type":' + str(element_types).replace("'", '"')
    payload = payload + '}'
    if __verbose: 
        print('Searching with following payload: ' + payload)

    response = re.post(get_server() + endpoints.DEMETER_SEARCH, headers=POST_HDR, data=payload, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
    else:
        if pandas:
            data = json.loads(response.text)
            return pd.json_normalize(data)
        else:
            return response.text

def get_criteria(criteria_name:str, element_id:int):
    counters_df = get_counters(element_id=element_id, pandas=True)
    if not counters_df.empty:
        row = counters_df.iloc[0]
        for criteria in row['criteria']:
            criteria = json.loads(json.dumps(criteria))
            if criteria['name'] == criteria_name:
                return criteria['value']
    return None

def get_criteria_value_list_from_dataframe(criteria_name:str, dataframe:pd.DataFrame):
    values = set()
    for criteria_list in dataframe['criteria']:
        print(criteria_list)
        for criteria in criteria_list:
            if criteria['name'] == criteria_name:
                values.add(criteria['value'])
    return values
    
def get_rtus(element_id:int = None, pandas = False):
    return __get_elements('rtus', element_id, pandas)
        
def get_counters(element_id:int = None, pandas = False):
    return __get_elements('counters', element_id, pandas)
        
def get_analog_inputs(element_id:int = None, pandas = False):
    return __get_elements('analogInputs', element_id, pandas)

def get_digital_inputs(element_id:int = None, pandas = False):
    return __get_elements('digitalInputs', element_id, pandas)
        
def get_iris_nb(element_id:int = None, pandas = False):
    return __get_elements('iris/nbiot', element_id, pandas)
        
def get_iris_lw(element_id:int = None, pandas = False):
    return __get_elements('iris/lorawan', element_id, pandas)
        
def get_iris_sigfox(element_id:int = None, pandas = False):
    return __get_elements('iris/sigfox', element_id, pandas)

def get_iris_gprs(element_id:int = None, pandas = False):
    return __get_elements('iris/gprs', element_id, pandas)

def get_installations(element_id:int = None, pandas = False):
    return __get_elements('installations', element_id, pandas)

def get_rtus_installation_dict(pandas = False):
    installations = __get_elements('installations', pandas=pandas)
    rtus = __get_elements('rtus', pandas=pandas)
    match_installations = pd.merge(installations, rtus, on='installationId', how='inner', validate='m:m')
    timezones = {}
    for index, match in match_installations.iterrows():
        timezones[match['rtuId']] = match['timeZone']
    return timezones

def get_centinel(element_id:int = None, pandas = False):
    return __get_elements('centinel', element_id, pandas)

def get_centaurus(element_id:int = None, pandas = False):
    return __get_elements('centaurus', element_id, pandas)
    
def global_update(rtu_id: int, timestamp: datetime.datetime, liters:int, position:int = 0, expansion:int = 0):
    
    payload = (
    '{"rtuId":"' + str(rtu_id) +
    '","timestamp":"' + time.strftime_demeter(timestamp) +
    '","value":' + str(int(liters)) +
    ',"position":' + str(int(position)) +
    ',"expansion":' + str(int(expansion)) +
    '}'
    )
    if __verbose:
        print('Updating global value with following payload: ' + payload)
    response = re.put(get_server() + endpoints.DEMETER_UPDATE_COUNTER_GLOBAL ,data=payload, headers=POST_HDR, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
    
def add_historics(rtu_id: int, historics: list[hist.Hist]):

    hist = '['
    for historic in historics[:-1]:
        hist = hist + '{'
        hist = hist + '"timestamp":"' + time.strftime_demeter(historic.timestamp) + '",'
        hist = hist + '"subtype":' + str(historic.type.subtype) + ','
        hist = hist + '"subcode":' + str(historic.type.subcode) + ','
        hist = hist + '"value":' + str(historic.value) + ','
        hist = hist + '"position":' + str(historic.position) + ','
        hist = hist + '"expansion":' + str(historic.expansion) + '},'
    historic = historics[-1]
    hist = hist + '{'
    hist = hist + '"timestamp":"' + time.strftime_demeter(historic.timestamp) + '",'
    hist = hist + '"subtype":' + str(historic.type.subtype) + ','
    hist = hist + '"subcode":' + str(historic.type.subcode) + ','
    hist = hist + '"value":' + str(historic.value) + ','
    hist = hist + '"position":' + str(historic.position) + ','
    hist = hist + '"expansion":' + str(historic.expansion) + '}'
    hist = hist + ']'
    
    payload = '{{"rtuId":{}, "historicDataEntities":{}}}'.format(rtu_id, hist)
    if __verbose:
        print('Adding following historical: ' + payload)
    response = re.post(get_server() + endpoints.DEMETER_HISTORICS ,data=payload, headers=POST_HDR, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)

def get_historics(start_date: datetime.datetime, end_date: datetime.datetime, element_ids: list[int], subtype: int, subcode:list[int] = [], pandas=False):
    start_date = time.strftime_demeter(start_date)
    end_date = time.strftime_demeter(end_date)
    payload = '{{"from":"{}", "until":"{}", "subcode":{}, "subtype":{}, "elementIds":{}}}'.format(start_date, end_date, subcode, subtype, element_ids)
    
    response = re.post(get_server() + endpoints.DEMETER_HISTORY_DATA, headers=POST_HDR, data=payload, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
    else:
        if pandas:
            data = json.loads(response.text)
            return pd.json_normalize(data)
        else:
            return response.text

def get_minute_consumption(start_date: datetime.datetime, end_date: datetime.datetime, element_ids: list[int], period_value: int, min_interval: bool = True, pandas=False):
    start_date = time.strftime_demeter(start_date)
    end_date = time.strftime_demeter(end_date)
    if min_interval:
        min_interval = "true"
    else:
        min_interval = "false"
    payload = '{{"from":"{}", "until":"{}", "minInterval":{}, "elementIds":{}, "periodValue":{}}}'.format(start_date, end_date, min_interval, element_ids, period_value)

    response = re.post(get_server() + endpoints.DEMETER_CONSUMPTION, headers=POST_HDR, data=payload, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
    else:
        if pandas:
            data = json.loads(response.text)
            unfolded = pd.DataFrame(columns=['code', 'timestamp'])
            df = pd.json_normalize(data)
            for ix, row in df.iterrows():
                unfolded_row = row['values']
                unfolded_list = []
                for x in unfolded_row:
                    x['code'] = row['series'][0]
                    x['values'] = x['values'][0]
                    unfolded_list.append(x)
                    x['timestamp'] = time.strptime_demeter(x['timestamp'])
                unfolded = pd.concat([unfolded, pd.json_normalize(unfolded_list)])
            return unfolded
        else:
            return response.text

def update_analog_input_value(rtu_id:int, position:int, expansion:int, value:int, timestamp:datetime.datetime):
    timestamp = time.strftime_demeter(timestamp)
    payload = '{{"rtuId":{}, "position":{}, "expansion":{}, "value":{}, "timestamp":"{}"}}'.format(rtu_id, position, expansion, value, timestamp)
    if __verbose:
        print('Updating analogical input value with payload: ' + payload)
    response = re.put(get_server() + endpoints.DEMETER_ANALOG_UPDATE ,data=payload, headers=POST_HDR, cookies=__stored_cookies)
    if response.status_code != 200:
        raise DemeterStatusCodeException(response.status_code, response.text)
      
def delete_element(elementid: int, type = tp.Element, confirmation = True):
    if confirmation:
        element = __get_elements(element=type, element_id=elementid, pandas=True)
        print('{} será eliminado de {}.'.format(element['code'].values.tolist()[0], get_server()))
        res = input('Desea continuar (y|n)? ')
        if res.capitalize() == 'Y': 
            print('Borrando')
            response = re.delete(get_server() + type + '/' + str(elementid), cookies=__stored_cookies)
            if response.status_code != 200:
                raise DemeterStatusCodeException(response.status_code, response.text)
        else:
            print('Cancelado')
    else:
        response = re.delete(get_server() + type + '/' + str(elementid), cookies=__stored_cookies)
        if response.status_code != 200:
            raise DemeterStatusCodeException(response.status_code, response.text)