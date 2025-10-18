from enum import Enum
from typing import Any

class Datum(Enum):
    ADIND = 1
    ARC50 = 2
    ARC60 = 3
    AGD66 = 4
    AGD84 = 5
    BUKIT = 6
    ASTRO = 7
    CHATM = 8
    CARTH = 9
    CAPE = 10
    DJAKA = 11
    EGYPT = 12
    ED50 = 13
    ED79 = 14
    GUNSG = 15
    GEO49 = 16
    GRB36 = 17
    GUAM = 18
    HAWAII = 19
    KAUAI = 20
    MAUI = 21
    OAHU = 22
    HERAT = 23
    HJORS = 24
    HONGK = 25
    HUTZU = 26
    INDIA = 27
    IRE65 = 28
    KERTA = 29
    KANDA = 30
    LIBER = 31
    LUZON = 32
    MINDA = 33
    MERCH = 34
    NAHR = 35
    NAD83 = 36
    CANADA = 37
    ALASKA = 38
    NAD27 = 39
    CARIBB = 40
    MEXICO = 41
    CAMER = 42
    MINNA = 43
    OMAN = 44
    PUERTO = 45
    QORNO = 46
    ROME = 47
    CHUA = 48
    SAM56 = 49
    SAM69 = 50
    CAMPO = 51
    SACOR = 52
    YACAR = 53
    TANAN = 54
    TIMBA = 55
    TOKYO = 56
    TRIST = 57
    VITI = 58
    WAK60 = 59
    WGS72 = 60
    WGS84 = 61
    ZANDE = 62
    USER = 63
    CSRS = 64
    ADIM = 65
    ARSM = 66
    ENW = 67
    HTN = 68
    INDB = 69
    INDI = 70
    IRL = 71
    LUZA = 72
    LUZB = 73
    NAHC = 74
    NASP = 75
    OGBM = 76
    OHAA = 77
    OHAB = 78
    OHAC = 79
    OHAD = 80
    OHIA = 81
    OHIB = 82
    OHIC = 83
    OHID = 84
    TIL = 85
    TOYM = 86
    NAD83OMNI = 87
    PE90 = 88

class FileSystemStatus(Enum):
    UNMOUNTED = 1
    MOUNTED = 2
    BUSY = 3
    ERROR = 4
    UNMOUNTING = 5
    MOUNTING = 6

class UserAccuracyLevelControl(Enum):
    DISABLE = 0
    ENABLE = 1
    CLEAR = 2

class AntennaPower(Enum):
    OFF = 0
    ON = 1
    ON3V3 = 2
    PRIMARY_ON_SECONDARY_OFF = 3
    PRIMARY_OFF_SECONDARY_ON = 4

class CanBitRate(Enum):
    _10K = 0
    _20K = 1
    _50K = 2
    _100K = 3
    _125K = 4
    _250K = 5
    _500K = 6
    _1M = 7
    CAN_BITRATE_INVALID = 8

class RTKCommand(Enum):
    USE_DEFAULTS = 0
    RESET = 1
    ENABLE = 2
    DISABLE = 3

class Feature(Enum):
    MAX_MSR_RATE = 0
    MAX_POS_RATE = 1
    MAX_RTK_BASELINE = 2
    MEAS_OUTPUT = 3
    DGPS_TX = 4
    RTK_TX = 5
    RTK_FLOAT = 6
    RTK_FIXED = 7
    RAIM = 8
    LOW_END_POSITIONING = 9
    ALIGN_HEADING = 10
    ALIGN_RELATIVE_POS = 11
    API = 12
    STROBES = 13
    OMNISTAR = 14
    NTRIP = 15
    HIGH_SPEED = 16
    DEBUG = 17
    MANUFACTURING = 18
    PPP = 19
    SCINTILLATION = 20
    VERIPOS = 21
    INS = 22
    IMU = 23
    OPEN_SERVICE_PPP = 24
    VERIPOS_RTCM_OUTPUT = 25
    INTERFERENCE_MITIGATION = 26
    RTKASSIST = 27
    ANTENNA = 28
    GENERIC_IMU = 29
    INS_PLUS_PROFILES = 30
    HEAVE = 31
    RELATIVE_INS = 32
    PRODUCT_FEATURE = 33
    SPRINKLER = 34
    TILT = 35
    MODEL_INVALID = 999

class EthernetPowerMode(Enum):
    AUTO = 1
    POWERDOWN = 2
    NORMAL = 3

class Frequency(Enum):
    GPSL1 = 0
    GPSL2 = 1
    GLONASSL1 = 2
    GLONASSL2 = 3
    GPSL1OFF = 4
    GPSL5 = 5
    LBAND = 6
    GALILEOE1 = 7
    GALILEOE5A = 8
    GALILEOE5B = 9
    GALILEOALTBOC = 10
    BEIDOUB1 = 11
    BEIDOUB2 = 12
    QZSSL1 = 13
    QZSSL2 = 14
    QZSSL5 = 15
    QZSSL6 = 16
    GALILEOE6 = 17
    BEIDOUB3 = 18
    GLONASSL3 = 19
    NAVICL5 = 20
    BEIDOUB1C = 21
    BEIDOUB2A = 22
    BEIDOUB2B = 23
    NONE = 24

class ProgFilterID(Enum):
    PF0 = 0
    PF1 = 1
    PF2 = 2

class Security(Enum):
    REMOVE = 0
    ADD = 1
    VERIFY = 2
    ADD_NO_RESET = 3
    ADD_DOWNLOAD = 4
    REMOVE_RECEIVER = 5
    COPY_SIGN_AUTH = 6
    ERASE_TABLE = 7
    CLEAN_TABLE = 8

class EthernetInterfaceConfig(Enum):
    NOTCONNECT = 1
    _10_FULL = 2
    _10_HALF = 3
    _100_FULL = 4
    _100_HALF = 5
    HARDWARE_FAILURE = 6

class PPPSeedStoreStatus(Enum):
    UNAVAILABLE = 0
    AVAILABLE = 1

class DatumAnchor(Enum):
    UNKNOWN = 0
    EARTH_FIXED = 1
    PLATE_FIXED = 2

class IMUPort(Enum):
    NO_PORT = 0
    COM1 = 1
    COM2 = 2
    COM3 = 3
    UNKNOWN = 5
    ARINC = 6
    SPI = 7
    I2C = 8
    CAN1 = 9
    CAN2 = 10
    COM4 = 19
    COM5 = 31
    COM6 = 32

class PPPConvergedCriteria(Enum):
    TOTAL_STDDEV = 1
    HORIZONTAL_STDDEV = 2
    TOTAL_STDDEV_RESTRICTIVE = 257
    HORIZONTAL_STDDEV_RESTRICTIVE = 258

class RxEventWord(Enum):
    ERROR = 0
    STATUS = 1
    AUX1 = 2
    AUX2 = 3
    AUX3 = 4
    AUX4 = 5
    RXEVENT_MAX = 6

class FileAutoTransferMode(Enum):
    OFF = 1
    COPY = 2
    MOVE = 3

class ComSignal(Enum):
    RTS = 0
    DTR = 1
    TX = 2

class TimingSystem(Enum):
    GPS = 0
    GLONASS = 1
    GALILEO = 2
    BEIDOU = 3
    NAVIC = 4
    EXTERNAL = 98
    AUTO = 99
    NONE = 100

class SatelError(Enum):
    NONE = 0
    COMMAND_FAILED = 1
    TIMEOUT = 2

class VeriposOperatingMode(Enum):
    UNASSIGNED = 0
    TERM = 1
    PAYG = 2
    MODEL = 5
    NCC_CONTROLLED = 7
    NO_DISABLE = 8
    BUBBLE = 100
    SUBSCRIPTION_ERROR = 103
    INCOMPATIBLE_SUBSCRIPTION = 104

class PDPFilterCommand(Enum):
    DISABLE = 0
    ENABLE = 1
    RESET = 2

class PDPFilterMode(Enum):
    NORMAL = 0
    RELATIVE = 1
    GL1DE = 2
    GLIDE = 3

class CorrectionsTimeOut(Enum):
    AUTO = 1
    SET = 2

class WifiSecurityType(Enum):
    OPEN = 1
    WPA = 2
    WPA2 = 3
    WEP = 4
    WPA_ENTERPRISE = 5
    WPA2_ENTERPRISE = 6

class SoftLoadStatus(Enum):
    NOT_STARTED = 1
    READY_FOR_SETUP = 2
    READY_FOR_DATA = 3
    DATA_VERIFIED = 4
    WRITING_FLASH = 5
    WROTE_FLASH = 6
    WROTE_AUTHCODE = 7
    COMPLETE = 8
    VERIFYING_DATA = 9
    COPIED_SIGNATURE_AUTH = 10
    WROTE_TRANSACTION_TABLE = 11
    MULTIPLE_IMAGES_IN_FLASH = 12
    PROCESSING_FILE = 13
    ERROR = 16
    RESET_ERROR = 17
    BAD_SRECORD = 18
    BAD_PLATFORM = 19
    BAD_MODULE = 20
    BAD_AUTHCODE = 21
    NOT_READY_FOR_SETUP = 22
    NO_MODULE = 23
    NO_PLATFORM = 24
    NOT_READY_FOR_DATA = 25
    MODULE_MISMATCH = 26
    OUT_OF_MEMORY = 27
    DATA_OVERLAP = 28
    BAD_IMAGE_CRC = 29
    IMAGE_OVERSIZE = 30
    AUTHCODE_WRITE_ERROR = 31
    BAD_FLASH_ERASE = 32
    BAD_FLASH_WRITE = 33
    TIMEOUT = 34
    INCOMPATIBLE_FLASH = 35

class PPPSeedApplicationStatus(Enum):
    UNAVAILABLE = 0
    AVAILABLE = 1
    PENDING = 2
    APPLIED = 3
    PENDING_MOTION_ALLOWED = 4
    REJECTED_MOTION_DETECTED = 10
    REJECTED_BAD_POSITION = 11
    DISCARDED_RAPID_CONVERGENCE = 20

class LBandAssign(Enum):
    IDLE = 0
    AUTO = 1
    MANUAL = 2
    CW = 3

class PosAveCommand(Enum):
    OFF = 0
    ON = 1
    FIX = 2

class SystemType(Enum):
    GPS = 0
    GLONASS = 1
    SBAS = 2
    GALILEO = 5
    BEIDOU = 6
    QZSS = 7
    LBAND = 8
    NAVIC = 9
    UNKNOWN = 30
    NONE = 31
    ALL = 32

class WifiBand(Enum):
    _2P4GHZ = 1
    _5GHZ = 2

class Satel9ModemMode(Enum):
    P2MP_MASTER = 2
    P2MP_SLAVE = 3
    P2MP_RX_SLAVE = 8

class INSStatus(Enum):
    INS_INACTIVE = 0
    INS_ALIGNING = 1
    INS_HIGH_VARIANCE = 2
    INS_SOLUTION_GOOD = 3
    INS_TEST_ALIGNING = 4
    INS_TEST_SOLUTION_GOOD = 5
    INS_SOLUTION_FREE = 6
    INS_ALIGNMENT_COMPLETE = 7
    DETERMINING_ORIENTATION = 8
    WAITING_INITIALPOS = 9
    WAITING_AZIMUTH = 10
    INITIALIZING_BIASES = 11
    MOTION_DETECT = 12
    TIMEOUT = 13
    WAITING_ALIGNMENTORIENTATION = 14

class SoftLoadSetup(Enum):
    PLATFORM = 1
    VERSION = 2
    DATATYPE = 3
    AUTHCODE = 4
    EXTRADATA = 5

class FFTSize(Enum):
    _1K = 0
    _2K = 1
    _4K = 2
    _8K = 3
    _16K = 4
    _32K = 5
    _64K = 6

class INSCalibrateTrigger(Enum):
    STOP = 0
    NEW = 1
    ADD = 2
    RESET = 3

class ManageUserDefinedAntenna(Enum):
    ADD = 0
    REMOVE = 1

class AntennaRaydomType(Enum):
    NONE = 0
    SPKE = 1
    SNOW = 2
    SCIS = 3
    SCIT = 4
    OLGA = 5
    PFAN = 6
    JVDM = 7
    LEIT = 8
    LEIC = 9
    LEIS = 10
    MMAC = 11
    NOVS = 12
    TPSH = 13
    CONE = 14
    TPSD = 15
    TCWD = 16
    UNAV = 17
    TZGD = 18
    CHCD = 19
    JAVC = 20
    LEIM = 21
    NOVC = 22
    ARFC = 23
    HXCS = 24
    JVGR = 25
    STHC = 26
    DUTD = 27
    JAVD = 28
    JVSD = 29

class ComSignalCtrl(Enum):
    DEFAULT = 0
    FORCEHIGH = 1
    FORCELOW = 2
    TOGGLE = 3
    TOGGLEPPS = 4
    PULSEPPSLOW = 5
    PULSEPPSHIGH = 6

class EthernetDuplex(Enum):
    AUTO = 1
    HALF = 2
    FULL = 3

class RefStation(Enum):
    UNKNOWN = 0
    RTCM = 1
    RTCA = 2
    CMR = 3
    RTCMV3 = 4
    NOVATELX = 5
    RTCA_ALIGN = 6
    NOVATELX_ALIGN = 7

class PPPDynamics(Enum):
    AUTO = 0
    STATIC = 1
    DYNAMIC = 2

class EpochOption(Enum):
    SERVICE_EPOCH = 0
    FIXED_EPOCH = 1
    CURRENT_EPOCH = 2

class WifiEncryptionType(Enum):
    OPEN = 1
    TKIP = 2
    CCMP = 3

class SourceStatus(Enum):
    NONE = 0
    FROM_NVM = 1
    CALIBRATING = 2
    CALIBRATED = 3
    FROM_COMMAND = 4
    RESET = 5
    FROM_DUAL_ANT = 6
    INS_CONVERGING = 7
    INSUFFICIENT_SPEED = 8
    HIGH_ROTATION = 9

class EmulatedRadarUpdateRate(Enum):
    _1HZ = 1
    _2HZ = 2
    _5HZ = 3
    _10HZ = 4
    _20HZ = 5

class HeadingUpdateStatus(Enum):
    INACTIVE = 0
    ACTIVE = 1
    USED = 2
    HIGH_STD_DEV = 3
    HIGH_ROTATION = 4
    BAD_MISC = 5

class RTKPortMode(Enum):
    RTK = 0
    ALIGN = 1

class RTKNetwork(Enum):
    DISABLE = 0
    VRS1 = 1
    IMAX1 = 2
    FKP1 = 3
    FKP2 = 4
    VRS = 5
    IMAX = 6
    FKP = 7
    MAX = 8
    UNKNOWN = 9
    AUTO = 10
    DISABLED = 11

class LogTrigger(Enum):
    ONNEW = 0
    ONCHANGED = 1
    ONTIME = 2
    ONNEXT = 3
    ONCE = 4
    ONMARK = 5

class AssignState(Enum):
    IDLE = 0
    ACTIVE = 1
    AUTO = 2
    NODATA = 4
    BIT = 5

class VelType(Enum):
    NONE = 1
    DOPPLER = 2
    DELTA_PHASE = 3
    INS = 4
    PROPAGATED = 5

class SpoofCalibrationCmdOption(Enum):
    ALL = 0
    REMAINING = 1

class Satel4BaseType(Enum):
    PACCREST = 0
    M3TR1 = 1
    M3TR3 = 2
    TRIMBLE = 4
    NONE = 9

class ITBFrontEndMode(Enum):
    CIC3 = 0
    HDR = 1

class RFInputGainMode(Enum):
    MANUAL = 1
    AUTO = 2

class CodePair(Enum):
    GPS_C1P1 = 0
    GPS_C2P2 = 1
    GLONASS_C1P1 = 2

class RTKElevMaskType(Enum):
    AUTO = 0
    USER = 1

class Satel4RadioBehaviour(Enum):
    RX = 0
    TX = 1

class RTCMVersion(Enum):
    V23 = 0
    V22 = 1
    V21 = 2
    UNKNOWN = 3

class Satel4Protocol(Enum):
    SATELLINE_3AS = 0
    PACCREST_4FSK = 1
    PACCREST_GMSK = 2
    TRIMTALK450S_P = 3
    TRIMTALK450S_T = 4
    PACCREST_FST = 5

class DatumTransformationStatus(Enum):
    GOOD = 0
    ECEF_EQUIVALENCY = 1
    SERVICE_DETAILS_UNKNOWN = 2
    REQUESTED_TRANSFORMATION_UNAVAILABLE = 3

class SBASSystem(Enum):
    NONE = 0
    AUTO = 1
    ANY = 2
    WAAS = 3
    EGNOS = 4
    MSAS = 5
    GAGAN = 6
    QZSS = 7
    DEFAULT = 99

class I2CStatus(Enum):
    OK = 0
    IN_PROGRESS = 1
    DATA_TRUNCATION = 2
    BUS_BUSY = 3
    NO_DEVICE_REPLY = 4
    BUS_ERROR = 5
    TIMEOUT = 6
    UNKNOWN_FAILURE = 7
    SHUTDOWN = 8

class TiltZeroAction(Enum):
    ZERO = 0
    SAVE = 1
    RESTORE = 2
    NEW = 3
    ADD = 4

