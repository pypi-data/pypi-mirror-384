class ZemaxError(Exception): pass
class ZemaxNotFound(ZemaxError): pass
class ZemaxInitError(ZemaxError): pass
class ZemaxConnectError(ZemaxError): pass
class ZemaxFileMissing(ZemaxError): pass
class ZemaxInitializationError(ZemaxError): pass
class ZemaxLicenseError(ZemaxError): pass
class ZemaxSystemError(ZemaxError): pass