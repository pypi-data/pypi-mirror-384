"""
ADO manager framework using plain Python objects & an automatic manager.

ADO classes are represented as Python classes in `declarative_manager`, with parameters as class variables and setters as decorated methods.
The AutoMan class detects and instantiates ADO instances defined in fecManager when supplied with an ADO manager name. 

Example:

    Here is an ADO with 2 parameters being created and instantiated with AutoMan:

        class simple(ADO):
            intS = Parameter(type=Type.Int)
            stringS = Parameter(type=Type.String, intial_value="Hello, world!", ppm_size=8)
            stringS.Description("This is the description for stringS")

            def start(self):
                super().start()
                print("simple ADO is starting...")

            @intS.setter
            def intS_setter(self, value, ppm):
                print("intS is set to", value)
                return value

        man = AutoMan(name="simple.test")
        man.start()
"""

import copy
import inspect
import logging
import signal
import socket
import warnings
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import partial
from threading import Timer
from typing import Any, Callable, Dict, List, MutableMapping, Optional, Tuple
from typing import Type as Type_
from typing import Union, cast

import pyodbc
from cad_error import RhicError

from cad_io import am, notif
from cad_io.adoIf import Feature

__all__ = [
    "Caller",
    "ADOException",
    "Category",
    "FeatureBuilder",
    "Type",
    "Parameter",
    "ParameterInstance",
    "PropertyInstance",
    "ADO",
    "AutoMan",
]

__pdoc__ = {
    "ParameterInstance.set": False,
    "ADO.custom_classes": False,
    "ADO.__init__": False,
}


@dataclass
class Caller:
    """Dataclass containing caller info for access control use."""

    host: str
    ip: str
    port: int


class ADOException(Exception):
    """Represents ADO errors as returned by setter functions.

    Stores ADO error code to be caught and returned to caller as ADO error.
    """

    def __init__(self, code):
        self.code = code

    @staticmethod
    def EngHigh():
        return ADOException(RhicError.ADOERRENGHIGH)

    @staticmethod
    def EngLow():
        return ADOException(RhicError.ADOERRENGLOW)

    @staticmethod
    def OpHigh():
        return ADOException(RhicError.ADOERROPHIGH)

    @staticmethod
    def OpLow():
        return ADOException(RhicError.ADOERROPLOW)

    @staticmethod
    def BadDiscrete():
        return ADOException(RhicError.ADOERRBADDISCRETE)

    @staticmethod
    def Locked():
        return ADOException(RhicError.ADO_LOCKED)

    @staticmethod
    def NotSettable():
        return ADOException(RhicError.ADO_NOT_SETTABLE)

    @staticmethod
    def OperationNotAllowed():
        return ADOException(RhicError.ADO_OPERATION_NOT_ALLOWED)

    @staticmethod
    def OperationNotSupported():
        return ADOException(RhicError.ADO_OPERATION_NOT_SUPPORTED)

    @staticmethod
    def ValueOutOfRange():
        return ADOException(RhicError.ADO_VALUE_OUT_OF_RANGE)

    @staticmethod
    def HardwareFailure():
        return ADOException(RhicError.ADO_HW_FAILURE)

    @staticmethod
    def PermissionDenied():
        return ADOException(RhicError.ADO_PERMISSION_DENIED)

    @staticmethod
    def NoSuchName():
        return ADOException(RhicError.ADO_NO_SUCH_NAME)

    @staticmethod
    def GarbledMessage():
        return ADOException(RhicError.ADO_GARBLED_MESSAGE)

    @staticmethod
    def SystemError():
        return ADOException(RhicError.ADO_SYSTEM_ERROR)

    @staticmethod
    def GenericError():
        return ADOException(RhicError.ADO_GENERIC_ERROR)

    @staticmethod
    def ValueNotYetInitialized():
        return ADOException(RhicError.ADO_VALUE_NOT_YET_INITIALIZED)

    @staticmethod
    def NotValidForMode():
        return ADOException(RhicError.ADO_NOT_VALID_FOR_MODE)

    @staticmethod
    def TimeOutGettingData():
        return ADOException(RhicError.ADO_TIME_OUT_GETTING_DATA)

    @staticmethod
    def DeviceOpenFailed():
        return ADOException(RhicError.ADO_DEVICE_OPEN_FAILED)

    @staticmethod
    def PossibleDataLoss():
        return ADOException(RhicError.ADO_POSSIBLE_DATA_LOSS)

    @staticmethod
    def NotValidAsConfigured():
        return ADOException(RhicError.ADO_NOT_VALID_AS_CONFIGURED)

    @staticmethod
    def NoData():
        return ADOException(RhicError.ADO_NO_DATA)

    @staticmethod
    def WrongPPMIndex():
        return ADOException(RhicError.ADO_WRONG_PPM_INDEX)

    @staticmethod
    def DataMissing():
        return ADOException(RhicError.ADO_DATA_MISSING)

    @staticmethod
    def FeatureUnavailable():
        return ADOException(RhicError.ADO_FEATURE_UNAVAILABLE)


class Category(IntEnum):
    """Enum defining parameter categories as combinations of feature flags."""

    NoCategory = 0
    """No Features"""

    Configuration = Feature.CONFIGURATION | Feature.READABLE
    """Configuration & Readable"""

    Diagnostic = Feature.DIAGNOSTIC
    """Diagnostic"""

    DiscreteSetting = (
        Feature.DISCRETE
        | Feature.READABLE
        | Feature.WRITABLE
        | Feature.EDITABLE
        | Feature.SAVABLE
        | Feature.RESTORABLE
        | Feature.ARCHIVABLE
    )
    """Discrete & Readable & Writable & Editable & Savable & Restorable & Archivable"""

    ContinuousSetting = (
        Feature.READABLE
        | Feature.WRITABLE
        | Feature.EDITABLE
        | Feature.SAVABLE
        | Feature.RESTORABLE
        | Feature.ARCHIVABLE
    )
    """Readable & Writable & Editable & Savable & Restorable & Archivable"""

    DiscreteMeasurement = Feature.READABLE | Feature.DISCRETE | Feature.SAVABLE
    """Readable & Savable & Discrete"""

    ContinuousMeasurement = Feature.READABLE
    """Readable"""

    DiscreteAction = Feature.WRITABLE | Feature.DISCRETE | Feature.EDITABLE
    """Writable & Editable & Discrete"""

    ContinuousAction = Feature.WRITABLE | Feature.EDITABLE
    """Writeable & Editable"""