class INSSeedInjection(Enum):
    VALIDATE = 0
    INJECT = 1

class Adjust1PPSMode(Enum):
    OFF = 0
    MANUAL = 1
    MARK = 2
    MARKWITHTIME = 3
    TIME = 4

class Polarity(Enum):
    NEGATIVE = 0
    POSITIVE = 1

class InOut(Enum):
    IN = 1
    OUT = 2
    IN2 = 3

class RTKDynamics(Enum):
    AUTO = 0
    STATIC = 1
    DYNAMIC = 2

class ChanConfigSignal(Enum):
    GPSL1 = 0
    GPSL1L2 = 1
    NONE = 2
    ALL = 3
    SBASL1 = 4
    GPSL5 = 5
    GPSL1L2C = 6
    GPSL1L2AUTO = 7
    GLOL1L2 = 8
    LBAND = 9
    GLOL1 = 10
    GALE1 = 11
    GALE5A = 12
    GALE5B = 13
    GALALTBOC = 14
    BEIDOUB1 = 15
    GPSL1L2PL2C = 16
    GPSL1L5 = 17
    SBASL1L5 = 18
    GPSL1L2PL2CL5 = 19
    GPSL1L2PL5 = 20
    GALE1E5AE5B = 21
    GALE1E5AE5BALTBOC = 22
    GALE1E5A = 23
    GLOL1L2C = 24
    GLOL1L2PL2C = 25
    QZSSL1CA = 26
    QZSSL1CAL2C = 27
    QZSSL1CAL2CL5 = 28
    QZSSL1CAL5 = 29
    BEIDOUB1B2 = 30
    GALE1E5B = 31
    BEIDOUB1B3 = 32
    BEIDOUB3 = 33
    BEIDOUB1B2B3 = 34
    GALE1E5AE5BALTBOCE6 = 35
    GPSL1L2PL2CL5L1C = 36
    QZSSL1CAL2CL5L1C = 37
    QZSSL1CAL2CL5L1CL6 = 38
    GLOL1L3 = 39
    GLOL3 = 40
    GLOL1L2PL2CL3 = 41
    GPSL1L2PL2CL1C = 42
    QZSSL1CAL2CL1C = 43
    NAVICL5 = 44
    BEIDOUB1C = 45
    BEIDOUB1B1C = 46
    BEIDOUB1B1CB2B3 = 47
    BEIDOUB1B1CB2 = 48
    BEIDOUB1B2IB2B = 49
    BEIDOUB1B2B = 50
    BEIDOUB1B1CB2IB2B = 51
    BEIDOUB1B1CB2IB2BB3 = 52
    BEIDOUB1B1CB2B = 53
    BEIDOUB1B2IB2BB3 = 54
    BEIDOUB1B2B2B = 55
    BEIDOUB1B1CB2B2B = 56
    BEIDOUB1B1CB2B2BB3 = 57
    BEIDOUB1B2B2BB3 = 58
    GPS = 99
    SBAS = 100
    GLONASS = 101
    GALILEO = 102
    BEIDOU = 103

class FileOperation(Enum):
    OPEN = 1
    CLOSE = 2

class Mark(Enum):
    MARK1 = 0
    MARK2 = 1
    MARK3 = 2
    MARK4 = 3
    MARK5 = 4
    MARK6 = 5
    MARK7 = 6
    MARK8 = 7
    MARK9 = 8
    NONE = 9

class BDSDataSource(Enum):
    B1D1 = 0
    B1D2 = 1
    B2D1 = 65536
    B2D2 = 65537
    B3D1 = 131072
    B3D2 = 131073

class GPSTimeStatus(Enum):
    UNKNOWN = 20
    APPROXIMATEADJUSTING = 40
    APPROXIMATE = 60
    COARSEADJUSTING = 80
    COARSE = 100
    COARSESTEERING = 120
    FREEWHEELING = 130
    FINEADJUSTING = 140
    FINE = 160
    FINEBACKUPSTEERING = 170
    FINESTEERING = 180
    SATTIME = 200
    EXTERN = 220
    EXACT = 240

class BluetoothControl(Enum):
    DISABLE = 0
    ENABLE = 1
    LOAD = 2

class WifiMode(Enum):
    OFF = 0
    AP = 1
    CLIENT = 2
    ON = 3
    CONCURRENT = 4
    NOT_SET = 99

class WheelStatus(Enum):
    INACTIVE = 0
    ACTIVE = 1
    USED = 2
    UNSYNCED = 3
    BAD_MISC = 4
    HIGH_ROTATION = 5
    DISABLED = 6
    ZUPT = 7
    HW_FAILURE = 8

class Sensor(Enum):
    SENSOR1 = 0
    SENSOR2 = 1
    SENSOR3 = 2
    SENSOR_NONE = 3

class ObservationStatus(Enum):
    GOOD = 0
    BADHEALTH = 1
    OLDEPHEMERIS = 2
    ELEVATIONERROR = 6
    MISCLOSURE = 7
    NODIFFCORR = 8
    NOEPHEMERIS = 9
    INVALIDIODE = 10
    LOCKEDOUT = 11
    LOWPOWER = 12
    OBSL2 = 13
    UNKNOWN = 15
    NOIONOCORR = 16
    NOTUSED = 17
    OBSL1 = 18
    OBSE1 = 19
    OBSL5 = 20
    OBSE5 = 21
    OBSB2 = 22
    OBSB1 = 23
    OBSB3 = 24
    NOSIGNALMATCH = 25
    SUPPLEMENTARY = 26
    OBSE6 = 27
    OBSL6 = 28
    NA = 99
    BAD_INTEGRITY = 100
    LOSSOFLOCK = 101
    NOAMBIGUITY = 102

