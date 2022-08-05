# Copyright (c) 2019-2020 Maxon Computer GmbH
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
#
# DISCLAIMER
# THIS SOFTWARE IS PROVIDED BY MAXON COMPUTER GMBH "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sys
import io
import os
import ctypes
import numbers as numbers
import collections
import enum

from typing import Optional  # noqa: F401

from . import type_traits
from . import classinspect
from . import core
from . import consts


from . data import Data, Struct, Id, Builtin  # noqa E402
from . datatype import DataType, MAXON_DATATYPE  # noqa E402
from . decorators import (MAXON_INTERFACE_NONVIRTUAL,
                          MAXON_METHOD, MAXON_STATICFUNCTION,
                          MAXON_STATICMETHOD,
                          MAXON_INTERFACE,
                          MAXON_FUNCTION_EXTEND,
                          MAXON_FUNCTION,
                          MAXON_OVERLOAD,
                          g_converters)  # noqa E402

import _maxon_data  # noqa E402
import _maxon_datatype  # noqa E402
import _maxon_core  # noqa E402
import _maxon_system  # noqa E402
import _maxon_component  # noqa E402
import _maxon_mapping  # noqa E402
import _maxon_memory  # noqa E402
import _maxon_configuration  # noqa E402
import _maxon_container  # noqa E402
import _maxon_application  # noqa E402


import builtins

from maxon_generated import _configuration as configuration  # noqa E402

# Maxon was not loaded yet
_maxon = None

config = configuration.Configurations()

# asap register after class declaration
_maxon_mapping.RegisterSpecialClass("Enum", enum.Enum)


def finally_once(func, *args, **kwargs):
    """
    Executes a function when the current scope is left.

    .. note::

        An optional parameter `canRaise` can be passed to notify that `func` may eventually raise.

    :param func: Function to be called.
    :type func: ``function(*args, **kwargs)``
    :param args: Optional arguments to be passed to func.
    :type args: Any
    :param kwargs: Optional settings like `canRaise` to control if `func` can raise an exception.
    :type kwargs: Any

    .. code-block:: python

        cleanup = finally_once(lambda x: MyFunction(x), canRaise=False)

    """
    canRaise = kwargs.get("canRaise", True)

    class _finally_once:

        _isEnabled = False

        def __call__(self):
            self._isEnabled = True
            try:
                return func(*args)
            except Exception:
                if canRaise:
                    return
                else:
                    raise

        def __del__(self):
            """on destruction the lambda gets executed."""
            if self._isEnabled is False:
                self()

        def Enable(self):
            self._isEnabled = True

        def Disable(self):
            self._isEnabled = False

    return _finally_once()


def PrivateMaxonAttribute(id):
    """
    Alias for a :class:`maxon.InternedId`.
    :param id: The string representation of the :class:`maxon.InternedId` you want to declare.
    :type id: str
    :return: The :class:`maxon.InternedId`.
    :rtype: :class:`maxon.InternedId`
    """
    return InternedId(id)


NOTOK = -1
MAXON_ATTRIBUTE = PrivateMaxonAttribute  # Alias for :class:`maxon.InternedId`.


def SystemPause():
    # os.system("pause") works only on windows
    try:
        eval(input("Press enter to continue..."))
    except SyntaxError:
        pass
    except KeyboardInterrupt:
        pass


def GetDataType(type):
    """
    GetDataType(obj)
    Retrieves the :class:`maxon.DataType` of the passed object.

    :param type: The object to retrieves the :class:`maxon.DataType` from.
    :type: Any maxon API class
    :return: The datatype.
    :rtype: :class:`maxon.DataType`
    """
    assert hasattr(type, "_dt")  # must have a datype
    return type._dt


class CONVERSIONMODE(enum.IntEnum):
    """
    Used by :func:`maxon.MaxonConvert` as last parameter to determine which kind of conversion to process.
    """
    #: Used by default, the inverse of the passed object.
    DEFAULT = 0

    #: # From Maxon API Type (e.g. maxon.Int32) to Python Type (e.g. int).
    TOBUILTIN = 1

    #: From Python Type (e.g. int) to Maxon API Type (e.g. maxon.Int32).
    TOMAXON = 2


def MaxonConvert(*args):
    """
    Convert all passed objects to a maxon or Python object, depending on the passed type.

    .. note::

        Latest arguments determine how the conversion is done by passing a :class:`maxon.CONVERSIONMODE`.

    .. code-block:: python

        import maxon

        # Returns a maxon.Int32 of value 10
        print maxon.MaxonConvert(10)

        # Returns a int of value 10
        print maxon.MaxonConvert(maxon.Int(10))

        # Forces a return value to Maxon API type, in this case a maxon.Int32 of value 10
        print maxon.MaxonConvert(maxon.Int(10), maxon.CONVERSIONMODE.TOMAXON)

        # Forces a return value to Python Builtin, in this case a int of value 10
        print maxon.MaxonConvert(10, maxon.CONVERSIONMODE.TOBUILTIN)

    :param args: The object to converts.
    :type args: Any
    :return: The object converted
    :rtype: Any
    """
    mode = args[-1:]
    if len(mode) > 0 and isinstance(mode[0], CONVERSIONMODE):
        # if the last entry is a converisonmode enum we have to filter it out since this
        # enum is not meant to be converted
        mode = mode[0]
        args = args[:-1]
    else:
        mode = CONVERSIONMODE.DEFAULT

    t = list()
    for data in args:
        if (mode == CONVERSIONMODE.DEFAULT or mode == CONVERSIONMODE.TOBUILTIN) and isinstance(data, Data):
            data = data.MaxonConvert()
        elif mode == CONVERSIONMODE.DEFAULT or mode == CONVERSIONMODE.TOMAXON:
            try:
                data = _maxon_mapping.MaxonConvertAuto(_maxon_data.Data_Create(Data._dt._data, data))
            except Exception:
                pass

        t.append(data)
    t = tuple(t)
    return t[0] if len(t) == 1 else t


class AutoIterator(object):
    """
    AutoIterator implements a foreach iterator for a BaseArray

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    def __init__(self, array, beginIndex=None):
        """
        __init__(array, beginIndex=None)
        Initializes the Iterator with the given BaseArray optionally with an offset.

        :param array: The Array to iterates.
        :type array: BaseArray
        :param beginIndex: Optional offset for the start of the array iteration.
        :type beginIndex: Optional[int]
        """
        if not isinstance(array, BaseArray):
            raise TypeError("expected BaseArray not %s" % str(type(array)))

        self._array = array

        if beginIndex:
            self._currentIndex = beginIndex
        else:
            self._currentIndex = _maxon_container.GenericBaseArray_Begin(self._array._data)

    def __next__(self):
        """
        Retrieves the next element in the array.

        :return: The next element of the array.
        :rtype: Any
        """
        o = _maxon_container.GenericBaseArray_Next(self._array._data, self._currentIndex)
        self._currentIndex += 1  # increment to the next element
        return _maxon_mapping.MaxonConvertAuto(o)


@MAXON_DATATYPE("net.maxon.datatype.sourcelocation")
class SourceLocation(Data, Struct):
    """
    An object to represents the current file location. This can either to trace error or memory leak.
    """
    #: (str) The file represented by this Source Location.
    file = str()

    #: (int) The line number represented by this Source Location.
    lineAndFlags = 0

    __maxon_array_convert__ = {"file": -1}

    def __init__(self, f=None, line=None):
        """
        __init__(f=None, line=None)
        Initializes a Source location with a given file and line

        :param f: The file represented.
        :type f: Optional[str]
        :param line: The line represented.
        :type line: Optional[int]
        """
        super(SourceLocation, self).__init__(None)
        if f is not None and line is not None:
            _maxon_data.SourceLocation_SetFileLineAndFlags(self._data, f, line)

    def GetLine(self):
        """
        GetLine()
        Retrieves the line represented by the source location object.

        :return: The line represented by the source location object.
        :rtype: int
        """
        return self.lineAndFlags

    def GetFile(self):
        """
        GetFile()
        Retrieves the file represented by the source location object.

        :return: The file represented by the source location object.
        :rtype: str
        """
        return self.file


def MAXON_SOURCE_LOCATION(offset=0):
    """
    MAXON_SOURCE_LOCATION(offset=0)
    Creates a SourceLocation object for the current Python Frame.

    :param offset: Optional trace back offset to retrieve the current source location from.
    :type offset: Optional[int])
    :return: The source location corresponding to the Python frame calling this function.
    :rtype: :class:`maxon.SourceLocation`
    """
    loc = _maxon_core.GetCurrentTraceback()[-1 - offset]
    return SourceLocation(loc[0], loc[1])


@MAXON_DATATYPE("net.maxon.python.datatype.unknowndatatype")
class UnknownDataType(Data, Struct):
    """
    Class for all data objects, that have no proper wrapper
    class in Python. This can happen, if a function returns an
    instance of an object, that is unknown to Python. To still
    be able to receive the object, an instance of this class is
    returned instead. It's use is limited, since Python doesn't
    know, how the underlying object looks like, or which functions
    it has on the C++ side. However, it can be automatically passed
    to a function, which accepts an object which matches the data
    type of it. If the data type of the object got registered via
    MAXON_DATATYPE_REGISTER_STRUCT on the C++ side, you can use
    UnknownDataType.MaxonConvert() to convert its members to a dict.
    The dict can alternatively be used then to pass to a function
    that expects a type of this object.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    def __str__(self):
        return "UnknownDataType({})".format(_maxon_datatype.DataType_GetId(_maxon_data.Data_GetRealType(self._data)))

    def __repr__(self):
        return "UnknownDataType({})".format(_maxon_datatype.DataType_GetId(_maxon_data.Data_GetRealType(self._data)))

    def GetId(self):
        """
        GetId()
        Retrieves the :class:`maxon.Id` of the current Data.

        :return: The :class:`maxon.Id` of the current Data holds by the current :class:`maxon.UnknownDataType` instance.
        :rtype: :class:`maxon.Id`
        """
        return _maxon_datatype.DataType_GetId(_maxon_data.Data_GetRealType(self._data))

    def GetType(self):
        """
        GetType()
        Returns the data type of the underlying data object.
        This function overwrites maxon.Data.GetType() because
        the data type of UnknownDataType would be returned instead.

        :return: Data type of the underlying data type.
        :rtype: :class:`maxon.DataType`
        """
        return DataType(_maxon_data.Data_GetRealType(self._data))

    def MaxonConvert(self, expected=dict):
        """
        MaxonConvert(expected=dict)
        | If the data type of the underlying object is a 'known' struct, the object will be converted
          to a dict, where each key and value matches the name and values of the C++ struct.
        | A 'known struct' is a data type, that got registered via MAXON_DATATYPE_REGISTER_STRUCT
          in the originated C++ module. If no proper conversion can be found, self will be returned.

        :return: Converted object or self if the datatype is not registered
                 internally as a struct via MAXON_DATATYPE_REGISTER_STRUCT.
        :rtype: Any
        """

        return super(UnknownDataType, self).MaxonConvert(expected)


@MAXON_DATATYPE("net.maxon.datatype.configinit")
class ConfigInit(Data, Struct):
    """
    Represents an config entry value.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.

    To access configuration, please use config.XXXX to access the configuration value.

    .. code-block:: python

        # Display the default preference path
        tempFile = maxon.config.g_prefsPath
    """

    __maxon_array_convert__ = {"key": -1,
                               "helpText": -1}

    #: The key representing the value into the maxon.config dict.
    key = str()

    #: A help text to know why this config is used for.
    helpText = str()

    #: The value stored for the key into the the maxon.config dict.
    value = None

    #: Stores the minimal value possible.
    minValue = None

    #: Stores the maximum value possible.
    maxValue = None

    #: Stores the default value.
    default = None

    #: Stores the type of the entry (bool, int, float, string).
    type = None

    #: Defines a boolean type.
    CONFIGURATION_DATATYPE_BOOL = 0

    #: Defines an integer type.
    CONFIGURATION_DATATYPE_INT = 1

    #: Defines a float type.
    CONFIGURATION_DATATYPE_FLOAT = 2

    #: Defines a pointer type.
    CONFIGURATION_DATATYPE_STRING_C = 3

    #: Defines a string type.
    CONFIGURATION_DATATYPE_STRING = 4


@MAXON_DATATYPE("net.maxon.datatype.universaldatetime")
class UniversalDateTime(Data):
    """
    | Class that represents the Universal date-time (UTC+0000).
    |
    | This class should be used whenever you store date and time data and should be converted to the
      :class:`maxon.LocalDateTime` for a local output as late as possible.
    | The internal representation is an unsigned 64-Bit integer and contains the standard Unix date-time starting
      with 01/01/1970-00:00 UTC+0000.
    |
    | The resolution of this date-time class is 1-second.

    .. seealso::

        :class:`maxon.LocalDateTime`
    """

    def ConvertToLocalDateTime(self):
        """
        ConvertToLocalDateTime()
        Converts the universal date-time to a local date-time object in the current timezone.

        :return: The local date-time object.
        :rtype: :class:`maxon.LocalDateTime`
        """
        return LocalDateTime(_maxon_data.UniversalDateTime_ConvertToLocalDateTime(self._data))

    @staticmethod
    def FromUnixTimestamp(timestamp):
        """
        FromUnixTimestamp(timestamp)
        Create a universal date-time object by passing a Unix time stamp.

        :param timestamp: The unix time stamp to be converted.
        :type timestamp: int
        :return: The universal date-time representation.
        :rtype: :class:`maxon.UniversalDateTime`
        """
        return UniversalDateTime(_maxon_data.UniversalDateTime_FromUnixTimestamp(timestamp))


@MAXON_DATATYPE("net.maxon.datatype.localdatetime")
class LocalDateTime(Data):
    """
    | At some point developers have to deal with times, dates and timezones.
    |
    | This topic can promote headaches because it can be quite complex.
    | In general you have to be aware of differences in timezones, especially when your software runs on mobile devices
      are you let the user share data across countries (or even within the same country).
    |
    | The implementation and definition of the classes rely on the ISO 8601.
    | Use the :class:`maxon.UniversalDateTime` whenever possible to store normalized time and date values and convert
      them to a :class:`maxon.LocalDateTime` instance as late as possible (e.g. for a local string output).
    |
    | An object representing a local 'time and date' of the current system time.
    | All members are public and are allowed to be modified for custom needs.
    | Keep in mind that you have to ensure that the values are correct and valid when converting an object back to
      :class:`maxon.UniversalDateTime`, otherwise the behavior is undefined.

    .. seealso::

        :class:`maxon.UniversalDateTime`
    """
    def ConvertUniversalDateTime(self):
        """
        ConvertUniversalDateTime()
        Converts the stored time to a Universal Date Time.

        :return: The universal date-time object.
        :rtype: :class:`maxon.UniversalDateTime`
        """
        return UniversalDateTime(_maxon_data.LocalDateTime_ConvertUniversalDateTime(self._data))

    @staticmethod
    def FromUnixTimestamp(timestamp):
        """
        FromUnixTimestamp(timestamp)
        Create a local date-time object by passing a Unix time stamp.

        :param timestamp: The unix time stamp to be converted.
        :type timestamp: int
        :return: The local date-time representation.
        :rtype: :class:`maxon.LocalDateTime`
        """
        return LocalDateTime(_maxon_data.LocalDateTime_FromUnixTimestamp(timestamp))


@MAXON_DATATYPE("net.maxon.datatype.delegatebase")
class DelegateBase(Data):
    """
    Delegate base class which can be used for :class:`maxon.DataType`.
    """
    pass


@MAXON_DATATYPE("net.maxon.datatype.threadref")
class ThreadRef(Data):
    """
    Reference to a :class:`maxon.ThreadInterface`.
    """
    pass


@MAXON_DATATYPE("Generic-B")
class Block(Data):
    """
    | A :class:`maxon.Block` stands for a number of elements with a regular memory layout.
    | It consists of a pointer for the first element, the element count and optionally a stride.
    | All elements are placed consecutively in memory, but with a possible padding in between.
    | The stride is the pointer difference between consecutive elements in bytes.
    | y default, the stride is just SIZEOF(T).
    |
    | You can use an alternative stride length to access only specific elements of your array.
    | For example if you have an array with XYZ vectors and want to access only the X-values as a block,
      you could use the pointer to the first X-value and a stride length of SIZEOF(Vector).
    | Or for a :class:`maxon.Block` whose elements are all the same, you can use a stride of 0 and a pointer to
      a single value.
    |
    | There is an important difference between a Block and arrays such as BaseArray with respect
    | to the meaning of a const Block: A const block can't be modified itself, so its pointer and length cannot be
    | changed, but the memory to which the block points is still non-const (if #T is a non-const type).
    | So you can modify the memory through a const block. In other words, a[13] = 42;
    |
    | A :class:`maxon.Block` supports the usual array functions which do not modify the length.
    | Also it can be converted to the Array interface.
    | If unsupported functions are invoked then, they will cause a DebugStop and indicate a failure on return.
    """
    pass


@MAXON_DATATYPE("Generic-S")
class StridedBlock(Data):
    """
    Similar to a :class:`maxon.Block`.

    .. seealso::

        :class:`maxon.Block`
    """
    pass


def ToBlock(data, size, stride=None, dt=None):
    """
    Makes a :class:`maxon.Block` or a :class:`maxon.StridedBlock` from a pointer, a size and a stride.

    :param data: The data to transform to a Block.
    :type data: Any.
    :param size: Number of elements.
    :type size: int
    :param stride: Element stride.
    :type stride: int
    :param dt: The Datatype of the data to be converted as block
    :type dt: :class:`maxon.DataType`
    :return: A block of elements for this data and datatype.
    :rtype: Union[:class:`maxon.StridedBlock`, :class:`maxon.Block`]
    """
    if stride is None:
        if dt is None:
            GENERIC = type_traits.std.is_same(data._dt, Generic._dt).value
            StrideType = type_traits.std.conditional(GENERIC, Char, data).type
            stride = type_traits.SIZEOF(StrideType)
        else:
            GENERIC = type_traits.std.is_same(data._dt, Generic._dt).value
            StrideType = type_traits.std.conditional(GENERIC, Char, data).type
            stride = dt.GetSize()

    if (dt if dt else data._dt).GetSize() != stride:
        return StridedBlock(_maxon_container.ToBlock(data, size, stride, True))
    else:
        return Block(_maxon_container.ToBlock(data, size, stride, False))


from maxon_generated import _enums as enums  # noqa E402