class Type(Enum):
    """Enum defining standard ADO parameter types"""

    Char = "CharType"
    UChar = "UCharType"
    Short = "ShortType"
    UShort = "UShortType"
    Int = "IntType"
    UInt = "UIntType"
    Long = "LongType"
    ULong = "ULongType"
    Float = "FloatType"
    Double = "DoubleType"
    String = "StringType"
    Struct = "StructType"
    Void = "VoidType"
    Blob = "BlobType"

    def python_type(self) -> Optional[type]:
        """Return the Python type corresponding to this ADO type.
        
        Returns:
            type: The Python type corresponding to this ADO type.
        """
        if self in (Type.String,):
            return str
        elif self in (
            Type.Char,
            Type.UChar,
            Type.Short,
            Type.UShort,
            Type.Int,
            Type.UInt,
            Type.Long,
            Type.ULong,
        ):
            return int
        elif self in (Type.Float, Type.Double):
            return float
        elif self in (Type.Struct, Type.Blob):
            return bytes
        else:
            return None

    def initial_value(self, count: int = 1) -> Any:
        """Used to get a default initial value for a parameter when not explicitly defined.

        Args:
            count (int, optional): if not equal to 1, returns an array value. Defaults to 1.

        Returns:
            Any: initial value of appropriate Python type for ADO parameter
        """
        val: Any
        if self in (
            Type.Int,
            Type.UInt,
            Type.Short,
            Type.UShort,
            Type.Long,
            Type.ULong,
            Type.Char,
            Type.UChar,
            Type.Float,
            Type.Double,
        ):
            val = 0
        elif self is Type.String:
            val = ""
        elif self in (Type.Blob, Type.Struct):
            val = b""
        else:
            val = None

        if count != 1:
            val = [val] * count

        return val


class FeatureBuilder(int):
    """Builder class to create complex features for ADO parameters

    Examples:
        Readable, writable, archivable parameter:

            Parameter(
                type=Type.Int, 
                features=FeatureBuilder().readable().writable().archivable()
            )

        Discrete setting category + diagnostic:

            Parameter(
                type=Type.Int,
                features=FeatureBuilder.DiscreteSetting().diagnostic()
            )
    """

    def __new__(cls, value=0):
        return int.__new__(cls, value)

    @staticmethod
    def NoCategory():
        """Returns blank feature
        """
        return FeatureBuilder(Category.NoCategory)

    @staticmethod
    def Configuration():
        """Return a readable configuration feature"""
        return FeatureBuilder(Category.Configuration)

    @staticmethod
    def Diagnostic():
        """Return a diagnostic feature"""
        return FeatureBuilder(Category.Diagnostic)

    @staticmethod
    def DiscreteSetting():
        """Return a discrete setting feature"""
        return FeatureBuilder(Category.DiscreteSetting)

    @staticmethod
    def ContinuousSetting():
        """Return a continuous setting feature"""
        return FeatureBuilder(Category.ContinuousSetting)

    @staticmethod
    def DiscreteMeasurement():
        """Return a discrete measurement feature"""
        return FeatureBuilder(Category.DiscreteMeasurement)

    @staticmethod
    def ContinuousMeasurement():
        """Return a continuous measurement feature"""
        return FeatureBuilder(Category.ContinuousMeasurement)

    @staticmethod
    def DiscreteAction():
        """Return a discrete action feature"""
        return FeatureBuilder(Category.DiscreteAction)

    @staticmethod
    def ContinuousAction():
        """Return a continuous action feature"""
        return FeatureBuilder(Category.ContinuousAction)

    def readable(self):
        """Add readable attribute to a feature"""
        return self.add_attr(Feature.READABLE)

    def writable(self):
        """Add writable attribute to a feature"""
        return self.add_attr(Feature.WRITABLE)

    def discrete(self):
        """Add discrete attribute to a feature"""
        return self.add_attr(Feature.DISCRETE)

    def archivable(self):
        """Add archivable attribute to a feature"""
        return self.add_attr(Feature.ARCHIVABLE)

    def configuration(self):
        """Add configuration attribute to a feature"""
        return self.add_attr(Feature.CONFIGURATION)

    def diagnostic(self):
        """Add diagnostic attribute to a feature"""
        return self.add_attr(Feature.DIAGNOSTIC)

    def savable(self):
        """Add savable attribute to a feature"""
        return self.add_attr(Feature.SAVABLE)

    def restorable(self):
        """Add restorable attribute to a feature"""
        return self.add_attr(Feature.RESTORABLE)

    def editable(self):
        """Add editable attribute to a feature"""
        return self.add_attr(Feature.EDITABLE)

    def add_attr(self, attr):
        """Add arbitrary attribute to a feature"""
        return FeatureBuilder(attr | self)