class PortAddress(Enum):
    NO_PORTS = 0
    COM1_ALL = 1
    COM2_ALL = 2
    COM3_ALL = 3
    USB_ALL = 4
    THISPORT_ALL = 6
    FILE_ALL = 7
    ALL_PORTS = 8
    XCOM1_ALL = 9
    XCOM2_ALL = 10
    USB1_ALL = 13
    USB2_ALL = 14
    USB3_ALL = 15
    AUX_ALL = 16
    XCOM3_ALL = 17
    COM4_ALL = 19
    ETH1_ALL = 20
    IMU_ALL = 21
    ICOM1_ALL = 23
    ICOM2_ALL = 24
    ICOM3_ALL = 25
    NCOM1_ALL = 26
    NCOM2_ALL = 27
    NCOM3_ALL = 28
    ICOM4_ALL = 29
    WCOM1_ALL = 30
    COM1 = 32
    COM1_1 = 33
    COM1_2 = 34
    COM1_3 = 35
    COM1_4 = 36
    COM1_5 = 37
    COM1_6 = 38
    COM1_7 = 39
    COM1_8 = 40
    COM1_9 = 41
    COM1_10 = 42
    COM1_11 = 43
    COM1_12 = 44
    COM1_13 = 45
    COM1_14 = 46
    COM1_15 = 47
    COM1_16 = 48
    COM1_17 = 49
    COM1_18 = 50
    COM1_19 = 51
    COM1_20 = 52
    COM1_21 = 53
    COM1_22 = 54
    COM1_23 = 55
    COM1_24 = 56
    COM1_25 = 57
    COM1_26 = 58
    COM1_27 = 59
    COM1_28 = 60
    COM1_29 = 61
    COM1_30 = 62
    COM1_31 = 63
    COM2 = 64
    COM2_1 = 65
    COM2_2 = 66
    COM2_3 = 67
    COM2_4 = 68
    COM2_5 = 69
    COM2_6 = 70
    COM2_7 = 71
    COM2_8 = 72
    COM2_9 = 73
    COM2_10 = 74
    COM2_11 = 75
    COM2_12 = 76
    COM2_13 = 77
    COM2_14 = 78
    COM2_15 = 79
    COM2_16 = 80
    COM2_17 = 81
    COM2_18 = 82
    COM2_19 = 83
    COM2_20 = 84
    COM2_21 = 85
    COM2_22 = 86
    COM2_23 = 87
    COM2_24 = 88
    COM2_25 = 89
    COM2_26 = 90
    COM2_27 = 91
    COM2_28 = 92
    COM2_29 = 93
    COM2_30 = 94
    COM2_31 = 95
    COM3 = 96
    COM3_1 = 97
    COM3_2 = 98
    COM3_3 = 99
    COM3_4 = 100
    COM3_5 = 101
    COM3_6 = 102
    COM3_7 = 103
    COM3_8 = 104
    COM3_9 = 105
    COM3_10 = 106
    COM3_11 = 107
    COM3_12 = 108
    COM3_13 = 109
    COM3_14 = 110
    COM3_15 = 111
    COM3_16 = 112
    COM3_17 = 113
    COM3_18 = 114
    COM3_19 = 115
    COM3_20 = 116
    COM3_21 = 117
    COM3_22 = 118
    COM3_23 = 119
    COM3_24 = 120
    COM3_25 = 121
    COM3_26 = 122
    COM3_27 = 123
    COM3_28 = 124
    COM3_29 = 125
    COM3_30 = 126
    COM3_31 = 127
    USB = 128
    USB_1 = 129
    USB_2 = 130
    USB_3 = 131
    USB_4 = 132
    USB_5 = 133
    USB_6 = 134
    USB_7 = 135
    USB_8 = 136
    USB_9 = 137
    USB_10 = 138
    USB_11 = 139
    USB_12 = 140
    USB_13 = 141
    USB_14 = 142
    USB_15 = 143
    USB_16 = 144
    USB_17 = 145
    USB_18 = 146
    USB_19 = 147
    USB_20 = 148
    USB_21 = 149
    USB_22 = 150
    USB_23 = 151
    USB_24 = 152
    USB_25 = 153
    USB_26 = 154
    USB_27 = 155
    USB_28 = 156
    USB_29 = 157
    USB_30 = 158
    USB_31 = 159
    SPECIAL = 160
    SPECIAL_1 = 161
    SPECIAL_2 = 162
    SPECIAL_3 = 163
    SPECIAL_4 = 164
    SPECIAL_5 = 165
    SPECIAL_6 = 166
    SPECIAL_7 = 167
    SPECIAL_8 = 168
    SPECIAL_9 = 169
    SPECIAL_10 = 170
    SPECIAL_11 = 171
    SPECIAL_12 = 172
    SPECIAL_13 = 173
    SPECIAL_14 = 174
    SPECIAL_15 = 175
    SPECIAL_16 = 176
    SPECIAL_17 = 177
    SPECIAL_18 = 178
    SPECIAL_19 = 179
    SPECIAL_20 = 180
    SPECIAL_21 = 181
    SPECIAL_22 = 182
    SPECIAL_23 = 183
    SPECIAL_24 = 184
    SPECIAL_25 = 185
    SPECIAL_26 = 186
    SPECIAL_27 = 187
    SPECIAL_28 = 188
    SPECIAL_29 = 189
    SPECIAL_30 = 190
    SPECIAL_31 = 191
    THISPORT = 192
    THISPORT_1 = 193
    THISPORT_2 = 194
    THISPORT_3 = 195
    THISPORT_4 = 196
    THISPORT_5 = 197
    THISPORT_6 = 198
    THISPORT_7 = 199
    THISPORT_8 = 200
    THISPORT_9 = 201
    THISPORT_10 = 202
    THISPORT_11 = 203
    THISPORT_12 = 204
    THISPORT_13 = 205
    THISPORT_14 = 206
    THISPORT_15 = 207
    THISPORT_16 = 208
    THISPORT_17 = 209
    THISPORT_18 = 210
    THISPORT_19 = 211
    THISPORT_20 = 212
    THISPORT_21 = 213
    THISPORT_22 = 214
    THISPORT_23 = 215
    THISPORT_24 = 216
    THISPORT_25 = 217
    THISPORT_26 = 218
    THISPORT_27 = 219
    THISPORT_28 = 220
    THISPORT_29 = 221
    THISPORT_30 = 222
    THISPORT_31 = 223
    FILE = 224
    FILE_1 = 225
    FILE_2 = 226
    FILE_3 = 227
    FILE_4 = 228
    FILE_5 = 229
    FILE_6 = 230
    FILE_7 = 231
    FILE_8 = 232
    FILE_9 = 233
    FILE_10 = 234
    FILE_11 = 235
    FILE_12 = 236
    FILE_13 = 237
    FILE_14 = 238
    FILE_15 = 239
    FILE_16 = 240
    FILE_17 = 241
    FILE_18 = 242
    FILE_19 = 243
    FILE_20 = 244
    FILE_21 = 245
    FILE_22 = 246
    FILE_23 = 247
    FILE_24 = 248
    FILE_25 = 249
    FILE_26 = 250
    FILE_27 = 251
    FILE_28 = 252
    FILE_29 = 253
    FILE_30 = 254
    FILE_31 = 255
    XCOM1 = 416
    XCOM1_1 = 417
    XCOM1_2 = 418
    XCOM1_3 = 419
    XCOM1_4 = 420
    XCOM1_5 = 421
    XCOM1_6 = 422
    XCOM1_7 = 423
    XCOM1_8 = 424
    XCOM1_9 = 425
    XCOM1_10 = 426
    XCOM1_11 = 427
    XCOM1_12 = 428
    XCOM1_13 = 429
    XCOM1_14 = 430
    XCOM1_15 = 431
    XCOM1_16 = 432
    XCOM1_17 = 433
    XCOM1_18 = 434
    XCOM1_19 = 435
    XCOM1_20 = 436
    XCOM1_21 = 437
    XCOM1_22 = 438
    XCOM1_23 = 439
    XCOM1_24 = 440
    XCOM1_25 = 441
    XCOM1_26 = 442
    XCOM1_27 = 443
    XCOM1_28 = 444
    XCOM1_29 = 445
    XCOM1_30 = 446
    XCOM1_31 = 447
    XCOM2 = 672
    XCOM2_1 = 673
    XCOM2_2 = 674
    XCOM2_3 = 675
    XCOM2_4 = 676
    XCOM2_5 = 677
    XCOM2_6 = 678
    XCOM2_7 = 679
    XCOM2_8 = 680
    XCOM2_9 = 681
    XCOM2_10 = 682
    XCOM2_11 = 683
    XCOM2_12 = 684
    XCOM2_13 = 685
    XCOM2_14 = 686
    XCOM2_15 = 687
    XCOM2_16 = 688
    XCOM2_17 = 689
    XCOM2_18 = 690
    XCOM2_19 = 691
    XCOM2_20 = 692
    XCOM2_21 = 693
    XCOM2_22 = 694
    XCOM2_23 = 695
    XCOM2_24 = 696
    XCOM2_25 = 697
    XCOM2_26 = 698
    XCOM2_27 = 699
    XCOM2_28 = 700
    XCOM2_29 = 701
    XCOM2_30 = 702
    XCOM2_31 = 703
    USB1 = 1440
    USB1_1 = 1441
    USB1_2 = 1442
    USB1_3 = 1443
    USB1_4 = 1444
    USB1_5 = 1445
    USB1_6 = 1446
    USB1_7 = 1447
    USB1_8 = 1448
    USB1_9 = 1449
    USB1_10 = 1450
    USB1_11 = 1451
    USB1_12 = 1452
    USB1_13 = 1453
    USB1_14 = 1454
    USB1_15 = 1455
    USB1_16 = 1456
    USB1_17 = 1457
    USB1_18 = 1458
    USB1_19 = 1459
    USB1_20 = 1460
    USB1_21 = 1461
    USB1_22 = 1462
    USB1_23 = 1463
    USB1_24 = 1464
    USB1_25 = 1465
    USB1_26 = 1466
    USB1_27 = 1467
    USB1_28 = 1468
    USB1_29 = 1469
    USB1_30 = 1470
    USB1_31 = 1471
    USB2 = 1696
    USB2_1 = 1697
    USB2_2 = 1698
    USB2_3 = 1699
    USB2_4 = 1700
    USB2_5 = 1701
    USB2_6 = 1702
    USB2_7 = 1703
    USB2_8 = 1704
    USB2_9 = 1705
    USB2_10 = 1706
    USB2_11 = 1707
    USB2_12 = 1708
    USB2_13 = 1709
    USB2_14 = 1710
    USB2_15 = 1711
    USB2_16 = 1712
    USB2_17 = 1713
    USB2_18 = 1714
    USB2_19 = 1715
    USB2_20 = 1716
    USB2_21 = 1717
    USB2_22 = 1718
    USB2_23 = 1719
    USB2_24 = 1720
    USB2_25 = 1721
    USB2_26 = 1722
    USB2_27 = 1723
    USB2_28 = 1724
    USB2_29 = 1725
    USB2_30 = 1726
    USB2_31 = 1727
    USB3 = 1952
    USB3_1 = 1953
    USB3_2 = 1954
    USB3_3 = 1955
    USB3_4 = 1956
    USB3_5 = 1957
    USB3_6 = 1958
    USB3_7 = 1959
    USB3_8 = 1960
    USB3_9 = 1961
    USB3_10 = 1962
    USB3_11 = 1963
    USB3_12 = 1964
    USB3_13 = 1965
    USB3_14 = 1966
    USB3_15 = 1967
    USB3_16 = 1968
    USB3_17 = 1969
    USB3_18 = 1970
    USB3_19 = 1971
    USB3_20 = 1972
    USB3_21 = 1973
    USB3_22 = 1974
    USB3_23 = 1975
    USB3_24 = 1976
    USB3_25 = 1977
    USB3_26 = 1978
    USB3_27 = 1979
    USB3_28 = 1980
    USB3_29 = 1981
    USB3_30 = 1982
    USB3_31 = 1983
    AUX = 2208
    AUX_1 = 2209
    AUX_2 = 2210
    AUX_3 = 2211
    AUX_4 = 2212
    AUX_5 = 2213
    AUX_6 = 2214
    AUX_7 = 2215
    AUX_8 = 2216
    AUX_9 = 2217
    AUX_10 = 2218
    AUX_11 = 2219
    AUX_12 = 2220
    AUX_13 = 2221
    AUX_14 = 2222
    AUX_15 = 2223
    AUX_16 = 2224
    AUX_17 = 2225
    AUX_18 = 2226
    AUX_19 = 2227
    AUX_20 = 2228
    AUX_21 = 2229
    AUX_22 = 2230
    AUX_23 = 2231
    AUX_24 = 2232
    AUX_25 = 2233
    AUX_26 = 2234
    AUX_27 = 2235
    AUX_28 = 2236
    AUX_29 = 2237
    AUX_30 = 2238
    AUX_31 = 2239
    XCOM3 = 2464
    XCOM3_1 = 2465
    XCOM3_2 = 2466
    XCOM3_3 = 2467
    XCOM3_4 = 2468
    XCOM3_5 = 2469
    XCOM3_6 = 2470
    XCOM3_7 = 2471
    XCOM3_8 = 2472
    XCOM3_9 = 2473
    XCOM3_10 = 2474
    XCOM3_11 = 2475
    XCOM3_12 = 2476
    XCOM3_13 = 2477
    XCOM3_14 = 2478
    XCOM3_15 = 2479
    XCOM3_16 = 2480
    XCOM3_17 = 2481
    XCOM3_18 = 2482
    XCOM3_19 = 2483
    XCOM3_20 = 2484
    XCOM3_21 = 2485
    XCOM3_22 = 2486
    XCOM3_23 = 2487
    XCOM3_24 = 2488
    XCOM3_25 = 2489
    XCOM3_26 = 2490
    XCOM3_27 = 2491
    XCOM3_28 = 2492
    XCOM3_29 = 2493
    XCOM3_30 = 2494
    XCOM3_31 = 2495
    COM4 = 2976
    COM4_1 = 2977
    COM4_2 = 2978
    COM4_3 = 2979
    COM4_4 = 2980
    COM4_5 = 2981
    COM4_6 = 2982
    COM4_7 = 2983
    COM4_8 = 2984
    COM4_9 = 2985
    COM4_10 = 2986
    COM4_11 = 2987
    COM4_12 = 2988
    COM4_13 = 2989
    COM4_14 = 2990
    COM4_15 = 2991
    COM4_16 = 2992
    COM4_17 = 2993
    COM4_18 = 2994
    COM4_19 = 2995
    COM4_20 = 2996
    COM4_21 = 2997
    COM4_22 = 2998
    COM4_23 = 2999
    COM4_24 = 3000
    COM4_25 = 3001
    COM4_26 = 3002
    COM4_27 = 3003
    COM4_28 = 3004
    COM4_29 = 3005
    COM4_30 = 3006
    COM4_31 = 3007
    ETH1 = 3232
    ETH1_1 = 3233
    ETH1_2 = 3234
    ETH1_3 = 3235
    ETH1_4 = 3236
    ETH1_5 = 3237
    ETH1_6 = 3238
    ETH1_7 = 3239
    ETH1_8 = 3240
    ETH1_9 = 3241
    ETH1_10 = 3242
    ETH1_11 = 3243
    ETH1_12 = 3244
    ETH1_13 = 3245
    ETH1_14 = 3246
    ETH1_15 = 3247
    ETH1_16 = 3248
    ETH1_17 = 3249
    ETH1_18 = 3250
    ETH1_19 = 3251
    ETH1_20 = 3252
    ETH1_21 = 3253
    ETH1_22 = 3254
    ETH1_23 = 3255
    ETH1_24 = 3256
    ETH1_25 = 3257
    ETH1_26 = 3258
    ETH1_27 = 3259
    ETH1_28 = 3260
    ETH1_29 = 3261
    ETH1_30 = 3262
    ETH1_31 = 3263
    IMU = 3488
    IMU_1 = 3489
    IMU_2 = 3490
    IMU_3 = 3491
    IMU_4 = 3492
    IMU_5 = 3493
    IMU_6 = 3494
    IMU_7 = 3495
    IMU_8 = 3496
    IMU_9 = 3497
    IMU_10 = 3498
    IMU_11 = 3499
    IMU_12 = 3500
    IMU_13 = 3501
    IMU_14 = 3502
    IMU_15 = 3503
    IMU_16 = 3504
    IMU_17 = 3505
    IMU_18 = 3506
    IMU_19 = 3507
    IMU_20 = 3508
    IMU_21 = 3509
    IMU_22 = 3510
    IMU_23 = 3511
    IMU_24 = 3512
    IMU_25 = 3513
    IMU_26 = 3514
    IMU_27 = 3515
    IMU_28 = 3516
    IMU_29 = 3517
    IMU_30 = 3518
    IMU_31 = 3519
    ICOM1 = 4000
    ICOM1_1 = 4001
    ICOM1_2 = 4002
    ICOM1_3 = 4003
    ICOM1_4 = 4004
    ICOM1_5 = 4005
    ICOM1_6 = 4006
    ICOM1_7 = 4007
    ICOM1_8 = 4008
    ICOM1_9 = 4009
    ICOM1_10 = 4010
    ICOM1_11 = 4011
    ICOM1_12 = 4012
    ICOM1_13 = 4013
    ICOM1_14 = 4014
    ICOM1_15 = 4015
    ICOM1_16 = 4016
    ICOM1_17 = 4017
    ICOM1_18 = 4018
    ICOM1_19 = 4019
    ICOM1_20 = 4020
    ICOM1_21 = 4021
    ICOM1_22 = 4022
    ICOM1_23 = 4023
    ICOM1_24 = 4024
    ICOM1_25 = 4025
    ICOM1_26 = 4026
    ICOM1_27 = 4027
    ICOM1_28 = 4028
    ICOM1_29 = 4029
    ICOM1_30 = 4030
    ICOM1_31 = 4031
    ICOM2 = 4256
    ICOM2_1 = 4257
    ICOM2_2 = 4258
    ICOM2_3 = 4259
    ICOM2_4 = 4260
    ICOM2_5 = 4261
    ICOM2_6 = 4262
    ICOM2_7 = 4263
    ICOM2_8 = 4264
    ICOM2_9 = 4265
    ICOM2_10 = 4266
    ICOM2_11 = 4267
    ICOM2_12 = 4268
    ICOM2_13 = 4269
    ICOM2_14 = 4270
    ICOM2_15 = 4271
    ICOM2_16 = 4272
    ICOM2_17 = 4273
    ICOM2_18 = 4274
    ICOM2_19 = 4275
    ICOM2_20 = 4276
    ICOM2_21 = 4277
    ICOM2_22 = 4278
    ICOM2_23 = 4279
    ICOM2_24 = 4280
    ICOM2_25 = 4281
    ICOM2_26 = 4282
    ICOM2_27 = 4283
    ICOM2_28 = 4284
    ICOM2_29 = 4285
    ICOM2_30 = 4286
    ICOM2_31 = 4287
    ICOM3 = 4512
    ICOM3_1 = 4513
    ICOM3_2 = 4514
    ICOM3_3 = 4515
    ICOM3_4 = 4516
    ICOM3_5 = 4517
    ICOM3_6 = 4518
    ICOM3_7 = 4519
    ICOM3_8 = 4520
    ICOM3_9 = 4521
    ICOM3_10 = 4522
    ICOM3_11 = 4523
    ICOM3_12 = 4524
    ICOM3_13 = 4525
    ICOM3_14 = 4526
    ICOM3_15 = 4527
    ICOM3_16 = 4528
    ICOM3_17 = 4529
    ICOM3_18 = 4530
    ICOM3_19 = 4531
    ICOM3_20 = 4532
    ICOM3_21 = 4533
    ICOM3_22 = 4534
    ICOM3_23 = 4535
    ICOM3_24 = 4536
    ICOM3_25 = 4537
    ICOM3_26 = 4538
    ICOM3_27 = 4539
    ICOM3_28 = 4540
    ICOM3_29 = 4541
    ICOM3_30 = 4542
    ICOM3_31 = 4543
    NCOM1 = 4768
    NCOM1_1 = 4769
    NCOM1_2 = 4770
    NCOM1_3 = 4771
    NCOM1_4 = 4772
    NCOM1_5 = 4773
    NCOM1_6 = 4774
    NCOM1_7 = 4775
    NCOM1_8 = 4776
    NCOM1_9 = 4777
    NCOM1_10 = 4778
    NCOM1_11 = 4779
    NCOM1_12 = 4780
    NCOM1_13 = 4781
    NCOM1_14 = 4782
    NCOM1_15 = 4783
    NCOM1_16 = 4784
    NCOM1_17 = 4785
    NCOM1_18 = 4786
    NCOM1_19 = 4787
    NCOM1_20 = 4788
    NCOM1_21 = 4789
    NCOM1_22 = 4790
    NCOM1_23 = 4791
    NCOM1_24 = 4792
    NCOM1_25 = 4793
    NCOM1_26 = 4794
    NCOM1_27 = 4795
    NCOM1_28 = 4796
    NCOM1_29 = 4797
    NCOM1_30 = 4798
    NCOM1_31 = 4799
    NCOM2 = 5024
    NCOM2_1 = 5025
    NCOM2_2 = 5026
    NCOM2_3 = 5027
    NCOM2_4 = 5028
    NCOM2_5 = 5029
    NCOM2_6 = 5030
    NCOM2_7 = 5031
    NCOM2_8 = 5032
    NCOM2_9 = 5033
    NCOM2_10 = 5034
    NCOM2_11 = 5035
    NCOM2_12 = 5036
    NCOM2_13 = 5037
    NCOM2_14 = 5038
    NCOM2_15 = 5039
    NCOM2_16 = 5040
    NCOM2_17 = 5041
    NCOM2_18 = 5042
    NCOM2_19 = 5043
    NCOM2_20 = 5044
    NCOM2_21 = 5045
    NCOM2_22 = 5046
    NCOM2_23 = 5047
    NCOM2_24 = 5048
    NCOM2_25 = 5049
    NCOM2_26 = 5050
    NCOM2_27 = 5051
    NCOM2_28 = 5052
    NCOM2_29 = 5053
    NCOM2_30 = 5054
    NCOM2_31 = 5055
    NCOM3 = 5280
    NCOM3_1 = 5281
    NCOM3_2 = 5282
    NCOM3_3 = 5283
    NCOM3_4 = 5284
    NCOM3_5 = 5285
    NCOM3_6 = 5286
    NCOM3_7 = 5287
    NCOM3_8 = 5288
    NCOM3_9 = 5289
    NCOM3_10 = 5290
    NCOM3_11 = 5291
    NCOM3_12 = 5292
    NCOM3_13 = 5293
    NCOM3_14 = 5294
    NCOM3_15 = 5295
    NCOM3_16 = 5296
    NCOM3_17 = 5297
    NCOM3_18 = 5298
    NCOM3_19 = 5299
    NCOM3_20 = 5300
    NCOM3_21 = 5301
    NCOM3_22 = 5302
    NCOM3_23 = 5303
    NCOM3_24 = 5304
    NCOM3_25 = 5305
    NCOM3_26 = 5306
    NCOM3_27 = 5307
    NCOM3_28 = 5308
    NCOM3_29 = 5309
    NCOM3_30 = 5310
    NCOM3_31 = 5311
    ICOM4 = 5536
    ICOM4_1 = 5537
    ICOM4_2 = 5538
    ICOM4_3 = 5539
    ICOM4_4 = 5540
    ICOM4_5 = 5541
    ICOM4_6 = 5542
    ICOM4_7 = 5543
    ICOM4_8 = 5544
    ICOM4_9 = 5545
    ICOM4_10 = 5546
    ICOM4_11 = 5547
    ICOM4_12 = 5548
    ICOM4_13 = 5549
    ICOM4_14 = 5550
    ICOM4_15 = 5551
    ICOM4_16 = 5552
    ICOM4_17 = 5553
    ICOM4_18 = 5554
    ICOM4_19 = 5555
    ICOM4_20 = 5556
    ICOM4_21 = 5557
    ICOM4_22 = 5558
    ICOM4_23 = 5559
    ICOM4_24 = 5560
    ICOM4_25 = 5561
    ICOM4_26 = 5562
    ICOM4_27 = 5563
    ICOM4_28 = 5564
    ICOM4_29 = 5565
    ICOM4_30 = 5566
    ICOM4_31 = 5567
    WCOM1 = 5792
    WCOM1_1 = 5793
    WCOM1_2 = 5794
    WCOM1_3 = 5795
    WCOM1_4 = 5796
    WCOM1_5 = 5797
    WCOM1_6 = 5798
    WCOM1_7 = 5799
    WCOM1_8 = 5800
    WCOM1_9 = 5801
    WCOM1_10 = 5802
    WCOM1_11 = 5803
    WCOM1_12 = 5804
    WCOM1_13 = 5805
    WCOM1_14 = 5806
    WCOM1_15 = 5807
    WCOM1_16 = 5808
    WCOM1_17 = 5809
    WCOM1_18 = 5810
    WCOM1_19 = 5811
    WCOM1_20 = 5812
    WCOM1_21 = 5813
    WCOM1_22 = 5814
    WCOM1_23 = 5815
    WCOM1_24 = 5816
    WCOM1_25 = 5817
    WCOM1_26 = 5818
    WCOM1_27 = 5819
    WCOM1_28 = 5820
    WCOM1_29 = 5821
    WCOM1_30 = 5822
    WCOM1_31 = 5823
    COM5_ALL = 5824
    COM6_ALL = 5825
    BT1_ALL = 5826
    COM7_ALL = 5827
    COM8_ALL = 5828
    COM9_ALL = 5829
    COM10_ALL = 5830
    CCOM1_ALL = 5831
    CCOM2_ALL = 5832
    CCOM3_ALL = 5833
    CCOM4_ALL = 5834
    CCOM5_ALL = 5835
    CCOM6_ALL = 5836
    CCOM7_ALL = 5837
    CCOM8_ALL = 5838
    ICOM5_ALL = 5839
    ICOM6_ALL = 5840
    ICOM7_ALL = 5841
    SCOM1_ALL = 5842
    SCOM2_ALL = 5843
    SCOM3_ALL = 5844
    SCOM4_ALL = 5845
    COM5 = 6048
    COM5_1 = 6049
    COM5_2 = 6050
    COM5_3 = 6051
    COM5_4 = 6052
    COM5_5 = 6053
    COM5_6 = 6054
    COM5_7 = 6055
    COM5_8 = 6056
    COM5_9 = 6057
    COM5_10 = 6058
    COM5_11 = 6059
    COM5_12 = 6060
    COM5_13 = 6061
    COM5_14 = 6062
    COM5_15 = 6063
    COM5_16 = 6064
    COM5_17 = 6065
    COM5_18 = 6066
    COM5_19 = 6067
    COM5_20 = 6068
    COM5_21 = 6069
    COM5_22 = 6070
    COM5_23 = 6071
    COM5_24 = 6072
    COM5_25 = 6073
    COM5_26 = 6074
    COM5_27 = 6075
    COM5_28 = 6076
    COM5_29 = 6077
    COM5_30 = 6078
    COM5_31 = 6079
    COM6 = 6304
    COM6_1 = 6305
    COM6_2 = 6306
    COM6_3 = 6307
    COM6_4 = 6308
    COM6_5 = 6309
    COM6_6 = 6310
    COM6_7 = 6311
    COM6_8 = 6312
    COM6_9 = 6313
    COM6_10 = 6314
    COM6_11 = 6315
    COM6_12 = 6316
    COM6_13 = 6317
    COM6_14 = 6318
    COM6_15 = 6319
    COM6_16 = 6320
    COM6_17 = 6321
    COM6_18 = 6322
    COM6_19 = 6323
    COM6_20 = 6324
    COM6_21 = 6325
    COM6_22 = 6326
    COM6_23 = 6327
    COM6_24 = 6328
    COM6_25 = 6329
    COM6_26 = 6330
    COM6_27 = 6331
    COM6_28 = 6332
    COM6_29 = 6333
    COM6_30 = 6334
    COM6_31 = 6335
    BT1 = 6560
    BT1_1 = 6561
    BT1_2 = 6562
    BT1_3 = 6563
    BT1_4 = 6564
    BT1_5 = 6565
    BT1_6 = 6566
    BT1_7 = 6567
    BT1_8 = 6568
    BT1_9 = 6569
    BT1_10 = 6570
    BT1_11 = 6571
    BT1_12 = 6572
    BT1_13 = 6573
    BT1_14 = 6574
    BT1_15 = 6575
    BT1_16 = 6576
    BT1_17 = 6577
    BT1_18 = 6578
    BT1_19 = 6579
    BT1_20 = 6580
    BT1_21 = 6581
    BT1_22 = 6582
    BT1_23 = 6583
    BT1_24 = 6584
    BT1_25 = 6585
    BT1_26 = 6586
    BT1_27 = 6587
    BT1_28 = 6588
    BT1_29 = 6589
    BT1_30 = 6590
    BT1_31 = 6591
    COM7 = 6816
    COM7_1 = 6817
    COM7_2 = 6818
    COM7_3 = 6819
    COM7_4 = 6820
    COM7_5 = 6821
    COM7_6 = 6822
    COM7_7 = 6823
    COM7_8 = 6824
    COM7_9 = 6825
    COM7_10 = 6826
    COM7_11 = 6827
    COM7_12 = 6828
    COM7_13 = 6829
    COM7_14 = 6830
    COM7_15 = 6831
    COM7_16 = 6832
    COM7_17 = 6833
    COM7_18 = 6834
    COM7_19 = 6835
    COM7_20 = 6836
    COM7_21 = 6837
    COM7_22 = 6838
    COM7_23 = 6839
    COM7_24 = 6840
    COM7_25 = 6841
    COM7_26 = 6842
    COM7_27 = 6843
    COM7_28 = 6844
    COM7_29 = 6845
    COM7_30 = 6846
    COM7_31 = 6847
    COM8 = 7072
    COM8_1 = 7073
    COM8_2 = 7074
    COM8_3 = 7075
    COM8_4 = 7076
    COM8_5 = 7077
    COM8_6 = 7078
    COM8_7 = 7079
    COM8_8 = 7080
    COM8_9 = 7081
    COM8_10 = 7082
    COM8_11 = 7083
    COM8_12 = 7084
    COM8_13 = 7085
    COM8_14 = 7086
    COM8_15 = 7087
    COM8_16 = 7088
    COM8_17 = 7089
    COM8_18 = 7090
    COM8_19 = 7091
    COM8_20 = 7092
    COM8_21 = 7093
    COM8_22 = 7094
    COM8_23 = 7095
    COM8_24 = 7096
    COM8_25 = 7097
    COM8_26 = 7098
    COM8_27 = 7099
    COM8_28 = 7100
    COM8_29 = 7101
    COM8_30 = 7102
    COM8_31 = 7103
    COM9 = 7328
    COM9_1 = 7329
    COM9_2 = 7330
    COM9_3 = 7331
    COM9_4 = 7332
    COM9_5 = 7333
    COM9_6 = 7334
    COM9_7 = 7335
    COM9_8 = 7336
    COM9_9 = 7337
    COM9_10 = 7338
    COM9_11 = 7339
    COM9_12 = 7340
    COM9_13 = 7341
    COM9_14 = 7342
    COM9_15 = 7343
    COM9_16 = 7344
    COM9_17 = 7345
    COM9_18 = 7346
    COM9_19 = 7347
    COM9_20 = 7348
    COM9_21 = 7349
    COM9_22 = 7350
    COM9_23 = 7351
    COM9_24 = 7352
    COM9_25 = 7353
    COM9_26 = 7354
    COM9_27 = 7355
    COM9_28 = 7356
    COM9_29 = 7357
    COM9_30 = 7358
    COM9_31 = 7359
    COM10 = 7584
    COM10_1 = 7585
    COM10_2 = 7586
    COM10_3 = 7587
    COM10_4 = 7588
    COM10_5 = 7589
    COM10_6 = 7590
    COM10_7 = 7591
    COM10_8 = 7592
    COM10_9 = 7593
    COM10_10 = 7594
    COM10_11 = 7595
    COM10_12 = 7596
    COM10_13 = 7597
    COM10_14 = 7598
    COM10_15 = 7599
    COM10_16 = 7600
    COM10_17 = 7601
    COM10_18 = 7602
    COM10_19 = 7603
    COM10_20 = 7604
    COM10_21 = 7605
    COM10_22 = 7606
    COM10_23 = 7607
    COM10_24 = 7608
    COM10_25 = 7609
    COM10_26 = 7610
    COM10_27 = 7611
    COM10_28 = 7612
    COM10_29 = 7613
    COM10_30 = 7614
    COM10_31 = 7615
    CCOM1 = 7840
    CCOM1_1 = 7841
    CCOM1_2 = 7842
    CCOM1_3 = 7843
    CCOM1_4 = 7844
    CCOM1_5 = 7845
    CCOM1_6 = 7846
    CCOM1_7 = 7847
    CCOM1_8 = 7848
    CCOM1_9 = 7849
    CCOM1_10 = 7850
    CCOM1_11 = 7851
    CCOM1_12 = 7852
    CCOM1_13 = 7853
    CCOM1_14 = 7854
    CCOM1_15 = 7855
    CCOM1_16 = 7856
    CCOM1_17 = 7857
    CCOM1_18 = 7858
    CCOM1_19 = 7859
    CCOM1_20 = 7860
    CCOM1_21 = 7861
    CCOM1_22 = 7862
    CCOM1_23 = 7863
    CCOM1_24 = 7864
    CCOM1_25 = 7865
    CCOM1_26 = 7866
    CCOM1_27 = 7867
    CCOM1_28 = 7868
    CCOM1_29 = 7869
    CCOM1_30 = 7870
    CCOM1_31 = 7871
    CCOM2 = 8096
    CCOM2_1 = 8097
    CCOM2_2 = 8098
    CCOM2_3 = 8099
    CCOM2_4 = 8100
    CCOM2_5 = 8101
    CCOM2_6 = 8102
    CCOM2_7 = 8103
    CCOM2_8 = 8104
    CCOM2_9 = 8105
    CCOM2_10 = 8106
    CCOM2_11 = 8107
    CCOM2_12 = 8108
    CCOM2_13 = 8109
    CCOM2_14 = 8110
    CCOM2_15 = 8111
    CCOM2_16 = 8112
    CCOM2_17 = 8113
    CCOM2_18 = 8114
    CCOM2_19 = 8115
    CCOM2_20 = 8116
    CCOM2_21 = 8117
    CCOM2_22 = 8118
    CCOM2_23 = 8119
    CCOM2_24 = 8120
    CCOM2_25 = 8121
    CCOM2_26 = 8122
    CCOM2_27 = 8123
    CCOM2_28 = 8124
    CCOM2_29 = 8125
    CCOM2_30 = 8126
    CCOM2_31 = 8127
    CCOM3 = 8352
    CCOM3_1 = 8353
    CCOM3_2 = 8354
    CCOM3_3 = 8355
    CCOM3_4 = 8356
    CCOM3_5 = 8357
    CCOM3_6 = 8358
    CCOM3_7 = 8359
    CCOM3_8 = 8360
    CCOM3_9 = 8361
    CCOM3_10 = 8362
    CCOM3_11 = 8363
    CCOM3_12 = 8364
    CCOM3_13 = 8365
    CCOM3_14 = 8366
    CCOM3_15 = 8367
    CCOM3_16 = 8368
    CCOM3_17 = 8369
    CCOM3_18 = 8370
    CCOM3_19 = 8371
    CCOM3_20 = 8372
    CCOM3_21 = 8373
    CCOM3_22 = 8374
    CCOM3_23 = 8375
    CCOM3_24 = 8376
    CCOM3_25 = 8377
    CCOM3_26 = 8378
    CCOM3_27 = 8379
    CCOM3_28 = 8380
    CCOM3_29 = 8381
    CCOM3_30 = 8382
    CCOM3_31 = 8383
    CCOM4 = 8608
    CCOM4_1 = 8609
    CCOM4_2 = 8610
    CCOM4_3 = 8611
    CCOM4_4 = 8612
    CCOM4_5 = 8613
    CCOM4_6 = 8614
    CCOM4_7 = 8615
    CCOM4_8 = 8616
    CCOM4_9 = 8617
    CCOM4_10 = 8618
    CCOM4_11 = 8619
    CCOM4_12 = 8620
    CCOM4_13 = 8621
    CCOM4_14 = 8622
    CCOM4_15 = 8623
    CCOM4_16 = 8624
    CCOM4_17 = 8625
    CCOM4_18 = 8626
    CCOM4_19 = 8627
    CCOM4_20 = 8628
    CCOM4_21 = 8629
    CCOM4_22 = 8630
    CCOM4_23 = 8631
    CCOM4_24 = 8632
    CCOM4_25 = 8633
    CCOM4_26 = 8634
    CCOM4_27 = 8635
    CCOM4_28 = 8636
    CCOM4_29 = 8637
    CCOM4_30 = 8638
    CCOM4_31 = 8639
    CCOM5 = 8864
    CCOM5_1 = 8865
    CCOM5_2 = 8866
    CCOM5_3 = 8867
    CCOM5_4 = 8868
    CCOM5_5 = 8869
    CCOM5_6 = 8870
    CCOM5_7 = 8871
    CCOM5_8 = 8872
    CCOM5_9 = 8873
    CCOM5_10 = 8874
    CCOM5_11 = 8875
    CCOM5_12 = 8876
    CCOM5_13 = 8877
    CCOM5_14 = 8878
    CCOM5_15 = 8879
    CCOM5_16 = 8880
    CCOM5_17 = 8881
    CCOM5_18 = 8882
    CCOM5_19 = 8883
    CCOM5_20 = 8884
    CCOM5_21 = 8885
    CCOM5_22 = 8886
    CCOM5_23 = 8887
    CCOM5_24 = 8888
    CCOM5_25 = 8889
    CCOM5_26 = 8890
    CCOM5_27 = 8891
    CCOM5_28 = 8892
    CCOM5_29 = 8893
    CCOM5_30 = 8894
    CCOM5_31 = 8895
    CCOM6 = 9120
    CCOM6_1 = 9121
    CCOM6_2 = 9122
    CCOM6_3 = 9123
    CCOM6_4 = 9124
    CCOM6_5 = 9125
    CCOM6_6 = 9126
    CCOM6_7 = 9127
    CCOM6_8 = 9128
    CCOM6_9 = 9129
    CCOM6_10 = 9130
    CCOM6_11 = 9131
    CCOM6_12 = 9132
    CCOM6_13 = 9133
    CCOM6_14 = 9134
    CCOM6_15 = 9135
    CCOM6_16 = 9136
    CCOM6_17 = 9137
    CCOM6_18 = 9138
    CCOM6_19 = 9139
    CCOM6_20 = 9140
    CCOM6_21 = 9141
    CCOM6_22 = 9142
    CCOM6_23 = 9143
    CCOM6_24 = 9144
    CCOM6_25 = 9145
    CCOM6_26 = 9146
    CCOM6_27 = 9147
    CCOM6_28 = 9148
    CCOM6_29 = 9149
    CCOM6_30 = 9150
    CCOM6_31 = 9151
    CCOM7 = 9376
    CCOM7_1 = 9377
    CCOM7_2 = 9378
    CCOM7_3 = 9379
    CCOM7_4 = 9380
    CCOM7_5 = 9381
    CCOM7_6 = 9382
    CCOM7_7 = 9383
    CCOM7_8 = 9384
    CCOM7_9 = 9385
    CCOM7_10 = 9386
    CCOM7_11 = 9387
    CCOM7_12 = 9388
    CCOM7_13 = 9389
    CCOM7_14 = 9390
    CCOM7_15 = 9391
    CCOM7_16 = 9392
    CCOM7_17 = 9393
    CCOM7_18 = 9394
    CCOM7_19 = 9395
    CCOM7_20 = 9396
    CCOM7_21 = 9397
    CCOM7_22 = 9398
    CCOM7_23 = 9399
    CCOM7_24 = 9400
    CCOM7_25 = 9401
    CCOM7_26 = 9402
    CCOM7_27 = 9403
    CCOM7_28 = 9404
    CCOM7_29 = 9405
    CCOM7_30 = 9406
    CCOM7_31 = 9407
    CCOM8 = 9632
    CCOM8_1 = 9633
    CCOM8_2 = 9634
    CCOM8_3 = 9635
    CCOM8_4 = 9636
    CCOM8_5 = 9637
    CCOM8_6 = 9638
    CCOM8_7 = 9639
    CCOM8_8 = 9640
    CCOM8_9 = 9641
    CCOM8_10 = 9642
    CCOM8_11 = 9643
    CCOM8_12 = 9644
    CCOM8_13 = 9645
    CCOM8_14 = 9646
    CCOM8_15 = 9647
    CCOM8_16 = 9648
    CCOM8_17 = 9649
    CCOM8_18 = 9650
    CCOM8_19 = 9651
    CCOM8_20 = 9652
    CCOM8_21 = 9653
    CCOM8_22 = 9654
    CCOM8_23 = 9655
    CCOM8_24 = 9656
    CCOM8_25 = 9657
    CCOM8_26 = 9658
    CCOM8_27 = 9659
    CCOM8_28 = 9660
    CCOM8_29 = 9661
    CCOM8_30 = 9662
    CCOM8_31 = 9663
    ICOM5 = 9888
    ICOM5_1 = 9889
    ICOM5_2 = 9890
    ICOM5_3 = 9891
    ICOM5_4 = 9892
    ICOM5_5 = 9893
    ICOM5_6 = 9894
    ICOM5_7 = 9895
    ICOM5_8 = 9896
    ICOM5_9 = 9897
    ICOM5_10 = 9898
    ICOM5_11 = 9899
    ICOM5_12 = 9900
    ICOM5_13 = 9901
    ICOM5_14 = 9902
    ICOM5_15 = 9903
    ICOM5_16 = 9904
    ICOM5_17 = 9905
    ICOM5_18 = 9906
    ICOM5_19 = 9907
    ICOM5_20 = 9908
    ICOM5_21 = 9909
    ICOM5_22 = 9910
    ICOM5_23 = 9911
    ICOM5_24 = 9912
    ICOM5_25 = 9913
    ICOM5_26 = 9914
    ICOM5_27 = 9915
    ICOM5_28 = 9916
    ICOM5_29 = 9917
    ICOM5_30 = 9918
    ICOM5_31 = 9919
    ICOM6 = 10144
    ICOM6_1 = 10145
    ICOM6_2 = 10146
    ICOM6_3 = 10147
    ICOM6_4 = 10148
    ICOM6_5 = 10149
    ICOM6_6 = 10150
    ICOM6_7 = 10151
    ICOM6_8 = 10152
    ICOM6_9 = 10153
    ICOM6_10 = 10154
    ICOM6_11 = 10155
    ICOM6_12 = 10156
    ICOM6_13 = 10157
    ICOM6_14 = 10158
    ICOM6_15 = 10159
    ICOM6_16 = 10160
    ICOM6_17 = 10161
    ICOM6_18 = 10162
    ICOM6_19 = 10163
    ICOM6_20 = 10164
    ICOM6_21 = 10165
    ICOM6_22 = 10166
    ICOM6_23 = 10167
    ICOM6_24 = 10168
    ICOM6_25 = 10169
    ICOM6_26 = 10170
    ICOM6_27 = 10171
    ICOM6_28 = 10172
    ICOM6_29 = 10173
    ICOM6_30 = 10174
    ICOM6_31 = 10175
    ICOM7 = 10400
    ICOM7_1 = 10401
    ICOM7_2 = 10402
    ICOM7_3 = 10403
    ICOM7_4 = 10404
    ICOM7_5 = 10405
    ICOM7_6 = 10406
    ICOM7_7 = 10407
    ICOM7_8 = 10408
    ICOM7_9 = 10409
    ICOM7_10 = 10410
    ICOM7_11 = 10411
    ICOM7_12 = 10412
    ICOM7_13 = 10413
    ICOM7_14 = 10414
    ICOM7_15 = 10415
    ICOM7_16 = 10416
    ICOM7_17 = 10417
    ICOM7_18 = 10418
    ICOM7_19 = 10419
    ICOM7_20 = 10420
    ICOM7_21 = 10421
    ICOM7_22 = 10422
    ICOM7_23 = 10423
    ICOM7_24 = 10424
    ICOM7_25 = 10425
    ICOM7_26 = 10426
    ICOM7_27 = 10427
    ICOM7_28 = 10428
    ICOM7_29 = 10429
    ICOM7_30 = 10430
    ICOM7_31 = 10431
    SCOM1 = 10656
    SCOM1_1 = 10657
    SCOM1_2 = 10658
    SCOM1_3 = 10659
    SCOM1_4 = 10660
    SCOM1_5 = 10661
    SCOM1_6 = 10662
    SCOM1_7 = 10663
    SCOM1_8 = 10664
    SCOM1_9 = 10665
    SCOM1_10 = 10666
    SCOM1_11 = 10667
    SCOM1_12 = 10668
    SCOM1_13 = 10669
    SCOM1_14 = 10670
    SCOM1_15 = 10671
    SCOM1_16 = 10672
    SCOM1_17 = 10673
    SCOM1_18 = 10674
    SCOM1_19 = 10675
    SCOM1_20 = 10676
    SCOM1_21 = 10677
    SCOM1_22 = 10678
    SCOM1_23 = 10679
    SCOM1_24 = 10680
    SCOM1_25 = 10681
    SCOM1_26 = 10682
    SCOM1_27 = 10683
    SCOM1_28 = 10684
    SCOM1_29 = 10685
    SCOM1_30 = 10686
    SCOM1_31 = 10687
    SCOM2 = 10912
    SCOM2_1 = 10913
    SCOM2_2 = 10914
    SCOM2_3 = 10915
    SCOM2_4 = 10916
    SCOM2_5 = 10917
    SCOM2_6 = 10918
    SCOM2_7 = 10919
    SCOM2_8 = 10920
    SCOM2_9 = 10921
    SCOM2_10 = 10922
    SCOM2_11 = 10923
    SCOM2_12 = 10924
    SCOM2_13 = 10925
    SCOM2_14 = 10926
    SCOM2_15 = 10927
    SCOM2_16 = 10928
    SCOM2_17 = 10929
    SCOM2_18 = 10930
    SCOM2_19 = 10931
    SCOM2_20 = 10932
    SCOM2_21 = 10933
    SCOM2_22 = 10934
    SCOM2_23 = 10935
    SCOM2_24 = 10936
    SCOM2_25 = 10937
    SCOM2_26 = 10938
    SCOM2_27 = 10939
    SCOM2_28 = 10940
    SCOM2_29 = 10941
    SCOM2_30 = 10942
    SCOM2_31 = 10943
    SCOM3 = 11168
    SCOM3_1 = 11169
    SCOM3_2 = 11170
    SCOM3_3 = 11171
    SCOM3_4 = 11172
    SCOM3_5 = 11173
    SCOM3_6 = 11174
    SCOM3_7 = 11175
    SCOM3_8 = 11176
    SCOM3_9 = 11177
    SCOM3_10 = 11178
    SCOM3_11 = 11179
    SCOM3_12 = 11180
    SCOM3_13 = 11181
    SCOM3_14 = 11182
    SCOM3_15 = 11183
    SCOM3_16 = 11184
    SCOM3_17 = 11185
    SCOM3_18 = 11186
    SCOM3_19 = 11187
    SCOM3_20 = 11188
    SCOM3_21 = 11189
    SCOM3_22 = 11190
    SCOM3_23 = 11191
    SCOM3_24 = 11192
    SCOM3_25 = 11193
    SCOM3_26 = 11194
    SCOM3_27 = 11195
    SCOM3_28 = 11196
    SCOM3_29 = 11197
    SCOM3_30 = 11198
    SCOM3_31 = 11199
    SCOM4 = 11424
    SCOM4_1 = 11425
    SCOM4_2 = 11426
    SCOM4_3 = 11427
    SCOM4_4 = 11428
    SCOM4_5 = 11429
    SCOM4_6 = 11430
    SCOM4_7 = 11431
    SCOM4_8 = 11432
    SCOM4_9 = 11433
    SCOM4_10 = 11434
    SCOM4_11 = 11435
    SCOM4_12 = 11436
    SCOM4_13 = 11437
    SCOM4_14 = 11438
    SCOM4_15 = 11439
    SCOM4_16 = 11440
    SCOM4_17 = 11441
    SCOM4_18 = 11442
    SCOM4_19 = 11443
    SCOM4_20 = 11444
    SCOM4_21 = 11445
    SCOM4_22 = 11446
    SCOM4_23 = 11447
    SCOM4_24 = 11448
    SCOM4_25 = 11449
    SCOM4_26 = 11450
    SCOM4_27 = 11451
    SCOM4_28 = 11452
    SCOM4_29 = 11453
    SCOM4_30 = 11454
    SCOM4_31 = 11455