@MAXON_DATATYPE("net.maxon.python.datatype.basearray")
class BaseArray(Data):
    """
    A generic array class template used to stored any kind of data. It is based on
    :class:`maxon.BaseCollection` and :class:`maxon.Collection`.
    """

    class BaseArrayOwnership:
        """Baseclass to define different :class:`maxon.BaseArray` ownership."""

    class BaseArrayNew(BaseArrayOwnership):
        """If BaseArray._owner is set with BaseArray.BaseArrayNew() then it's clear that the creator is the owner of the array."""

    class BaseArrayBorrowed(BaseArrayOwnership):
        """If BaseArray._owner is set with BaseArray.BaseArrayBorrowed() then it's clear that the array belongs to someone else and that
        it will be freed by someone else since BaseArrays are not refounted internally (behind the native layer).
        """

    __typeBorrowed = BaseArrayBorrowed()
    __typeNew = BaseArrayNew()

    def __maxon_init__(self, capsule):
        if not isinstance(capsule, _maxon_data.Data_GetCapsuleType()):
            raise TypeError("expected capsule type")

        dt = DataType(_maxon_data.Data_GetRealType(capsule))

        # too early to import maxon_generated for VALUEKIND::BASEARRAY
        # on top-level, so define value manually, 1LL << 26
        VALUEKIND_BASEARRAY = 1 << 26

        if not dt.CheckValueKind(VALUEKIND_BASEARRAY):
            raise TypeError("passed capsule is not an array (ob={})".format(capsule))

        self._data = capsule
        self._dt = dt
        return self

    def __init__(self, ob=None, input=None, count=None):  # noqa C901
        """
        | Initialize the BaseContainer in order to store a given type. At the moment only maxon Data Type are supported.
        |
        | If it is an iterable the items are copied over

        :param ob: If it's a string:

            1. Example 1: "net.maxon.interface.string-C" creates an array of string objects

            2. Example 2: "net.maxon.interface.string-C[A]" creates an array of string arrays

            If it's a datatype capsule e.g :class:`maxon.Int32` it will only accept this kind of datatype later.

        :type ob: Union[str, datatype capsule, WrapperClass] (e.g. maxon.Int32 or maxon.BaseTime)
        :param input: If it's an integer, resize the array with this number, if it's an iterable the data are copied.
        :type input: Optional(Union[int, collections.Iterable])
        :param count: Number of elements to fill/copy in case if input is passed.
        :type count: Optional(int)
        """

        if ob is None:
            return  # create empty BaseArray wrapper
        elif isinstance(ob, BaseArray):
            raise TypeError("copy constructor not implemented")
        elif isinstance(ob, str):
            # strings can be used to force create a
            # Example 1: "net.maxon.interface.string-C" creates an array of string objects
            # Example 2: "net.maxon.interface.string-C[A]" creates an array of string arrays
            dt = DataType.Get(ob)
        elif isinstance(ob, type) and issubclass(ob, Data):
            dt = ob._dt
        elif isinstance(ob, type) and (ob is int or ob is float or ob is str):
            # support standard Python types for int, float, long and str
            dt = DataType.Get(ob.__name__, lookupPythonTypes=True)
        elif isinstance(ob, DataType):
            dt = ob
        else:
            raise TypeError("unknown type of 'ob' to initialize BaseArray (ob={})".format(ob))

        self._dt = dt.GetBaseArrayType()
        if self._data is None:
            self._data = self._dt.Create()

        # This basearray must be freed when quitted
        # If Borrowed() the BaseArray belongs to someone else
        # self._owner = BaseArray.Borrowed()
        self._owner = BaseArray.__typeNew

        if input and count:
            # the user must pass an iterable
            raise AttributeError("input or count is supported, not both")
        elif isinstance(input, int):
            self.Resize(input)
        elif isinstance(input, collections.abc.Iterable):
            self.Resize(len(input))
            for i, item in enumerate(input):
                self[i] = item
        elif isinstance(count, int):
            if count:
                self.Resize(count)
        elif input is not None or count is not None:
            raise AttributeError("invalid constructor call")
        # else input and count are None it's fine
        # as long as the input type was given

    def __iter__(self):
        return AutoIterator(self)

    def __len__(self):
        # __len__() and GetCount() return the same value
        return _maxon_container.GenericBaseArray_GetCount(self._data)

    def __getitem__(self, item):
        o = _maxon_container.GenericBaseArray_GetByIndex(self._data, item)
        return _maxon_mapping.MaxonConvertAuto(o)

    def __setitem__(self, index, value):
        return _maxon_container.GenericBaseArray_Set(self._data, index, value)

    def __str__(self):
        dt = self._dt.GetElementType()
        return "maxon.BaseArray('" + dt.GetId() + "', input=" + str(self.GetCount()) + ")"

    def __repr__(self):
        return self.__str__()

    def Resize(self, newCnt, resizeFlags=enums.COLLECTION_RESIZE_FLAGS.DEFAULT):
        """
        Resize(newCnt, resizeFlags=enums.COLLECTION_RESIZE_FLAGS.DEFAULT)
        | Resizes the array to contain `newCnt` elements.
        | If `newCnt` is smaller than :func:`BaseArray.GetCount` all extra elements are being deleted.
        | If it is greater the array is expanded and the default constructor is called for new elements.

        :param newCnt: New array size.
        :type newCnt: int
        :param resizeFlags: How the resizing should be performed.
        :type resizeFlags: :class:`maxon.COLLECTION_RESIZE_FLAGS`
        """
        return _maxon_container.GenericBaseArray_Resize(self._data, newCnt, resizeFlags)

    def Insert(self, index, value):
        """
        Insert(index, value)
        Inserts a new element at index position.

        :param index: position
        :type index: int
        :param value: The value to be copied.
        :type value: Any
        """
        o = _maxon_container.GenericBaseArray_Insert(self._data, index, value)
        return _maxon_mapping.MaxonConvertAuto(o)

    def Append(self, value):
        """
        Not Implemented yet, use Resize and [].
        """
        self.Resize(self.GetCount()+1)
        self[self.GetCount()-1] = value

        return self[self.GetCount()-1]

    def GetCount(self):
        """
        GetCount()
        Gets the number of array elements.

        :return: Number of array elements.
        :rtype: int
        """
        # __len__() and GetCount() return the same value
        return _maxon_container.GenericBaseArray_GetCount(self._data)

    def ToBlock(self):
        """
        ToBlock
        Returns a :class:`maxon.Block` which represents the elements of the array.

        :return: The content of this array as a block.
        :return: :class:`maxon.Block`
        """
        return ToBlock(self, self.GetCount(), dt=self._dt.GetElementType())

    def CopyFrom(self, other):
        if not isinstance(other, BaseArray):
            raise TypeError("Expected a BaseArray")
        return _maxon_container.GenericBaseArray_CopyFrom(self._data, other._data)


# directly register after basearray definition
_maxon_mapping.RegisterSpecialClass("BaseArray", BaseArray)


class Pair(Data):
    """
    | :class:`maxon.Pair` provides in-place static storage for elements of arbitrary types.
    | It is similar to a :class:`maxon.Tuple`, but supports only 2 elements.
    """

    _returnType = CONVERSIONMODE.TOMAXON
    _ownership = consts.ReturnTypeOwnership.CALLEE_BUT_COPY

    def __maxon_convert__(self, expected=None):
        if expected is None:
            expected = tuple

        if expected is tuple or expected is list:
            count = len(_maxon_datatype.DataType_GetTypeArguments(_maxon_data.Data_GetRealType(self._data)))
            return expected(_maxon_container.Tuple_GetMember(self._data, x, None, self._ownership) for x in range(count))
        else:
            raise TypeError()

    def __init__(self, typename):
        super().__init__()
        if isinstance(typename, collections.abc.Iterable):
            firstType = typename[0]
            if not issubclass(firstType, Data):
                raise TypeError("typename argument must be str, or list with types of Data, not {}".format(typename))
            constructedTypename = "(" + firstType._dt.GetId()
            secondType = None

            if len(typename) == 2:
                secondType = typename[1]
                if not issubclass(secondType, Data):
                    raise TypeError("typename argument must be str, or list with types of Data, not {}".format(typename))
                constructedTypename += "," + secondType._dt.GetId()

            typename = constructedTypename + ")"

        if isinstance(typename, str):  # also accepts string for typename in datatype syntax. e.g: (maxon.datatype.int32, maxon.datatype.int32)
            self._data = DataType.Get(typename).Create()
        elif isinstance(typename, self._capsuleType):
            self._dt = DataType(_maxon_data.Data_GetRealType(typename))
            self._data = typename

    def __getitem__(self, item):
        return self.Get(item)

    def __setitem__(self, key, value):
        return self.Set(key, value)

    def __iter__(self):
        yield self.GetFirst()
        yield self.GetSecond()

    def SetReturnType(self, type):
        """
        SetReturnType(type)
        Defined the returned type.

        :param type: The return type expected.
        :type: type
        """
        self._returnType = type

    def GetFirst(self):
        """
        GetFirst()
        Retrieves the first entry stored in the `maxon.Pair`.

        :return: The first entry of this `maxon.Pair`.
        :rtype: Any
        """
        return self.Get(0)

    def GetSecond(self):
        """
        GetSecond()
        Retrieves the second entry stored in the `maxon.Pair`.

        :return: The second entry of this `maxon.Pair`.
        :rtype: Any
        """
        return self.Get(1)

    def GetTypeArguments(self):
        """
        GetTypeArguments()
        Retrieves the :class:`maxon.DataType` from an argument

        :return: The list of argument and :class:`maxon.DataType`.
        :rtype: list[:class:`maxon.DataType`, type)
        """
        return [DataType(x[0]) for x in _maxon_datatype.DataType_GetTypeArguments(_maxon_data.Data_GetRealType(self._data))]

    def _GetIndex(self, ELEMENTTYPE):
        if isinstance(ELEMENTTYPE, numbers.Number):
            return ELEMENTTYPE
        elif issubclass(ELEMENTTYPE, Data):
            ELEMENTTYPE = ELEMENTTYPE._dt
        elif isinstance(ELEMENTTYPE, str):
            ELEMENTTYPE = DataType.Get(ELEMENTTYPE)

        index = -1
        for i, dt in enumerate(self.GetTypeArguments()):
            if ELEMENTTYPE == dt:
                if index != -1:
                    raise LookupError("ELEMENTTYPE must occur exactly once in given tuple")

                index = i
                # no break here, we have to check how many times the elementtype occurs to raise an exception if it does more than once

        if index == -1:
            raise LookupError("{} not found in tuple".format(ELEMENTTYPE.GetId()))
        else:
            return index

    def Get(self, ELEMENTTYPE):
        """
        Get(ELEMENTTYPE)
        Returns an entry of the Pair.

        :param ELEMENTTYPE: The index of the element to retrieve from the this `maxon.Pair`.
        :type ELEMENTTYPE: int
        :return: The data stored
        :rtype: Any
        """
        return _maxon_container.Tuple_GetMember(self._data, self._GetIndex(ELEMENTTYPE), Data
                                                if self._returnType == CONVERSIONMODE.TOMAXON else None, self._ownership)

    def Set(self, ELEMENTTYPE, obj):
        """
        Set(ELEMENTTYPE, obj)
        Defines a value of the Pair.

        :param ELEMENTTYPE: The index of the element to set the value from the this `maxon.Pair`.
        :type ELEMENTTYPE: int
        :param obj: The data to store stored
        :type obj: Any
        """
        return _maxon_container.Tuple_SetMember(self._data, self._GetIndex(ELEMENTTYPE), obj)


class Tuple(Pair):
    """
    | :class:`maxon.Tuple` provides in-place static storage for elements of arbitrary types.
    | It is similar to a :class:`maxon.Pair`, but supports a variable number of elements.
    """
    def __init__(self, typename):
        super().__init__(typename)
        if isinstance(typename, collections.abc.Iterable):
            constructedTypename = "(" + ",".join([str(x._dt.GetId()) for x in typename]) + ")"
            typename = constructedTypename

        # also accepts string for typename in datatype syntax. e.g: (maxon.datatype.int32, maxon.datatype.int32)
        if isinstance(typename, str):
            self._data = DataType.Get(typename).Create()
        elif isinstance(typename, self._capsuleType):
            self._dt = DataType(_maxon_data.Data_GetRealType(typename))
            self._data = typename


@MAXON_DATATYPE("net.maxon.python.datatype.tuple")
def PairAndTupleFactory(data):
    """
    Creates a :class:`maxon.Tuple` or :class:`maxon.Pair` according the amount of argument passed.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    if len(_maxon_datatype.DataType_GetTypeArguments(_maxon_data.Data_GetRealType(data))) > 2:
        return Tuple(data)
    else:
        return Pair(data)


_maxon_mapping.RegisterSpecialClass("Tuple", Tuple)


try:
    _maxon = __import__("_maxon")
except ImportError:
    # If _maxon cannot be imported we can assume we are outside of the kernel
    # so a dummy module can be used that simple imports don't fail

    class DummyCreator(object):
        def __getattr__(self, name):
            """TODO."""
            raise ImportError("failed to import _maxon")
    _maxon = DummyCreator


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.string")
class StringInterface(Builtin):
    """
    | Class to store unicode strings. String stores 16bit unicode characters.
    | Any characters are legal, including 0C (strings are not null-terminated).
    | Strings are reference-counted objects.
    |
    | This means that as long as you copy and do not modify strings they are just referenced.
    | The first modification breaks the link and it becomes a unique new object.
    """
    pass


@MAXON_DATATYPE("Generic")  # special Id for Generic
class Generic(Builtin):
    """
    The data type represents the :class:`maxon.Generic` type.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    c_type_p = ctypes.POINTER(ctypes.c_char)


@MAXON_DATATYPE("bool")
class Bool(Builtin):
    """Boolean type, possible values are only False/True, 8 bits."""
    c_type_p = ctypes.POINTER(ctypes.c_bool)


@MAXON_DATATYPE("float32")
class Float32(Builtin):
    """
    Floating point value 32 bits (float).
    """
    #: Stores the ctype type (ctypes.c_float).
    c_type = ctypes.c_float

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (-3.402823466e+38).
    MIN = -3.402823466e+38

    #: Stores the minimal value possible for this class (3.402823466e+38).
    MAX = 3.402823466e+38


@MAXON_DATATYPE("float64")
class Float64(Builtin):
    """
    Floating point value 64 bits (double).
    """
    #: Stores the ctype type (ctypes.c_double).
    c_type = ctypes.c_double

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (-1.7976931348623158e+308).
    MIN = -1.7976931348623158e+308

    #: Stores the minimal value possible for this class (1.7976931348623158e+308).
    MAX = 1.7976931348623158e+308

    #: Stores the size of the DataType (8).
    SIZEOF = 8


@MAXON_DATATYPE("uint16")
class UInt16(Builtin):
    """
    Unsigned integer 16 bits (always positive number).
    """
    #: Stores the ctype type (ctypes.c_uint16).
    c_type = ctypes.c_uint16

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (0).
    MIN = 0

    #: Stores the minimal value possible for this class (65535).
    MAX = 0xffff


@MAXON_DATATYPE("uint32")
class UInt32(Builtin):
    """
    Unsigned integer 32 bits (always positive number).
    """
    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(ctypes.c_uint32)

    #: Stores the minimal value possible for this class (0).
    MIN = 0

    #: Stores the minimal value possible for this class (4294967295).
    MAX = 0xffffffff


@MAXON_DATATYPE("uint64")
class UInt64(Builtin):
    """
    Unsigned integer 64 bits (always positive number).
    """
    #: Stores the ctype type (ctypes.c_uint64).
    c_type = ctypes.c_uint64

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (0).
    MIN = 0

    #: Stores the minimal value possible for this class (18446744073709551615).
    MAX = 0xffffffffffffffff

    #: Stores the size of the DataType (8).
    SIZEOF = 8


@MAXON_DATATYPE("int16")
class Int16(Builtin):
    """
    Signed integer 16 bits (either positive or negative number).
    """
    #: Stores the ctype type (ctypes.c_int16).
    c_type = ctypes.c_int16

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (-32768).
    MIN = -32767 - 1

    #: Stores the minimal value possible for this class (32767).
    MAX = 32767


@MAXON_DATATYPE("int32")
class Int32(Builtin):
    """
    Signed integer 32 bits (either positive or negative number).
    """
    #: Stores the ctype type (ctypes.c_int32).
    c_type = ctypes.c_int32

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (-2147483648).
    MIN = -2147483647 - 1

    #: Stores the minimal value possible for this class (2147483647).
    MAX = 2147483647


@MAXON_DATATYPE("int64")
class Int64(Builtin):
    """
    Signed integer 64 bits (either positive or negative number).
    """
    #: Stores the ctype type (ctypes.c_int64).
    c_type = ctypes.c_int64

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (-9223372036854775808).
    MIN = -9223372036854775807 - 1

    #: Stores the minimal value possible for this class (9223372036854775807).
    MAX = 9223372036854775807

    #: Stores the size of the DataType (8).
    SIZEOF = 8


@MAXON_DATATYPE("char")
class Char(Builtin):
    """
    Signed 8 bits character.
    """
    #: Stores the ctype type (ctypes.c_char).
    c_type = ctypes.c_char

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (-128).
    MIN = -127 - 1

    #: Stores the minimal value possible for this class (127).
    MAX = 127


@MAXON_DATATYPE("uchar")
class UChar(Builtin):
    """
    Unsigned 8 bits character.
    """
    #: Stores the ctype type (ctypes.c_ubyte).
    c_type = ctypes.c_ubyte

    #: Stores the ctype pointer type.
    c_type_p = ctypes.POINTER(c_type)

    #: Stores the minimal value possible for this class (0).
    MIN = 0

    #: Stores the minimal value possible for this class (255).
    MAX = 0xff


@MAXON_DATATYPE("net.maxon.datatype.internedid")
class InternedId(Builtin):
    """
    | :class:`maxon.InternedId` represents an :class:`maxon.Id` which has been interned into a pool of unique
      :class:`maxon.Id` objects.
    |
    | I.e., there are no two different Id objects with an equal id string,
      so for equality comparison you can compare pointers instead of whole strings.
    """

    def __repr__(self):
        return "maxon.InternedId('" + self.ToString() + "')"


class IdStruct(ctypes.Structure, Data):
    """
    Structure that represents an :class:`maxon.Id`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
        | Directly use :class:`maxon.Id`
    """
    _fields_ = [("value", ctypes.c_char_p),
                ("hash", UInt64.c_type)]


class InternedIdStruct(ctypes.Structure):
    """Structure that represents an :class:`maxon.InternedId`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
        | Directly use :class:`maxon.InternedId`

    """
    _fields_ = [("_id", ctypes.POINTER(IdStruct)), ]


Int = Int64 if core.MAXON_TARGET_64BIT else Int32
Float = Float64 if core.MAXON_TARGET_64BIT else Float32
UInt = UInt64 if core.MAXON_TARGET_64BIT else UInt32


def InternedIdToString(addr):
    """
    InternedIdToString(addr)
    Converts a :class:`maxon.InternedId` to a Python string

    :param addr: The :class:`maxon.InternedId` to convert.
    :type addr: :class:`maxon.InternedId`
    :return: The string representation.
    :rtype: str
    """
    iid = ctypes.cast(addr, ctypes.POINTER(InternedIdStruct))[0]
    return iid._id[0].value