class Parameter:
    """Class to instantiate a parameter on an ADO (subclass of `ADO`).
    """

    def __init__(
        self,
        type: Type,
        initial_value: Any = None,
        name: Optional[str] = None,
        count: int = 1,
        ppm_size: int = 0,
        category: Category = Category.NoCategory,
        features: int = Feature.READABLE,
    ):
        """Instantiate a parameter

        Args:
            type (Type): ADO data type associated with parameter
            initial_value (Any, optional): Initial value for parameter. Defaults to default value for type.
            name (Optional[str], optional): Explicit name for parameter, used when variable name does not match parameter name. Defaults to None.
            count (int, optional): Number of elements held by parameter. Defaults to 1.
            ppm_size (int, optional): Number of PPM users supported by parameter. Defaults to 1.
            category (Category, optional): Category for parameter. Defaults to Category.NoCategory.
            features (int, optional): Features for parameter (added to category). Defaults to Feature.READABLE.

            
        Example:

            Creating an array integer parameter with 3 elements, a starting value of `[10]*3`, a PPM size of 8, and explicitly named "alternateNameM":
            
                class MyAdo(ADO):
                    someParameterM = Parameter(Type.Int, initial_value=10, name="alternateNameM", count=3, ppm_size=8)

                    def do_something(self):
                        ppm_user = 1
                        self.someParameterM[ppm_user].value = 0
        """
        if initial_value is None and type is not Type.Void:
            initial_value = type.initial_value(count=count)

        self._user_name = name
        self._type = type
        self._initial_value = initial_value
        self._count = count
        self._ppm_size = ppm_size
        self._features = category | features
        self._properties: List[tuple] = []
        self._user_setter: Optional[Callable[[ADO, Any, int], Any]] = None
        self._user_getter: Optional[Callable[[ADO, Any, int], Any]] = None

    def __get__(self, inst, cls=None) -> "ParameterInstance":
        """INTERNAL: called when retrieving parameter from ADO instance"""
        return inst.parameter_dict[self._name]

    def __set_name__(self, cls, name: str):
        """INTERNAL: sets default name from variable name"""
        self._set_name = name

    @property
    def logger(self):
        """Return logger for this parameter"""
        return logging.getLogger("Parameter(name={})".format(self._name))

    @property
    def _name(self):
        """INTERNAL: get name of parameter"""
        return self._user_name or self._set_name

    def setter(self, f):
        """Decorator for method serving as parameter setter.

        ## Decorated method signature:

        Args:
            self: ADO instance.
            value: Value received to be set.
            ppm_user: PPM user value is being set on.
            parameter (str, omittable): Name of parameter being set, useful for multiple parameters per setter. Only passed if `parameter` argument is present in function signature.
            caller (Caller, omittable): Information about client. Only passed if `caller` argument is present in function signature. 


        Example:

            The `my_setter` function is being used as setter for the `parameterM` parameter:

                parameterM = Parameter(Type.Int)

                @parameterM.setter
                def my_setter(self, value, ppm_user, parameter="", caller=None):
                    # Do something with the value
                    value = value + 1
                    return value # Make sure to return the value when done!
        """
        self._user_setter = f
        return f

    def getter(self, f):
        """Decorator for method serving as parameter getter.

        ## Decorated method signature:

        Args:
            self: ADO instance.
            value: Value received to be set.
            ppm_user: PPM user value is being set on.
            parameter (str, omittable): Name of parameter being set, useful for multiple parameters per getter. Only passed if `parameter` argument is present in function signature.
            caller (Caller, omittable): Information about client. Only passed if `caller` argument is present in function signature. 


        Example:

            The `my_setter` function is being used as getter for the `parameterM` parameter:

                parameterM = Parameter(Type.Int)

                @parameterM.getter
                def my_getter(self, value, ppm_user, parameter="", caller=None):
                    # Do something with the value
                    value = value + 1
                    return value # Make sure to return the value when done!
        """
        self._user_getter = f
        return f

    def Property(
        self,
        name: str,
        ptype: Type,
        value: Any,
        count: int = 1,
        ppm_size: int = None,
        category: Category = Category.NoCategory,
        features: int = Feature.READABLE,
    ):
        """Create a new property on the parameter

        Args:
            name (str): Name of property
            ptype (Type): Type held by property
            value (Any): Initial value of property
            count (int, optional): Number of elements in property. Defaults to 1.
            ppm_size (int, optional): Number of PPM users supported by property. Defaults to 1.
            category (Category, optional): Category for property. Defaults to Category.NoCategory.
            features (int, optional): Features for property (added to category). Defaults to Feature.READABLE.

        Returns:
            Property: Handle to access property on parameter
        """
        if not isinstance(name, str):
            raise TypeError("Property name must be a string")

        ppm_size = self._ppm_size if ppm_size is None else ppm_size

        self._properties.append(
            (name, ptype.value, count, ppm_size, category | features, value)
        )
        return Property(self, ptype, value, name, count, ppm_size, category | features)

    def Description(self, value):
        """Default Description property holding a string value"""
        return self.Property("description", Type.String, value)

    def Unit(self, value):
        """Default Unit property holding a string value"""
        return self.Property("unit", Type.String, value)

    def Format(self, value):
        """Default Format property holding a string value"""
        return self.Property("format", Type.String, value)

    def LegalValues(self, *values):
        """Default Legal Values property holding string values"""
        if self._features & Feature.DISCRETE == 0:
            raise TypeError(
                "LegalValues property only valid for discrete setting parameters"
            )

        return self.Property(
            "legalValues",
            Type.String,
            ",".join(str(v) for v in values),
            features=Feature.READABLE | Feature.DISCRETE,
        )

    def OperationalHigh(self, value):
        """Default Operational High property holding a value of parameter type"""
        return self.Property("opHigh", self._type, value)

    def OperationalLow(self, value):
        """Default Operational Low property holding a value of parameter type"""
        return self.Property("opLow", self._type, value)

    def EngineeringHigh(self, value):
        """Engineering High property holding a value of parameter type"""
        return self.Property("engHigh", self._type, value)

    def EngineeringLow(self, value):
        """Engineering Low property holding a value of parameter type"""
        return self.Property("engLow", self._type, value)

    def Alarm(
        self,
        low: Union[int, float] = 0,
        high: Union[int, float] = 0,
        level: notif.NotifCategory = notif.NotifCategory.WARNING,
        alarm_text: Optional[str] = None,
        threshold: notif.NotifCategory = notif.NotifCategory.OK,
        delay: int = 0,
        latching: bool = False,
    ):
        """Adds required alarm properties to this parameter
        
        Args:
            low (Any): Low value for alarm
            high (Any): High value for alarm
            level (notif3.NotifCategory, optional): Level of alarm. Defaults to notif3.NotifCategory.WARNING.
            alarm_text (str, optional): Text to display when alarm is triggered. Defaults to "range error" for continuous, and "discrete value error" for discrete measurements.
            threshold (notif3.NotifCategory, optional): Threshold level of alarm. Defaults to notif3.NotifCategory.OK.
            delay (int, optional): Number of times alarm triggers before showing on AlarmDisplay. Defaults to 0.
            latching (bool, optional): Whether alarm is latching. Defaults to False.

        Returns:
            tol: tolerance values property
            level: alarm level property
            thresh: alarm threshold property
            text: alarm text property
            delay: alarm delay property
            latch: alarm latching property (if latching == true, otherwise None)
        """
        if self._type == Type.String:
            tol_prop = self.Property(
                "toleranceValues",
                Type.Int,
                (-1, -1, level, *[0] * 7),
                count=10,
                category=Category.ContinuousSetting,
            )
            if alarm_text is None:
                alarm_text = "discrete value error"
        else:
            tol_prop = self.Property(
                "toleranceValues",
                self._type,
                (low, high, level, *[0] * 7),
                count=10,
                category=Category.ContinuousSetting,
            )
            if alarm_text is None:
                alarm_text = "range error"

        level_prop = self.Property(
            "alarmLevel", Type.Int, notif.NotifCategory.OK, category=Category.ContinuousSetting
        )
        thresh_prop = self.Property(
            "alarmThreshold", Type.Int, threshold, category=Category.ContinuousSetting
        )
        text_prop = self.Property(
            "alarmText", Type.String, alarm_text, category=Category.ContinuousSetting
        )
        delay_prop = self.Property(
            "alarmDelay", Type.Int, delay, category=Category.ContinuousSetting
        )
        latch_prop = (
            self.Property(
                "latchCount", Type.Int, 0, category=Category.ContinuousSetting
            )
            if latching
            else None
        )
        return tol_prop, level_prop, thresh_prop, text_prop, delay_prop, latch_prop