class Adjust1PPSPeriod(Enum):
    ONCE = 0
    CONTINUOUS = 1

class ProfileOption(Enum):
    CREATE = 1
    DELETE = 2
    CREATEELEMENT = 3
    DELETEELEMENT = 4
    ACTIVATE = 5
    DEACTIVATE = 6
    EXECUTE = 32768
    CHECKEXISTS = 32769

class SatelControlAction(Enum):
    POWER = 1
    SL = 2
    SERVICE = 3
    FRESET = 4

class SprinklerChannel(Enum):
    CHAN0 = 0
    CHAN1 = 1
    CHAN2 = 2

class IPConfigMode(Enum):
    DHCP = 1
    STATIC = 2

class NMEAField(Enum):
    GGA_LATITUDE = 0
    GGA_LONGITUDE = 1
    GGA_ALTITUDE = 2
    GGA_UNDULATION = 3
    GGA_AGE = 4
    GGALONG_LATITUDE = 10
    GGALONG_LONGITUDE = 11
    GGALONG_ALTITUDE = 12
    GGALONG_UNDULATION = 13
    GGALONG_AGE = 14
    COUNT = 15

class RTKResetType(Enum):
    FILTER = 1

class ClockAdjustCommand(Enum):
    DISABLE = 0
    ENABLE = 1
    RESET = 2