def MAXON_INTERFACE_REFERENCE():
    """
    Decorator to defines an Interface that can be treated as Reference at the same time.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    def PRIVATE_MAXON_INTERFACE_REFERENCE(cls):
        if not issubclass(cls, Data):
            raise Exception("the class must be derived from maxon.Data")

        cls._isReference = True
        cls._id = classinspect.MetaClassInformation.mro(cls)
        cls._ids = classinspect.MetaClassInformation.CreateDataTypeId(cls)

        # cls._dt = datatype.DataType.Get(cls._ids)
        # _mapping.RegisterClass(cls._dt._data, cls)

        return cls
    return PRIVATE_MAXON_INTERFACE_REFERENCE


@MAXON_INTERFACE_REFERENCE()
@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.registryentryiterator")
class RegistryEntryIteratorInterface(Data):
    """
    RegistryEntryIteratorInterface is used internally by :func:`Registry.Iterator`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """

    _returnType = CONVERSIONMODE.DEFAULT

    def __del__(self):
        self.Free(self._data)

    def SetReturnType(self, returnType):
        self._returnType = returnType

    @MAXON_METHOD("net.maxon.interface.registryentryiterator.HasValue")
    def HasValue(self):
        """
        HasValue()
        True if the object still contains value to iterate.

        :return: True if the object still contains value to iterate.
        :rtype: bool
        """
        pass

    @MAXON_METHOD("net.maxon.interface.registryentryiterator.MoveToNext")
    def MoveToNext(self):
        """
        MoveToNext()
        Move to the next entry from the :class:`maxon.DataDictionary`.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.registryentryiterator.GetId", returnOwnership=consts.ReturnTypeOwnership.CALLEE)
    def GetId(self):
        """
        GetId()
        Returns the :class:`maxon.Id`.

        :return: The id
        :rtype: :class:`maxon.Id`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.registryentryiterator.GetEntry", returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def _PrivateGetEntryDefault(self):
        pass

    @MAXON_METHOD("net.maxon.interface.registryentryiterator.GetEntry", returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY, returnType=consts.ReturnTypeConversion.NO)
    def _PrivateGetEntryDefaultToBuiltin(self):
        pass

    @MAXON_METHOD("net.maxon.interface.registryentryiterator.GetEntry", returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY, returnType=consts.ReturnTypeConversion.NO)
    def _PrivateGetEntryToMaxon(self):
        pass

    @MAXON_FUNCTION("net.maxon.interface.registryentryiterator.GetEntry")
    def GetEntry(self):
        """
        GetEntry()
        Retrieve the current entry

        :return: The value for the current entry.
        :rtype: Any
        """
        if self._returnType == CONVERSIONMODE.DEFAULT:
            return self._PrivateGetEntryDefault()
        elif self._returnType == CONVERSIONMODE.TOBUILTIN:
            return self._PrivateGetEntryDefaultToBuiltin()
        else:
            return MaxonConvert(self._PrivateGetEntryDefaultToBuiltin())

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.registryentryiterator.Free")
    def Free():
        """
        Free()
        Free the resource used by the iterator.
        """
        pass

    def __iter__(self):
        while self.HasValue():
            yield self.GetEntry()
            self.MoveToNext()


@MAXON_INTERFACE_REFERENCE()
@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.registry")
class RegistryInterface(Data):
    """
    :class:`maxon.RegistryInterface` is used internally by :class:`maxon.Registry`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    @MAXON_METHOD("net.maxon.interface.registry.GetStamp")
    def GetStamp(self):
        """
        GetStamp()
        Returns the registry stamp.

        :return: The registry stamp.
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.registry.GetId")
    def GetId(self):
        """
        GetId()
        Returns the :class:`maxon.Id`.

        :return: The id
        :rtype: :class:`maxon.Id`
        """
        pass

    @staticmethod
    def InsertEntry(registry, eid, value):
        """
        InsertEntry(registry, eid, value)
        Registers an entry at the registry under the given identifier.

        .. note::

            If an entry already exists for the identifier, nothing happens, and an error is raised.

        :param registry: The registry to add the data.
        :type registry: :class:`maxon.Registry`
        :param eid: Identifier within this registry.
        :type eid: :class:`maxon.Id`
        :param value: Value to register.
        :type value: :class:`maxon.Data`
        """
        _maxon_data.RegistryInterface_InsertEntry(registry, eid, value)

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.registry.EraseEntry")
    def EraseEntry(registry, eid):
        """
        EraseEntry(registry, eid)
        Removes the entry identified by eid from registry.

        .. note::

            If no such entry exists, nothing happens.

        :param registry: The registry to add the data.
        :type registry: :class:`maxon.Registry`
        :param eid: Identifier within this registry.
        :type eid: :class:`maxon.Id`
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.registry.PrivateCreateIterator', returnOwnership=consts.ReturnTypeOwnership.CALLEE)
    # INFORMATION: The return value of PrivateCreateIterator is owned by the caller, NOT the callee. But we pretend it is the case, so the caller has to manually
    # execute RegistryEntryIteratorInterface.Free(..) so it matches the look and feel of cpp code.
    def CreateIterator(reg):
        """
        CreateIterator(reg)
        Returns an iterator over all entries registered at this registry.

        :param reg: The registry.
        :type reg: :class:`maxon.Registry`
        :return: An iterator.
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.registry.Find', returnOwnership=consts.ReturnTypeOwnership.CALLEE)
    def Find(id):
        """
        Find(id)
        Returns the registry entry registered at this registry under the given identifier

        .. note::

            If no entry exists for the given identifier, None is returned.

        :param id: Identifier within this registry.
        :param id: :class:`maxon.Id`
        :return: The value stored in the registry.
        :rtype: Any
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.registry.FindEntryValue')
    def FindEntryValue(registry, eid):
        """
        FindEntryValue(registry, eid)
        Returns the registry entry registered at the passed registry under the given identifier

        :param registry: The registry to find the value from.
        :type registry: :class:`maxon.Registry`
        :param eid:  Identifier within this registry.
        :type eid: :class:`maxon.Id`
        :return: The value stored in the registry.
        :rtype: Any
        """
        pass


from . object import ObjectInterface  # noqa E402


def Cast(T, o):
    """
    Cast(T, o)
    Cast the object `o` to the type `T`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
        | Use :func:`maxon.MaxonConvert` instead.

    :param T: The type to cast the object to.
    :type T: type
    :param o:  The Initial object
    :type o: Any
    :return: The casted object
    :rtype: T
    """
    # if the object is not a reference, cast it to it's registered reference type
    if issubclass(T, ObjectInterface) and not T._isReference:
        T = T._refClsOfInterface
    return _maxon_mapping.MaxonConvertAuto(_maxon_datatype.DataType_Cast(T._dt._data, o._data))


def reinterpret_cast(T, o):
    """
    Cast(T, o)
    Cast the object `o` to the type `T`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
        | Use :func:`maxon.MaxonConvert` instead.

    :param T: The type to cast the object to.
    :type T: type
    :param o:  The Initial object
    :type o: Any
    :return: The casted object
    :rtype: T
    """
    # TODO: (Seb) If T references to o in any way, o must be alive as long as the references object
    return _maxon_datatype.DataType_ReinterpretCast(T, o)