class Property:
    def __init__(
        self,
        param: Parameter,
        type: Type,
        value: Any = None,
        name: Optional[str] = None,
        count: int = 1,
        ppm_size: int = 1,
        features: int = Feature.READABLE,
    ):
        """Do not instantiate directly! Use Parameter.Property instead."""
        if value is None and type is not Type.Void:
            value = type.initial_value()
        self._param = param
        self._user_name = name
        self._type = type
        self._value = value
        self._count = count
        self._ppm_size = ppm_size
        self._features = features

    def __get__(self, inst, cls=None) -> "PropertyInstance":
        """INTERNAL: called when retreiving property value from ADO instance"""
        ado_param: ParameterInstance = inst.parameter_dict[self._param._name]
        return ado_param.property_dict[self._name]

    def __set_name__(self, cls, name: str):
        self._set_name = name

    @property
    def _name(self):
        return self._user_name or self._set_name


class PropertyInstance(am.AdoProperty):
    parameter: "ParameterInstance"

    def __init__(
        self,
        adoparameter: "ParameterInstance",
        name: str,
        ptype: Union[str, Type],
        count: int,
        features: int,
        value: Any,
        ppmSize=0,
    ):
        super().__init__(
            adoparameter,
            name,
            ptype.value if isinstance(ptype, Type) else ptype,
            count,
            features,
            value,
            ppmSize,
        )
        self.type_enum = Type(ptype)
        self._old_value = copy.deepcopy(self.value)

    def setInternal(self, value, ppmIndex):
        cast = self.type_enum.python_type()
        if cast is not None:
            try:
                if self.count != 1:
                    value = [cast(item) for item in value]
                else:
                    value = cast(value)
            except ValueError:
                raise ValueError(
                    f"Could not convert '{value.__class__.__name__}' to {self.type_enum} for {self.parameter.ado.name}:{self.parameter.name}:{self.name}"
                )
            except TypeError:
                raise ValueError(
                    f"Iterable expected for {self.parameter.ado.name}:{self.parameter.name}:{self.name}, not {type(value)}"
                )

        if self.ppmSize > 0:
            if not (0 <= ppmIndex < self.ppmSize):
                raise ValueError(f"Invalid PPM index {ppmIndex}")
            self._old_value[ppmIndex] = copy.deepcopy(self.value[ppmIndex])
        elif self.ppmSize == 0:
            ppmIndex = 0
            self._old_value = copy.deepcopy(self.value)

        return super().setInternal(value, ppmIndex)

    # Override __getitem__ to make accessing property values easier
    def __getitem__(self, ppm_user):
        if self.ppmSize > 0:
            if ppm_user < 1 or ppm_user > self.ppmSize:
                raise ValueError(
                    f"Invalid PPM user {ppm_user}. Must be between 1 and {self.ppmSize}."
                )
            ppmIndex = ppm_user - 1
        elif self.ppmSize == 0:
            ppmIndex = 0

        return self.value[ppmIndex] if self.ppmSize > 1 else self.value

    # Override __setitem__ to make setting property values easier
    def __setitem__(self, ppm_user, value):
        """INTERNAL: Custom setter for am3.AdoProperty class. Used for ppm_user <-> index conversion."""
        if self.ppmSize > 0:
            if ppm_user < 1 or ppm_user > self.ppmSize:
                raise ValueError(
                    f"Invalid PPM user {ppm_user}. Must be between 1 and {self.ppmSize}."
                )
            ppmIndex = ppm_user - 1
        elif self.ppmSize == 0:
            # if ppm is not 0, just set it to 0 assuming the ADO developer knows that the parameter is non-ppm
            ppmIndex = 0
        self.setInternal(value, ppmIndex)
        self.update(ppmIndex)