class ScaleFactor(Enum):
    SCALE_DEFAULT = 0
    SCALE_ALT1 = 1
    SCALE_ALT2 = 2
    SCALE_ALT3 = 3
    SCALE_CUSTOM = 4

class PPPSource(Enum):
    NONE = 0
    TERRASTAR = 1
    VERIPOS = 2
    RTCMV3 = 4
    ULTRA = 5
    APEX = 7
    TERRASTAR_L = 8
    NOT_IN_USE = 9
    TERRASTAR_C = 10
    OCEANIX = 11
    FILE = 20
    AUTO = 100

class UTMZoneCommand(Enum):
    AUTO = 0
    CURRENT = 1
    SET = 2
    MERIDIAN = 3

class VeriposDecoderSyncState(Enum):
    NO_SIGNAL = 0
    SEARCH = 1
    LOCKED = 2
    WRONG_BEAM = 3

class PhysicalInterface(Enum):
    NONE = 0
    ALL = 1
    ETHA = 2
    ETHB = 3
    WIFI = 10
    WIFI_CLIENT = 11
    CELL = 20

class PCVModeling(Enum):
    DISABLE = 0
    ENABLE = 1

class IonoCondition(Enum):
    QUIET = 0
    NORMAL = 1
    DISTURBED = 2
    EXTREME = 3
    AUTO = 10

class PlatformAuthCodeType(Enum):
    STANDARD = 1
    SIGNATURE = 2
    EMBEDDED = 3

class DMI(Enum):
    DMI1 = 0
    DMI2 = 1
    DMI3 = 2
    DMI4 = 3

class INSThresholds(Enum):
    DEFAULT = 0
    LOW = 1
    HIGH = 2

class SatelStatus(Enum):
    OFF = 0
    UNDETECTED = 1
    DETECTING = 2
    READY = 3
    BUSY = 4
    ERROR = 5

class ExtClockFreq(Enum):
    _0MHZ = 0
    _5MHZ = 1
    _10MHZ = 2
    _20MHZ = 3

class ClockCalibrate(Enum):
    SET = 0
    AUTO = 1
    OFF = 2
    MOVE = 3

class EthernetCrossover(Enum):
    AUTO = 1
    MDI = 2
    MDIX = 3

class RTKAssistState(Enum):
    INACTIVE = 0
    ACTIVE = 1

class Component(Enum):
    UNKNOWN = 0
    GPSCARD = 1
    CONTROLLER = 2
    ENCLOSURE = 3
    IBOARD = 4
    L5_FPGA = 5
    IMUCARD = 7
    USERINFO = 8
    OEM6FPGA = 12
    GPSCARD2 = 13
    BLUETOOTH = 14
    WIFI = 15
    CELLULAR = 16
    EXTENSION = 17
    RADIO = 18
    WWW_CONTENT = 19
    REGULATORY = 20
    OEM7FPGA = 21
    APPLICATION = 22
    PACKAGE = 23
    NETBOOT = 24
    DEFAULT_CONFIG = 25
    WHEELSENSOR = 26
    EMBEDDED_AUTH = 27
    HWCONFIG = 28
    LUA_SCRIPTS = 29
    DB_HEIGHTMODEL = 981073920
    DB_USERAPP = 981073921
    DB_L5FPGA = 981073923
    DB_USERAPPAUTO = 981073925
    DB_OEMVFPGA = 981073926
    DB_OEMVINTARM = 981073927
    DB_WWWISO = 981073928
    CRASH_DUMP = 981073929
    DB_LUA_SCRIPTS = 981073930
    INVALID = 2147483647

class OEM4_Parity(Enum):
    N = 0
    E = 1
    O = 2

class RxStatusFlag(Enum):
    CLEAR = 0
    SET = 1
    UPDATE = 2

class VeriposRegionRestriction(Enum):
    NONE = 0
    GEOGATED = 1
    LOCAL_AREA = 2
    NEARSHORE = 3
    COASTAL = 4

class BaseReceiverType(Enum):
    UNKNOWN = 0
    NOVATEL = 1
    TRIMBLE = 2
    TOPCON = 3
    MAGELLAN = 4
    LEICA = 5
    SEPTENTRIO = 6
    SUPPORTED = 50
    ALL = 51

class ClockType(Enum):
    DISABLE = 0
    TCXO = 1
    OCXO = 2
    RUBIDIUM = 3
    CESIUM = 4
    USER = 5

class SetBestPosCriteria(Enum):
    POS3D = 0
    POS2D = 1

class EgressRoutingDest(Enum):
    LOCAL = 0
    OEMV3 = 1
    OEMV2 = 2

class IMUEvent(Enum):
    OFF = 1
    DEFAULT = 2
    EVENT1 = 3
    EVENT2 = 4
    EVENT3 = 5
    EVENT4 = 6

class ClockModelStatus(Enum):
    VALID = 0
    CONVERGING = 1
    ITERATING = 2
    INVALID = 3
    ERROR = 4

class ITIntDetectMethod(Enum):
    SPECTRUMANALYSIS = 0
    STATISTICANALYSIS = 1

class SpoofDetectSignalType(Enum):
    GPSL1CA = 0
    GALE1 = 1
    GLOL1 = 2
    BDSB1 = 3

class NTripType(Enum):
    DISABLED = 1
    CLIENT = 2
    SERVER = 3

class AlignmentMode(Enum):
    UNAIDED = 0
    AIDED_STATIC = 1
    AIDED_TRANSFER = 2
    AUTOMATIC = 3
    STATIC = 4
    KINEMATIC = 5

class TectonicsCompensationStatus(Enum):
    UNAVAILABLE = 0
    AVAILABLE = 1
    WARNING = 2
    OFF_PLATE = 3

class SystemVariant(Enum):
    NONE = 0
    UNKNOWN = 1
    WAAS = 2
    EGNOS = 3
    MSAS = 4
    GAGAN = 5
    UNSUPPORTED = 6
    QZSS = 7

class EventInEnable(Enum):
    DISABLE = 0
    EVENT = 1
    COUNT = 2
    ENABLE = 3

class RTKAssistTimeOutLimit(Enum):
    SUBSCRIPTION_LIMIT = 0
    USER_LIMIT = 1

class L2CodeType(Enum):
    AUTO = 0
    P = 1
    C = 2
    DEFAULT = 3

class InterfaceMode(Enum):
    NONE = 0
    NOVATEL = 1
    RTCM = 2
    RTCA = 3
    CMR = 4
    OMNISTAR = 5
    IMU = 7
    RTCMNOCR = 8
    CDGPS = 9
    TCOM1 = 10
    TCOM2 = 11
    TCOM3 = 12
    TAUX = 13
    RTCMV3 = 14
    NOVATELBINARY = 15
    ARINC429 = 16
    LEICALITE = 17
    GENERIC = 18
    IMARIMU = 19
    MRTCA = 20
    IGIIMU = 21
    SEATEXIMU = 22
    KVHIMU = 23
    MICROIRSIMU = 24
    TCOM4 = 26
    AUTO = 27
    LITEFIMU = 28
    LANDMARK20 = 29
    GENERIC_IMU = 30
    TAMAMIMU = 31
    MIC = 32
    TCOM5 = 33
    TCOM6 = 34
    NOVATELX = 35
    TBT1 = 36
    TCOM7 = 37
    TCOM8 = 38
    TCOM9 = 39
    TCOM10 = 40
    KVH1750IMU = 41
    VERIPOS = 42
    PAV80 = 43
    IMARFRIMU = 44
    TCCOM1 = 46
    TCCOM2 = 47
    TCCOM3 = 48
    NOVATELMINBINARY = 49
    TCCOM4 = 50
    TCCOM5 = 51
    TCCOM6 = 52
    TCCOM7 = 53
    TCCOM8 = 54
    VERIPOS_RTCM = 55
    SONARDYNE = 56
    NOVATELMULTI = 57
    AUTO_FIXED = 58
    STIM300DIMU = 59
    TSCOM1 = 60
    TSCOM2 = 61
    TSCOM3 = 62
    TSCOM4 = 63
    LUA = 64
    HONEYWELLIMU = 65

class FileStatus(Enum):
    OPEN = 1
    CLOSED = 2
    BUSY = 3
    ERROR = 4
    COPY = 5
    PENDING = 6

class PDPFilterDynamics(Enum):
    AUTO = 0
    STATIC = 1
    DYNAMIC = 2
    AUTO_STATIC = 3
    AUTO_DYNAMIC = 4

class CommPort(Enum):
    NOPORT = 0
    COM1 = 1
    COM2 = 2
    COM3 = 3
    ACK = 4
    UNKNOWN = 5
    THISPORT = 6
    FILE = 7
    ALL = 8
    XCOM1 = 9
    XCOM2 = 10
    USB1 = 13
    USB2 = 14
    USB3 = 15
    AUX = 16
    XCOM3 = 17
    COM4 = 19
    ETH1 = 20
    IMU = 21
    ICOM1 = 23
    ICOM2 = 24
    ICOM3 = 25
    NCOM1 = 26
    NCOM2 = 27
    NCOM3 = 28
    ICOM4 = 29
    WCOM1 = 30
    COM5 = 31
    COM6 = 32
    BT1 = 33
    COM7 = 34
    COM8 = 35
    COM9 = 36
    COM10 = 37
    CCOM1 = 38
    CCOM2 = 39
    CCOM3 = 40
    CCOM4 = 41
    CCOM5 = 42
    CCOM6 = 43
    CCOM7 = 44
    CCOM8 = 45
    ICOM5 = 46
    ICOM6 = 47
    ICOM7 = 48
    SCOM1 = 49
    SCOM2 = 50
    SCOM3 = 51
    SCOM4 = 52

class VeriposGeogatingStatus(Enum):
    DISABLED = 0
    WAITING_FOR_POSITION = 1
    ONSHORE = 129
    OFFSHORE = 130
    NEARSHORE = 131
    POSITION_TOO_OLD = 255
    PROCESSING = 1000

class ClockSteeringState(Enum):
    FIRST_ORDER = 0
    SECOND_ORDER = 1
    CALIBRATE_HIGH = 2
    CALIBRATE_LOW = 3
    CALIBRATE_CENTER = 4

class DDCFilterType(Enum):
    PASSTHROUGH = 0
    CIC1 = 1
    CIC2 = 2
    CIC3 = 3
    HALFBAND = 4

class TectonicsCompensationVelocitySource(Enum):
    NONE = 0
    PLATE_MOTION_MODEL = 1

class PositionReference(Enum):
    L1PC = 0
    ARP = 1
    UNKNOWN = 2

class LuaStatus(Enum):
    NOT_STARTED = 0
    EXECUTING = 1
    COMPLETED = 2
    SCRIPT_ERROR = 3
    EXECUTOR_ERROR = 4
    EXCEPTION = 5

class RAIMMode(Enum):
    DISABLE = 0
    USER = 1
    DEFAULT = 2
    APPROACH = 3
    TERMINAL = 4
    ENROUTE = 5
    VERIPOS = 6

class FileTransferStatus(Enum):
    NONE = 1
    TRANSFERRING = 2
    FINISHED = 3
    ERROR = 4
    CANCELLED = 5

class RelINSRx(Enum):
    INVALID = 0
    ROVER = 1
    MASTER = 2

class CanPort(Enum):
    CAN_NONE = 0
    CAN1 = 1
    CAN2 = 2

class RTKCorrectionSet(Enum):
    RTCM = 2
    RTCA = 3
    CMR = 4
    MSM = 5
    MSM12 = 6
    MSM3 = 7
    MSM4 = 8
    MSM5 = 9
    MSM6 = 10
    MSM7 = 11
    RTCMV3 = 14
    NOVATELX = 35

class INSOffsetFrame(Enum):
    IMUBODY = 0
    VEHICLE = 1

class RTKIntegerCriteria(Enum):
    TOTAL_STDDEV = 1
    HORIZONTAL_STDDEV = 2

class FixCmd(Enum):
    NONE = 0
    AUTO = 1
    HEIGHT = 2
    POSITION = 3
    VELOCITY = 4

class TropoModel(Enum):
    NONE = 1
    AUTO = 2

class ClockSource(Enum):
    INTERNAL = 0
    EXTERNAL = 1
    INTERNAL_AUTO = 2

class Hold(Enum):
    NOHOLD = 0
    HOLD = 1

class SoftLoadSource(Enum):
    COM = 1
    COM_NO_ERROR = 2
    USERAPP = 128

class NTripProtocol(Enum):
    DISABLED = 1
    V1 = 2
    V2 = 3

class RxStatusConfigType(Enum):
    PRIORITY = 0
    SET = 1
    CLEAR = 2
    DISABLE = 3
    IGNORELIVE = 4

class PPPResetType(Enum):
    FILTER = 1
    ALL = 10
    SIGNAL_BIASES = 100
    SATELLITE_BIASES = 101

class INSSeed(Enum):
    DISABLE = 0
    ENABLE = 1
    CLEAR = 2
    SAVE = 3
    SAVEERRORMODEL = 4

