# Integrations-PythonAPI
Python API to facilitate access to Demeter REST interface endpoints.
https://pypi.org/project/hidroconta/

Current version: 1.6.1 (02/07/2025)

Added:
```
# 1.6.0:
# Added historical type FlowHist
# Added historical type CustomHist to add a custom subtype and subcode

# 1.6.1
# Fixed FlowHist, named FlowlHist in 1.6.0

# 1.7.0
# Added IrisCounterGlobalHist to types module
```

The API allows the management of large amounts of data using the Pandas library, provided that the following directive is used in method calls:
```
# Pandas = True returns a pandas dataframe instead a json
```

The way to use the API is the following:

- Import the desired modules:
```
import hidroconta.api as demeter
import hidroconta.types as hidrotypes
import pandas as pd
import datetime
import hidroconta.endpoints as hidroendpoints
```
- Select the server with which you want to communicate (you can modify it at any time):
```
# Set server
demeter.set_server(hydroendpoints.Server.MAIN)
```

- Login to this server
```
# Login
demeter.login('USERNAME', 'PASSWORD')
```

Once the previous steps have been followed, you can make any query about the system.
Some of them are:

- Search
```
# Search
df = demeter.search(text='SAT', element_types=[hidrotypes.Element.COUNTER, hidrotypes.Element.ANALOG_INPUT, hidrotypes.Element.RTU], status=hidrotypes.Status.ENABLED, pandas=True)
print(df)
```

- Getting history
```
# Get historics
df = demeter.get_historics(start_date=datetime.datetime.now(), end_date=datetime.datetime.now(), element_ids=[1000], subtype=hidrotypes.AnalogInputHist.subtype, subcode=[hidrotypes.AnalogInputHist.subcode], pandas=True)
print(df)
```

- Getting elements
```
# Get
df = demeter.get_rtus(element_id=17512, pandas=True)
print(df)
```
The API also defines a special exception when the call to the Demeter endpoint does not return the expected result.
The exception is called 'DemeterStatusCodeException' and contains the HTTP error code.
```
# Exception treatment
try:
    df = demeter.get_rtus(element_id=17512, pandas=True).
except demeter.DemeterStatusCodeException as status_code:
    print('Error {}'.format(status_code))
```
- Finally, a logout should be made on the server
```
demeter.logout()
```