class ParameterInstance(am.AdoParameter):
    ado: "ADO"
    property_dict: MutableMapping[str, PropertyInstance] # type: ignore
    _initialized = False

    def __init__(
        self, ado, name, ptype, count, features, value, ppmSize=0, setter=None, getter=None
    ):
        super().__init__(
            ado, name, ptype.value, count, features, value, ppmSize=ppmSize
        )
        # self.properties_dict: Dict[str, PropertyInstance] = {}
        self._user_setter = setter
        self._user_getter = getter
        self.type = ptype
        self.checkers = []
        self.add("timestamps", 0)
        self._initialized = True

    def set(self, ppm_index, caller=None):
        """INTERNAL: handle calling setter(s) for parameter"""
        ppm_user = ppm_index + 1
        param = self.ado[self.name]
        new_val = param[ppm_user] if param.value.ppmSize > 0 else param[0]

        if self.ado.manager and self.ado.manager.last_caller and caller is None:
            addr, port = self.ado.manager.last_caller
            hostname, _, _ = socket.gethostbyaddr(addr)
            caller = Caller(hostname, addr, port, None)

        try:
            validator = getattr(self.ado, "global_validator", None)
            if validator:
                sig = inspect.signature(validator)
                if "caller" in sig.parameters:
                    new_val = validator(
                        param, new_val, ppm_user, caller=caller
                    )
                else:
                    new_val = validator(param, new_val, ppm_user)
            if callable(self._user_setter):
                if self.value.ppmSize > 0:
                    self.value.value[ppm_index] = self.value._old_value[ppm_index]
                else:
                    self.value.value = self.value._old_value
                    
                sig = inspect.signature(self._user_setter)
                kwargs: Dict[str, Any] = {}
                if "caller" in sig.parameters:
                    kwargs["caller"] = caller
                if "parameter" in sig.parameters:
                    kwargs["parameter"] = self.name
                # param[ppm_user] = self._user_setter(new_val, ppm_user, **kwargs)
                setter_value = self._user_setter(new_val, ppm_user, **kwargs)
                param.property_dict["value"].setInternal(setter_value, ppm_index)
        except ADOException as e:
            return e.code
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.ado.logger.error("Error on set", exc_info=e)
            return RhicError.ADO_GENERIC_ERROR

        return 0

    def get(self, ppm_index):
        """INTERNAL: handle calling setter(s) for parameter"""
        ppm_user = ppm_index + 1
        param = self.ado[self.name]
        val = param[ppm_user] if param.value.ppmSize > 0 else param[0]

        if self.ado.manager and self.ado.manager.last_caller:
            addr, port = self.ado.manager.last_caller
            hostname, _, _ = socket.gethostbyaddr(addr)
            caller = Caller(hostname, addr, port)
        else:
            caller = None

        try:
            if callable(self._user_getter):
                sig = inspect.signature(self._user_getter)
                kwargs: Dict[str, Any] = {}
                if "caller" in sig.parameters:
                    kwargs["caller"] = caller
                if "parameter" in sig.parameters:
                    kwargs["parameter"] = self.name
                # param[ppm_user] = self._user_getter(val, ppm_user, **kwargs)
                getter_value = self._user_getter(val, ppm_user, **kwargs)
                param.property_dict["value"].setInternal(getter_value, ppm_index)
        except ADOException as e:
            return e.code
        except Exception as e:
            self.ado.logger.error("Error on set", exc_info=e)
            return RhicError.ADO_GENERIC_ERROR

        return 0

    def addProperty(
        self,
        name: str,
        ptype: Union[Type, str],
        count: int,
        ppmSize: int,
        features: int,
        value: Any,
    ) -> Optional[PropertyInstance]:
        """Add any property to this parameter."""
        # check if property already exists
        if name in self.property_dict:
            return None

        prop = PropertyInstance(
            self, name, ptype, count, features, value, ppmSize=ppmSize
        )
        self.property_dict[name] = prop
        return prop

    def publish(self, value=None, timestamp=None, ppm_user=0):
        """Publish a parameter update explicitly, with an optional timestamp.

        Args:
            value (Any, optional): Value to set to parameterr. Defaults to None.
            timestamp (Union[int, float], optional): Timestamp for parameter, in Unix time. Defaults to system time.
            ppm_user (int, optional): PPM user to update. Defaults to 0.

        Raises:
            ValueError: If PPM user specified is invalid for the parameter.
        """

        if self.value.ppmSize > 0:
            if ppm_user < 1 or ppm_user > self.value.ppmSize:
                raise ValueError(f"Invalid PPM user {ppm_user}")
            ppm_index = ppm_user - 1
        elif self.value.ppmSize == 0:
            ppm_index = None

        self.value.setInternal(value, ppm_index)
        self.setTimestamps(timestamp, ppm_index)
        self.updateValueTimestamp(ppm_index)

    def addAlarm(
        self,
        low: Union[int, float] = 0,
        high: Union[int, float] = 0,
        level: notif.NotifCategory = notif.NotifCategory.WARNING,
        alarm_text: str = "range error",
        threshold: notif.NotifCategory = notif.NotifCategory.OK,
        delay: int = 0,
        latching: bool = False,
        tolerance_function: Callable[[Any], notif.NotifCategory] = None,
    ) -> Tuple[
        Optional["PropertyInstance"],
        Optional["PropertyInstance"],
        Optional["PropertyInstance"],
        Optional["PropertyInstance"],
        Optional["PropertyInstance"],
        Optional["PropertyInstance"],
    ]:
        """Adds required alarm properties to this parameter
        
        Args:
            low (Any): Low value for alarm (unused if tolerance_function specified)
            high (Any): High value for alarm (unused if tolerance_function specified)
            level (notif3.NotifCategory, optional): Level of alarm. Defaults to notif3.NotifCategory.WARNING.
            alarm_text (str, optional): Text to display when alarm is triggered. Defaults to "range error".
            threshold (notif3.NotifCategory, optional): Threshold level of alarm. Defaults to notif3.NotifCategory.OK.
            delay (int, optional): Number of times alarm triggers before showing on AlarmDisplay. Defaults to 0.
            latching (bool, optional): Whether alarm is latching. Defaults to False.
            tolerance_function (Callable[[Any], NotifCategory], optional): Custom tolerance function

        Returns:
            tol: tolerance values property (if tolerance_function == None, otherwise None)
            level: alarm level property
            thresh: alarm threshold property
            text: alarm text property
            delay: alarm delay property
            latch: alarm latching property (if latching == true, otherwise None)
        """
        if tolerance_function:
            self.toleranceFunction = tolerance_function
            tol = None
        else:
            numeric = [Type.Double, Type.Float, Type.Int, Type.Long, Type.Short, Type.UInt, Type.ULong, Type.UShort]
            t = self.value.type_enum if self.value.type_enum in numeric else Type.Int
            tol = self.addProperty(
                "toleranceValues",
                t,
                value=(low, high, level, *[0] * 7),
                count=10,
                features=Category.ContinuousSetting,
                ppmSize=self.value.ppmSize,
            )

        level = self.addProperty(
            "alarmLevel",
            Type.Int,
            count=1,
            value=notif.NotifCategory.OK,
            features=Category.ContinuousSetting,
            ppmSize=self.value.ppmSize,
        )
        thresh = self.addProperty(
            "alarmThreshold",
            Type.Int,
            count=1,
            value=threshold,
            features=Category.ContinuousSetting,
            ppmSize=self.value.ppmSize,
        )
        text = self.addProperty(
            "alarmText",
            Type.String,
            count=1,
            value=alarm_text,
            features=Category.ContinuousSetting,
            ppmSize=self.value.ppmSize,
        )
        delay = self.addProperty(
            "alarmDelay",
            Type.Int,
            count=1,
            value=delay,
            features=Category.ContinuousSetting,
            ppmSize=self.value.ppmSize,
        )
        latch = (
            self.addProperty(
                "latchCount",
                Type.Int,
                count=1,
                value=0,
                features=Category.ContinuousSetting,
                ppmSize=self.value.ppmSize,
            )
            if latching
            else None
        )
        return tol, level, thresh, text, delay, latch

    def _handle_checks(self, value):
        st = 0
        for checker in self.checkers:
            if st != 0:
                break
            st = checker(value)
        return st

    # Override __getitem__ to make accessing parameter values easier
    def __getitem__(self, ppm_user):
        return self.value[ppm_user]

    # Override __setitem__ to make setting parameter values easier
    def __setitem__(self, ppm_user, value):
        """INTERNAL: Custom setter for am3.AdoParameter class. Used for ppm_user <-> index conversion."""
        self.publish(value=value, ppm_user=ppm_user)

    def __getattr__(self, name) -> "PropertyInstance":
        return super().__getattr__(name)  # type: ignore

    def __setattr__(self, __name: str, __value: Any) -> None:
        if self._initialized and __name in self.property_dict:
            raise AttributeError(
                '"{}" is already a property. Set the value using "{}.{}[<ppm>] = {}"'.format(
                    __name, self.name, __name, __value
                )
            )
        return super().__setattr__(__name, __value)