class RFInputFrequency(Enum):
    NONE = 0
    DEFAULT = 1
    L1 = 2
    L2 = 3
    LBAND = 4
    L5 = 5

class TimeOut(Enum):
    SPEC = 0
    AUTO = 1
    SET = 2

class LuaAction(Enum):
    START = 1
    PROMPT = 2

class RAIMIntegrityStatus(Enum):
    NOT_AVAILABLE = 0
    PASS = 1
    FAIL = 2

class RAIMProtectionLevelStatus(Enum):
    NOT_AVAILABLE = 0
    PASS = 1
    ALERT = 2

class INSCommand(Enum):
    RESET = 0
    DISABLE = 1
    ENABLE = 2
    START_NO_TIME = 3
    START_FINE_TIME = 4
    RESTART = 5
    MAXGYRO_ENABLE = 6
    MAXGYRO_DISABLE = 7

class AntennaModel(Enum):
    NONE = 0
    USER = 1
    AUTO = 2
    AERAT2775_43 = 3
    AOAD_M_B = 4
    AOAD_M_T = 5
    AOAD_M_TA_NGS = 6
    APSAPS_3 = 7
    ASH700228A = 8
    ASH700228B = 9
    ASH700228C = 10
    ASH700228D = 11
    ASH700228E = 12
    ASH700699_L1 = 13
    ASH700700_A = 14
    ASH700700_B = 15
    ASH700700_C = 16
    ASH700718A = 17
    ASH700718B = 18
    ASH700829_2 = 19
    ASH700829_3 = 20
    ASH700829_A = 21
    ASH700829_A1 = 22
    ASH700936A_M = 23
    ASH700936B_M = 24
    ASH700936C_M = 25
    ASH700936D_M = 26
    ASH700936E = 27
    ASH700936E_C = 28
    ASH700936F_C = 29
    ASH701008_01B = 30
    ASH701073_1 = 31
    ASH701073_3 = 32
    ASH701933A_M = 33
    ASH701933B_M = 34
    ASH701933C_M = 35
    ASH701941_1 = 36
    ASH701941_2 = 37
    ASH701941_A = 38
    ASH701941_B = 39
    ASH701945B_M = 40
    ASH701945C_M = 41
    ASH701945D_M = 42
    ASH701945E_M = 43
    ASH701945G_M = 44
    ASH701946_2 = 45
    ASH701946_3 = 46
    ASH701975_01A = 47
    ASH701975_01AGP = 48
    JAV_GRANT_G3T = 49
    JAV_RINGANT_G3T = 50
    JAVRINGANT_DM = 51
    JNSMARANT_GGD = 52
    JPLD_M_R = 53
    JPLD_M_RA_SOP = 54
    JPSLEGANT_E = 55
    JPSODYSSEY_I = 56
    JPSREGANT_DD_E = 57
    JPSREGANT_SD_E = 58
    LEIAR10 = 59
    LEIAR25 = 60
    LEIAR25_R3 = 61
    LEIAR25_R4 = 62
    LEIAS05 = 63
    LEIAX1202GG = 64
    LEIAS10 = 65
    LEIAX1203_GNSS = 66
    LEIAT202_GP = 67
    LEIAT202_GP = 68
    LEIAT302_GP = 69
    LEIAT302_GP = 70
    LEIAT303 = 71
    LEIAT502 = 72
    LEIAT503 = 73
    LEIAT504 = 74
    LEIAT504GG = 75
    LEIATX1230 = 76
    LEIATX1230_GNSS = 77
    LEIATX1230GG = 78
    LEIAX1202 = 79
    LEIGG02PLUS = 80
    LEIGS08 = 81
    LEIGS09 = 82
    LEIGS12 = 83
    _3S_02_TSADM = 84
    _3S_02_TSATE = 85
    LEIGS15 = 86
    LEIMNA950GG = 87
    LEISR299_INT = 88
    LEISR399_INT = 89
    LEISR399_INTA = 90
    MAC4647942 = 91
    MPL_WAAS_2224NW = 92
    MPL_WAAS_2225NW = 93
    MPLL1_L2_SURV = 94
    NAVAN2004T = 95
    NAVAN2008T = 96
    NAX3G_C = 97
    NOV_WAAS_600 = 98
    NOV501 = 99
    NOV501_CR = 100
    NOV502 = 101
    NOV502_CR = 102
    NOV503_CR = 103
    NOV531 = 104
    NOV531_CR = 105
    NOV600 = 106
    NOV702 = 107
    NOV702GG = 108
    NOV750_R4 = 109
    SEN67157596_CR = 110
    SOK_RADIAN_IS = 111
    SOK502 = 112
    SOK600 = 113
    SOK702 = 114
    SPP571212238_GP = 115
    STXS9SA7224V3_0 = 116
    TOP700779A = 117
    TOP72110 = 118
    TPSCR_G3 = 119
    TPSCR3_GGD = 120
    TPSCR4 = 121
    TPSG3_A1 = 122
    TPSHIPER_GD = 123
    TPSHIPER_GGD = 124
    TPSHIPER_LITE = 125
    TPSHIPER_PLUS = 126
    TPSLEGANT_G = 127
    TPSLEGANT2 = 128
    TPSLEGANT3_UHF = 129
    TPSODYSSEY_I = 130
    TPSPG_A1 = 131
    TPSPG_A1_GP = 132
    TRM14177_00 = 133
    TRM14532_00 = 134
    TRM14532_10 = 135
    TRM22020_00_GP = 136
    TRM22020_00_GP = 137
    TRM23903_00 = 138
    TRM27947_00_GP = 139
    TRM27947_00_GP = 140
    TRM29659_00 = 141
    TRM33429_00_GP = 142
    TRM33429_00_GP = 143
    TRM33429_20_GP = 144
    TRM39105_00 = 145
    TRM41249_00 = 146
    TRM41249USCG = 147
    TRM4800 = 148
    TRM55971_00 = 149
    TRM57970_00 = 150
    TRM57971_00 = 151
    TRM5800 = 152
    TRM59800_00 = 153
    TRM59800_80 = 154
    TRM59900_00 = 155
    TRMR8_GNSS = 156
    TRMR8_GNSS3 = 157
    ASH701023_A = 158
    CHCC220GR = 159
    CHCC220GR2 = 160
    CHCX91_S = 161
    GMXZENITH10 = 162
    GMXZENITH20 = 163
    GMXZENITH25 = 164
    GMXZENITH25PRO = 165
    GMXZENITH35 = 166
    JAVRINGANT_G5T = 167
    JAVTRIUMPH_1M = 168
    JAVTRIUMPH_1MR = 169
    JAVTRIUMPH_2A = 170
    JAVTRIUMPH_LSA = 171
    JNSCR_C146_22_1 = 172
    JPSREGANT_DD_E1 = 173
    JPSREGANT_DD_E2 = 174
    JPSREGANT_SD_E1 = 175
    JPSREGANT_SD_E2 = 176
    LEIAR20 = 177
    LEIGG03 = 178
    LEIGS08PLUS = 179
    LEIGS14 = 180
    LEIICG60 = 181
    NOV533_CR = 182
    NOV703GGG_R2 = 183
    NOV750_R5 = 184
    RNG80971_00 = 185
    SEPCHOKE_B3E6 = 186
    SEPCHOKE_MC = 187
    STXS10SX017A = 188
    STXS8PX003A = 189
    STXS9PX001A = 190
    TIAPENG2100B = 191
    TIAPENG2100R = 192
    TIAPENG3100R1 = 193
    TIAPENG3100R2 = 194
    TPSCR_G5 = 195
    TPSG5_A1 = 196
    TPSPN_A5 = 197
    TRM55970_00 = 198
    TRMR10 = 199
    TRMR4_3 = 200
    TRMR6_4 = 201
    TRMR8_4 = 202
    TRMR8S = 203
    TRMSPS985 = 204
    AERAT1675_120 = 205
    ITT3750323 = 206
    NOV702GGL = 207
    NOV704WB = 208
    ARFAS1FS = 209
    CHAPS9017 = 210
    CHCI80 = 211
    GMXZENITH15 = 212
    HXCCGX601A = 213
    IGAIG8 = 214
    LEICGA60 = 215
    LEIGS15_R2 = 216
    LEIGS16 = 217
    MVEGA152GNSSA = 218
    SEPALTUS_NR3 = 219
    SJTTL111 = 220
    SOKGCX3 = 221
    SOKSA500 = 222
    STHCR3_G3 = 223
    STXS9I = 224
    TPSCR_G5C = 225
    TPSHIPER_HR = 226
    TPSHIPER_HR_PS = 227
    TRM105000_10 = 228
    TRM115000_00 = 229
    TRM115000_10 = 230
    TRMR2 = 231
    TWIVP6000 = 232
    TWIVP6050_CONE = 233
    JAVTRIUMPH_2A_G = 234
    JAVTRIUMPH_2A_P = 235
    LEIGS18 = 236
    LEIGG04PLUS = 237
    STXS800 = 238
    STXS800A = 239
    NOV850 = 240
    TRM159800_00 = 241
    TRM159900_00 = 242
    LEIGG04 = 243
    LEIICG70 = 244
    JAV_GRANT_G3T_G = 245
    JAVGRANT_G5T_GP = 246
    JAVTRIUMPH_3A = 247
    TPSHIPER_VR = 248
    TRM59800_00C = 249
    TRM59800_99 = 250
    TRMR10_2 = 251
    TRMR12 = 252
    TRMSPS986 = 253
    TWIVC6050 = 254
    TWIVC6150 = 255
    GMXZENITH60 = 256
    ASH701945B_99 = 257
    LEIAS11 = 258
    UNKNOWN = 999
    USER_ANTENNA_1 = 1001
    USER_ANTENNA_2 = 1002
    USER_ANTENNA_3 = 1003
    USER_ANTENNA_4 = 1004
    USER_ANTENNA_5 = 1005

class RTKQuality(Enum):
    NORMAL = 1
    NORMAL2 = 2
    NORMAL3 = 3
    EXTRA_SAFE = 4

class RTKAssistStatus(Enum):
    UNAVAILABLE = 0
    COAST = 1
    ASSIST = 2

class DatumDataStore(Enum):
    SAVE = 1
    DELETE = 2

class USBMode(Enum):
    DEVICE = 0
    HOST = 1
    OTG = 2
    INVALID = 3
    NONE = 4
    TRANSITION = 5

class USBDetectionType(Enum):
    NONE = 1
    USBSTICK = 2
    PC = 3
    ERROR = 4

class SolType(Enum):
    NONE = 0
    FIXEDPOS = 1
    FIXEDHEIGHT = 2
    FIXEDVEL = 3
    FLOATCONV = 4
    WIDELANE = 5
    NARROWLANE = 6
    DOPPLER_VELOCITY = 8
    SINGLE = 16
    PSRDIFF = 17
    WAAS = 18
    PROPAGATED = 19
    OMNISTAR = 20
    L1_FLOAT = 32
    IONOFREE_FLOAT = 33
    NARROW_FLOAT = 34
    L1L2_FLOAT = 35
    L1L2_INT = 46
    L1L2_INT_VERIFIED = 47
    L1_INT = 48
    WIDE_INT = 49
    NARROW_INT = 50
    RTK_DIRECT_INS = 51
    INS_SBAS = 52
    INS_PSRSP = 53
    INS_PSRDIFF = 54
    INS_RTKFLOAT = 55
    INS_RTKFIXED = 56
    INS_OMNISTAR = 57
    INS_OMNISTAR_HP = 58
    INS_OMNISTAR_XP = 59
    OMNISTAR_HP = 64
    OMNISTAR_XP = 65
    CDGPS = 66
    EXT_CONSTRAINED = 67
    PPP_CONVERGING = 68
    PPP = 69
    OPERATIONAL = 70
    WARNING = 71
    OUT_OF_BOUNDS = 72
    INS_PPP_CONVERGING = 73
    INS_PPP = 74
    PPP_PLUS = 75
    INS_PPP_PLUS = 76
    PPP_BASIC_CONVERGING = 77
    PPP_BASIC = 78
    INS_PPP_BASIC_CONVERGING = 79
    INS_PPP_BASIC = 80

class NVM_DataType(Enum):
    STANDARD = 0
    COMMAND = 1
    GPSALMANAC = 2
    GPSEPHEM = 3
    GLOEPHEM = 4
    MODEL = 5
    NEWMODEL = 6
    MSGDEFN = 7
    CHANCONFIG = 8
    RSVD = 9
    USERDATA = 10
    CLKCALIBRATION = 11
    OMNIALMANAC = 12
    OMNIDATA = 13
    OMNISITES = 14
    OMNISUBSCRIPTION = 15
    OMNIHPKEY = 16
    OMNIHPDATA = 17
    OMNIHPCONFIG = 18
    OMNIHPSUBSCRIPTION = 19
    SBASALMANAC = 20
    LAST_POSITION = 21
    VEHICLE_BODY_R = 22
    INS_HOT_START = 23
    INS_LEVER_ARM = 24
    USERVERINFO = 25
    ENCLOSURE = 26
    TESTPACKET = 27
    HPSEED = 28
    STATUS_INFO = 29
    OMNISERVICE = 30
    GLOALMANAC = 31
    VISIONREFFUNC = 32
    LB2_ATX_TYPE = 33
    PRXSTATUS = 34
    OMNIVISDATA = 35
    FIX_COMMAND = 36
    UTC_LEAP_SEC = 37
    GALFNAV_EPH = 39
    GALINAV_EPH = 40
    GALFNAV_ALM = 45
    GALINAV_ALM = 46
    BASE_WEEK = 47
    OPTION_BITS = 48
    CHANCFG_INUSE = 49
    PROFILEINFO = 52
    STANDARD_EXCEPT_USER_CFG = 53
    QZSSALMANAC = 54
    QZSSEPHEMERIS = 55
    PPPSEED = 56
    BDSALMANAC = 57
    BDSEPHEMERIS = 58
    BDSALMANACHEALTH = 59
    USER_ACCOUNTS = 60
    NVM_BLUETOOTH_DATA = 61
    GPSCARD2 = 62
    WIFI_REGULATORY_DOMAIN = 63
    ETHERNET = 64
    WIFI_MODULE_VERSION = 65
    BT_MODULE_VERSION = 66
    CELL_MODULE_VERSION = 67
    VERIPOS_DATA = 68
    NVM_DYNAMIC_CHAN_CONFIG = 69
    RADIO_MODULE_VERSION = 70
    WWW_CONTENT_VERSION = 71
    EXTENSION_MODULE_VERSION = 72
    WEBUI_SESSION_DATA = 73
    VERIPOS_STATIONS = 74
    COLDSTART = 76
    WARMSTART = 77
    SURVEY_POSITION_ARRAY = 78
    GPS_SATELLITE_ANTENNA_PCV = 79
    GLONASS_SATELLITE_ANTENNA_PCV = 80
    MFGTEST_DATA = 81
    USBCONFIG = 82
    INSSEED = 83
    SATELLITE_ANTENNA_PCV = 84
    SRTK_SUBSCRIPTIONS = 85
    LBAND_CENTER_FREQUENCY = 86
    NAVICEPHEMERIS = 87
    NAVICALMANAC = 88
    DUALANTENNAPVT_MODE = 89
    USER_ANTENNA = 90
    SMCC = 91
    TILT = 92
    USER_DATUM = 93
    USER_DATUM_TRANSFORMATION = 94
    VERIPOSRTCMDATA_TYPE41 = 95
    SENSITIVE_DATA = 96
    SKCALIBRATIONS = 97
    SRTK_KEY = 98
    BDSBCNAV1EPHEMERIS = 99
    BDSBCNAV2EPHEMERIS = 100
    BDSBCNAV3EPHEMERIS = 101
    INS_LOGISTICS = 102

class FileTransferOperation(Enum):
    COPY = 1
    MOVE = 2
    CANCEL = 3

class IPService(Enum):
    NO_PORT = 0
    FTP_SERVER = 1
    WEB_SERVER = 2
    SECURE_ICOM = 3
    SOFTLOADFILE = 4

class SafeModeStatus(Enum):
    SAFE_MODE_OK = 0
    SAFE_MODE_WARNING = 1
    SAFE_MODE_DISABLE_SATELLITE_DATA = 2
    SAFE_MODE_DISABLE_NON_COMMUNICATION_NVM = 3
    SAFE_MODE_DISABLE_ALL_NVM = 4
    SAFE_MODE_DISABLE_AUTH = 5
    SAFE_MODE_FAILED = 6
    SAFE_MODE_UNEXPECTED_MAIN_FIRMWARE = 7
    SAFE_MODE_DISABLE_STARTUP_EMMC_CHKDSK = 8

class OnOff(Enum):
    OFF = 0
    ON = 1
    AUTO = 2
    DEFAULT = 3

class Enable(Enum):
    DISABLE = 0
    ENABLE = 1

class UndulationType(Enum):
    TABLE = 0
    USER = 1
    OSU89B = 2
    EGM96 = 3
    ZERO = 4

