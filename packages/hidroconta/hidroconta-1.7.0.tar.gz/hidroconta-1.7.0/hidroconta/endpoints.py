DEMETER_LOGIN = 'login'
DEMETER_DAAT = 'login/requestBotToken'
DEMETER_DAAT_REVOKE = 'login/revokeBotToken'
DEMETER_LOGOUT = 'logout'
DEMETER_USER_UNLOCK = 'login/unlock'
DEMETER_GET = ''
DEMETER_UPDATE_COUNTER_GLOBAL = 'counters/global/update'
DEMETER_HISTORICS = 'historics'
DEMETER_HISTORY_DATA = 'history/data'
DEMETER_ANALOG_UPDATE = 'analogInputs/value/update'
DEMETER_SEARCH = 'search'
DEMETER_CONSUMPTION = 'history/consumption/minute/volume'
DEMETER_IRIS_LORAWAN = 'iris/lorawan'
DEMETER_IRIS_NB = 'iris/nbiot'
USERS = 'users'
PERMISSIONS = 'permissions'

class Server(enumerate):
    MAIN = 'https://demeter2.hidroconta.com/Demeter2/v2/'
    GESTAGUA = 'https://demeter-gestagua.hidroconta.com/Demeter2/v2/'
    TUDELA = 'https://demeter-tudela-de-duero.hidroconta.com/Demeter2/v2/'
    AIC = 'https://demeter-aic.hidroconta.com/Demeter2/v2/'
    UTEBO = 'https://demeter-utebo.hidroconta.com/Demeter2/v2/'

__server = Server.MAIN

def set_server(server: Server):
    global __server
    __server = server

def get_server():
    return __server