class ADO(am.Ado):
    """ADO class used by AutoMan.

    Parameters are defined as class variables of type `Parameter`.

    *Note:* This class **should not** be manually instantiated. Perform all bootstap code in the `ADO.start` method.

    Attributes:
        args (List[str]): Arguments for current ADO instance as specified in fecManager. Maximum 9 elements.

    """

    custom_classes: Dict[str, type] = {}
    parameter_dict: MutableMapping[str, ParameterInstance] # type: ignore

    __slots__ = ("args", "parameter_dict")

    def __init_subclass__(cls, **kwargs):
        """INTERNAL: Add new ADO classes to global dict for instantiation with AutoMan"""
        super().__init_subclass__(**kwargs)  # type: ignore
        cls.__parameters__ = params = dict()
        
        def get_parameters(cls: type, seen: set[type], collected_params: list[Parameter]):
            for member in vars(cls).values():
                if isinstance(member, Parameter):
                    collected_params.append(member)
            seen.add(cls)

            for parent in cls.mro():
                if parent in seen:
                    continue
                get_parameters(parent, seen, collected_params)
            return collected_params
        
        for param in get_parameters(cls, set(), []):
            params[param._name] = param

        cls.custom_classes[str(cls.__name__)] = cls

    def __init__(
        self,
        name: str,
        ado_class: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        read_cache: bool = True,
        args: List[str] = [],
    ):
        # Use either ado_class parameter or Python class name
        self.__parameters__: Dict[str, Parameter]
        self.ado_class = ado_class or str(self.__class__.__name__)
        # self.__parameter_instances__: Dict[str, ParameterInstance] = {}

        super().__init__(
            name,
            description or str(self.__class__.__doc__),
            self.ado_class,
            version or str(getattr(self, "__version__", None)),
        )
        self.args = args
        # Create dict of parameter instances
        # Loop through class members of type Parameter
        for name, param in self.__parameters__.items():
            # Instantiate parameter as am3.AdoParameter with same properties
            new_param = ParameterInstance(
                self,
                param._name,
                param._type,
                param._count,
                param._features,
                param._initial_value,
                param._ppm_size,
                partial(param._user_setter, self) if param._user_setter else None,
                partial(param._user_getter, self) if param._user_getter else None,
            )
            # If setter is present, bind to this ADO instance
            # new_param.set = partial(new_param._setter, self)  # type: ignore
            for prop in param._properties:
                # Add all properties for each parameters
                new_param.addProperty(*prop)
            # Save to instances dict
            self.parameter_dict[name] = new_param
        if read_cache:
            try:
                self.readCache()
            except Exception as e:
                self.logger.warning("Error reading cache", exc_info=e)

    def addParameter(
        self,
        name: str,
        ptype: Union[Type, str],
        count: int = 1,
        ppm_size: int = 8,
        features: int = Category.ContinuousMeasurement,
        value: Optional[Any] = None,
        setter: Optional[Callable[[Any, int], Any]] = None,
    ):
        """
        Dynamically add a parameter to this ADO instance.
        
        Args:
            name (str): Name of parameter.
            ptype (Union[str, int]): Parameter type.
            count (int, optional): Number of elements in parameter. Defaults to 1.
            ppm_size (int, optional): PPM size of parameter. Defaults to 8.
            features (int, optional): Parameter features. Defaults to Category.ContinuousMeasurement.
            value (Any, optional): Initial value of parameter. Defaults to None.
            setter (Callable[[Any], None], optional): Setter function for parameter. Defaults to None.

        Raises:
            ValueError: If parameter name already exists.
        """
        if isinstance(ptype, str):
            ptype = Type(ptype)

        if value is None:
            value = ptype.initial_value(count)

        self.parameter_dict[name] = parameter = ParameterInstance(
            self, name, ptype, count, features, value, ppm_size
        )
        parameter._user_setter = setter
        return parameter

    def __getitem__(self, item) -> ParameterInstance:
        return self.parameter_dict[item]

    @property
    def logger(self) -> logging.Logger:
        """Retrieve named logger for this ADO"""
        return logging.getLogger(self.name)

    @property
    def manager(self) -> Optional["AutoMan"]:
        """Retrieve manager instance hosting this ADO"""
        return cast(AutoMan, am.activeServer)

    def start(self):
        """Override to perform some action when this ADO's manager starts"""
        pass

    def stop(self):
        """Override to perform some action when this ADO's manager stops"""
        self.writeCache()

    def __setattr__(self, __name: str, __value: Any) -> None:
        if hasattr(self, "parameter_dict") and __name in self.parameter_dict:
            raise AttributeError(
                '"{}" is already a parameter. Set the values using "{}.value[<ppm>] = {}"'.format(
                    __name, __name, __value
                )
            )
        return super().__setattr__(__name, __value)