@MAXON_INTERFACE(consts.MAXON_REFERENCE_CONST, "net.maxon.interface.iohandler")
class IoHandlerInterface(ObjectInterface):
    """
    | The IoHandler class offers some I/O functionality for filenames.
    | This handler needs to be implemented for each scheme.
    """

    @MAXON_METHOD("net.maxon.interface.iohandler.GetUrlScheme")
    def GetUrlScheme(self):
        """
        GetUrlScheme()
        Returns the url scheme to use in Urls for this handler (such as "file" if this is the IoHandler for the file system).

        :return: Url scheme of this handler.
        :rtype: :class:`maxon.Url`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iohandler.SetSystemPath")
    def SetSystemPath(self, url, systemPath):
        """
        SetSystemPath(self, url, systemPath)
        Converts an OS or handler-specific system path to a :class:`maxon.Url`.

        :param url: The url that will be filled.
        :type url: :class:`maxon.Url`
        :param systemPath: The path.
        :type systemPath: str
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iohandler.GetSystemPath")
    def GetSystemPath(self, url):
        """
        GetSystemPath(url)
        Translates a :class:`maxon.Url` to a OS or handler-specific system path.

        :param url: The :class:`maxon.Url` to translate.
        :type url: :class:`maxon.Url`
        :return: The generated path.
        :rtype: str
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iohandler.RemoveUrl")
    def RemoveUrl(self, url):
        """
        RemoveUrl(url)
        Removes the last part of the given url and returns the parent url.

        :param url: The :class:`maxon.Url`
        :type url: :class:`maxon.Url`
        :return: The modified :class:`maxon.Url`.
        :rtype: :class:`maxon.Url`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iohandler.OpenConnection")
    def OpenConnection(self, url):
        """
        OpenConnection(url)
        Opens a connection and returns the specified :class:`maxon.IoConnectionRef` handler for this type of protocol.

        :param url: :class:`maxon.Url` of the connection to open.
        :type url: :class:`maxon.Url`
        :return: A reference to the specialized :class:`maxon.IoConnectionRef`.
        :rtype: :class:`maxon.IoConnectionRef`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iohandler.IoNormalize")
    def IoNormalize(self, flags=enums.NORMALIZEFLAGS.SCHEME_BASED):
        """
        IoNormalize(self, flags=maxon.NORMALIZEFLAGS.SCHEME_BASED):
        Returns a normalized :class:`maxon.Url`. If the normalized :class:`maxon.Url` is a link,
        the :class:`maxon.IoHandler` can resolve it (if supported).

        .. note::

            The file:/// handler resolves symbolic links, where the http:// handler does not resolve links.

        :param flags: Flags to define type of normalization.
        :type flags: :class:`maxon.NORMALIZEFLAGS`
        :return: The normalized :class:`maxon.Url`.
        :rtype: :class:`maxon.Url`
        """
        pass

    # TODO: (Seb) Why can this function not be found? Manual implementation
    # @MAXON_STATICMETHOD("net.maxon.interface.iohandler.GetHandlerForScheme")
    @staticmethod
    def GetHandlerForScheme(scheme):
        """
        GetHandlerForScheme(scheme)
        Returns the :class:`maxon.IoHandler` which is responsible for the given scheme.
        The :class:`maxon.IoHandler` is searched for at the IoHandlers registry.

        :param scheme: The :class:`maxon.Url` scheme for which the matching IoHandler shall be found.
        :type scheme: :class:`maxon.Url`
        :return: The matching IoHandler, or a null reference.
        :rtype: :class:`maxon.IoHandler`

        :raise LookupError: If the searched scheme can't be found in the "net.maxon.registry.iohandlers" registry.
        """
        r = RegistryInterface.Find("net.maxon.registry.iohandlers")
        if not r:
            raise LookupError("could not find {}".format(scheme))
        return RegistryInterface.FindEntryValue(r, "net.maxon.iohandler." + str(scheme))


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_CONST, "net.maxon.interface.class")
class ClassInterface(ObjectInterface):
    """
    | A :class:`maxon.ClassInterface` object represents an object class at runtime.
    | Such an object class can be published by :func:`MAXON_DECLARATION`, and it is then typically defined by
      :func:`MAXON_COMPONENT_CLASS_REGISTER`.
    |
    | A class consists of several components (see ComponentDescriptor), each of which may implement several virtual
      interfaces (declared by :func:`ComponentDescriptor`).
    | The class itself then implements all interfaces of all of its components.
    | Information about components and interfaces can be obtained from the ClassInfo object returned by
      :func:`ObjectInterface.GetClassInfo`.
    |
    | After allocation of a class, you have to add the components of which it shall consist via
      :func:`ClassInterface.AddComponent` or :func:`ClassInterface.AddComponents`.
    | Afterwards, you can invoke :func:`ClassInterface.Finalize` to make the class ready for use.
    | From then on, only const methods may be invoked on a class.
    | If you use :class:`maxon.GenericClass` or :class:`maxon.Class` to access a class,
      this is automatically guaranteed as those are const references.
    | If you don't invoke :func:`ClassInterface.Finalize`,
      this will be done implicitly when the first instance of the class is allocated.
    |
    | The :func:`MAXON_COMPONENT_CLASS_REGISTER` and :func:`MAXON_COMPONENT_OBJECT_REGISTER` macros greatly
      simplify the setup of a class.
    |
    | :class:`maxon.ClassInterface` objects are automatically registered in the :class:`maxon.Classes` registry.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    class KIND(enum.IntEnum):
        """
        Represents the KIND of a :class:`maxon.ClassInterface`.
        """
        #: Default Behavior for a class.
        NORMAL = 0

        #: A singleton object class, i.e., a class with exactly one instance.
        #: The instance can be obtained with :func:`ClassInterface.Create`.
        SINGLETON = 1

        #: An abstract object class. :func:`ClassInterface.Create` will raise an error.
        ABSTRACT = 2

    #: Stores the passed reference type if created e.g. via Class(FooRef)
    R = None

    @MAXON_METHOD("net.maxon.interface.class.GetId")
    def GetId(self):
        """
        GetId()

        :return:
        """
        pass

    @MAXON_METHOD("net.maxon.interface.class.GetKind")
    def GetKind(self):
        """
        GetKind()
        Returns the identifier of this object class. Class identifiers are unique.

        :return: :class:`maxon.Class` identifier.
        :rtype: :class:`maxon.Id`
        """
        pass

    @MAXON_FUNCTION("net.maxon.interface.class.Create")
    def Create(self, type=None):
        """
        Create(type=None)
        | Constructs a new instance of this class.
        | This will invoke the constructors of each component in the order of addition, and then the
          `ComponentRoot.InitComponent` functions of each component.
        | When one of the :func:`ComponentRoot.InitComponent` functions fails with an error,
          :func:`ComponentRoot.FreeComponent` will be invoked on the previous (already initialized) components,
          the component destructors will be invoked, the memory will by freed, and :func:`ClassInterface.Create` returns
          the error.
        |
        | For a singleton class, this doesn't create a new instance, but returns the singleton instance of this class.
        | This instance is automatically created on finalization of the class.
        |
        | For an abstract class, this will always raise an error.

        :param type: The expected type of object to create.
        :param type: maxon API type.
        :return: Reference to new instance, or an error if the allocation or initialization failed.
        :rtype: Any.
        """
        if type is None:
            # the R got attached by MAXON_DECLARATION(..)
            # if the return type hint was Class(..)
            if hasattr(self, "R"):
                type = self.R
            else:
                type = ObjectInterface._refClsOfInterface
        return Cast(type, self.CreateRef())

    @MAXON_METHOD("net.maxon.interface.class.Finalize")
    def Finalize(self):
        """
        Finalize()
        | Finalizes this class so that it can be used afterwards.
        | The class has to be built before by :func:`ClassInterface.AddComponent`.
        |
        | Some internal data will be set-up for the class so that it is ready for use.
        | If you don't invoke :func:`ClassInterface.Finalize`, it will be done implicitly when an object of the
          class is instantiated for the first time.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.class.IsFinalized")
    def IsFinalized(self):
        """
        IsFinalized()
        Returns True if the class has been finalized successfully before.

        :return: True if the class is finalized.
        :rtype: bool
        """
        pass

    @MAXON_METHOD("net.maxon.interface.class.GetDataType")
    def GetDataType(self):
        """
        GetDataType()
        Returns the data type corresponding to the set of implemented interfaces of this class.

        .. note::

            For an abstract class this will return None.

        :return: Data type of this class.
        :rtype: :class:`maxon.DataType`
        """
        pass


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.url")
class UrlInterface(ObjectInterface):
    """Interface class for :class:`maxon.Url`.
    | A :class:`maxon::Url` defines the location of a file or a similar resource.
    | The class allows to construct a file path and to handle files.
    |
    | Urls consist of three parts:

        #. | A scheme, an authority and a path. The readable text-representation is "scheme://authority/path".
           | The scheme defines which handler is used, e.g. "http" for web-based connections or "file" for the
             regular file system.

        #. | The authority defines the machine, which can be empty for "localhost", a network drive or a webserver.
           | It can also refer to an embedded file, e.g. a ZIP. To distinguish that case
             the readable text representation contains brackets: "scheme://[authority]/path".
           | Nesting is possible repeatedly.

        #. Finally the path component defines the unique location of a file or directory on the target machine.

    """

    @MAXON_METHOD("net.maxon.interface.url.GetScheme")
    def GetScheme(self):
        """
        GetScheme()
        | Gets the UrlScheme of the Url. Is guaranteed to be lowercase (canonical form for urls)
        | if scheme was automatically determined through :func:`maxon.UrlInterface.SetUrl`, otherwise as set.
        |
        | In most schemes paths are a combination of the directory path and file path, but the path could also be a
          network query or database entry. Path components are always separated by a forward slash and the
          forward slash is a reserved character that cannot be used for names.

        :return: The scheme name.
        :rtype: str
        """

    @MAXON_METHOD("net.maxon.interface.url.SetScheme")
    def _PrivateSetScheme(self, scheme):
        """set the scheme"""

    @MAXON_FUNCTION("net.maxon.interface.url.SetScheme")
    def SetScheme(self, scheme):
        """
        SetScheme(scheme)
        Sets the scheme of the Url. Path and authority will stay unchanged.

        :param scheme: The new scheme
        :type scheme: str
        """
        # an Id must be alive as long as the Url is alive
        self._scheme = scheme
        self._PrivateSetScheme(scheme)

    @MAXON_METHOD("net.maxon.interface.url.Compare")
    def Compare(name, mode=enums.URLCOMPARE.DEFAULT):
        """
        Compare(name, mode=maxon.URLCOMPARE.DEFAULT)
        Compares the object against 'name'.

        .. note::

            | By default the comparison is case-sensitive, so './Test.tif' and './test.tif' are not the same.
            | To check if Urls point to the identical item use :func:`maxon.Url.IoNormalizeAndResolve` instead.

        :param name: The :class:`maxon.Url` to be compared with.
        :type name: :class:`maxon.UrlInterface`
        :param mode: The comparison mode.
        :type mode: :class:`maxon.URLCOMPARE`
        :return: The compared result.
        :rtype: maxon.COMPARERESULT
        """

    @MAXON_METHOD("net.maxon.interface.url.Append@d85d74e087a2f051")
    def _AppendString(self, name):
        """append a string"""

    @MAXON_METHOD("net.maxon.interface.url.Append@1db4eca46d9225b9")
    def _AppendUrl(self, name):
        """append a string"""

    @MAXON_OVERLOAD()
    def Append(self, relativeUrl):
        """
        Append(relativeUrl)
        Appends a relative string or a :class:`maxon.Url` to the current one.

        .. note::

            If the Url is `file:///c:/directory` a call of

            .. code-block:: python

                url.Append(maxon.Url("test/file.txt"))

            will result in `file:///c:/directory/test/file.txt`.

        :param srelativeUrl: The relative :class:`maxon.Url` to append.
        :type relativeUrl: Union[str, :class:`maxon.Url`]
        """
        if isinstance(relativeUrl, str):
            self._AppendString(relativeUrl)
        elif isinstance(relativeUrl, UrlInterface):
            self._AppendUrl(relativeUrl)
        else:
            raise TypeError("unknown type %s" % str(type(relativeUrl)))

    @MAXON_METHOD("net.maxon.interface.url.RemoveName")
    def RemoveName(self):
        """
        RemoveName()
        Removes the last part of a Url.

        .. note::

            If the :class:`maxon.Url` is "file:///c:/directory/file.txt" a call of RemoveName()
            will result in "file:///c:/directory".
        """

    @MAXON_METHOD("net.maxon.interface.url.GetEmbeddedUrl")
    def GetEmbeddedUrl(self):
        """
        GetEmbeddedUrl()
        Returns an embedded :class:`maxon.Url`.

        .. note::

            If the Url is "zip://[file:///c:/images.zip]/image01.jpg" a call to GetEmbeddedUrl()
            will return "file:///c:/images.zip".

        :return: The embedded :class:`maxon.Url` or if there was none, an empty :class:`maxon.Url`.
        :rtype: :class:`maxon.Url`
        """

    @MAXON_METHOD("net.maxon.interface.url.SetEmbeddedUrl")
    def SetEmbeddedUrl(self, url):
        """
        SetEmbeddedUrl(url)
        Replaces and sets an embedded :class:`maxon.Url`.

        .. note::

            If the Url is "zip://[file:///c:/images.zip]/image01.jpg" a call to SetEmbeddedUrl("file:///c:/otherimages.zip"_s) will result in "zip://[file:///c:/otherimages.zip]/image01.jpg".

        :param url: The new embedded :class:`maxon.Url`.
        """

    @MAXON_METHOD("net.maxon.interface.url.GetName")
    def GetName(self):
        """
        GetName()
        Returns the name of the last component.

        .. note::

            if the Url is "file:///c:/directory/file.txt" a call to GetName() will return "file.txt".

        :return: The name of the last path component.
        :rtype: str
        """

    @MAXON_METHOD("net.maxon.interface.url.SetName")
    def SetName(self, name):
        """
        SetName(name)
        Replaces the last component of a :class:`maxon.Url`.
        The name must not contain a forward slashes and under Windows additionally no backslashes.

        .. note::

            If the Url is "file:///c:/directory/file.txt" a call of SetName("change.tif"_s)
            will result in "file:///c:/directory/change.tif".

        :param name: The new name.
        :type name: str
        """

    @MAXON_METHOD("net.maxon.interface.url.GetDirectory")
    def GetDirectory(self):
        """
        GetDirectory()
        Returns the :class:`maxon.Url` of the directory.

        .. note::

            If the Url was "file:///c:/directory/file.txt" a call of GetDirectory() will return "file:///c:/directory".

        :return: The directory.
        :rtype: :class:`maxon.Url`
        """

    @MAXON_METHOD("net.maxon.interface.url.SetPath")
    def SetPath(self, path):
        """
        SetPath(path)
        Replaces the path component of the :class:`maxon.Url`. The path is stored unchanged with the exception that
        under Windows all backslashes will be changed into forward slashes.

        :param path: The new path.
        :type path: str
        """

    @MAXON_METHOD("net.maxon.interface.url.GetPath")
    def GetPath(self):
        """
        GetPath()
        Returns the path component of the :class:`maxon.Url`.

        .. note::

            This doesn't contain scheme and authority. E.g. if the :class:`maxon.Url` is
            "file:///c:/directory/file.txt" a call will return "c:/directory/file.txt".

        :return: The path component of the :class:`maxon.Url` (with no authority and scheme).
        :rtype: str
        """

    @MAXON_METHOD("net.maxon.interface.url.SetSystemPath")
    def SetSystemPath(self, path):
        """
        SetSystemPath(path)
        | Stores a system path in a :class:`maxon.Url`.
        |
        | This call needs to be done after the appropriate scheme has been set.
        | If no scheme is set :py:attr:`maxon.URLSCHEME_FILESYSTEM` will be automatically set.
        |
        | The system path may be converted to a different internal representation,
        | e.g. split into authority and path components.
        |

        .. note::

            Under Windows all backslashes will be changed into forward slashes.

        :param path: The system path
        :type path: str
        """

    @MAXON_METHOD("net.maxon.interface.url.GetSystemPath")
    def GetSystemPath(self):
        """
        GetSystemPath()
        | Returns a path from the :class:`maxon.Url` that the current operating system (or scheme handler) can understand.
        | If the :class:`maxon.Url` contains no valid scheme an error will be returned.
        |
        | An error will also be returned if the :class:`maxon.Url` contains illegal characters for the scheme,
          e.g. backslashes on Windows in a file scheme.

        :return: The system path.
        :rtype: str
        """

    @MAXON_METHOD("net.maxon.interface.url.SetUrl")
    def SetUrl(self, urlString, enableDefaultFallbackScheme):
        """
        SetUrl(urlString, enableDefaultFallbackScheme)
        | Sets the :class:`maxon.Url`.
        | The scheme is detected automatically and converted to the canonical lowercase version
          (as described in rfc3986#3.1).
        |
        | If a scheme isn't found and enableDefaultFallbackScheme is False the function returns an IllegalArgumentError,
        | otherwise :py:attr:`maxon.URLSCHEME_FILESYSTEM` will be assumed (or :py:attr:`maxon.URLSCHEME_RELATIVE` if
          'urlString' starts with no drive letter).
        |
        | Please note that Urls only use forward slashes as delimiter,
        | backslashes are considered to be a part of names and not a delimiter.
        |
        | '?' will be considered as the start of :py:attr:`maxon.URLFLAGS.QUERY` parameters.
        |
        | Everything behind the '?' will be placed in that property.
        | Use url.Get(:py:attr:`maxon.URLFLAGS.QUERY`) to get the query parameters.

        :param urlString: The new :class:`maxon.Url` to be set.
        :type urlString: str
        :param enableDefaultFallbackScheme: If False and no scheme is set an error will be returned.
        :type enableDefaultFallbackScheme: bool
        """

    @MAXON_METHOD("net.maxon.interface.url.GetUrl")
    def GetUrl(urlType):
        """
        GetUrl(urlType)

        Returns the :class:`maxon.Url` as a string.

        .. note::

            A :class:`maxon.Url` has the format scheme://authority/path.

        :return: The :class:`maxon.Url` as a string.
        :rtype: str
        """
        return str()

    @MAXON_METHOD('net.maxon.interface.url.SetAuthority@d85d74e087a2f051')
    def _SetAuthorityString(self, authority):
        pass

    @MAXON_METHOD('net.maxon.interface.url.SetAuthority@1db4eca46d9225b9')
    def _SetAuthorityUrl(self, authority):
        pass

    @MAXON_FUNCTION('net.maxon.interface.url.SetAuthority')
    def SetAuthority(self, authority):
        """
        SetAuthority(authority)
        Sets the authority of a :class:`maxon.Url`. This can be a machine or server.

        .. note::

            Empty string can be passed for no authority / localhost. The authority scheme will be URLSCHEME_AUTHORITY.

        :param authority: The new authority.
        :type authority: Union[str, :class:`maxon.Url`]
        :return:
        """
        if isinstance(authority, str):
            return self._SetAuthorityString(authority)
        elif isinstance(self, UrlInterface):
            return self._SetAuthorityUrl(authority)
        else:
            raise TypeError("unsupported type for authority")

    @MAXON_METHOD('net.maxon.interface.url.GetAuthority', returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def GetAuthority(self):
        """
        GetAuthority()
        Returns the authority of a :class:`maxon.Url`. The authority can be a machine, server or embedded file.

        :return: The authority of the :class:`maxon.Url`.

            | If the machine is localhost the returned :class:`maxon.Url` is empty.
            | If it is a machine or server the scheme will be :py:attr:`maxon.URLSCHEME_AUTHORITY`.
            | Otherwise it defines an embedded file.

        :rtype: :class:`maxon.Url`
        """
        pass

    # TODO: (Seb) Not implemented yet
    @MAXON_METHOD('net.maxon.interface.url.GetComponents')
    def GetComponents(self, authority):
        """
        GetComponents(authority)
        Returns all parts of the :class:`maxon.Url` system path as separated strings.

        .. note::

            If the :class:`maxon.Url` was "file:///c:/directory/file.txt" a call of GetComponents will
            return: { "C:", "directory", "file.txt" }.

        :param authority:
        :return:
        """
        pass

    @MAXON_METHOD("net.maxon.interface.url.GetSuffix")
    def GetSuffix(self):
        """
        GetSuffix()
        Returns the suffix of the :class:`maxon.Url`.

        .. note::

            If the :class:`maxon.Url` was "file:///c:/directory/file.txt" a call of GetSuffix() will return "txt".

        :return: The suffix without dot.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.url.CheckSuffix')
    def CheckSuffix(self, suffix):
        """
        CheckSuffix(suffix)
        Checks whether the :class:`maxon.Url` has the a given suffix.

        .. note::

            If the :class:`maxon.Url` is "file:///c:/directory/file.txt" a call of CheckSuffix("txt"_s)
            will return true.

        :param suffix: The suffix without dot to check against.
        :type suffix: str
        :return: True if the suffix matches.
        :rtype: bool
        """
        return bool()

    @MAXON_METHOD('net.maxon.interface.url.SetSuffix')
    def SetSuffix(self, suffix):
        """
        SetSuffix(suffix)
        | Replaces the suffix of the :class:`maxon.Url`.
        | If the :class:`maxon.Url` had no suffix before a dot will be added together with the suffix string.

        .. note::

            If the :class:`maxon.Url` is "file:///c:/directory/file.txt" a call of SetSuffix("jpg"_s)
            will result in "file:///c:/directory/file.jpg".

        :param suffix: The new suffix of the :class:`maxon.Url` without dot.
        :type suffix: str
        """
        return bool

    @MAXON_METHOD('net.maxon.interface.url.ClearSuffix')
    def ClearSuffix(self):
        """
        ClearSuffix()
        Deletes the suffix of the :class:`maxon.Url`.

        .. note::

            If the :class:`maxon.Url` was "file:///c:/directory/file.txt" a call will
            result in "file:///c:/directory/file".
        """
        return bool()

    @MAXON_METHOD('net.maxon.interface.url.IsEmpty')
    def IsEmpty(self):
        """
        IsEmpty()
        | Returns if the :class:`maxon.Url` has no content.
        |
        | A :class:`maxon.Url` is considered empty if it has no path component and no authority
          (even if a scheme is set).

        :return: True if the :class:`maxon.Url` is empty.
        :rtype: bool
        """
        return bool()

    @MAXON_METHOD('net.maxon.interface.url.GetData')
    def GetData(self, key):
        """
        GetData(key)
        Returns :class:`maxon.Url` attributes. See :class:`maxon.URLFLAGS` for details.

        :param key: The id of the property to get. The possible values for id depend on the scheme.
        :type key: Union[:class:`maxon.URLFLAGS`, :class:`maxon.Url`]
        :return: The attribute value or an error if there was none.
        :rtype: :class:`maxon.Data`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.url.SetData@347fe24919b69e97')
    def SetData(self, key, value):
        """
        SetData(key, value)
        Modifies or sets a :class:`maxon.Url` attribute. See :class:`maxon.URLFLAGS` for details.

        :param key: The id of the property to set. The possible values for id depend on the scheme.
        :type key: Union[:class:`maxon.URLFLAGS`, :class:`maxon.Url`]
        :param value: :class:`maxon.Data` to be set.
        :type value: :class:`maxon.Data`
        """
        pass

    @MAXON_FUNCTION("net.maxon.interface.url.IsPopulated")
    def IsPopulated(self):
        """
        IsPopulated()
        | Returns if the :class:`maxon.Url` has any content.
        | A :class:`maxon.Url` is considered populated if it has a path component or authority set.

        :return: True if the :class:`maxon.Url` has content.
        :rtype: bool
        """
        return not self.IsEmpty()

    @MAXON_FUNCTION("net.maxon.interface.url.Set")
    def Set(self, key, value):
        """
        Modifies or sets a :class:`maxon.Url` attribute.

        .. seealso::

            :class:`maxon.URLFLAGS` for details.

        :param key: The id of the property to set. The possible values for id depend on the scheme.
        :type key: Union[:class:`maxon.URLFLAGS`, :class:`maxon.Url`]
        :param value: :class:`maxon.Data` to be set.
        :type value: :class:`maxon.Data`
        """
        return self.SetData(key, value)

    @MAXON_FUNCTION("net.maxon.interface.url.Get")
    def Get(self, key, defaultValue=None):
        """
        Returns :class:`maxon.Url` attributes.

        .. seealso::

            :class:`maxon.URLFLAGS` for details.

        :param key: The id of the property to get. The possible values for id depend on the scheme.
        :type key: Union[:class:`maxon.URLFLAGS`, :class:`maxon.Url`]
        :param defaultValue: The default value returned if the key was not found.
        :type defaultValue: Any
        :return: The attribute value or an error if there was none.
        :rtype: Any
        """
        try:
            data = self.GetData(key)
            assert data
            return data
        except ValueError:  # ValueError exception raised if key was not found
            if isinstance(defaultValue, type):
                return defaultValue()
            else:
                return defaultValue


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.networkipaddr")
class NetworkIpAddrInterface(ObjectInterface):
    """
    | This class represents an Internet Protocol (IP) address.
    | It is version agnostic and supports both IPv4 and IPv6.
    """

    @MAXON_METHOD("net.maxon.interface.networkipaddr.Flush")
    def Flush(self):
        """
        Flush()

        .. deprecated:: 20
            Use :func:`NetworkIpAddrInterface.Reset` instead.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddr.GetProtocol")
    def GetProtocol(self):
        """
        GetProtocol()
        Returns the type of the IP address used in this object.

        :return: The IP address type.
        :rtype: :class:`maxon.PROTOCOL`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddr.GetNativeProtocol")
    def GetNativeProtocol(self):
        """
        GetNativeProtocol()
        Returns the type of the IP address used in this object.

        :return: The Protocol type.
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddr.SetIPv4@36568859b846ccc8")
    def SetIPv4(self):
        """
        SetIPv4()
        Sets an IP v4 address from the native in_addr structure.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddr.SetIPv6@cb90a5a5527fcd58")
    def SetIPv6(self):
        """
        SetIPv6()
        Sets an IP v6 address from the native in_addr structure.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddr.GetString")
    def GetString(self, port=0):
        """
        GetString(port=0)
        Retrieves the string representation of the current IP address.

        :param port: The port to be appended at the end of the IP address.
        :type port: int
        :return: The string representation of the current IP address.
        :rtype: str
        """
        pass

    def __repr__(self):
        return "maxon.NetworkIpAddr('" + self.GetString(0) + "')"


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.networkipaddrport")
class NetworkIpAddrPortInterface(NetworkIpAddrInterface):
    """
    | Provides an Internet Protocol (IP) address + port.
    | This class extends the :class:`maxon.NetworkIpAddrInterface` with a port.
    """

    @MAXON_METHOD("net.maxon.interface.networkipaddrport.SetPort")
    def SetPort(self, port):
        """
        SetPort(port)
        Sets the port.

        :param port: The port or 0 to reset port information.
        :type port: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddrport.GetPort")
    def GetPort(self):
        """
        GetPort(self)
        Returns the port.

        :return: The port or 0 if no port was set.
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.networkipaddrport.GetAddress")
    def GetAddress(self):
        """
        GetAddress()
        Returns the address without the port.

        :return: Returns the address without the port.
        :rtype: :class:`maxon.NetworkIpAddr`
        """
        pass


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.iobrowse")
class IoBrowseInterface(ObjectInterface):
    """
    | The :class:`IoBrowseIterator` interface for a given :class:`maxon.Url`.
    | This :class:`IoBrowseIterator` needs to be implemented for each protocol that support kind of directories
      (e.g. "file", "zip").
    """

    @MAXON_METHOD("net.maxon.interface.iobrowse.Init")
    def Init(self, connection, flags):
        """
        Init(connection, flags)
        Private

        :param connection: :class:`maxon.IoConnectionRef` Connected to this :class:`maxon.IoBrowseRef`.
        :type connection: :class:`maxon.IoConnectionRef`
        :param flags: Defines how the iterator should behave.
        :type flags: :class:`maxon.GETBROWSEITERATORFLAGS`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.GetBasePath", returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def GetBasePath(self):
        """
        GetBasePath()
        Returns corresponding :class:`maxon.Url`.

        :return: Name of the connection.
        :rtype: :class:`maxon.Url`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.Reset")
    def Reset(self):
        """
        Reset()
        Restart browsing of the directory.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.HasEntry")
    def HasEntry(self):
        """
        HasEntry()
        Checks if there is any entry left

        :return: True if the iterator still get content to iterate.
        :rtype: bool
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.GetNext")
    def GetNext(self):
        """
        GetNext()
        Browses to the next object in the list. You need to call GetNext() before you get the first object.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.IoGetFlags")
    def IoGetFlags(self):
        """
        IoGetFlags()
        Returns the flags (:class:`maxon.IOBROWSEFLAGS`) of the children.

        :return: The children flags.
        :rtype: :class:`maxon.IOBROWSEFLAGS`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.IoGetAttributes")
    def IoGetAttributes(self):
        """
        IoGetAttributes()
        Returns the flags (:class:`maxon.IOATTRIBUTES`) of the children.

        :return: The children flags.
        :rtype: :class:`maxon.IOATTRIBUTES`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.GetSize")
    def GetSize(self):
        """
        GetSize()
        Returns the size of the current file.

        :return: Size in bytes. -1 means unknown size.
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.GetCurrentPath")
    def GetCurrentPath(self):
        """
        GetCurrentPath()
        Returns the current :class:`maxon.Url`.

        :return: The current :class:`maxon.Url`.
        :rtype: :class:`maxon.Url`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.iobrowse.GetExtraData")
    def GetExtraData(self):
        """
        GetExtraData()
        Returns some extra data.

        .. note::

            :py:attr:`maxon.URLSCHEME_VOLUME` returns the human readable drive name.

        :return: The return value depends on the handler what it returns.
        :rtype: str
        """
        pass


class IoBrowseIterator:
    """
    Represents a python iterator for an :class:`maxon.IoBrowseInterface`

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """

    @classmethod
    def Init(cls, iteratorObject):
        """
        Init(cls, iteratorObject)
        Initializes the passed cls object with the iterator.

        :param iteratorObject: an IteratorObject
        :type iteratorObject: :class:`maxon.IoBrowseRef`
        :return: The initialized Iterator
        :rtype: :class:`maxon.IoBrowseRef`
        """
        return cls(iteratorObject)

    def GetIoBrowse(self):
        """
        Retrieves the internal iterator object.
        :return:
        """
        return self._iteratorObject

    def __init__(self, iteratorObject):
        if not isinstance(iteratorObject, IoBrowseInterface):
            raise TypeError("expected IoBrowseInterface not %s" % str(type(iteratorObject)))

        self._iteratorObject = iteratorObject

    def __iter__(self):
        iteratorObject = self._iteratorObject

        while iteratorObject.GetNext():
            yield iteratorObject


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.application")
class Application(object):
    """
    | Application wide functions.
    | Implement this interface to be able to link against the kernel library.
    """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.GetMachineInfo")
    def GetMachineInfo():
        """
        GetMachineInfo()
        | Returns information about the system and processor.
        | See :class:`maxon.MACHINEINFO` for :class:`maxon.DataDictionary` properties.

        :return: System and processor information.
        :rtype: :class:`maxon.DataDictionary`
        """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.GetModulePaths")
    def GetModulePaths():
        """
		Returns all module paths configured through g_modulePath, g_additionalModulePath and user preferences.

		:return: Array containing all paths that are searched for modules.
		:rtype: :class:`maxon.BaseArray`
        """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.GetCommandLineArgCount")
    def GetCommandLineArgCount():
        """
        GetCommandLineArgCount()
        Returns the number of command line arguments delivered to the app on startup.

        :return: Number of arguments to request via :func:`Application.GetCommandLineArg`.
        :rtype: int
        """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.GetCommandLineArg")
    def GetCommandLineArg(idx):
        """
        GetCommandLineArg(idx)
        Returns a command line argument.

        :param idx: The index of the argument. (0 >= idx < GetCommandLineArgCount()).
        :type idx: int
        :return: The requested argument.
        :rtype: str
        """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.GetApplicationMode")
    def GetApplicationMode():
        """
        GetApplicationMode()
        | Retrieves the current application mode.
        | This mode defines the behavior after after the startup is done.

        :return: The current application mode.
        :rtype: :class:`maxon.APPLICATIONMODE`
        """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.SetApplicationMode")
    def SetApplicationMode(mode):
        """
        SetApplicationMode(mode)
        | Sets a new application mode. This mode defines the behavior after the startup is done.
        | Please note that it's only possible to raise the mode from
          :py:attr:`maxon.APPLICATIONMODE.DONTWAIT` to :py:attr:`maxon.APPLICATIONMODE.KEEPRUNNING`.

        :param mode: The new mode to be set.
        :type mode: :class:`maxon.APPLICATIONMODE`
        :return: True if the function changed the mode successfully.
        :rtype: bool
        """

    @staticmethod
    @MAXON_STATICFUNCTION("net.maxon.interface.application.GetUrl")
    def GetUrl(urlType):
        """
        GetUrl()
        Returns the requested :class:`maxon.Url`.

        .. code-block:: python

            tempfile = maxon.Application.GetUrl(maxon.APPLICATION_URLTYPE.TEMP_DIR))

        :param urlType: Type of the url.
        :type urlType: :class:`maxon.APPLICATION_URLTYPE`
        :return: :class:`maxon.Url` containing the requested.
        :rtype: :class:`maxon.Url`
        """
        return _maxon_application.Application_GetUrl(urlType)

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.application.GetTempUrl")
    def GetTempUrl(directory):
        """
        GetTempUrl(directory)
        | Returns a new unique :class:`maxon.Url` for a temporary file.
        | A typical use for this is

        .. code-block:: python

            tempfile = maxon.Application.GetTempUrl(maxon.Application.GetUrl(maxon.APPLICATION_URLTYPE.TEMP_DIR))

        :param directory: Directory url where the temporary file should be created in.
        :type directory: :class:`maxon.Url`
        :return: :class:`maxon.Url` pointing to the temporary file.
        :rtype: :class:`maxon.Url`
        """

    if core.MAXON_TARGET_WINDOWS:
        @staticmethod
        @MAXON_STATICMETHOD("net.maxon.interface.application.GetWindowsSubsystem")
        def GetWindowsSubsystem():
            """
            GetWindowsSubsystem()
            Returns information about the subsystem of the application.

            .. warning::

                This method is only available on Windows.

            :return: The current subsystem of the current process.
            :rtype: :class:`maxon.SUBSYSTEM`
            """


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.system")
class System:
    """
    | Application wide system functions.
    | Do not use any of those functions directly.
    | Implement this interface to link against the kernel library.
    """
    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.system.PrivateGetInternedId", returnOwnership=consts.ReturnTypeOwnership.CALLEE)
    def PrivateGetInternedId(value):
        """
        PrivateGetInternedId(value)
        Retrieve a :class:`maxon.Componenent` from a :class:`maxon.Id`.

        :param value: The :class:`maxon.Id` of the registered maxon component you want to retrieve.
        :type value: :class:`maxon.Id`
        :return: The maxon component
        :rtype: Any
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.system.GetCustomTimer')
    def GetCustomTimer():
        """
        GetCustomTimer()
        Returns the current system time which is being used by the Timer class.

        :return: :class:`maxon.Seconds` of the system time.
        :rtype: float
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.system.GetConfigurationCount')
    def GetConfigurationCount():
        """
        GetConfigurationCount()
        Returns the number of configuration values registered with ConfigurationRegister.

        :return: Number of configuration values.
        :rtype: int
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.system.GetConfiguration')
    def _PrivateGetConfiguration(index, config):
        pass

    @classmethod
    @MAXON_STATICFUNCTION('net.maxon.interface.system.GetConfiguration')
    def GetConfiguration(cls, index, config):
        """
        GetConfiguration(index, config)
        Gets the configuration value by a given index.

        :param index: index	Index of the configuration value. 0 <= index < :func:`System.GetConfigurationCount`
        :type index: int
        :param config: The config that will be filled with the data.
        :type config: :class:`maxon.ConfigInit`
        :return: True on success or false if the index is out of range.
        :rtype: bool
        """
        # retrieve key, helpText and category through the standard interface
        cls._PrivateGetConfiguration(index, config)

        # value, type, minValue and maxValue are not captured yet so they need to be manually added
        d = _maxon_configuration.GetConfigurationByIndex(index)
        config.value = d["value"]
        config.type = d["type"]
        if "minValue" in d:
            config.minValue = d["minValue"]
        if "maxValue" in d:
            config.minValue = d["maxValue"]

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.system.GetConsoleOutputType')
    def GetConsoleOutputType():
        """
        GetConsoleOutputType()
        Retrieves which types of output shall be supported.

        :return: Diagnostic, warning and/or critical output.
        :rtype: :class:`maxon.OUTPUT`
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.system.GetDefinitionCount')
    def GetDefinitionCount(type):
        """
        GetDefinitionCount(type)
        | Returns the total number of definitions for the given entity type.
        | This is used for statistics about the complexity of the whole application.

        :param type: Entity type.

            Use :py:attr:`maxon.EntityBase.TYPE.COUNT` for the total number of
            methods of all (virtual and non-virtual) interfaces.

        :type type: :class:`maxon.EntityBase.TYPE`
        :return: Number of definitions of the given type.
        :rtype: int
        """
        pass

    @staticmethod
    @MAXON_STATICFUNCTION('net.maxon.interface.system.FindDefinition')
    def FindDefinitionGetData(type, id, expected=None):
        """
        FindDefinitionGetData(type, id, expected=None)
        Returns the definition of the given entity type.

        :param type: Entity type.

            | Use :py:attr:`maxon.EntityBase.TYPE.COUNT` for the total number of methods of all
              (virtual and non-virtual) interfaces.

        :type type: :class:`maxon.EntityBase.TYPE`
        :param id: Entity id.
        :type id: :class:`maxon.Id`
        :param expected: The expected :class:`maxon.DataType` of the return value
        :type expected: :class:`maxon.DataType`
        :return: The definition of the given entity type.
        :rtype: :class:`maxon.DataType` specified for *expected*
        """
        # since EntityDefinition is not covered by
        return _maxon_system.System_FindDefinitionGetData(type, id, expected)


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.datadictionaryobject")
class DataDictionaryObjectInterface(ObjectInterface):
    """
    Class to store and find any :class:`maxon.Data` type under any type of key.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """

    @MAXON_METHOD("net.maxon.interface.datadictionaryobject.GetData")
    def GetData(self, key):
        """
        GetData(key)
        Get data stored under a specific id.

        :param key: :class:`maxon.Id` under which the data is stored.
        :type key: :class:`maxon.Id`
        :return: :class:`maxon.Data` as :class:`maxon.Data` class.
        :rtype: Any :class:`maxon.Data`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryobject.EraseData")
    def EraseData(self, key):
        """
        EraseData(key)
        Remove a data entry from the dictionary.

        .. warning::

            This function doesn't check if the dictionary contained the key.

        :param key: :class:`maxon.Id` under which the data is stored.
        :type key: :class:`maxon.Id`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryobject.SetData")
    def SetData(self, key, value):
        """
        SetData(key, value)
        Set :class:`maxon.Data` under a specific id.

        :param key: :class:`maxon.Id` under which the data is stored.
        :type key: :class:`maxon.Id`
        :param value: Move reference to the data.
        :type value: Any :class:`maxon.Data`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryobject.Reset")
    def Reset(self):
        """
        Reset()
        Frees the entire dictionary. After this call the DataDictionary is empty.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryobject.IsEmpty")
    def IsEmpty(self):
        """
        IsEmpty()
        Checks if the dictionary is empty.

        :return: True if the dictionary does not contain any elements.
        :rtype: bool
        """
        pass

    @MAXON_FUNCTION("net.maxon.interface.datadictionaryobject.Get")
    def Set(self, key, value):
        """
        Set(key, value)
        | Set data under a specific id. this function is template to allow implicit Set calls for each data type.
        | This functions offers 2 possible calls:

            #. Using an FId `dict.Set(maxon.MAXCHINEINFO.COMPUTERNAME, "data")`.

            #. Using any type directly `dict.Set(maxon.Int32(5), "data")`. The data type needs to be registered.

        :param key: :class:`maxon.Id` under which the data is stored.
        :type key: Any
        :param value: Move reference to the data.
        :type value: Any
        """
        return self.SetData(key, value)

    @MAXON_FUNCTION("net.maxon.interface.datadictionaryobject.Get")
    def Get(self, key, defaultValue=None):
        """
        Get(key, defaultValue=None)
        | Get data stored under a specific key. If the key is not found an error will be returned.
        | This functions offers 2 possible calls:

            #. Using an FId "dict.Get(maxon.MAXCHINEINFO.COMPUTERNAME)".

            #. | Using any type directly together with the result type "dict.Get<String>(Int32(5))".
               | The data type needs to be registered.

        :param key: Key under which the data is stored.
        :type key: Any
        :param defaultValue: Default value which should be returned if the key cannot be found.
        :type defaultValue: Any.
        :return: :class:`maxon.Data` converted to the right type if found in the dictionary,

            otherwise the default value.
        """
        try:
            value = self.GetData(key)
            return value
        except Exception:
            # if no default value is passed then re-raise the exception
            if defaultValue is None:
                raise
            return defaultValue


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.datadictionary")
class DataDictionaryInterface(ObjectInterface):
    """
    Class to store and find any data type under any type of key.
    """

    @MAXON_METHOD("net.maxon.interface.datadictionary.InitIterator")
    def InitIterator(self, end):
        """
        InitIterator(end)
        Helper functions for initialize an iterator.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionary.Reset")
    def Reset(self):
        """
        Reset()
        Frees the entire dictionary. After this call the DataDictionary is empty.
        """

    @MAXON_METHOD("net.maxon.interface.datadictionary.IsEmpty")
    def IsEmpty(self):
        """
        IsEmpty()
        Checks if the dictionary is empty.

        :return: True if the dictionary does not contain any elements.
        :rtype: bool
        """
        """Returns the length of the stream"""

    @MAXON_METHOD("net.maxon.interface.datadictionary.SetData@d6bc5a29ae638c7d")
    def _SetData(self, key, data):
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionary.GetData")
    def _GetData(self, key):
        pass

    @MAXON_FUNCTION("net.maxon.interface.datadictionary.Set")
    def Set(self, key, value):
        """
        Set(key, value)
        | Set data under a specific id. this function is template to allow implicit Set calls for each data type.
        | This functions offers 2 possible calls:

            #. Using an FId `dict.Set(maxon.MAXCHINEINFO.COMPUTERNAME, "data")`.

            #. Using any type directly `dict.Set(maxon.Int32(5), "data")`. The data type needs to be registered.

        :param key: :class:`maxon.Id` under which the data is stored.
        :type key: Any
        :param value: Move reference to the data.
        :type value: Any
        """
        # key must be cloned to stay alive, because the original parameter is
        # ForwardingDataPtr and will move the content of the key to the dictionary
        return self._SetData(Data(key), value)

    @MAXON_FUNCTION("net.maxon.interface.datadictionary.Get")
    def Get(self, key, defaultValue=None):
        """
        Get(key, defaultValue=None)
        | Get data stored under a specific key. If the key is not found an error will be returned.
        | This functions offers 2 possible calls:

            #. Using an FId "dict.Get(MAXCHINEINFO::COMPUTERNAME)".

            #. | Using any type directly together with the result type "dict.Get<String>(Int32(5))".
               | The data type needs to be registered.

        :param key: Key under which the data is stored.
        :type key: Any
        :param defaultValue: Default value which should be returned if the key cannot be found.
        :type defaultValue: Any.
        :return: :class:`maxon.Data` converted to the right type if found in the dictionary,

            otherwise the default value.
        """
        try:
            return self._GetData(Data(key))
        except ValueError:  # ValueError exception raised if key was not found
            # if defaultValue is a type create an empty object from it
            if isinstance(defaultValue, type):
                return defaultValue()
            else:
                return defaultValue


