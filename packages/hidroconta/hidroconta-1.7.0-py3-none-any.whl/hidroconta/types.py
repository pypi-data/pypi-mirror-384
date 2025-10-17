import enum
class AnalogInputHist:
    subtype = 4
    subcode = 0

class CounterGlobalHist:
    subtype = 2
    subcode = 2

class IrisCounterGlobalHist:
    subtype = 7
    subcode = 2

class FlowHist:
    subtype = 2
    subcode = 4

class CustomHist:
    def __init__(self, subtype:int, subcode:int):
        self.subtype = subtype
        self.subcode = subcode

class Element(enumerate):
    ANALOG_INPUT = 'analogInputs'
    COUNTER = 'counters'
    RTU = 'rtus'
    IRIS = 'iris'
    IRIS_NBIOT = 'iris/nbiot'
    IRIS_SIGFOX = 'iris/sigfox'
    IRIS_LORAWAN = 'iris/lorawan'
    IRIS_3COM = 'iris/3com'
    HYDRANT = 'hydrants'
    VALVE = 'valves'
    DIGITAL_INPUT = 'digitalInputs'
    DIGITAL_OUTPUT = 'digitalOutputs'
    CENTINEL = 'centinels'
    WMBUS_COUNTER = 'wmbusCounters'
    CENTAURUS = 'centaurus'
    CENTAURUS_NBIOT = 'centaurus/nbiot'
    CENTAURUS_3COM = 'centaurus/3com'

class Status(enumerate):
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    ALL = 'all'

class Role(enum.Enum):
    BASIC = 'BASIC',
    INSTALLER = 'INSTALLER',
    MANUFACTURING = 'MANUFACTURING',
    ADMIN = 'ADMIN',
    ADVANCED = 'ADVANCED',
    HIDROCONTA = 'HIDROCONTA'

class Access(enumerate):
    COMMON = 'COMMON',
    ALL_READ = 'ALL_READ',
    ALL_WRITE = 'ALL_WRITE'