class FeatureStatus(Enum):
    AUTHORIZED = 0
    UNAUTHORIZED = 1
    _0HZ = 2
    _1HZ = 3
    _5HZ = 4
    _10HZ = 5
    _20HZ = 6
    _50HZ = 7
    _100HZ = 8
    RATE_INVALID = 9
    _3KM = 10
    _5KM = 11
    _10KM = 12
    UNLIMITED = 13
    BASELINE_INVALID = 14
    STANDARD = 15
    INS_STANDARD_HEAVE = 16
    INS_STANDARD_GNP10 = 17
    INS_STANDARD_AMRAAM = 18
    INS_STANDARD_EXTERNAL_AIDING = 19
    COMMERCIAL_MEMS = 20
    TACTICAL = 21
    HIGH_GRADE_TACTICAL = 22
    NAVIGATION = 23
    INS_STANDARD_RELATIVE = 24
    SINGLE = 25
    DUAL = 26
    RESERVED1 = 27
    RESERVED2 = 28
    INS_STANDARD_PROFILES_PLUS = 29
    LITE = 30
    CONSUMER_MEMS = 33
    FEATURE_1 = 34
    FEATURE_2 = 35
    FEATURE_3 = 36
    RADIO_TX = 37
    GLIDE = 38
    TILT = 39
    GLIDE_STEADYLINE = 40
    GLIDE_STEADYLINE_CAN = 41
    STATUS_INVALID = 999

class SampleBufferCollectionStatus(Enum):
    COMPLETE = 0
    COMPLETE_DELAY = 1
    COMPLETE_BADTIMETAG = 2
    REJECT_BY_DELAY = 3
    REJECT_BADTIMETAG = 4

class PosAveStatus(Enum):
    OFF = 0
    INPROGRESS = 1
    COMPLETE = 2

class DMISource(Enum):
    EXT_COUNT = 0
    EXT_VELOCITY = 1
    IMU = 2
    ENCLOSURE = 3
    DELTA = 4

class NavStatus(Enum):
    GOOD = 0
    NOVELOCITY = 1
    BADNAV = 2
    FROM_TO_SAME = 3
    TO_CLOSE_TO_TO = 4
    ANTIPODAL_WAYPTS = 5

class SBASTestMode(Enum):
    NONE = 0
    ZEROTOTWO = 1
    IGNOREZERO = 2
    WAAS = 3
    EGNOS = 4
    MSAS = 5

class WifiStatus(Enum):
    STARTUP = 0
    OFF = 1
    ON = 2
    CONFIGURING_ACCESSPOINT = 3
    ACCESSPOINT_OPERATIONAL = 4
    CONFIGURING_CLIENT = 5
    CLIENT_OPERATIONAL = 6
    BOOTING_UP = 7
    BOOTUP_COMPLETE = 8
    UPGRADE_REQUIRED = 9
    UPGRADING_FIRMWARE = 10
    UPGRADING_FIRMWARE_10 = 11
    UPGRADING_FIRMWARE_20 = 12
    UPGRADING_FIRMWARE_30 = 13
    UPGRADING_FIRMWARE_40 = 14
    UPGRADING_FIRMWARE_50 = 15
    UPGRADING_FIRMWARE_60 = 16
    UPGRADING_FIRMWARE_70 = 17
    UPGRADING_FIRMWARE_80 = 18
    UPGRADING_FIRMWARE_90 = 19
    FIRMWARE_UPGRADE_COMPLETE = 20
    ERROR = 21
    CONFIGURING_CONCURRENT = 22
    CONCURRENT_OPERATIONAL = 23
    CONNECTING_TO_AP = 24
    CONNECTED_TO_AP = 25
    CONNECTION_FAILURE = 26
    CONFIGURING_NETWORK_PARAMETERS = 27
    CONNECTION_REFUSED = 28
    PREFERRED_NETWORK_MISCONFIGURED = 29
    CONCURRENT_CONNECTING_TO_AP = 30
    CONCURRENT_CONFIGURING_NETWORK_PARMS = 31
    CONCURRENT_CONNECTED_TO_AP = 32
    DISCONNECTING_FROM_AP = 33
    CONCURRENT_DISCONNECTING_FROM_AP = 34
    BOOTUP_CONNECTING_TO_WIFI_MODULE = 35
    BOOTUP_ERROR = 36
    REJOIN_IN_PROGRESS = 37

class SpoofCalibrationResult(Enum):
    PASS = 0
    FAIL = 1
    INPROGRESS = 2
    NONE = 3

class INSOffset(Enum):
    INVALID = 0
    ANT1 = 1
    ANT2 = 2
    EXTERNAL = 3
    USER = 4
    MARK1 = 5
    MARK2 = 6
    GIMBAL = 7
    ALIGN = 8
    MARK3 = 9
    MARK4 = 10
    RBV = 11
    RBM = 12
    ENCLOSURE = 13
    DMI = 14

class PortProtocol(Enum):
    RS232 = 0
    RS422 = 1
    N_A = 2

class TrackSignal(Enum):
    NONE = 0
    GPSL2 = 1
    GPSL2P = 2
    GPSL2C = 3
    GPSL5 = 4
    GPSL1C = 5
    SBASL5 = 6
    GLOL2 = 7
    GLOL2P = 8
    GLOL2C = 9
    GLOL3 = 10
    GALE5A = 11
    GALE5B = 12
    GALALTBOC = 13
    GALE6 = 14
    QZSSL2C = 15
    QZSSL5 = 16
    QZSSL1C = 17
    QZSSL6 = 18
    BEIDOUB1C = 19
    BEIDOUB2 = 20
    BEIDOUB3 = 21
    BEIDOUB2B = 22
    BEIDOUB2A = 23

class VeriposRegionRestrictionStatus(Enum):
    UNKNOWN = 0
    IN_REGION = 1
    OUT_OF_REGION = 2

class INSProfile(Enum):
    DEFAULT = 0
    LAND = 1
    MARINE = 2
    FIXEDWING = 3
    FOOT = 4
    VTOL = 5
    RAIL = 6
    AGRICULTURE = 7
    LAND_PLUS = 33
    MARINE_PLUS = 34
    LAND_BASIC = 65
    MARINE_BASIC = 66
    FIXEDWING_BASIC = 67
    FOOT_BASIC = 68
    VTOL_BASIC = 69
    RAIL_BASIC = 70

class CNoUpdateRate(Enum):
    DEFAULT = 0
    _20HZ = 1

class GALE6CodeType(Enum):
    E6B = 0
    E6C = 1

class PPPSeedMode(Enum):
    CLEAR = 0
    SET = 1
    STORE = 2
    RESTORE = 3
    AUTO = 4
    MANUAL = 5

class SpectralAnalysisSource(Enum):
    OFF = 0
    PREDECIMATION = 1
    POSTDECIMATION = 2
    POSTFILTER = 3

class PPSEnable(Enum):
    DISABLE = 0
    ENABLE = 1
    ENABLE_FINETIME = 2
    ENABLE_FINETIME_MINUTEALIGN = 3

class BestVelType(Enum):
    BESTPOS = 1
    DOPPLER = 2
    INS = 3

class MassStorageDevice(Enum):
    SD = 0
    USBSTICK = 1
    RAMDRIVE = 2
    DEFAULT_NO_STORAGE = 3
    INTERNAL_FLASH = 4

class DopplerWindowMode(Enum):
    AUTO = 0
    USER = 1

class FreqOutEnable(Enum):
    DISABLE = 0
    ENABLE = 1
    ENABLESYNC = 2

class Dynamics(Enum):
    AIR = 0
    LAND = 1
    FOOT = 2
    AUTO = 3

class DGPSType(Enum):
    RTCM = 0
    RTCA = 1
    CMR = 2
    SBAS = 5
    RTK = 6
    AUTO = 10
    NONE = 11
    FKP = 12
    RTCMV3 = 13
    NOVATELX = 14
    VERIPOS = 15

class TrackSV(Enum):
    NEVER = 1
    GOODHEALTH = 2
    ANYHEALTH = 3
    ALWAYS = 4

class SolStatus(Enum):
    SOL_COMPUTED = 0
    INSUFFICIENT_OBS = 1
    NO_CONVERGENCE = 2
    SINGULARITY = 3
    COV_TRACE = 4
    TEST_DIST = 5
    COLD_START = 6
    V_H_LIMIT = 7
    VARIANCE = 8
    RESIDUALS = 9
    DELTA_POS = 10
    NEGATIVE_VAR = 11
    OLD_SOLUTION = 12
    INTEGRITY_WARNING = 13
    INS_INACTIVE = 14
    INS_ALIGNING = 15
    INS_BAD = 16
    IMU_UNPLUGGED = 17
    PENDING = 18
    INVALID_FIX = 19
    UNAUTHORIZED = 20
    ANTENNA_WARNING = 21
    INVALID_RATE = 22
    INS_AIDED = 23

class INSSeedStatus(Enum):
    NOT_INITIALIZED = 0
    INVALID = 1
    FAILED = 2
    PENDING = 3
    INJECTED = 4
    IGNORED = 5
    ERRORMODELINJECTED = 6

class ProgFilterMode(Enum):
    NOTCHFILTER = 0
    BANDPASSFILTER = 1
    NONE = 2

class CanProtocol(Enum):
    NONE = 0
    RAW = 1
    J1939 = 2
    NMEA2000 = 3
    ISO15765 = 4
    ISO11783 = 5

class SurveyPosition(Enum):
    SAVE = 1
    DELETE = 2

class DMIEvent(Enum):
    OFF = 1
    EVENT1 = 2
    EVENT2 = 3
    EVENT3 = 4
    EVENT4 = 5

class DiskFullAction(Enum):
    STOP = 0
    OVERWRITE = 1

class FileSystemEntryType(Enum):
    NONE = 0
    FILE = 1
    DIR = 2

class HandShake(Enum):
    N = 0
    XON = 1
    CTS = 2

class UTCTimeStatus(Enum):
    INVALID = 0
    VALID = 1
    WARNING = 2

class J1939Node(Enum):
    NONE = 0
    NODE1 = 1
    NODE2 = 2
    NODE3 = 3
    NODE4 = 4
    NODE5 = 5
    NODE6 = 6
    NODE7 = 7
    NODE8 = 8
    NODE9 = 9
    NODE10 = 10

class ITFrequency(Enum):
    NONE = 0
    ALL = 1
    L1 = 2
    L2 = 3
    L5 = 4

class J1939NodeStatus(Enum):
    DISABLED = 1
    CLAIMING = 2
    CLAIMED = 3
    FAILED = 4

class SignatureStatus(Enum):
    NONE = 1
    INVALID = 2
    VALID = 3
    DEVELOPER = 4
    HIGH_SPEED = 5

class NMEABeidouTalkerID(Enum):
    GB = 0
    BD = 1

class RelINSOutput(Enum):
    INVALID = 0
    ROVER = 1
    MASTER = 2
    ECEF = 3
    LOCALLEVEL = 4

class AssignSystem(Enum):
    GPSL1 = 0
    GPSL1L2 = 1
    ALL = 3
    WAASL1 = 4
    GPSL1L2C = 6
    GPSL1L2AUTO = 7
    GLOL1L2 = 8
    GLOL1 = 10
    GPS = 99
    SBAS = 100
    GLONASS = 101
    GALILEO = 102
    BEIDOU = 103
    QZSS = 104
    NAVIC = 105

class FrequencyPlan(Enum):
    DEFAULT = 0
    ALTERNATIVE = 1

class SteadyLineCommand(Enum):
    DISABLE = 0
    MAINTAIN = 1
    TRANSITION = 2
    RESET = 3
    PREFER_ACCURACY = 4
    UAL = 5

class SpoofCalibrationCmdMode(Enum):
    VOID = 0
    START = 1
    MANU = 2

class IMUType(Enum):
    UNKNOWN = 0
    HG1700_AG11 = 1
    HG1700_AG12 = 2
    HG1700_AG13 = 3
    HG1700_AG17 = 4
    HG1900_CA29 = 5
    BAE_MEMS = 6
    MICRO_IRU = 7
    LN200 = 8
    LN200_400HZ = 9
    DEPRECATED = 10
    HG1700_AG58 = 11
    HG1700_AG62 = 12
    IMAR_FSAS = 13
    IGI_64_037HZ = 14
    SEATEX_MRU5 = 15
    KVH_COTS = 16
    GLADIATOR_LANDMARK20 = 17
    LN200_AMRAAM = 18
    LITEF_LCI1 = 19
    HG1930_AA99 = 20
    MICROIRS = 21
    GENERIC = 22
    IMAR_FSAS_400HZ = 23
    GLADIATOR_LANDMARK30 = 24
    GLADIATOR_LANDMARK40 = 25
    ISA100C = 26
    HG1900_CA50 = 27
    HG1930_CA50 = 28
    TAMAM_90V = 29
    ADIS16485 = 30
    ADIS16488 = 31
    STIM300 = 32
    KVH_1750 = 33
    ISA100 = 34
    LCI100C = 35
    LCI100C_500HZ = 36
    IMAR_FR = 37
    ISA100_400HZ = 38
    ISA100C_400HZ = 39
    HG1700_AG71 = 40
    EPSON_G320 = 41
    EPSON_G362P = 42
    ADIS16445 = 43
    ADIS16460 = 44
    KVH_1725 = 45
    KVH_1775 = 46
    LODESTAR = 47
    HG9900 = 48
    BOSCH_MM7 = 49
    BOSCH_SMI130 = 50
    EPSON_V340 = 51
    LITEF_MICROIMU = 52
    GENERIC_LOW = 53
    ADIS16490 = 54
    INVENSENSE_ICM20602 = 55
    STIM300D = 56
    INVENSENSE_IAM20680 = 57
    HG4930_AN01 = 58
    GENERIC_TYPEA = 59
    ADIS16495 = 60
    EPSON_G370 = 61
    EPSON_G320_200HZ = 62
    ST_ASM330LHH = 63
    GENERIC_TYPEB = 64
    GENERIC_TYPEC = 65
    GENERIC_TYPED = 66
    GENERIC_TYPEE = 67
    HG4930_AN04 = 68
    HG4930_AN04_400HZ = 69
    LITEF_MICROIMU_400HZ = 70
    LITEF_MICROIMUD_400HZ = 71
    HG4930_CN31 = 72
    HG4930_CA31 = 73
    IMU_UNKNOWN = 32768
    IMU_HG1700_AG11 = 32769
    IMU_HG1700_AG17 = 32772
    IMU_HG1900_CA29 = 32773
    IMU_LN200 = 32776
    IMU_LN200_400HZ = 32777
    IMU_HG1700_AG58 = 32779
    IMU_HG1700_AG62 = 32780
    IMU_IMAR_FSAS = 32781
    IMU_KVH_COTS = 32784
    IMU_LN200_AMRAAM = 32786
    IMU_HG1930_AA99 = 32788
    IMU_MICROIRS = 32789
    IMU_GENERIC = 32790
    IMU_IMAR_FSAS_400HZ = 32791
    IMU_ISA100C = 32794
    IMU_HG1900_CA50 = 32795
    IMU_HG1930_CA50 = 32796
    IMU_TAMAM_90V = 32797
    IMU_ADIS16488 = 32799
    IMU_STIM300 = 32800
    IMU_KVH_1750 = 32801
    IMU_ISA100 = 32802
    IMU_LCI100C = 32803
    IMU_LCI100C_500HZ = 32804
    IMU_IMAR_FR = 32805
    IMU_ISA100_400HZ = 32806
    IMU_ISA100C_400HZ = 32807
    IMU_HG1700_AG71 = 32808
    IMU_EPSON_G320 = 32809
    IMU_EPSON_G362P = 32810
    IMU_ADIS16445 = 32811
    IMU_ADIS16460 = 32812
    IMU_LODESTAR = 32815
    IMU_BOSCH_MM7 = 32817
    IMU_BOSCH_SMI130 = 32818
    IMU_EPSON_V340 = 32819
    IMU_LITEF_MICROIMU = 32820
    IMU_GENERIC_LOW = 32821

class INSUpdate(Enum):
    POS = 0
    ZUPT = 1
    PSR = 2
    ADR = 3
    DOPPLER = 4
    ALIGN = 5
    DMI = 6
    VEL = 7
    DR = 8
    PWU = 9
    EXTPOS = 10
    EXTVEL = 11
    EXTATT = 12
    EXTHDG = 13
    EXTHGT = 14
    COG = 15
    POS2 = 16
    RESIDUAL = 17