class AutoMan(am.AdoServer):
    logger = logging.getLogger("AutoMan")

    """Manager class which automatically instantiates ADOs based on class names"""

    def __init__(
        self,
        name: str,
        classes: Dict[str, Type_[ADO]] = {},
        notif_server: str = "RHICNotifServer",
        host: str = "",
        prog: Optional[int] = None,
        vers: Optional[int] = None,
    ) -> None:
        """Instantiate AutoMan instance

        Args:
            name (str): Manager name, must be present in fecManager
            classes (Dict[str, Type[ADO]], optional): Explicitly define ADO classes, such as when alternate Python class names are used. Defaults to {}.
            notif_server (str, optional): Name of notif server to use for this manager. Defaults to "RHICNotifServer".
            host (str, optional): Hostname of machine. Defaults to "".
            prog (Optional[int], optional): RPC program number. Defaults to None.
            vers (Optional[int], optional): RPC version number. Defaults to None.
        """

        # This sets up the global notif server for all ADOs
        if notif_server in notif.SERVERS:
            am.NOTIF_SERVER = notif_server
        else:
            warnings.warn(
                f"Notif server {notif_server} not found, using {am.NOTIF_SERVER} instead"
            )

        super().__init__(name, host, prog, vers)

        # Dictionary of ADO instances
        self.ados: Dict[str, ADO] = {}
        self.custom_classes = classes

        self.reload_ados()

    def reload_ados(self, and_start=False):
        # Connect to serverAdo database
        db_server = "OPSYB1"
        # Find server hostname
        hostname = None
        port = None
        with open("/home/cfsb/sybase/interfaces") as f:
            # print("===open interface file...")
            line = f.readline()
            while line:
                # print("===", line)
                if line.strip() == db_server:
                    line = f.readline()
                    data = line.strip().split()
                    hostname = data[3]
                    port = data[4]
                    # print("====Found host:", hostname, port)
                    break
                line = f.readline()

        if None in (hostname, port):
            raise RuntimeError(f"Could not find hostname or port for {db_server}")

        conn = pyodbc.connect(
            "DRIVER={{Sybase ASE}};SERVER={server};PORT={port};DATABASE={db};UID={username};PWD={password};autocommit=True;timeout=5".format(
                server=hostname,
                port=port,
                db="serverAdo",
                username="harmless",
                password="harmless",
            )
        )

        cursor = conn.cursor()
        # Get all ADO name,class pairs for manager name
        cursor.execute(
            f'select name, adoClass, {", ".join(f"adoArg{i}" for i in range(1, 10))} from adoInst where srvName = ? and (isDisabled != 1 or isDisabled is NULL)',
            (self.name,),
        )

        results = cursor.fetchall()
        conn.close()

        # Use explicit classes, or subclasses of base ADO class
        classes = self.custom_classes or ADO.custom_classes
        bad_classes = set()
        insts: List[ADO] = []
        for name, adoClass, *args in results:
            if name in self.ados:
                # Already instantiated, skip
                continue

            # Attempt to instantiate ADOs for each class instance in DB
            if adoClass not in classes:
                if adoClass not in bad_classes:
                    # Throw warning when Python class not defined for ADO
                    bad_classes.add(adoClass)
                    self.logger.warning("No class supplied for %s", adoClass)
                continue
            cls = classes[adoClass]
            # Instantiate ADO of class `adoClass` and with name `name`
            self.ados[name] = inst = cls(name=name, args=args)
            insts.append(inst)
            self.logger.debug("Created %s(name='%s')", adoClass, name)
            if and_start:
                inst.start()
        return insts

    def start(self, auto_reload=False):
        """Start hosting all detected ADOs (blocks waiting on KeyboardInterrupt, stopping manager after)

        Args:
            auto_reload (bool, optional): Reload ADOs when they change. Changes to existing parameter & property *values* are pushed asynchronously; new, deleted, and modified properties must be refreshed manually. Defaults to False.

        Example:
        
            To hook into this method, override start in a subclass:

                class MyAutoMan(AutoMan):
                    def start(self):
                        # do your thing
                        super().start()
        """
        if auto_reload:
            self._start_reload()
        else:
            self._start_normal()

    def _handle_signal(self, signum, frame):
        self.logger.info("Received signal %d", signum)
        self.reload_ados(and_start=True)

    def _trigger_reload(self):
        import importlib

        self.logger.info("Reloading...")
        classes: Dict[Any, List[Type_]] = {}
        for ado in self.ados.values():
            cls_list = classes.setdefault(inspect.getmodule(type(ado)), [])
            cls_list.append(type(ado))

        new_classes = {}
        for module, classes in classes.items():
            module = importlib.reload(module)

            for class_ in classes:
                new_classes[class_.__name__] = getattr(module, class_.__name__)

        old_ados = self.ados.copy()
        for name, ado in old_ados.items():
            if not ado.__class__.__name__ in new_classes:
                continue
            self.logger.info("Reloading %s", name)
            ado.stop()
            del am.adodict[name]
            inst: ADO = new_classes[ado.__class__.__name__](name=name)
            inst.start()

            param: am.AdoParameter
            prop: am.AdoProperty
            for pname, param in ado.parameter_dict.items():
                if pname not in inst.parameter_dict:
                    continue
                new_param = inst.parameter_dict[pname]
                for prop in param.properties:
                    new_prop: am.AdoProperty = getattr(new_param, prop.name)
                    new_prop.async_requests = [
                        (a1, a2, a3, [new_prop], a5)
                        for a1, a2, a3, a4, a5 in prop.async_requests
                    ]
                    # print(new_prop.async_requests)
                    for i in range(new_prop.ppmSize or 1):
                        new_prop.update(i)

            self.ados[name] = inst

    def _start_reload(self):
        try:
            from watchdog.events import (FileModifiedEvent,
                                         PatternMatchingEventHandler)
            from watchdog.observers import Observer
        except ModuleNotFoundError:
            print("You must install watchdog to use auto reload!")
            print("- Add 'watchdog' to requirements/development.txt")
            print("- Run 'cadpip switch d' to install development dependencies")
            exit(-1)

        class Handler(PatternMatchingEventHandler):
            delay = 1500

            def __init__(self, manager) -> None:
                super().__init__(patterns=["*.py"])
                self.manager = manager
                self.timer: Optional[Timer] = None

            def on_timer(self):
                self.timer = None
                self.manager._trigger_reload()

            def on_modified(self, event):
                if isinstance(event, FileModifiedEvent):
                    if self.timer is not None:
                        self.timer.cancel()
                    self.timer = Timer(self.delay / 1000, self.on_timer)
                    self.timer.start()

        h = Handler(self)
        observer = Observer()
        # paths = set(os.path.dirname(module.__file__) for module in sys.modules.values() if hasattr(module, "__file__") and isinstance(module.__file__, str))
        # for path in paths:
        #     observer.schedule(h, path, recursive=False)
        observer.schedule(h, ".", recursive=True)

        observer.start()
        try:
            self._start_normal()
        finally:
            observer.stop()
            observer.join()

    def _start_normal(self):
        self.logger.info("Starting manager %s with %d ADOs", self.name, len(self.ados))
        for ado in self.ados.values():
            ado.start()

        signal.signal(signal.SIGUSR1, self._handle_signal)
        try:
            self.loop()
        except KeyboardInterrupt:
            self.logger.info("Stopping manager.")
        finally:
            self.stop()

    def stop(self):
        """Stop hosting all detected ADOs

        Example:

            To hook into this method, override stop in a subclass:

                class MyAutoMan(AutoMan):
                    def stop(self):
                        # do your thing
                        super().stop()
        """
        self.run = False
        self.unregister()

        for ado in self.ados.values():
            ado.stop()


