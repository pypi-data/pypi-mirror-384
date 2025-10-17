from enum import Enum

class ErrorCode(Enum):
    Success                           = 0
    InvalidParameter                  = 1
    InvalidSettings                   = 2
    Failed                            = 3
    AnalysisUnavailableForProgramMode = 4
    NotYetImplemented                 = 5
    NoSolverLicenseAvailable          = 6
    ToolAlreadyOpen                   = 7
    SequentialOnly                    = 8
    NonSequentialOnly                 = 9
    SingleNSCRayTraceSupported        = 10
    HPCNotAvailable                   = 11
    FeatureNotSupported               = 12
    NotAvailableInLegacy              = 13
    Unknown                           = -1   # fallback when we can't decode