class SignalType(Enum):
    GPSL1CW = 32
    GPSL1CA = 33
    GPSL1P = 34
    GPSL1Y = 35
    GPSL1CD = 46
    GPSL1CP = 47
    GPSL1CX = 48
    GPSL1BIT = 63
    GPSL2Y = 68
    GPSL2C = 69
    GPSL2P = 70
    GPSL2CW = 73
    GPSL2CL = 75
    GPSL2CX = 76
    GPSL2CA = 81
    GPSL2BIT = 95
    GPSL5 = 103
    GPSL5TEST = 104
    GPSL5CW = 106
    GPSL5I = 109
    GPSL5X = 114
    GPSL5BIT = 127
    GLOL1CW = 2176
    GLOL1CA = 2177
    GLOL1P = 2178
    GLOL1BIT = 2207
    GLOL2CA = 2211
    GLOL2P = 2212
    GLOL2CW = 2213
    GLOL2BIT = 2239
    GLOL3 = 2662
    GLOL3CW = 2663
    GLOL3BIT = 2687
    SBASL1 = 4129
    SBASL5 = 4194
    SBASL5Q = 4195
    SBASL5_I_Q_ = 4196
    GALE1 = 10433
    GALE1TEST = 10438
    GALE1B = 10443
    GALE1A = 10448
    GALE1X = 10449
    GALE1Z = 10450
    GALE5A = 10466
    GALE5ATEST = 10471
    GALE5AI = 10479
    GALE5AX = 10487
    GALE5BCW = 10496
    GALE5B = 10499
    GALE5BTEST = 10504
    GALE5BI = 10509
    GALE5BX = 10518
    GALE5BBIT = 10527
    GALALTBOC = 10532
    GALALTBOCTEST = 10537
    GALALTBOCCW = 10538
    GALALTBOCI = 10542
    GALALTBOCX = 10552
    GALALTBOCBIT = 10559
    GALE6C = 10565
    GALE6CW = 10570
    GALE6B = 10572
    GALE6A = 10579
    GALE6X = 10580
    GALE6Z = 10581
    BDSB1ICW = 12672
    BDSB1D1 = 12673
    BDSB1D2 = 12674
    BDSB1D1Q = 12677
    BDSB1D1X = 12678
    BDSB1D2Q = 12681
    BDSB1D2X = 12682
    BDSB1BIT = 12703
    BDSB2D1 = 12803
    BDSB2D2 = 12804
    BDSB2D1Q = 12807
    BDSB2D1X = 12808
    BDSB2D2Q = 12811
    BDSB2D2X = 12812
    BDSB3CW = 12864
    BDSB3D1 = 12877
    BDSB3D1Q = 12878
    BDSB3D1X = 12879
    BDSB3D2 = 12880
    BDSB3D2Q = 12881
    BDSB3D2X = 12882
    BDSB3BIT = 12895
    BDSB1C = 12979
    BDSB1CD = 12982
    BDSB1CX = 12983
    BDSB2A = 13012
    BDSB2AD = 13016
    BDSB2AX = 13017
    BDSB2BI = 13077
    QZSSL1CA = 14753
    QZSSL1CD = 14759
    QZSSL1CP = 14760
    QZSSL1CX = 14761
    QZSSL2C = 14787
    QZSSL2CL = 14797
    QZSSL2CX = 14798
    QZSSL5 = 14820
    QZSSL5I = 14821
    QZSSL5X = 14822
    QZSSL6D = 14890
    QZSSL6P = 14891
    QZSSL6X = 14892
    QZSSL6E = 14893
    QZSSL6Z = 14894
    LBANDCW = 16736
    LBAND = 16737
    NAVICL5SPS = 19073
    NONE = 65535

class INSSeedValidity(Enum):
    INVALID = 0
    ALLVALID = 1
    ERRORMODELVALID = 2

class Region(Enum):
    NONE = 0
    US = 1
    EU = 2
    AU = 3
    JP = 4
    NZ = 5
    BR = 6

class NMEATalkerID(Enum):
    GP = 0
    AUTO = 1
    GP_HE = 2

class MagVarType(Enum):
    AUTO = 0
    CORRECTION = 1

class LuaOutSource(Enum):
    STDOUT = 1
    STDERR = 2

class NMEAVersion(Enum):
    V31 = 0
    V41 = 1
    V21 = 2

class IonoCorrType(Enum):
    NONE = 0
    KLOBUCHAR = 1
    GRID = 2
    L1L2 = 3
    AUTO = 4
    UNKNOWN = 15
    MIXED = 16
    PSRDIFF = 17

class RTKTrackingControl(Enum):
    DISABLE = 0
    AUTO = 1

class EthernetProtocol(Enum):
    DISABLED = 1
    TCP = 2
    UDP = 3
    TCP_SERVER = 4
    TCP_NAGLE = 5

class I2CBitRate(Enum):
    _100K = 1
    _400K = 2

class EthernetSpeed(Enum):
    AUTO = 1
    _10 = 2
    _100 = 3

class I2COperationMode(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    SHUTDOWN = 3

class VeriposLocalAreaStatus(Enum):
    DISABLED = 0
    WAITING_FOR_POSITION = 1
    RANGE_CHECK = 16
    IN_RANGE = 129
    OUT_OF_RANGE = 130
    POSITION_TOO_OLD = 255

class EmulatedRadarResponseMode(Enum):
    _1 = 1
    _2 = 2
    _500 = 500
    _1000 = 1000
    _2000 = 2000

class Responses(Enum):
    RESPONSE_OK = 1
    LOG_DOES_NOT_EXIST = 2
    INSUFFICIENT_RESOURCES = 3
    RESPONSE_VERIFY_FAIL = 4
    RESPONSE_FAIL = 5
    INVALID_MESSAGE_ID = 6
    INVALID_MESSAGE_FORMAT = 7
    INVALID_CHECKSUM = 8
    RESPONSE_MISSING_REQUIRED_FIELD = 9
    RESPONSE_INDEX_OUT_OF_RANGE = 10
    RESPONSE_PARAMETER_OUT_OF_RANGE = 11
    MSG_ALREADY_EXISTS = 12
    RESPONSE_INVALID_TOKEN = 13
    INVALID_TRIGGER = 14
    AUTH_TABLE_FULL = 15
    AUTH_INVALID_DATE = 16
    AUTH_INVALID_PARAMETER = 17
    AUTH_NO_MATCH = 18
    NO_MODEL = 19
    INVALID_CHANNEL = 20
    RESPONSE_INVALID_RATE = 21
    RX_STATUS_NO_MASK = 22
    CHANNEL_LOCKOUT = 23
    INVALID_INJECT_TIME = 24
    INVALID_COM_PORT = 25
    INVALID_BINARY_MSG = 26
    INVALID_PRN = 27
    PRN_NOT_LOCKED_OUT = 28
    PRN_LOCKOUT_LIST_FULL = 29
    PRN_ALREADY_LOCKED_OUT = 30
    RESPONSE_TIME_OUT = 31
    RESPONSE_PDC_TIME_OUT = 32
    UNKNOWN_PORT = 33
    INVALID_HEX_STRING = 34
    INVALID_BAUD_RATE = 35
    RESPONSE_PARAMETER_MSG_INVALID = 36
    PDC_COMMAND_FAILED = 37
    SAVECONFIG_FAIL = 38
    SAVECONFIG_FULL = 39
    NVM_NOT_FAILED = 40
    RESPONSE_INVALID_OFFSET = 41
    FILE_ALT_NAME = 42
    FILE_CONFLICT = 43
    FILE_NOT_FOUND = 44
    FILE_OPEN = 45
    FILE_NOT_OPEN = 46
    FILENAME_INVALID = 47
    CHANNEL_IN_USE = 48
    CHANNELS_FULL = 49
    FILE_CLOSE_FAIL = 50
    NO_DISK = 51
    DISK_ERROR = 52
    DISK_FULL = 53
    GROUP_NOT_FOUND = 54
    GROUP_NAME_CONFLICT = 55
    GROUP_TABLE_EMPTY = 56
    GROUP_TABLE_FULL = 57
    SPECS_EMPTY = 58
    SPECS_FULL = 59
    GROUP_LOG_NOT_FOUND = 60
    GROUP_LOG_CONFLICT = 61
    GROUP_USE_INACATIVE = 62
    SCHED_OVERLAP = 63
    SCHED_EMPTY = 64
    SCHED_FULL = 65
    SCHED_MIN_INTERVAL = 66
    SCHED_ENTRY_INTERVAL = 67
    SCHED_NOT_FOUND = 68
    START_TIME_SYNTAX = 69
    END_TIME_SYNTAX = 70
    NOT_ON_SITE = 71
    SITE_OCCUPIED = 72
    PROJECT_DEFINED = 73
    NVM_WRITE_FAIL = 74
    NVM_READ_FAIL = 75
    ACTIVE_SCHEDULE_ENTRY = 76
    INVALID_INPUT = 77
    NVM_MSGDEF_FULL = 78
    USERMSG_DECRYPT_FAIL = 79
    HM_MEMORY_ERROR = 80
    HM_CRC_ERROR = 81
    HM_NO_MODEL = 82
    HM_CANT_INITIALIZE = 83
    PRECISE_TIME_KNOWN = 84
    COARSE_TIME_ALREADY_SET = 85
    INS_INACTIVE = 86
    MSG_CREATE_FAILED = 87
    APPLICATION_NOT_FOUND = 88
    APPLICATION_NOT_RUNNING = 89
    APPLICATION_RUNNING = 90
    APPLICATION_ELF_ERROR = 91
    SOFTLOAD_BAD_SREC = 95
    SOFTLOAD_BAD_MODULE = 96
    SOFTLOAD_OUTOFMEMORY = 97
    SOFTLOAD_BAD_ERASE = 98
    SOFTLOAD_BAD_WRITE = 99
    SOFTLOAD_BAD_SRC = 100
    SOFTLOAD_BAD_AUTH = 101
    FLASH_BAD_WRITE = 102
    FLASH_BAD_READ = 103
    FLASH_BAD_ERASE = 104
    FLASH_BAD_ADDRESS = 105
    APPLICATION_OUTOFMEMORY = 113
    RESPONSE_NO_DATA_AVAILABLE = 114
    INVALID_HANDSHAKING = 117
    MSG_NAME_ALREADY_EXISTS = 118
    MSG_NAME_INVALID = 119
    SETMSG_TYPE_INVALID = 120
    MSG_ID_RESERVED = 121
    MSG_SIZE_TOO_LARGE = 122
    OUTPUT_LIMIT_EXCEEDED = 123
    OUTPUT_NOT_ALLOWED = 124
    INVALID_REFERENCE_TYPE = 125
    RESPONSE_INVALID_SECURITY_KEY = 126
    RESPONSE_HARDWARE_NOT_AVAILABLE = 127
    SYSTEM_ALREADY_LOCKED_OUT = 128
    SYSTEM_NOT_LOCKED_OUT = 129
    RESPONSE_INVALID_PULSEWIDTH = 131
    COARSE_TIME_NOT_ACHIEVED = 133
    CONFIG_CODE_INVALID_PARAMETER = 134
    CONFIG_CODE_TABLE_FULL = 135
    UNKNOWN_OBJECT = 136
    INVALID_OPERATION = 137
    INVALID_SEQUENCE = 138
    USER_VARF_IN_USE = 140
    MUST_ENABLE_CLOCK_ADJUST = 141
    DISK_BUSY = 142
    RX_STATUS_INVALID_WORD = 143
    RESPONSE_PARAMETER_INVALID_FOR_MODEL = 148
    INS_ZUPT_DISABLED = 149
    IMU_SPECS_LOCKED = 150
    RESPONSE_INVALID_INTERFACE_MODE = 151
    INVALID_FOR_IMU = 154
    IMU_PROTOCOL_LOCKED = 155
    INVALID_IMU_TYPE = 157
    TRIGGER_TIME_INVALID = 159
    INVALID_SENSOR = 160
    TRIGGER_BUFFER_FULL = 161
    NOT_FINESTEERING = 162
    SENSOR_LOCKED = 163
    RESPONSE_PROFILE_NAME_INVALID = 165
    RESPONSE_PROFILE_MAX_EXCEED = 166
    RESPONSE_PROFILE_DELETE_FAIL = 167
    RESPONSE_PROFILE_NAME_EXIST = 168
    RESPONSE_PROFILE_COMMAND_NVM_FULL = 169
    RESPONSE_PROFILE_ACTIVATED = 170
    AUTH_COPY_FAIL = 171
    RESPONSE_PROFILE_MAXCMD_EXCEED = 172
    RESPONSE_PROFILE_SAVECONFIG_FAIL = 173
    APPLICATION_SEND_STOP_CMD_ERROR = 174
    APPLICATION_STOP_USER_API_ERROR = 175
    APPLICATION_START_ERROR = 176
    VEHICLEBODYROTATION_INACTIVE = 177
    RESPONSE_PPP_BAD_SEED = 178
    RESPONSE_PPP_SEED_INTEGRITY_FAILURE = 179
    RESPONSE_INVALID_PASSWORD = 180
    TOO_MANY_FILES = 181
    RESPONSE_DES_WEAK_KEY = 182
    RESPONSE_DES_WRONG_KEY_LENGTH = 183
    RESPONSE_DES_BAD_KEY_TYPE = 184
    RESPONSE_DES_SELFTEST_FAILED = 185
    RESPONSE_DES_OUTPUT_NOT_ALLOWED = 186
    SECURE_PORT = 187
    NMEA2000_J1939_STACK_RUNNING = 188
    APPLICATION_MAX_MEMORY_EXCEEDED = 190
    RESPONSE_PPP_NO_SAVED_SEED = 191
    RESPONSE_INVALID_SYSTEM = 192
    INVALID_COMMAND_MODEL = 193
    POSAVE_NOT_STARTED = 194
    RESPONSE_PDP_INVALIDCMD_FOR_NORMALMODE = 200
    RESPONSE_PPP_SEED_INVALID_WHEN_DYNAMIC = 201
    RESPONSE_PARAMETERS_WRONG_COMBINATION = 202
    RESPONSE_INVALID_CALIBRATION = 203
    RESPONSE_ACTIVE_GIMBAL = 204
    AUTH_TABLE_FULL_NEEDS_ERASE = 205
    RESPONSE_PROFILE_NOT_RUNNING = 206
    RESPONSE_ID_ALREADY_IN_USE = 208
    RESPONSE_ID_DOES_NOT_EXIST = 209
    RESPONSE_CALIBRATION_IN_PROGRESS = 210
    RESPONSE_FILTER_FS_MISMATCH = 211
    RESPONSE_FILTER_PF_FREQUENCY_MISMATCH = 212
    RESPONSE_FILTER_CASCADING_ERROR = 213
    RESPONSE_FILTER_NOT_APPLIED = 214
    RESPONSE_ID_SHOULD_BE_FOUR_CHARACTER_LONG = 215
    SRTK_INVALID_SUBSCRIPTION_CODE = 216
    SRTK_SUBSCRIPTION_TABLE_FULL = 217
    SRTK_NETWORK_ID_MISMATCH = 218
    SRTK_SUBSCRIPTION_NOT_FOUND = 219
    SRTK_SUBSCRIPTION_NOT_ACTIVE = 220
    SRTK_SUBSCRIPTION_EXPIRED = 221
    RESPONSE_MAXIMUM_LOGGERCHILDREN_EXCEEDED = 222
    RESPONSE_PPP_SEED_LATENT = 223
    RESPONCE_LAST_LOGGERCHILD_RESERVED = 224
    REGION_NOT_SET = 226
    RESPONSE_INVALID_COMMAND_ORDER = 227
    NO_ACTIVE_FILETRANSFER = 228
    RESPONSE_INS_SEED_DISABLED = 229
    RESPONSE_PCAP_INTERFACE_FAIL = 230
    RESPONSE_PCAP_INITIALIZE_FAIL = 231
    RESPONSE_MAX_SCRIPTS = 232
    RESPONSE_SCRIPT_INTERPRETER_RUNNING = 233
    RESPONSE_SCRIPT_PORT_IN_USE = 234
    RESPONSE_PARAMETER_LOCKED_BY_APP = 242
    RESPONSE_PPP_SEED_DISCARDED_RAPID_CONVERGENCE = 248
    RESPONSE_GEODETIC_DATUM_TABLE_FULL = 249
    RESPONSE_DATUM_TRANSFORMATION_TABLE_FULL = 250
    RESPONSE_DATUM_ID_DOES_NOT_EXIST = 251
    RESPONSE_DATUM_ID_IS_RESERVED = 252
    RESPONSE_PORT_NOT_OPENED_OR_NOT_OWNED = 253
    RESPONSE_INVALID_ENCRYPTED_MESSAGE_FORMAT = 255
    RESPONSE_CALIBRATION_NOTACTIVE = 256
    RESPONSE_IN_USE_BY_IMU = 263
    RESPONSE_CONFLICTING_SPRINKLER_CHANNELS = 247
    RESPONSE_SIGNAL_ALREADY_LOCKED_OUT = 257
    RESPONSE_SIGNAL_NOT_LOCKED_OUT = 258
    RESPONSE_SIGNAL_LOCKOUT_LIST_IS_FULL = 259
    RESPONSE_SYSTEM_ALREADY_LOCKED_OUT = 260
    RESPONSE_SYSTEM_LOCKOUT_LIST_IS_FULL = 261
    RESPONSE_SYSTEM_NOT_LOCKED_OUT = 262
    MULTIPLEX_IO_CONFLICT = 239
    RESPONSE_INS_NOT_ALIGNED = 254
    RESPONSE_SURVEY_POSITION_ALREADY_EXISTS = 246
    RESPONSE_WIFI_CHANNEL_INVALID_FOR_REGION = 225
    RESPONSE_INVALID_COMBINATION = 236
    RESPONSE_RADIO_NOT_DETECTED = 237
    RESPONSE_NO_RADIO_CONTROL = 238
    RESPONSE_WIFIALIGNAUTOMATION_ENABLED = 240
    RESPONSE_WIFIALIGNAUTOMATION_NETWORK_DISABLED = 241
    RESPONSE_NO_BLUETOOTH_CONTROL = 243
    RESPONSE_BLUETOOTH_NOT_POWERED = 244
    RESPONSE_BLUETOOTH_POWERED = 245