class PlainIterator(Data):
    """
    Base class for iterator

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    _isVirtual = False
    _refkind = consts.MAXON_REFERENCE_NONE


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.datadictionaryiterator")
class DataDictionaryIteratorInterface(PlainIterator):
    """
    :class:`maxon.DataDictionaryIteratorInterface` is used internally by :func:`DataDictionary.Iterator`.

    .. warning::

        It should not be used directly.
    """
    @MAXON_METHOD("net.maxon.interface.datadictionaryiterator.Destruct")
    def Destruct(self):
        """
        Destruct()
        Destructs the current iterator
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryiterator.HasValue")
    def HasValue(self):
        """
        HasValue()
        Checks if there is still value to iterate.

        :return: Returns True if this object contains a value.
        :rtype: bool
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryiterator.MoveToNext")
    def MoveToNext(self):
        """
        MoveToNext()
        Move to the next entry from the :class:`maxon.DataDictionary`.
        """
        pass

    @MAXON_METHOD("net.maxon.interface.datadictionaryiterator.GetKeyAndData")
    def GetKeyAndData(self, res):
        """
        GetKeyAndData(res)
        Retrieves the key and value for the current entry of the iterator.

        :param res: The key and the value stored for this key.
        :type res: tuple(:class:`maxon.Data`, :class:`maxon.Data`)
        :return:
        """
        pass

    def __init__(self, memory):
        """
        __init__(memory)

        :param memory:
        """
        self._data = memory


class DataDictionaryIterator(Data):
    """
    Iterator to iterate through all elements of a :class:`maxon.DataDictionaryIterator`.
    """

    _iteratorMemory = None
    _hasIterator = True
    _pair = None

    class IteratorMemory(object):

        def __init__(self):
            # We need an object that is bigger than Int[10], that is why we use a Matrix here
            self._memory = _maxon_memory.NewMemClear(80)
            self._interface = DataDictionaryIteratorInterface(self._memory)

        def __del__(self):
            _maxon_memory.DeleteMem(self._memory)

        def GetCastedInterface(self):
            return self._interface

    def GetIterator(self):
        """
        GetIterator()
        Retrieves the :class:`maxon.DataDictionaryIterator` attached to the current iterator.

        :return: The attached :class:`maxon.DataDictionaryIterator` iterator.
        :type: :class:`maxon.DataDictionaryIterator`
        """
        return self._iteratorMemory.GetCastedInterface()

    def __init__(self, dict, end):
        self._end = end
        self._pair = DataType.Get("(net.maxon.datatype.data-c&,net.maxon.datatype.data-c&)").Create()
        self._iteratorMemory = DataDictionaryIterator.IteratorMemory()

        dict.InitIterator(self.GetIterator(), end)

    def __next__(self):
        if not self._end and self.GetIterator().HasValue():
            self.GetIterator().GetKeyAndData(self._pair)
            self.GetIterator().MoveToNext()
            return Tuple(self._pair)
        else:
            raise StopIteration()


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.unittest")
class UnitTestInterface(ObjectInterface):

    # @MAXON_METHOD("net.maxon.interface.unittest.AddResult")
    def AddResult(self):
        """Returns the current position of the stream"""


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.basestream")
class BaseStreamInterface(DataDictionaryObjectInterface):
    """
    | Interface is the base interface for all stream interfaces.
    | It contains the general functions to work with streams (e.g. error handling).
    """
    softspace = False

    @MAXON_FUNCTION_EXTEND("object.__enter__")
    def __enter__(self):
        return self

    @MAXON_FUNCTION_EXTEND("object.__exit__")
    def __exit__(self, exc_type, exc_value, traceback):
        # at the moment we suppress errors on Close
        try:
            self.Close()
        except Exception:
            pass

    @MAXON_METHOD("net.maxon.interface.basestream.GetStreamLength")
    def GetStreamLength(self):
        """
        GetStreamLength()
        | Returns the length of the stream/file.
        | Be aware that some streams cannot return the file size
          (e.g. http streams with gzip+chunked transfer encoding).
        |
        | With this example code you can handle both cases correctly.
        | In most cases it's better to not use :func:`maxon.BaseStreamInterface.GetStreamLength` and better use
          :func:`maxon.InputStreamInterface.ReadEOS` to read as much as available.

        :rtype: Returns the length in bytes.
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.basestream.GetPosition")
    def GetPosition(self):
        """
        GetPosition()
        | Returns the current stream position.
        | This is the position where the next bytes will be read to or written from.

        :return: The current stream position.
        :rtype: int
        """

    @MAXON_METHOD("net.maxon.interface.basestream.Close")
    def Close(self):
        """
        Close()
        Closes the stream.
        """

    @MAXON_METHOD("net.maxon.interface.basestream.SeekSupported")
    def SeekSupported(self):
        """
        SeekSupported()
        Returns if the stream supports :func:`BaseStreamInterface.Seek`.

        .. note::

            Seeking in stream may effect performance because the caches will be flushed.

        :return: True if the output stream supports :func:`BaseStreamInterface.Seek`.
        :rtype: bool
        """

    @MAXON_METHOD("net.maxon.interface.basestream.Seek")
    def Seek(self, position):
        """
        Seek(position)
        Sets the read/write position to this absolute position from the beginning of the stream.

        .. note::

            For :class:`maxon.InputStreamInterface`: If you want to :func:`BaseStreamInterface.Seek`
            forward :func:`InputStreamInterface.Skip` is the preferred method to call from the performance perspective.

        :param position: Position to jump to within the stream.
        :type position: int
        """

    @MAXON_METHOD("net.maxon.interface.basestream.DisableBuffering")
    def DisableBuffering(self):
        """
        DisableBuffering()
        | The stream may disable buffering when this routine is called (if it supports it).
        | This method is typically used when the buffering is done from the outside.
        """

    @MAXON_FUNCTION_EXTEND("io.close")
    def close(self):
        return self.Close()

    @MAXON_FUNCTION_EXTEND("io.seek")
    def seek(self, offset, whence=os.SEEK_SET):
        # os.SEEK_SET or 0 (absolute file positioning)
        # which is the option Seek supports
        if whence != os.SEEK_SET:
            raise RuntimeError("only os.SEEK_SET(0) for absolute seek is supported")
        return self.Seek(offset)

    @MAXON_FUNCTION_EXTEND("io.seekable")
    def seekable(self):
        return self.SeekSupported()

    @MAXON_FUNCTION_EXTEND("io.tell")
    def tell(self):
        return self.GetPosition()

    # The documentation provides some information for for-like objects
    #
    # io.fileno    - File-like objects which do not have a real file descriptor should not provide this method!
    # io.isatty    - File-like objects which do not have a real file descriptor should not provide this method!
    # io.read      - This function is simply a wrapper for the underlying fread() C function, and will behave the
    #                  same in corner cases, such as whether the EOF value is cached.
    # io.encoding  - The attribute is read-only and may not be present on all file-like objects.
    # io.mode      - This is a read-only attribute and may not be present on all file-like objects.


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.loggertype")
class LoggerTypeInterface(ObjectInterface):
    """
    | Each object of :class:`maxon.LoggerLine` represents an entry in the logger with several meta information.
    | See documentation of members for more information.
    """

    @MAXON_METHOD('net.maxon.interface.loggertype.Flush')
    def Flush(self):
        """
        Flush()
        Implement function to consume string and write to a specified destination.
        """
        pass


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.logger")
class LoggerInterface(ObjectInterface):
    """
    | The logger interface allows to create new custom loggers for specific tasks and to access existing loggers.
    | Loggers are presented in the "Console" window in Cinema 4D and registered at the :class:`maxon.Loggers` registry.
    """

    @MAXON_METHOD('net.maxon.interface.logger.GetName')
    def GetName(self):
        """
        GetName()
        Returns the name of the logger.

        :return: The name.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.logger.SetName')
    def SetName(self, name):
        """
        SetName(name)
        Sets the name of the logger.

        :param name: The name.
        :type name: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.logger.Enable')
    def Enable(self, enable):
        """
        Enable(enable)
        | Enable or disable the logger.
        | If disabled, the logger still consumes strings but discards them.

        :param enable: True or False to enable or disable the logger.
        :type enable: bool
        """
        pass

    @MAXON_METHOD('net.maxon.interface.logger.IsEnabled')
    def IsEnabled(self):
        """
        IsEnabled()
        Returns if the logger is enabled.

        :return: True or False.
        :rtype: bool
        """
        pass

    @MAXON_METHOD('net.maxon.interface.logger.Write')
    def Write(self, ta=14, str="test", loc=None, level=1):
        """
        Write(ta=14, str="test", loc=None, level=1)
        Sends a string to all added logger types.

        :param ta: All logger types which match the target audience will receive the string.
        :type ta: :class:`maxon.TARGETAUDIENCE`
        :param str: Text to print.
        :type str: str
        :param loc: Source location where the string was printed from.
        :type loc: :class:`maxon.SourceLocation`
        :param level: Meta information for the current write operation.
        :type level: :class:`maxon.WRITEMETA`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.logger.AddLoggerType')
    def AddLoggerType(self, ta, loggerTypeCls, cb=None):
        """
        AddLoggerType(ta, loggerTypeCls, cb=None)
        Adds a logger type to the logger.

        :param ta: Set the audience.

            | The logger type will get the string if the target audience matches
              when :func:`LoggerInterface.Write` is used.

        :type ta: :class:`maxon.TARGETAUDIENCE`
        :param loggerTypeCls: The logger type reference to add.
        :type loggerTypeCls: :class:`maxon.LoggerTypeRef`
        :param cb: Optional callback that is executed to initialize a logger type after added to the logger. E.g. the file logger needs to be initialized with a destination path.
        :type cb: function
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.logger.AddNewLogger')
    def AddNewLogger(id, logger, moduleInfo=None):
        """
        AddNewLogger(id, logger, moduleInfo=None)
        | Add a new logger to the system.
        | Does the same as :func:`Loggers.Insert`, but also triggers the observers.

        :param id: The maxon Id corresponding to the logger.
        :type id: :class:`maxon.Url`
        :param logger: The logger reference to add.
        :type logger: :class:`maxon.LoggerRef`
        :param moduleInfo: The module which initiates the call. When the module is freed, the logger will be freed too.
        :type moduleInfo: :class:`maxon.ModuleInfo`
        """
        pass


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.inputstream")
class InputStreamInterface(BaseStreamInterface):
    """
    | Interface for input streams. It allows to read data from streams.
    | This interface needs to be implemented for each protocol.
    """

    @MAXON_METHOD("net.maxon.interface.inputstream.BytesAvailable")
    def BytesAvailable(self):
        """
        BytesAvailable()
        Returns an estimate of the number of bytes that can be read (or skipped over)
        from this input stream without blocking by the next invocation of a method for this input stream.

        :return: Available number of bytes to read/skip.
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.inputstream.ReadEOS")
    def ReadEOS(self, data):
        """
        ReadEOS(data)
        Reads up to len bytes of data from the input stream into an array of bytes.
        'bytes' and the result are of type Int (not Int64) as 'buffer' can never hold more bytes on a 32-bit system.

        :param data: Buffer which receives the read bytes.
        :type data: :class:`maxon.Block`
        :return: Number of bytes that has been read. If less bytes read than requested the end of

            the stream has been reached.

        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.inputstream.Skip")
    def Skip(self, bytes):
        """
        Skip(bytes)
        | Skips over and discards n bytes of data from this input stream.
        | If you want to :func:`BaseStreamInterface.Seek` forward :func:`InputStreamInterface.Skip` is the preferred
          method to call from the performance perspective.

        :param bytes: Number of bytes to skip from the current position.
        :type bytes: bytes
        """
        pass

    @MAXON_FUNCTION("maxon.InputStreamInterface.Read")
    def Read(self, len=None, chunk=io.DEFAULT_BUFFER_SIZE):
        """
        Read(len=None, chunk=io.DEFAULT_BUFFER_SIZE)
        Reads all bytes up to len bytes of data from the input stream into an array of bytes.
        'bytes' and the result are of type Int (not Int64) as 'buffer' can never hold more bytes on a 32-bit system.

        :param len: size of buffer to read.
        :type len: int
        :param chunk: The type of the data to read
        :return: The buffer with the data.
        :rtype: bytes
        """
        if len is None or len < 0:
            if self.BytesAvailable():
                len = self.GetStreamLength()
            else:
                # in case we don't know how long the stream is, we can
                # read it blockwise (use convinient chunk)
                res = bytearray(0)
                while True:
                    b = bytearray(chunk)
                    try:
                        read = self.ReadEOS(b)
                        if read == 0:
                            break
                    except Exception:
                        break
                    else:
                        res.extend(memoryview(b)[:read])
                return res

        b = bytearray(len)
        read = self.ReadEOS(memoryview(b), len)
        return b[:read]

    @MAXON_FUNCTION_EXTEND("io.read")
    def read(self, n=-1):
        return self.Read(n)


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.outputstream")
class OutputStreamInterface(BaseStreamInterface):
    """
    Creates an :class:`maxon.OutputStreamInterface` class to write bytes into streams.
    """

    @MAXON_METHOD("net.maxon.interface.outputstream.Flush")
    def Flush(self):
        """
        Flush()
        Flushes the output stream and forces any buffered output bytes to be written.
        """
        pass

    @MAXON_FUNCTION("net.maxon.interface.outputstream.Write")
    def Write(self, data):
        """
        Write(data)
        Write bytes to the stream. 'bytes' is of type Int (not Int64) as 'buffer'
        can never hold more bytes on a 32-bit system.

        :param data: :class:`maxon.Data` that should be written to the stream.
        :type data: :class:`maxon.Data`
        """
        pass

    @MAXON_FUNCTION_EXTEND("io.write")
    def write(self, data):
        """
        write(data)
        Write bytes to the stream. 'bytes' is of type Int (not Int64) as 'buffer'
        can never hold more bytes on a 32-bit system.

        :param data: :class:`maxon.Data` that should be written to the stream.
        :type data: :class:`maxon.Data`
        """
        return self.Write(data)

    @MAXON_FUNCTION_EXTEND("io.flush")
    def flush(self):
        """
        flush()
        Flushes the output stream and forces any buffered output bytes to be written.
        """
        return self.Flush()


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.inoutputstream")
class InOutputStreamInterface(InputStreamInterface, OutputStreamInterface):
    """
    | Creates an :class:`maxon.InOutputStreamInterface` class to read/write bytes from/into streams.
    | This interface combines both :class:`maxon.InputStreamInterface` and :class:`maxon.OutputStreamInterface`.
    """
    pass


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.ioconnection")
class IoConnectionInterface(DataDictionaryObjectInterface):
    """
    | The connection interface a given :class:`maxon.Url`.
    | This connection needs to be implemented for each protocol.
    """

    @MAXON_METHOD("net.maxon.interface.ioconnection.GetUrl")
    def GetUrl(self):
        """
        GetUrl()
        Returns the corresponding :class:`maxon.Url` connected to the :class:`maxon.IoConnectionRef`.
        :return: Returns the name of the connection.
        :rtype: :class:`maxon.Url`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.GetBrowseIterator")
    def GetBrowseIterator(self, flags):
        """
        GetBrowseIterator(flags)
        | Returns a :class:`maxon.IoBrowseInterface` class to browse through all children of an Url.
        | The return value needs to be checked against None.

        :param flags: Defines how the iterator resolve data.
        :type flags: :class:`maxon.GETBROWSEITERATORFLAGS`
        :return: The iterator.
        :rtype: :class:`maxon.IoBrowseInterface`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.OpenInputStream")
    def OpenInputStream(self, flags=enums.OPENSTREAMFLAGS.NONE):
        """
        OpenInputStream(flags=maxon.OPENSTREAMFLAGS.NONE)
        | Opens an :class:`maxon.InputStreamRef` for the given connection.
        | With this kind of streams it's only possible to read from it.

        :param flags: Defines how the stream will be handled.
        :type flags: :class:`maxon.OPENSTREAMFLAGS`
        :return: An input stream, should be free with :func:`ObjectInterface.Free`.
        :rtype: :class:`maxon.InputStreamRef`
        """
        """opens an input stream"""

    @MAXON_METHOD("net.maxon.interface.ioconnection.OpenOutputStream")
    def OpenOutputStream(self, flags=enums.OPENSTREAMFLAGS.NONE):
        """
        OpenOutputStream(flags=maxon.OPENSTREAMFLAGS.NONE)
        | Opens an :class:`maxon.OutputStreamRef` for the given connection.
        | With this kind of streams it's only possible to write to it.

        :param flags: Defines how the stream will be handled.
        :type flags: :class:`maxon.OPENSTREAMFLAGS`
        :return: An input stream, should be free with :func:`ObjectInterface.Free`.
        :rtype: :class:`maxon.OutputStreamRef`
        """
        """opens an output stream"""

    @MAXON_METHOD("net.maxon.interface.ioconnection.OpenInOutputStream")
    def OpenInOutputStream(self, flags=enums.OPENSTREAMFLAGS.NONE):
        """
        OpenInOutputStream(flags=maxon.OPENSTREAMFLAGS.NONE)
        | Opens an :class:`maxon.InOutputStreamRef` for the given connection.
        | With this kind of streams it's possible to read/write to it.

        :param flags: Defines how the stream will be handled.
        :type flags: :class:`maxon.OPENSTREAMFLAGS`
        :return: An input stream, should be free with :func:`ObjectInterface.Free`.
        :rtype: :class:`maxon.InOutputStreamRef`
        """
        """opens an output stream"""

    @MAXON_METHOD("net.maxon.interface.ioconnection.GetContentLength")
    def GetContentLength(self):
        """
        GetContentLength()
        Returns length of the content.

        :return: The effective size in bytes of the :class:`maxon.IoConnectionInterface` (e.g. filesize).
        :rtype: int
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoDetect")
    def IoDetect(self):
        """
        IoDetect()
        | Detects the type of the :class:`maxon.Url`.
        | This allows to check if a file or directory exists.

        :return: Flags defining the detection state.
        :rtype: :class:`maxon.IODETECT`
        """
        """Detects the type of the Url"""

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoGetAttributes")
    def IoGetAttributes(self):
        """
        IoGetAttributes()
        Returns the file attributes.

        :return: IOATTRIBUTES of the files.
        :rtype: :class:`maxon.IOATTRIBUTES`
        """
        """Returns the file attributes of the object behind Url."""

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoSetAttributes")
    def IoSetAttributes(self, flags, mask):
        """
        IoSetAttributes(flags, mask)
        Modify the file attributes.

        :param flags: Flags to set/clear.
        :param flags: :class:`maxon.IOATTRIBUTES`
        :param mask: Mask with all flags to be changed.
        :param mask: :class:`maxon.IOATTRIBUTES`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoGetTime")
    def IoGetTime(self, mode):
        """
        IoGetTime(mode)
        | Returns the :class:`maxon.DateTime` of the current file.
        | The time is in local time.

        :param mode: IOTIMEMODE of the requested time.
        :type mode: :class:`maxon.IOTIMEMODE`
        :return: Returns the :class:`maxon.DateTime` or an error.
        :rtype: :class:`maxon.UniversalDateTime`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoSetTime")
    def IoSetTime(self, mode, dateTime):
        """
        IoSetTime(mode, dateTime)
        Modifies the :class:`maxon.DateTime` of the current file. the time is in local time.

        :param mode: IOTIMEMODE of the requested time.
        :type mode: :class:`maxon.IOTIMEMODE`
        :param dateTime: New datetime for the file.
        :type dateTime: :class:`maxon.UniversalDateTime`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoDelete")
    def IoDelete(self, force):
        """
        IoDelete(force)
        Deletes the file physically on the medium.

        :param force: True tries to deletes the file/directory even if the file/directory has read only flags set.
        :return: True if the file/directory could be removed successfully.
        :rtype: bool
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoCreateDirectory")
    def IoCreateDirectory(self, createParents, createDirs=None):
        """
        IoCreateDirectory(createParents, createDirs=None)
        Creates a new directory.

        .. note::

            The function returns false if the directory already exists.

        :param createParents: Check if parent directory exists and if not create them recursively.
        :type createParents: bool
        :param createDirs:

            | An array that will contain all newly created subdirectories in the order in which they
              were created.
            | If this parameter is None it will be ignored.

        :type createDirs: :class:`maxon.BaseArray` (:class:`maxon.Url`)
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoCopyFile")
    def IoCopyFile(self, destName, overwrite, removeReadOnly):
        """
        IoCopyFile(destName, overwrite, removeReadOnly)
        Copies a file to a different location, the path must exist otherwise the function returns an error.

        :param destName: Destination name for the copy operation.
        :type destName: :class:`maxon.Url`
        :param overwrite: True to allow overwriting destName file if it was already there.
        :type overwrite: bool
        :param removeReadOnly: True to remove the read only flag on the newly created copy.
        :type removeReadOnly: bool
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoMove")
    def IoMove(self, destName):
        """
        IoMove(destName)
        | Moves a file or directory (including hierarchy) to a different location.
        | The path must exist otherwise the function returns an error.
        |
        | If the destName file or directory does already exist the function returns with an error.
        |
        | Moving a file or directory on the same partition will perform without a temporary copy.

        :param destName: Destination name for the move operation.
        :type destName: :class:`maxon.Url`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoRename")
    def IoRename(self, newName):
        """
        IoRename(newName)
        Renames a file or directory.

        .. warning::

            The newName must not be the name of an existing file or directory.

        :param newName: New name for the rename operation.
        :param newName: :class:`maxon.Url`
        :return:
        """
        pass

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoGetFreeVolumeSpace")
    def _PrivateIoGetFreeVolumeSpace(self, availableBytes, totalBytes):
        pass

    @MAXON_FUNCTION("net.maxon.interface.ioconnection.IoGetFreeVolumeSpace")
    def IoGetFreeVolumeSpace(self):
        """
        IoGetFreeVolumeSpace()
        Calculates the free space on a volume.

        .. note::

            The :class:`maxon.Url` can point to a volume or directory.

        :return: In the next order:

            #. The number of available bytes on the volume.

            #. The total size of the volume in bytes.

        :rtype: tuple(int, int)
        """
        availableBytes = Int64()
        totalBytes = Int64()
        self._PrivateIoGetFreeVolumeSpace(availableBytes, totalBytes)
        return availableBytes, totalBytes

    @MAXON_METHOD("net.maxon.interface.ioconnection.IoShowInOS")
    def IoShowInOS(self, flags):
        """
        IoShowInOS()
        | Opens or shows the file in the systems explorer (desktop/finder).
        |
        | Under windows that would be on the desktop/explorer.
        | Under OSX this would be the Finder.
        |
        | Depending on the url scheme this could also open another browser.

        :param flags: Flags to define how to show/open that file.
        :type flags: :class:`maxon.IOSHOWINOSFLAGS`
        """
        """Opens or shows the file in the systems explorer"""


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.observerobject")
class ObserverObjectInterface(ObjectInterface):
    """
    :class:`maxon.Component` to allow :class:`maxon.ObjectInterface` interfaces to use the observable concept.
    """
    pass  # TODO: (Seb) Add methods


