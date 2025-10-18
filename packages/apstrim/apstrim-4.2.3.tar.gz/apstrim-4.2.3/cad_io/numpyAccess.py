__version__="02 2020-08-25"# added get()

import numpy as np
def ndarray(data, shape=None, dtype=float):
    """Extract numpy array from the IORequest.get() data"""
    if isinstance(data,dict):
        try:
            bbuffer = bytes(data['value'])
            shape = data['shape']
            dtype = data['dtype']
        except: pass
    else:
        bbuffer = bytes(data)
    nparray = np.frombuffer(bbuffer).astype(dtype)
    return nparray.reshape(shape)

def get(adoName, parName):
    """Get a numpy parameter from ADO"""
    from cad_io.adoaccess import IORequest
    adoAccess = IORequest()
    r = adoAccess.get((adoName,parName),(adoName,parName,'shape')\
    , (adoName,parName,'dtype'))
    #print(f'r:{r}')
    firstDictOfProperties = next(iter(r.values()))
    #print(f'first:{firstDictOfProperties}')
    if 'error' in firstDictOfProperties:
        msg = f'ERROR getting {adoName, parName}:{firstDictOfProperties}'
        raise NameError(msg)
    ndarr = ndarray(firstDictOfProperties)
    #print(f'ndarray:\n{ndarr}')
    return ndarr