if __name__ == "__main__":
    import threading
    import time

    logging.basicConfig(level=logging.DEBUG)

    class simpleSam(ADO):
        """This is the description for the simple ADO class"""

        __version__ = "1.0"  # Specify version w/ a variable

        intS = Parameter(Type.Int, category=Category.ContinuousSetting)
        intS.OperationalHigh(100)

        discreteM = Parameter(Type.String, category=Category.DiscreteMeasurement)
        discreteM.LegalValues("on", "off")
        discreteM.Alarm()

        discreteAlarmS = Parameter(Type.Void, category=Category.DiscreteAction)

        @discreteAlarmS.setter
        def discreteAlarmS_setter(self, value, ppm_user):
            self.discreteM[0] = "fake"
            return value

        intAlarmM = Parameter(Type.Int, category=Category.ContinuousMeasurement)
        tol, level, thresh, text, delay, latch = intAlarmM.Alarm(
            -10, 50, alarm_text="bad bad news", latching=True, delay=0
        )

        int2S = Parameter(Type.Int, category=Category.ContinuousMeasurement)
        mirrorIntM = Parameter(
            Type.Int, category=Category.ContinuousMeasurement, ppm_size=8
        )
        mirrorIntM.Description("This parameter mirrors intS")
        intArrayS = Parameter(Type.Int, count=6, category=Category.ContinuousSetting)
        timeM = Parameter(Type.Int, category=Category.ContinuousMeasurement)

        int3S = Parameter(Type.Int, category=Category.DiscreteSetting)
        int3S.LegalValues(0, 1, 2, 3)

        paramNameS = Parameter(Type.String, category=Category.ContinuousSetting)
        addParamS = Parameter(Type.Void, category=Category.DiscreteAction)

        noSetterS = Parameter(Type.String, category=Category.ContinuousSetting, initial_value=None)

        def __init__(
            self,
            name: str,
            ado_class: Optional[str] = None,
            description: Optional[str] = None,
            version: Optional[str] = None,
            read_cache: bool = True,
            args: List[str] = [],
        ):
            super().__init__(
                name,
                ado_class=ado_class,
                description=description,
                version=version,
                read_cache=read_cache,
                args=args,
            )
            param = self.addParameter(
                "proceduralIntS",
                Type.Int,
                value=0,
                features=Category.ContinuousSetting,
                setter=self.set_intS,
            )
            param.addAlarm(tolerance_function=lambda x: notif.NotifCategory.INFO if (10 < x < 20) else notif.NotifCategory.OK)

        @addParamS.setter
        def add_setter(self, value, ppm):
            name = self.paramNameS[0]
            print("Adding {}".format(name))
            self.addParameter(name, Type.String, features=Category.ContinuousSetting)
            return value
        
        # @intS.setter
        # def set_intS(self, value, ppm):
        #     print("setting intS to", value)
        #     return value

        @intS.getter
        def get_intS(self, value, ppm):
            print("This is the getter", value)
            return value

        # @int2S.setter
        @intS.setter  # Decorates function to be called when intS is set externally
        def set_intS(self, value, ppm, parameter=""):
            print(parameter)
            # print(self[parameter].value.value)
            print(f"parameter {parameter} was {self[parameter][0]} and now is {value}")
            # self.mirrorIntM[
            #     ppm
            # ] = value  # Access the PPM user for the parameter using the indexing operator
            # print(
            #     "mirrorIntM Timestamp:", self.mirrorIntM.timestampSeconds[ppm]
            # )  # Access a property on the parameter
            # self.intArrayS.publish(
            #     [value] * 6, timestamp=0
            # )  # Publish value programatically with explicit timestamp

            # if parameter == "intS":
            #     self.text[0] = "this is a custom alarm text"
            #     self.intAlarmM[0] = value

            return value  # You can return a modified value to replace the one the user supplied

        def start(self):
            print("simple ado starting", self.name)
            threading.Thread(target=self.set_time, daemon=True).start()

        def set_time(self):
            while True:
                t = int(time.time())
                self.timeM[0] = t
                time.sleep(1)

        def stop(self):
            print("simple ado stopping", self.name)

    manager = AutoMan(name="simpleManSam")
    manager.start()