@MAXON_INTERFACE(consts.MAXON_REFERENCE_CONST, "net.maxon.interface.fileformathandler")
class FileFormatHandlerInterface(ObjectInterface):
    """
    | FileFormatHandlerInterface implements a handler for a specific FileFormat.

    .. note::

        | Two different implementations could offer different loaders for one and the same FileFormat.
        | FileFormat::Zip implements one handler for Directory Browsing
          (:class:`maxon.IoBrowseRef`) and one for :class:`maxon.ReadArchiveRef`.
    """

    @MAXON_METHOD("net.maxon.interface.fileformathandler.GetFileFormat")
    def GetFileFormat(self):
        """
        GetFileFormat()
        Returns the :class:`maxon.FileFormat` which is handled by this :class:`maxon.FileFormatHandler`.

        :return: The file format.
        :rtype: :class:`maxon.FileFormat`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.fileformathandler.GetHandlerType")
    def GetHandlerType(self):
        """
        GetHandlerType()
        Returns the :class:`maxon.DataType` of the reference class of the handler returned by
        :func:`FileFormatHandlerInterface.CreateHandler`.

        :return: The data type of the reference class.
        :rtype: :class:`maxon.DataType`
        """
        pass

    @MAXON_METHOD("net.maxon.interface.fileformathandler.CreateHandler")
    def _CreateHandler(self, url):
        pass

    @MAXON_FUNCTION("net.maxon.interface.fileformathandler.CreateHandler")
    def CreateHandler(self, HANDLER, url):
        """
        CreateHandler(HANDLER, url)
        Creates an :class:`maxon.ObjectRef` which handles the given url with the specific interface.

        .. note::

            FileFormat::Zip implements one handler for Directory Browsing
            ":class:`maxon.IoBrowseRef`" and one for workign with archives ":class:`maxon.ReadArchiveRef`".

        :param HANDLER: Reference class to be expected with the result of CreateHandler.
        :type HANDLER: Union[:class:`maxon.UrlInterface`, :class:`maxon.Data`, type]
        :param url: :class:`maxon.Url` to be used with this handler.
        :type url: :class:`maxon.Url`
        :return: Reference class to be expected with the result of CreateHandler.
        :rtype: same as HANDLER
        """
        if isinstance(HANDLER, UrlInterface):
            return self._CreateHandler(HANDLER)
        elif isinstance(HANDLER, type) and issubclass(HANDLER, Data):
            if not url:
                raise AttributeError("url is not set")

            return Cast(HANDLER, self._CreateHandler(url))
        else:
            raise TypeError("invalid arguments")

    @MAXON_METHOD("net.maxon.interface.fileformathandler.GetDependends")
    def GetDependends(self, url):
        """
        | Returns the dependencies of this :class:`maxon.FileFormatHandler`.
        | This allows to give an priority order for a implementation.

        .. warning::

            This function should not be called except from :func:`FileFormatDetectionInterface.DetectAll`.

        :return: Defines the priority order of file formats. The lower the value the later it will be called.
        :rtype: :class:`maxon.FILEFORMAT_PRIORITY`
        """
        pass


@MAXON_INTERFACE(consts.MAXON_REFERENCE_CONST, "net.maxon.interface.fileformat")
class FileFormatInterface(DataDictionaryObjectInterface):
    """
    | :class:`maxon.FileFormatInterface` allows to implement and register file formats with its detection algorithm.
    | The :class:`maxon.FileFormats` registry allows to register any format
      (e.g. FileFormats.Browsable, FileFormats.ImageJpg...).
    """
    pass


@MAXON_INTERFACE(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.machine")
class MachineInterface(ObserverObjectInterface):
    """
    | This class is the entry point to access machine interfaces.
    | So there is no difference if the machine is running local or remote via rpc.
    """
    @MAXON_METHOD('net.maxon.interface.machine.GetUniqueId')
    def GetUniqueId(self):
        """
        GetUniqueId()
        Returns the service name of the local machine. This name is a unique name which allows to identify the machine.

        :return: The service name.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.machine.GetMachineInfo')
    def GetMachineInfo(self):
        """
        GetMachineInfo()
        | Returns information about the system and processor.
        | See :class:`maxon.MACHINEINFO` for :class:`maxon.DataDictionary` properties.

        :return: System and processor information.
        :rtype: :class:`maxon.MACHINEINFO`
        """
        pass


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.configuration")
class Configuration:
    """
    :class:`maxon.Configuration` database functions.

    .. note::

        To access configuration, please use config.XXXX to access the configuration value.

        .. code-block:: python

            # Display the default preference path
            tempFile = maxon.config.g_prefsPath
    """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.QueryBool@fdec8f5c8324ab0f")
    def _QueryBool(key, result, origin, state):
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.QueryInt@46a8b37f17640ea")
    def _QueryInt(key, result, origin, state):
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.QueryFloat@e833dabcb1e6777f")
    def _QueryFloat(key, result, origin, state):
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.QueryString@a8c95af7bf9e30bc")
    def _QueryString(key, result, origin, state):
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.BroadcastBool")
    def BroadcastBool(key, value):
        """
        BroadcastBool(key, value)
        Copies a value into all modules that defined it.

        .. note::

            In case of a crash situation g_inCrashhandler can be set to true with this routine.

        :param key: Case-Sensitive key that is processed.
        :type key: str
        :param value: Value to be set.
        :type value: bool
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.BroadcastInt")
    def BroadcastInt(key, value):
        """
        BroadcastInt(key, value)
        Copies a value into all modules that defined it.

        .. note::

            In case of a crash situation g_inCrashhandler can be set to true with this routine.

        :param key: Case-Sensitive key that is processed.
        :type key: str
        :param value: Value to be set.
        :type value: int
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.BroadcastFloat")
    def BroadcastFloat(key, value):
        """
        BroadcastFloat(key, value)
        Copies a value into all modules that defined it.

        .. note::

            In case of a crash situation g_inCrashhandler can be set to true with this routine.

        :param key: Case-Sensitive key that is processed.
        :type key: str
        :param value: Value to be set.
        :type value: float
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.configuration.BroadcastString")
    def BroadcastString(key, value):
        """
        BroadcastString(key, value)
        Copies a value into all modules that defined it.

        .. note::

            In case of a crash situation g_inCrashhandler can be set to true with this routine.

        :param key: Case-Sensitive key that is processed.
        :type key: str
        :param value: Value to be set.
        :type value: str
        """
        pass


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.fileformatdetection")
class FileFormatDetectionInterface:
    """
    :class:`maxon.FileFormatDetectionInterface` offers functions to detect file formats.
    """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.fileformatdetection.DetectAll")
    def _DetectAll(url, limitDetection, detectedCallback):
        pass

    @staticmethod
    @MAXON_STATICFUNCTION("net.maxon.interface.fileformatdetection.DetectAll")
    def DetectAll(LIMITTYPESorUrl, url=None, detectedCallback=None):
        """
        DetectAll(LIMITTYPESorUrl, url=None, detectedCallback=None)
        | Detects all available :class:`maxon.FileFormatHandler` in the order of priority.
        | The first value in the array should be used first.

        :param LIMITTYPESorUrl: List with reference types to limit the DetectAll call.
        :param LIMITTYPESorUrl: Union[:class:`maxon.DataType`, :class:`maxon.Url`]
        :param url: :class:`maxon.Url` to detect.
        :param url: :class:`maxon.Url`
        :param detectedCallback: The callback should return True if the file format detection should stop at this point.

            | Returning False will search other compatible fileformat handlers.
            | If you return a error the search will be continued.

        :param detectedCallback: function (:class:`maxon.Url`, :class:`maxon.FileFormatHandler`)
        :return: Returns an array with :class:`maxon.FileFormatHandler` which all can handle this :class:`maxon.Url`.
        :rtype: :class:`maxon.FileFormatHandler`
        """
        if isinstance(LIMITTYPESorUrl, UrlInterface):
            # if LIMITTYPESorUrl is an Url we can assume no limittypes are requested
            url = LIMITTYPESorUrl  # backup
            LIMITTYPESorUrl = BaseArray(GetDataType(DataType).GetPointerType(), count=0)
        elif isinstance(LIMITTYPESorUrl, collections.abc.Iterable):
            # if LIMITTYPESorUrl is an iterable we can fill this for the limit types
            # The *Ref classes and DataType instances are supported
            LIMITTYPESorUrl = BaseArray(GetDataType(DataType).GetPointerType(), input=[x._dt if issubclass(x, Data) else x for x in LIMITTYPESorUrl])
            if url is None:
                raise AttributeError("url must be set when limit types are passed")
        if detectedCallback is None:
            def returnTrue(u, h):
                # return true to stop execution when the first format was found.
                return True
            detectedCallback = returnTrue

        #
        return FileFormatDetectionInterface._DetectAll(url, LIMITTYPESorUrl, detectedCallback)


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.networkip")
class NetworkIpInterface:
    """
    Static interface to access network functionality.
    """

    @staticmethod
    @MAXON_STATICMETHOD("net.maxon.interface.networkip.SplitAddress")
    def _SplitAddress(address, scheme, host, port):
        pass

    @staticmethod
    @MAXON_FUNCTION("net.maxon.interface.networkip.SplitAddress")
    def SplitAddress(address):
        """
        SplitAddress(address)
        Splits a passed address in its elements.

        :param address: The address.
        :type address: str
        :return: A tuple with the Scheme, host and port in this order.
        :rtype: tuple(str, str, int)
        """
        scheme, host, port = StringInterface(), StringInterface(), Int32(-1)
        NetworkIpInterface._SplitAddress(address, scheme, host, port)
        return MaxonConvert(scheme, host, port)


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NONE, "net.maxon.interface.machines")
class MachinesInterface:
    """
    | This class declares functions to access and manage machines.
    | There is no difference when accessing the machines using the available rpc interfaces where the machine runs
      (local, remote, webbrowser).
    """

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.machines.GetLocal')
    def GetLocal():
        """
        GetLocal()
        | Returns the local machine.
        |
        | It can be used like every other machine in the network.
        | The difference is that the functions for this machine are called directly not using rpc.

        :return: Handle to the machine.
        :rtype: :class:`maxon.MachineRef`
        """
        pass


class MACHINEINFO:
    #: (str) Computer name returned by the OS.
    COMPUTERNAME                   = MAXON_ATTRIBUTE("net.maxon.machineinfo.computername")

    #: (str) User name of the currently logged in user.
    USERNAME                       = MAXON_ATTRIBUTE("net.maxon.machineinfo.username")

    #: (str) OS Version in text format.
    OSVERSION                      = MAXON_ATTRIBUTE("net.maxon.machineinfo.osversion")

    #: (int) OS build number as integer value.
    OSBUILDNUMBER                  = MAXON_ATTRIBUTE("net.maxon.machineinfo.osbuildnumber")

    #: :class:`maxon.BaseArray` (:class:`maxon.Id`)) Languages in order of preference.
    #: The first language is the most preferred language.
    LANGUAGES                      = MAXON_ATTRIBUTE("net.maxon.machineinfo.languages")

    #: (int) Linux and OSX only (getuid).
    USER_ID                        = MAXON_ATTRIBUTE("net.maxon.machineinfo.user_id")

    #: (int) Linux and OSX only (geteuid).
    EFFECTIVE_USER_ID              = MAXON_ATTRIBUTE("net.maxon.machineinfo.effective_user_id")

    #: (int) Linux and OSX only (getgid).
    GROUP_ID                       = MAXON_ATTRIBUTE("net.maxon.machineinfo.group_id")

    #: (int) Linux and OSX only (getegid).
    EFFECTIVE_GROUP_ID             = MAXON_ATTRIBUTE("net.maxon.machineinfo.effective_group_id")

    #: (str) CPU id string.
    PROCESSORTYPE                  = MAXON_ATTRIBUTE("net.maxon.machineinfo.processortype")

    #: (str) Name of the processor.
    PROCESSORNAME                  = MAXON_ATTRIBUTE("net.maxon.machineinfo.processorname")

    #: (str) Supported cpu features.
    PROCESSORFEATURES              = MAXON_ATTRIBUTE("net.maxon.machineinfo.processorfeatures")

    #: (float) Nominal processor frequency.
    PROCESSORFREQMHZ               = MAXON_ATTRIBUTE("net.maxon.machineinfo.processorfreqmhz")

    #: (str) Processor architecture.
    PROCESSORARCHITECTURE          = MAXON_ATTRIBUTE("net.maxon.machineinfo.processorarchitecture")

    #: (int) Number of threads including hyper threading cores.
    NUMBEROFPROCESSORS             = MAXON_ATTRIBUTE("net.maxon.machineinfo.numberofprocessors")

    #: (int) Number of physical cpu cores.
    NUMBEROFPHYSICALCORES          = MAXON_ATTRIBUTE("net.maxon.machineinfo.numberofphysicalcores")

    #: (bool) True if AVX is supported.
    SUPPORTAVX                     = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportavx")

    #: (bool) True if AVX2 is supported.
    SUPPORTAVX2                    = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportavx2")

    #: (bool) True if SSE is supported.
    SUPPORTSSE                     = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportsse")

    #: (bool) True if SSE2 is supported.
    SUPPORTSSE2                    = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportsse2")

    #: (bool) True if SSE3 is supported.
    SUPPORTSSE3                    = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportsse3")

    #: (bool) True if SSE41 is supported.
    SUPPORTSSE41                   = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportsse41")

    #: (bool) True if SSE42 is supported.
    SUPPORTSSE42                   = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportsse42")

    #: (bool) True if FMA is supported.
    SUPPORTFMA                     = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportfma")

    #: (bool) True if AES is supported.
    SUPPORTAES                     = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportaes")

    #: (bool) True if PCLMULQDQ is supported.
    SUPPORTPCLMULQDQ               = MAXON_ATTRIBUTE("net.maxon.machineinfo.supportpclmulqdq")


class URLFLAGS:
    #: (bool) Set to True, if file should be unbuffered.
    UNBUFFERED_FILE                = MAXON_ATTRIBUTE("net.maxon.url.unbuffered_file")

    #: (:class:`maxon.TimeValue`) Connection time out for network connections.
    NETWORK_CONNECTTIMEOUT         = MAXON_ATTRIBUTE("net.maxon.url.network_connecttimeout")

    #: (:class:`maxon.TimeValue`) Session time out for network connections.
    NETWORK_SESSIONTIMEOUT         = MAXON_ATTRIBUTE("net.maxon.url.network_sessiontimeout")

    #: (str) ser name for the the url. RFC3986 (7.5)
    USERNAME                       = MAXON_ATTRIBUTE("net.maxon.url.username")

    #: (str) Password for the url. RFC3986 (7.5)
    USERPASSWORD                   = MAXON_ATTRIBUTE("net.maxon.url.userpassword")

    #: (str) Serves to identify a resource within the scope of the url scheme e.g. "date=today"
    QUERY                          = MAXON_ATTRIBUTE("net.maxon.url.query")

    #: (str) Holds additional identifying information that provides direction to a secondary resource.
    FRAGMENT                       = MAXON_ATTRIBUTE("net.maxon.url.fragment")

    #: (:class:`maxon.DataDictionary`) Each entry in the dictionary will be added
    #: to the http request in the form `key: value\\r\\n`.
    HTTP_ADDITIONAL_REQUEST_HEADER = MAXON_ATTRIBUTE("net.maxon.url.http_additional_request_header")

    #: (:class:`maxon.DataDictionary`) Writes the response header into the datadictionary.
    HTTP_RESPONSE_HEADER           = MAXON_ATTRIBUTE("net.maxon.url.http_response_header")

    #: (bool) Set to true if a http connection should follow "301 permanently moved file" and open the moved file instead.
    HTTP_FOLLOWMOVEDFILES          = MAXON_ATTRIBUTE("net.maxon.url.http_followmovedfiles")

    #: (bool) Set to true if a you want to send a POST request, otherwise GET will be assumed.
    HTTP_POSTMETHOD                = MAXON_ATTRIBUTE("net.maxon.url.http_postmethod")

    #: (str) If HTTPPOST is true, add additional data. the data needs to be url encoded.
    HTTP_POSTDATA                  = MAXON_ATTRIBUTE("net.maxon.url.http_postdata")

    #: (bool) If a proxy Server is used set the "Cache-Control: no-cache".
    HTTP_NO_PROXY_CACHING          = MAXON_ATTRIBUTE("net.maxon.url.http_no_proxy_caching")

    #: (bool) Set to true, if gzip compression is not allowed.
    HTTP_DISALLOW_GZIP             = MAXON_ATTRIBUTE("net.maxon.url.http_disallow_gzip")

    #: (bool) If true, the cache is created in the RAM, otherwise in the machines temp directory on harddrive.
    CACHE_IN_RAM                   = MAXON_ATTRIBUTE("net.maxon.url.cache_in_ram")

    #: (:class:`maxon.Url`) If defined set the custom certificate file to be used.
    USECUSTOMCLIENTCERTIFICATE     = MAXON_ATTRIBUTE("net.maxon.url.usecustomclientcertificate")


class STREAMFLAGS:
    #: (:class:`maxon.NetworkIpAddrPort`) [readonly] Returns the remote server
    #:  address for the current http stream.
    HTTP_REMOTEADDRESS             = MAXON_ATTRIBUTE("net.maxon.stream.http_remoteaddress")

    #: (:class:`maxon.NetworkIpAddrPort`) [readonly] Returns the remote server
    HTTP_HEADER                    = MAXON_ATTRIBUTE("net.maxon.stream.http_header")


# TODO: (Seb) make native like vector
class TimeValue(object):
    """
    The :class:`maxon.TimeValue` class encapsulates a timer value.
    """
    _value = 0.0

    def __init__(self, seconds):
        self._value = seconds

    def __sub__(self, b):
        return TimeValue(self._value - b._value)

    def __rsub__(self, b):
        return TimeValue(self._value - b._value)

    def __add__(self, b):
        return TimeValue(self._value + b._value)

    def __radd__(self, b):
        return TimeValue(self._value + b._value)

    def GetSeconds(self):
        """
        GetSeconds()
        Get the :class:`maxon.TimeValue`

        :return: Time value in seconds.
        :rtype: :class:`maxon.TimeValue`
        """
        return self._value

    def SetSeconds(self, seconds):
        """
        SetSeconds(seconds)
        Set the :class:`maxon.TimeValue`

        :param seconds: seconds	time value in seconds.
        :type seconds: float
        """
        self._value = seconds

    def __str__(self):
        return str(self._value) + " sec."

    def __repr__(self):
        return str(self._value) + " sec."


class Seconds(TimeValue):
    """
    Timer value in seconds.
    """
    def __init__(self, seconds):
        TimeValue.__init__(self, seconds)


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.uuid")
class UuidInterface:

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.uuid.Alloc@d7b47574339c8827', returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def AllocEmpty():
        """
        AllocEmpty()
        Return a new Uuid.

        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.uuid.Alloc@13d0493b3524a408', returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def AllocFromUuid(uuid):
        """
        AllocFromUuid(uuid)
        Return a copy of the passed Uuid.

        :param uuid: The uuid to copy.
        :type uuid: :class:`maxon.Uuid`
        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.uuid.Alloc@207c095f1c7399ad', returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def AllocFromString(uuidStr):
        """
        AllocFromString(uuidStr)
        Create a new Uuid based on a string representing a valid Uuid.

        :param uuid: The sting to copy to an Uuid.
        :type uuid: str
        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        pass

    @staticmethod
    @MAXON_OVERLOAD()
    def Alloc(uuid=None):
        """
        AllocFromUuid(obj=None)
        Create a new Uuid.

        :param uuid: None if a totally new Uuid should be returned otherwise a copy will be performed.
        :type uuid: Union[None, SourceLocation, String, str, Uuid]
        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        if uuid is None:
            return UuidInterface.AllocEmpty(MAXON_SOURCE_LOCATION())
        elif isinstance(uuid, SourceLocation):
            return UuidInterface.AllocEmpty(MAXON_SOURCE_LOCATION())
        elif isinstance(uuid, (str, StringInterface)):
            return UuidInterface.AllocFromString(MAXON_SOURCE_LOCATION(), uuid)
        elif isinstance(uuid, UuidInterface):
            return UuidInterface.AllocFromUuid(MAXON_SOURCE_LOCATION(), uuid)
        else:
            raise TypeError("unknown type %s" % str(type(uuid)))

    @MAXON_METHOD('net.maxon.interface.uuid.IsEmpty')
    def IsEmpty(self):
        """
        IsEmpty()
        | Returns whether the object is empty or not.
        | A Uuid is empty if it hasn't been constructed yet, or if a copy operation on the object failed, or if it just contains 0-values.

        :return: Returns whether the object is empty or not.
        :rtype: bool
        """
        pass

    @MAXON_FUNCTION('net.maxon.interface.uuid.IsPopulated')
    def IsPopulated(self):
        """
        IsPopulated()
        | Returns whether the object is populated or not.
        | Always the opposite of IsEmpty().

        :return: Returns whether the object is populated or not.
        :rtype: bool
        """
        return not self.IsEmpty()

    @MAXON_METHOD('net.maxon.interface.uuid.CreateId')
    def CreateId(self):
        """
        CreateId()
        Creates a new uuid.

        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        pass

    @MAXON_METHOD('net.maxon.interface.uuid.Set@d85d74e087a2f051')
    def Set(self, uuid):
        """
        Set(uuid)
        Sets a given uuid string. The id must be of the format "00000000-0000-0000-0000-000000000000".

        :param uuid: String with a valid uuid.
        :type uuid: Union[str, StringInterface]
        :raise IllegalArgumentError: if the id could not be parsed.
        """
        pass

    @MAXON_METHOD('net.maxon.interface.uuid.ToString')
    def ToString(self):
        """
        ToString()
        | Converts the uuid into a string.
        | The format will be "00000000-0000-0000-0000-000000000000" and the letters will be uppercase.

        :return: String representation of the uuid.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.uuid.Compare')
    def Compare(self):
        """
        Compare(uuid)
        Compares the uuid against another uuid.

        :type uuid: :class:`maxon.Uuid`
        :param uuid: The uuid to compare with.
        :rtype: maxon.COMPARERESULT
        :return: See COMPARERESULT.
        """
        pass

    @MAXON_METHOD('net.maxon.interface.uuid.GetHashCode')
    def GetHashCode(self):
        """
        GetHashCode()
        Returns the hash code of the uuid.

        .. note::

            The return value is 0 if the object IsEmpty().

        :rtype: int
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.uuid.DescribeIO')
    def DescribeIO(stream):
        """
        DescribeIO(stream)
        Describes all elements of this class for I/O operations.

        :param stream: The stream that is used to register the class members.
        :type stream: :class:`maxon.DataSerializeInterface`
        """
        pass

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.uuid.CreateUuidString')
    def CreateUuidString():
        """
        CreateUuidString()
        Creates a new uuid and returns the string of it.

        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        pass


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_NORMAL, "net.maxon.interface.language")
class LanguageInterface:

    @staticmethod
    @MAXON_STATICMETHOD('net.maxon.interface.language.Alloc', returnOwnership=consts.ReturnTypeOwnership.CALLEE_BUT_COPY)
    def _Alloc():
        """
        AllocEmpty()
        Return a new Uuid.

        :rtype: :class:`maxon.Uuid`
        :return: The newly created Uuid.
        """
        pass

    @staticmethod
    @MAXON_FUNCTION_EXTEND('net.maxon.interface.language.Alloc')
    def Alloc(source_locaton=MAXON_SOURCE_LOCATION()):
        return LanguageInterface._Alloc(source_locaton)

    @MAXON_METHOD('net.maxon.interface.language.LoadResourceString')
    def LoadResourceString(self, scope, keyValue):
        """Loads a string from the resource.

        :param scope: The resource scope of a resource symbol.
        :type scope: :class:`maxon.Id`
        :param keyValue: The value of a resource symbol.
        :type keyValue: :class:`maxon.InternedId`
        :return: String.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.language.GetName')
    def GetName(self):
        """Returns the real (country-specific) name of a language.

        :return: The name.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.language.GetIdentifier')
    def GetIdentifier(self):
        """ Returns the identifier of a language.
        
        :return: The name.
        :rtype: :class:`maxon.Id`
        """

    @MAXON_METHOD('net.maxon.interface.language.GetFallbackLanguage')
    def GetFallbackLanguage(self):
        """ Returns the fallback language of this language.

        :return: **None** if the language has no fallback language (e.g. "en-US" has none because it's the root of all languages).
        :rtype: :class:`maxon.LanguageRef`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.language.ToString')
    def ToString(self):
        pass


@MAXON_INTERFACE_NONVIRTUAL(consts.MAXON_REFERENCE_COPY_ON_WRITE, "net.maxon.interface.datadescription")
class DataDescriptionInterface:

    @MAXON_METHOD('net.maxon.interface.datadescription.GetInfo')
    def GetInfo(self):
        """Returns the info dictionary.

        :return: The info dictionary.
        :rtype: :class:`maxon.DataDictionary`.
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.SetInfo')
    def SetInfo(self, info):
        """The info dictionary of the description.

        :param info: Dictionary with infos.
        :type info: :class:`maxon.DataDictionary`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.GetEntryCount')
    def GetEntryCount(self):
        """Returns the number of entries in the description.

        :return: The number of entries in the description.
        :rtype: int
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.GetEntries')
    def GetEntries(self):
        """Returns a array with all entries.

        :return: A array with all entries.
        :rtype: :class:`maxon.BaseArray`( :class:`maxon.DataDictionary`)
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.GetEntry')
    def GetEntry(self, id):
        """Returns a specific entry with the given id.

        :param id: Id to find.
        :type id: :class:`maxon.Id`
        :return: DataDictionary on success. Error if the requested attribute was not in the description-
        :rtype: :class:`maxon.DataDictionary`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.SetEntry')
    def _SetEntry(self, props, merge):
        """SetEntry description.

        :param props: Properties to set. The DESCRIPTION::BASE::IDENTIFIER will be used as key for the hashmap.
        :type props: :class:`maxon.DataDictionary`
        :param merge: **True** if the container should be merged with the existing props im the description. The given props will have priority over the existing.
        :type merge: bool
        :return: **True** if properties has been changed.
        :rtype: bool
        """
        pass

    @MAXON_FUNCTION_EXTEND("net.maxon.interface.datadescription.SetEntry")
    def SetEntry(self, props, merge=False):
        """SetEntry description.

        :param props: Properties to set. The DESCRIPTION::BASE::IDENTIFIER will be used as key for the hashmap.
        :type props: :class:`maxon.DataDictionary`
        :param merge: **True** if the container should be merged with the existing props im the description. The given props will have priority over the existing.
        :type merge: bool
        :return: **True** if properties has been changed.
        :rtype: bool
        pass
        """

    @MAXON_METHOD('net.maxon.interface.datadescription.EraseEntry')
    def EraseEntry(self, id):
        """Deletes a attribute from the description.

        :param id: :class:`maxon.Id` of the attribute to delete.
        :type id: :class:`maxon.InternedId`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.Reset')
    def Reset(self):
        """Resets the description and clear all attributes.
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.IsEqual')
    def IsEqual(self, other, equality):
        """Compares two descriptions.

        :param other: Other description to compare.
        :type other: :class:`maxon.DataDescriptionInterface`
        :param equality: See @EQUALITY.
        :type equality: :class:`maxon.EQUALITY`
        :return: True in equality.
        :rtype: bool
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.Compare')
    def Compare(self, other):
        """Compares the 2 values.

        :param other: Other description to compare.
        :type other: :class:`maxon.DataDescriptionInterface`
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.GetHashCode')
    def GetHashCode(self):
        """Returns the hashcode of the description.

        :return: The hashcode.
        :rtype: int
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.ToString')
    def ToString(self):
        """ Returns a readable string of the content.

        :return: A readable string of the content.
        :rtype: str
        """
        pass

    @MAXON_METHOD('net.maxon.interface.datadescription.DescribeIO')
    def DescribeIO(self, stream):
        """ Describe all elements of this class for I/O operations.

        :param stream: The stream that is used to register the class members.
        :type stream: :class:`maxon.DataSerializeInterface`
        """
        pass


class Timer:
    """
    A timer class to retrieve the current time.
    """
    @staticmethod
    def Get():
        """
        Get()
        Returns the current system time which is being used by the Timer class.

        :return: Returns the current system time.
        :rtype: :class:`maxon.Seconds`
        """
        return Seconds(System.GetCustomTimer())


class Declaration(object):
    """
    | Maxon API rely on object that are declared. Such object are stored under a :class:`maxon.Declaration` object.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    _ids = None
    _cachedObj = None

    # If this declaration is belongs to a registry, the following two members are set / changed by
    # RegistryMeta.__getattribute__. See RegistryMeta.__getattribute__ for more information.
    _registryIds = None
    _returnType = None

    def __init__(self, ids, entityBaseType=None, returnType=None):
        self._ids = ids
        self._entityBaseType = entityBaseType
        self._returnType = returnType

    def GetId(self):
        """
        GetId()
        Retrieves the Id of the declaration

        :return: The declaration id
        :rtype: :class:`maxon.Id`
        """
        return self._ids

    def __call__(self):  # noqa C901
        if self._cachedObj is None:
            if self._registryIds:
                t = RegistryInterface.FindEntryValue(self._registry, self._ids)
                if not t:
                    raise LookupError("could not find registry entry {}".format(self._ids))
                # if return type is of type maxon.Class(TYPE) like maxon.Class(ObjectRef)
                if hasattr(self._returnType, "R") and self._returnType.R:
                    self._cachedObj = Cast(self._returnType.R, t)
                elif self._returnType == CONVERSIONMODE.TOBUILTIN:
                    self._cachedObj = MaxonConvert(t, CONVERSIONMODE.TOBUILTIN)
                elif self._returnType == CONVERSIONMODE.TOMAXON:
                    self._cachedObj = t
                else:  # default
                    if t.GetType() in g_converters:
                        self._cachedObj = t.MaxonConvert()
                    else:
                        self._cachedObj = t
            else:
                # Enums are not loaded yet, so we have to use hardcoded constants
                EntityBase_TYPE_OBJECT = 4  # A published object with a single definition, declared by #MAXON_DECLARATION.
                EntityBase_TYPE_CLASS = 6  # An object of type GenericClass or Class<T>

                firstAttempt = EntityBase_TYPE_OBJECT if self._entityBaseType is None else self._entityBaseType
                try:
                    self._cachedObj = System.FindDefinitionGetData(firstAttempt, self._ids, Data
                                                                   if isinstance(self._returnType, CONVERSIONMODE) and self._returnType == CONVERSIONMODE.TOMAXON else None)
                except LookupError:
                    # if the first lookup failed and the entityBaseType is None, it means we have to automatically check if the
                    # requested object is not rather a class type (EntityBase_TYPE_CLASS)
                    if self._entityBaseType is None:
                        try:
                            self._cachedObj = System.FindDefinitionGetData(EntityBase_TYPE_CLASS, self._ids, Data
                                                                           if isinstance(self._returnType, CONVERSIONMODE) and self._returnType == CONVERSIONMODE.TOMAXON else None)
                        except LookupError:
                            # if the second lookup failed as well, we can't find the object
                            self._cachedObj = None
                    else:
                        self._cachedObj = None

            # if the return type is a class, we attach the type to the cached declaration object
            # so Class.Create() without any arguments will cast the returned object to the requested type automatically
            if hasattr(self._returnType, "R") and self._returnType.R:
                self._cachedObj.R = self._returnType.R

            # if there is no return type hint set, we automatically detect the datatype for Class(..) objects
            elif isinstance(self._cachedObj, ClassInterface):
                dt = self._cachedObj.GetDataType()
                self._cachedObj.R = _maxon_mapping.GetAssociatedDataType(dt)

        return self._cachedObj


def MAXON_DECLARATION(ids, entityBaseType=None, returnType=None):
    """
    MAXON_DECLARATION(ids, entityBaseType=None, returnType=None)
    Decorator to mark an element as a maxon API element (available from a registry).

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.

    :param ids: The :class:`maxon.Id` linked to the registered element.
    :type ids: :class:`maxon.Id`
    :param entityBaseType: The base class of the entity to be registered.
    :type entityBaseType: Union[None, :class:`maxon.DataType`, :class:`maxon.Data`)
    :param returnType: The expected Python Type object
    :type returnType: Union[None, :class:`maxon.DataType`, :class:`maxon.Data`)
    :return: The declaration object.
    :rtype: :class:`maxon.Declaration`
    """
    return Declaration(ids, entityBaseType, returnType)


def MAXON_COMPONENT(kind=ClassInterface.KIND.NORMAL, *ARGS):
    """
    MAXON_COMPONENT(kind=ClassInterface.KIND.NORMAL, *ARGS)
    Decorator to mark an element as a maxon API component (available from a registry)

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.

    :param kind: The kind of interface to be exposed
    :type kind: :class:`maxon.ClassInterface.KIND`
    :param ARGS: Any Interface to inherit from.
    :return: The component object
    """
    def PRIVATE_MAXON_COMPONENT(cls):
        cls._kind = kind
        cls._vinterfaces = ARGS

        return cls
    return PRIVATE_MAXON_COMPONENT


class ComponentRoot(object):
    """
    | :class:`maxon.ComponentRoot` is the base class of all components (see :class:`maxon.MAXON_COMPONENT`).
    |
    | Usually you don't have to take care of this because the :class:`maxon.Component` template automatically sets
      :class:`maxon.ComponentRoot` as base class.
    |
    | But if you use :class:`maxon.ComponentWithBase` instead, you have to make sure that the base class you use for
      that template derives from :class:`maxon.ComponentRoot`.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """

    _object = None  # ObjectDefinition, will be set by MAXON_COMPONENT_CLASS_XXX
    _data = None  # is set when the object is set

    def __init__(self, data=None):
        self._data = data

    def InitComponent(self):
        """
        | Gets called right after a new object has been constructed.
        |
        | You can override this function in a component class to initialize the component.
        | Unlike the constructor this function can return an error.
        |
        | Also all components have been constructed when this function gets called, so you can call methods or access
          other components.
        | But keep in mind that only super components have been initialized.
        """
        pass

    def FreeComponent(self):
        """
        | Gets called before an object gets destructed.
        |
        | You can override this function in a component class to free the component at a point of time where the
          whole object is still valid, so you can call methods or access other components which is not allowed in the
          destructor.
        |
        | But keep in mind that later components might already have done clean-up in their
          :func:`ComponentRoot.FreeComponent` functions.
        """
        pass

    @classmethod
    def Get(cls, ref):
        """
        Get(ref)

        :param ref:
        :return:
        """
        return _maxon_component.Component_GetAttr(ref)

    @classmethod
    def GetClass(cls):
        """
        GetClass()
        Retrieve the stored class
        """
        return cls._object.PrivateGetClass()

    @classmethod
    def CreateInit(cls, *args):
        """
        CreateInit(*args)
        :param args:
        :return:
        """
        c = cls.GetClass().CreateRef()
        _maxon_component.Component_GetAttr(c).Init(*args)
        return c


def Component(*INTERFACES):
    """
    Component(*INTERFACES)
    | A component implements the functions of a given interface.
    |
    | Different implementations of the same interface define different components.
    | Since these different implementations implement the functionality of the same interface they may have a lot
      of code in common.
    |
    | To reduce redundant code it is possible to define a base component that
      can be reused in different implementations.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.

    :param INTERFACES: Any Interface to inherit from.
    """
    d = dict(ComponentRoot.__dict__)

    def __new__(cls, *args):
        return object.__new__(cls)

    d["__new__"] = __new__
    return type("ComponentWithBase", (ComponentRoot,) + INTERFACES, d)


def PRIVATE_MAXON_CLASS_REGISTER(impl, registryOrCid, cid="", printErrors=True, createObject=False, dt=None):
    registryId = ""  # registryId can be empty if no registration is needed
    if cid:  # if cid is set, we expect registryOrCid to be a registry
        registryId = registryOrCid.GetId()
    else:
        cid = registryOrCid

    # extract ids from all baseclasses
    baseClassIds = BaseArray(ob=Id, count=len(impl._vinterfaces))
    for i, v in enumerate(impl._vinterfaces):
        baseClassIds[i] = v.GetId()

    # the implementation must be derived from a temporary created ComponentWithBase
    componentBaseCls = impl.__bases__[0]
    assert componentBaseCls.__name__ == "ComponentWithBase"

    interfaceClasses = [x for x in componentBaseCls.__bases__ if x is not ComponentRoot]

    # extract all ids from all interfaces
    interfaceReferenceIds = BaseArray(ob=Id, count=len(interfaceClasses))
    for i, v in enumerate(interfaceClasses):
        for id in v._id:
            if id not in interfaceClasses:
                interfaceReferenceIds[i] = id

    return _maxon_component.RegisterComponentProxy(impl, registryId, interfaceReferenceIds, baseClassIds, cid, printErrors, impl._kind, MAXON_SOURCE_LOCATION(2), createObject, dt)


class ObjectDefinition(object):
    """
    Represent an Object

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    def __init__(self, iid, object):
        self._iid = iid
        self._object = object

    def GetId(self):
        """
        Retrieve the :class:`maxon.Id` stored representing the object.
        :return: The Unique definition identifier of the current object.
        :rtype: :class:`maxon.Id`
        """
        return self._iid

    def PrivateGetClass(self):
        """
        Retrieves the current class of the object.
        """
        return self._object


def MAXON_COMPONENT_OBJECT_REGISTER(impl, registryOrCid, cid="", printErrors=True, dt=None):
    """
    | MAXON_COMPONENT_OBJECT_REGISTER registers a component, creates an object class which uses the component and
      finally creates an instance of the object class.
    | The instance is registered under the given identifier.
    |
    | As for MAXON_COMPONENT_CLASS_REGISTER, the object class consists of the base components and base classes
      (if any) which you have specified in the MAXON_COMPONENT macro,
      and then the component itself.
    | You can obtain the object class by the GetClass() function of the component implementation class.
    | In addition to MAXON_COMPONENT_CLASS_REGISTER this macro also creates an instance of the object class
      (using Create() on the class).
    | This instance will be registered using the identifier given as argument to the macro.
    | So you use this macro e.g. for registries like IoHandlers with entries of type IoHandler,
      while you use MAXON_COMPONENT_CLASS_REGISTER for registries like
    | UnitTestClasses with entries of type Class<UnitTestRef>.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    clsObject = PRIVATE_MAXON_CLASS_REGISTER(impl, registryOrCid, cid, printErrors, createObject=True, dt=dt.R()._dt if dt else None)
    impl._object = ObjectDefinition(cid if cid else registryOrCid, clsObject)


def MAXON_COMPONENT_CLASS_REGISTER(impl, registryOrCid, cid="", printErrors=True):
    """
    | MAXON_COMPONENT_OBJECT_REGISTER registers a component, creates an object class which uses the component and
      finally creates an instance of the object class.
    | The instance is registered under the given identifier.
    |
    | As for MAXON_COMPONENT_CLASS_REGISTER, the object class consists of the base components and base classes
      (if any) which you have specified in the MAXON_COMPONENT macro,
      and then the component itself.
    | You can obtain the object class by the GetClass() function of the component implementation class.
    | In addition to MAXON_COMPONENT_CLASS_REGISTER this macro also creates an instance of the object class
      (using Create() on the class).
    | This instance will be registered using the identifier given as argument to the macro.
    | So you use this macro e.g. for registries like IoHandlers with entries of type IoHandler,
      while you use MAXON_COMPONENT_CLASS_REGISTER for registries like
    | UnitTestClasses with entries of type Class<UnitTestRef>.

    .. warning::

        | This function is only there to expose a C++ Object to Python.
        | As a Python developer you normally don't have to deal with this function.
    """
    clsObject = PRIVATE_MAXON_CLASS_REGISTER(impl, registryOrCid, cid, printErrors, createObject=False, dt=None)
    impl._object = ObjectDefinition(cid if cid else registryOrCid, clsObject)

