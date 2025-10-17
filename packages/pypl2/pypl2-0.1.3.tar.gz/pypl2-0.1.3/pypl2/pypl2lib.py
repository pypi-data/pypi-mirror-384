# pypl2lib.py - Classes and functions for accessing functions
# in PL2FileReader.dll
#
# (c) 2016 Plexon, Inc., Dallas, Texas
# www.plexon.com
#
# This software is provided as-is, without any warranty.
# You are free to modify or share this file, provided that the above
# copyright notice is kept intact.

from ctypes import *
import os
import platform
import pathlib

class tm(Structure):
    _fields_ = [("tm_sec",c_int),
                ("tm_min",c_int),
                ("tm_hour",c_int),
                ("tm_mday",c_int),
                ("tm_mon",c_int),
                ("tm_year",c_int),
                ("tm_wday",c_int),
                ("tm_yday",c_int),
                ("tm_isdst",c_int)]

class FileInfo(Structure):
    _fields_ = [("m_CreatorComment",c_char * 256),
                ("m_CreatorSoftwareName",c_char * 64),
                ("m_CreatorSoftwareVersion",c_char * 16),
                ("m_CreatorDateTime",tm),
                ("m_CreatorDateTimeMilliseconds",c_int),
                ("m_TimestampFrequency",c_double),
                ("m_NumberOfChannelHeaders",c_uint),
                ("m_TotalNumberOfSpikeChannels",c_uint),
                ("m_NumberOfRecordedSpikeChannels",c_uint),
                ("m_TotalNumberOfAnalogChannels",c_uint),
                ("m_NumberOFRecordedAnalogChannels",c_uint),
                ("m_NumberOfDigitalChannels",c_uint),
                ("m_MinimumTrodality",c_uint),
                ("m_MaximumTrodality",c_uint),
                ("m_NumberOfNonOmniPlexSources",c_uint),
                ("m_Unused",c_int),
                ("m_ReprocessorComment",c_char * 256),
                ("m_ReprocessorSoftwareName",c_char * 64),
                ("m_ReprocessorSoftwareVersion",c_char * 16),
                ("m_ReprocessorDateTime",tm),
                ("m_ReprocessorDateTimeMilliseconds",c_int),
                ("m_StartRecordingTime",c_ulonglong),
                ("m_DurationOfRecording",c_ulonglong)]

class AnalogChannelInfo(Structure):
    _fields_ = [("m_Name",c_char * 64),
                ("m_Source",c_uint),
                ("m_Channel",c_uint),
                ("m_ChannelEnabled",c_uint),
                ("m_ChannelRecordingEnabled",c_uint),
                ("m_Units",c_char * 16),
                ("m_SamplesPerSecond",c_double),
                ("m_CoeffToConvertToUnits",c_double),
                ("m_SourceTrodality",c_uint),
                ("m_OneBasedTrode",c_ushort),
                ("m_OneBasedChannelInTrode",c_ushort),
                ("m_NumberOfValues",c_ulonglong),
                ("m_MaximumNumberOfFragments",c_ulonglong)]
                
class SpikeChannelInfo(Structure):
    _fields_ = [("m_Name",c_char * 64),
                ("m_Source",c_uint),
                ("m_Channel",c_uint),
                ("m_ChannelEnabled",c_uint),
                ("m_ChannelRecordingEnabled",c_uint),
                ("m_Units",c_char * 16),
                ("m_SamplesPerSecond",c_double),
                ("m_CoeffToConvertToUnits",c_double),
                ("m_SamplesPerSpike",c_uint),
                ("m_Threshold",c_int),
                ("m_PreThresholdSamples",c_uint),
                ("m_SortEnabled",c_uint),
                ("m_SortMethod",c_uint),
                ("m_NumberOfUnits",c_uint),
                ("m_SortRangeStart",c_uint),
                ("m_SortRangeEnd",c_uint),
                ("m_UnitCounts",c_ulonglong * 256),
                ("m_SourceTrodality",c_uint),
                ("m_OneBasedTrode",c_ushort),
                ("m_OneBasedChannelInTrode",c_ushort),
                ("m_NumberOfSpikes",c_ulonglong)]

class DigitalChannelInfo(Structure):
    _fields_ = [("m_Name",c_char * 64),
                ("m_Source",c_uint),
                ("m_Channel",c_uint),
                ("m_ChannelEnabled",c_uint),
                ("m_ChannelRecordingEnabled",c_uint),
                ("m_NumberOfEvents",c_ulonglong)]

class BlockInfo(Structure):
    _fields_ = [("m_BlockType",c_int),
                ("m_Source",c_uint),
                ("m_Channel",c_uint),
                ("m_NumberOfItems",c_int)]

BLOCK_TYPE_SPIKE = 1
BLOCK_TYPE_ANALOG = 2
BLOCK_TYPE_DIGITAL_EVENT = 3
BLOCK_TYPE_STARTSTOP_EVENT = 4
BLOCK_TYPE_NONOMNIPLEX = 5

platform_ = platform.architecture()[0]
dll_path = pathlib.Path(__file__).parent / "bin"
dll_success = True

if platform_ == '32bit':
    dll_filename = str(dll_path / 'PL2FileReader.dll')
else:
    dll_filename = str(dll_path / 'PL2FileReader64.dll')

try:
    dll = CDLL(dll_filename)
except (WindowsError):
    print("Error: Can't load PL2FileReader.dll at: " + dll_filename)
    print("PL2FileReader.dll is bundled with the C++ PL2 Offline Files SDK")
    print("located on the Plexon Inc website: www.plexon.com")
    print("Contact Plexon Support for more information: support@plexon.com")
    dll_success = False
    
def lib_open_file(pl2_filename):
    """
    Opens and returns a handle to a PL2 file.
    
    Args:
        pl2_filename - full path of the file
        file_handle - file handle
        
    Returns:
        file_handle > 0 if success
        file_handle = 0 if failure
        
    """
    file_handle = c_int(0)
    result = c_int(0)
    result = dll.PL2_OpenFile(pl2_filename.encode('ascii'), byref(file_handle))

    return file_handle.value    

def lib_close_file(file_handle):
    """
    Closes handle to PL2 file.
    
    Args:
        file_handle - file handle of file to be closed
        
    Returns:
        None
    """
    
    dll.PL2_CloseFile(c_int(file_handle))
        
def lib_close_all_files():
    """
    Closes all files that have been opened by the .dll
    
    Args:
        None
    
    Returns:
        None
    """
    
    dll.PL2_CloseAllFiles()
    
def lib_get_last_error(buffer, buffer_size):
    """
    Retrieve description of the last error
    
    Args:
        buffer - instance of c_char array
        buffer_size - size of buffer
    
    Returns:
        1 - Success
        0 - Failure
        buffer is filled with error message
    """
    
    result = c_int(0)
    result = dll.PL2_GetLastError(byref(buffer), c_int(buffer_size))
    
    return result

def lib_get_file_info(file_handle, pl2_file_info):
    """
    Retrieve information about pl2 file.
    
    Args:
        file_handle - file handle
        pl2_file_info - PL2FileInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2FileInfo passed to function is filled with file info
    """
    
    result = c_int(0)
    result = dll.PL2_GetFileInfo(c_int(file_handle), byref(pl2_file_info))
    
    return result
    
def lib_get_analog_channel_info(file_handle, zero_based_channel_index, pl2_analog_channel_info):
    """
    Retrieve information about an analog channel
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero-based analog channel index
        pl2_analog_channel_info - PL2AnalogChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2AnalogChannelInfo passed to function is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetAnalogChannelInfo(c_int(file_handle), zero_based_channel_index, byref(pl2_analog_channel_info))

    return result
    
def lib_get_analog_channel_info_by_name(file_handle, channel_name, pl2_analog_channel_info):
    """
    Retrieve information about an analog channel
    
    Args:
        file_handle - file handle
        channel_name - analog channel name
        pl2_analog_channel_info - PL2AnalogChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2AnalogChannelInfo is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetAnalogChannelInfoByName(c_int(file_handle), channel_name.encode('ascii'), byref(pl2_analog_channel_info))

    return result
    
def lib_get_analog_channel_info_by_source(file_handle, source_id, one_based_channel_index_in_source, pl2_analog_channel_info):
    """
    Retrieve information about an analog channel
    
    Args:
        file_handle - file handle
        source_id - numeric source ID
        one_based_channel_index_in_source - one-based channel index within the source
        pl2_analog_channel_info - PL2AnalogChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure        
        The instance of PL2AnalogChannelInfo is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetAnalogChannelInfoBySource(c_int(file_handle), c_int(source_id), c_int(one_based_channel_index_in_source), byref(pl2_analog_channel_info))

    return result        
    
def lib_get_analog_channel_data(file_handle, zero_based_channel_index, num_fragments_returned, num_data_points_returned, fragment_timestamps, fragment_counts, values):
    """
    Retrieve analog channel data
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero based channel index
        num_fragments_returned - c_ulonglong class instance
        num_data_points_returned - c_ulonglong class instance
        fragment_timestamps - c_longlong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        fragment_counts - c_ulonglong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        values - c_short class instance array the size of PL2AnalogChannelInfo.m_NumberOfValues
        
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """

    result = c_int(0)
    result = dll.PL2_GetAnalogChannelData(c_int(file_handle), c_int(zero_based_channel_index), byref(num_fragments_returned), byref(num_data_points_returned), byref(fragment_timestamps), byref(fragment_counts), byref(values))

    return result
    
def lib_get_analog_channel_data_subset(file_handle, zero_based_channel_index, zero_based_start_value_index, num_subset_values, num_fragments_returned, num_data_points_returned, fragment_timestamps, fragment_counts, values):
    """
    Retrieve analog channel data subset
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero based channel index
        zero_based_start_value_index - zero based sample index of the start of the subset
        num_subset_values - how many values to return in the subset
        num_fragments_returned - c_ulonglong class instance
        num_data_points_returned - c_ulonglong class instance
        fragment_timestamps - c_longlong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        fragment_counts - c_ulonglong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        values - c_short class instance array the size of PL2AnalogChannelInfo.m_NumberOfValues
        
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """
    result = c_int(0)
    result = dll.PL2_GetAnalogChannelDataSubset(c_int(file_handle), c_int(zero_based_channel_index), c_ulonglong(zero_based_start_value_index), c_uint(num_subset_values), byref(num_fragments_returned), byref(num_data_points_returned), byref(fragment_timestamps), byref(fragment_counts), byref(values))

    return result
    
def lib_get_analog_channel_data_by_name(file_handle, channel_name, num_fragments_returned, num_data_points_returned, fragment_timestamps, fragment_counts, values):
    """
    Retrieve analog channel data
    
    Args:
        file_handle - file handle
        channel_name - analog channel name
        num_fragments_returned - c_ulonglong class instance
        num_data_points_returned - c_ulonglong class instance
        fragment_timestamps - c_longlong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        fragment_counts - c_ulonglong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        values - c_short class instance array the size of PL2AnalogChannelInfo.m_NumberOfValues
        
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """

    result = c_int(0)
    result = dll.PL2_GetAnalogChannelDataByName(c_int(file_handle), channel_name.encode('ascii'), byref(num_fragments_returned), byref(num_data_points_returned), byref(fragment_timestamps), byref(fragment_counts), byref(values))
    
    return result
    
def lib_get_analog_channel_data_by_source(file_handle, source_id, one_based_channel_index_in_source, num_fragments_returned, num_data_points_returned, fragment_timestamps, fragment_counts, values):
    """
    Retrieve analog channel data
    
    Args:
        file_handle - file handle
        source_id - numeric source ID
        one_based_channel_index_in_source - one-based channel index within the source
        num_fragments_returned - c_ulonglong class instance
        num_data_points_returned - c_ulonglong class instance
        fragment_timestamps - c_longlong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        fragment_counts - c_ulonglong class instance array the size of PL2AnalogChannelInfo.m_MaximumNumberOfFragments
        values - c_short class instance array the size of PL2AnalogChannelInfo.m_NumberOfValues
        
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """
    
    result = c_int(0)
    result = dll.PL2_GetAnalogChannelDataBySource(c_int(file_handle), c_int(source_id), c_int(one_based_channel_index_in_source), byref(num_fragments_returned), byref(num_data_points_returned), byref(fragment_timestamps), byref(fragment_counts), byref(values))
    
    return result
    
def lib_get_spike_channel_info(file_handle, zero_based_channel_index, pl2_spike_channel_info):
    """
    Retrieve information about a spike channel
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero-based spike channel index
        pl2_spike_channel_info - PL2SpikeChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2SpikeChannelInfo passed to function is filled with channel info
    """

    result = c_int(0)
    result = dll.PL2_GetSpikeChannelInfo(c_int(file_handle), c_int(zero_based_channel_index), byref(pl2_spike_channel_info))
    
    return result

def lib_get_spike_channel_info_by_name(file_handle, channel_name, pl2_spike_channel_info):
    """
    Retrieve information about a spike channel
    
    Args:
        file_handle - file handle
        channel_name - spike channel name
        pl2_spike_channel_info - PL2SpikeChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2SpikeChannelInfo passed to function is filled with channel info
    """

    result = c_int(0)
    result = dll.PL2_GetSpikeChannelInfoByName(c_int(file_handle), channel_name.encode('ascii'), byref(pl2_spike_channel_info))
    
    return result

def lib_get_spike_channel_info_by_source(file_handle, source_id, one_based_channel_index_in_source, pl2_spike_channel_info):
    """
    Retrieve information about a spike channel
    
    Args:
        file_handle - file handle
        source_id - numeric source ID
        one_based_channel_index_in_source - one-based channel index within the source
        pl2_spike_channel_info - PL2SpikeChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2SpikeChannelInfo passed to function is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetSpikeChannelInfoBySource(c_int(file_handle), c_int(source_id), c_int(one_based_channel_index_in_source), byref(pl2_spike_channel_info))
    
    return result        

def lib_get_spike_channel_data(file_handle, zero_based_channel_index, num_spikes_returned, spike_timestamps, units, values):
    """
    Retrieve spike channel data
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero based channel index
        num_spikes_returned - c_ulonglong class instance
        spike_timestamps - c_ulonglong class instance array the size of PL2SpikeChannelInfo.m_NumberOfSpikes
        units - c_ushort class instance array the size of PL2SpikeChannelInfo.m_NumberOfSpikes
        values - c_short class instance array the size of (PL2SpikeChannelInfo.m_NumberOfSpikes * PL2SpikeChannelInfo.m_SamplesPerSpike)
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """

    result = c_int(0)
    result = dll.PL2_GetSpikeChannelData(c_int(file_handle), c_int(zero_based_channel_index), byref(num_spikes_returned), byref(spike_timestamps), byref(units), byref(values))
    
    return result

def lib_get_spike_channel_data_by_name(file_handle, channel_name, num_spikes_returned, spike_timestamps, units, values):
    """
    Retrieve spike channel data
    
    Args:
        file_handle - file handle
        channel_name = channel name
        num_spikes_returned - c_ulonglong class instance
        spike_timestamps - c_ulonglong class instance array the size of PL2SpikeChannelInfo.m_NumberOfSpikes
        units - c_ushort class instance array the size of PL2SpikeChannelInfo.m_NumberOfSpikes
        values - c_short class instance array the size of (PL2SpikeChannelInfo.m_NumberOfSpikes * PL2SpikeChannelInfo.m_SamplesPerSpike)
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """

    result = c_int(0)
    result = dll.PL2_GetSpikeChannelDataByName(c_int(file_handle), channel_name.encode('ascii'), byref(num_spikes_returned), byref(spike_timestamps), byref(units), byref(values))    
    
    return result
    
def lib_get_spike_channel_data_by_source(file_handle, source_id, one_based_channel_index_in_source, num_spikes_returned, spike_timestamps, units, values):
    """
    Retrieve spike channel data
    
    Args:
        file_handle - file handle
        source_id - numeric source ID
        one_based_channel_index_in_source - one-based channel index within the source
        num_spikes_returned - c_ulonglong class instance
        spike_timestamps - c_ulonglong class instance array the size of PL2SpikeChannelInfo.m_NumberOfSpikes
        units - c_ushort class instance array the size of PL2SpikeChannelInfo.m_NumberOfSpikes
        values - c_short class instance array the size of (PL2SpikeChannelInfo.m_NumberOfSpikes * PL2SpikeChannelInfo.m_SamplesPerSpike)
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """

    result = c_int(0)
    result = dll.PL2_GetSpikeChannelDataBySource(c_int(file_handle), c_int(source_id), c_int(one_based_channel_index_in_source), byref(num_spikes_returned), byref(spike_timestamps), byref(units), byref(values))    
    
    return result

def lib_get_digital_channel_info(file_handle, zero_based_channel_index, pl2_digital_channel_info):
    """
    Retrieve information about a digital event channel
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero-based digital event channel index
        pl2_digital_channel_info - PL2DigitalChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2DigitalChannelInfo passed to function is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetDigitalChannelInfo(c_int(file_handle), c_int(zero_based_channel_index), byref(pl2_digital_channel_info))
    
    return result
    
def lib_get_digital_channel_info_by_name(file_handle, channel_name, pl2_digital_channel_info):
    """
    Retrieve information about a digital event channel
    
    Args:
        file_handle - file handle
        channel_name - digital event channel name
        pl2_digital_channel_info - PL2DigitalChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2DigitalChannelInfo passed to function is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetDigitalChannelInfoByName(c_int(file_handle), channel_name.encode('ascii'), byref(pl2_digital_channel_info))
    
    return result
    
def lib_get_digital_channel_info_by_source(file_handle, source_id, one_based_channel_index_in_source, pl2_digital_channel_info):
    """
    Retrieve information about a digital event channel
    
    Args:
        file_handle - file handle
        source_id - numeric source ID
        one_based_channel_index_in_source - one-based channel index within the source
        pl2_digital_channel_info - PL2DigitalChannelInfo class instance
    
    Returns:
        1 - Success
        0 - Failure
        The instance of PL2DigitalChannelInfo passed to function is filled with channel info
    """
    
    result = c_int(0)
    result = dll.PL2_GetDigitalChannelInfoBySource(c_int(file_handle), c_int(source_id), c_int(one_based_channel_index_in_source), byref(pl2_digital_channel_info))
    
    return result

def lib_get_digital_channel_data(file_handle, zero_based_channel_index, num_events_returned, event_timestamps, event_values):
    """
    Retrieve digital even channel data
    
    Args:
        file_handle - file handle
        zero_based_channel_index - zero-based digital event channel index
        num_events_returned - c_ulonglong class instance
        event_timestamps - c_longlong class instance array the size of PL2DigitalChannelInfo.m_NumberOfEvents
        event_values - c_ushort class instance array the size of PL2DigitalChannelInfo.m_NumberOfEvents
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """        

    result = c_int(0)
    result = dll.PL2_GetDigitalChannelData(c_int(file_handle), c_int(zero_based_channel_index), byref(num_events_returned), byref(event_timestamps), byref(event_values))
    
    return result
    
def lib_get_digital_channel_data_by_name(file_handle, channel_name, num_events_returned, event_timestamps, event_values):
    """
    Retrieve digital even channel data
    
    Args:
        file_handle - file handle
        channel_name - digital event channel name
        num_events_returned - c_ulonglong class instance
        event_timestamps - c_longlong class instance array the size of PL2DigitalChannelInfo.m_NumberOfEvents
        event_values - c_ushort class instance array the size of PL2DigitalChannelInfo.m_NumberOfEvents
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """        

    result = c_int(0)
    result = dll.PL2_GetDigitalChannelDataByName(c_int(file_handle), channel_name.encode('ascii'), byref(num_events_returned), byref(event_timestamps), byref(event_values))
    
    return result        
    
def lib_get_digital_channel_data_by_source(file_handle, source_id, one_based_channel_index_in_source, num_events_returned, event_timestamps, event_values):
    """
    Retrieve digital even channel data
    
    Args:
        file_handle - file handle
        source_id - numeric source ID
        one_based_channel_index_in_source - one-based channel index within the source
        num_events_returned - c_ulonglong class instance
        event_timestamps - c_longlong class instance array the size of PL2DigitalChannelInfo.m_NumberOfEvents
        event_values - c_ushort class instance array the size of PL2DigitalChannelInfo.m_NumberOfEvents
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """        

    result = c_int(0)
    result = dll.PL2_GetDigitalChannelDataBySource(c_int(file_handle), c_int(source_id), c_int(one_based_channel_index_in_source), byref(num_events_returned), byref(event_timestamps), byref(event_values))
    
    return result   

def lib_get_start_stop_channel_info(file_handle, number_of_start_stop_events):
    """
    Retrieve information about start/stop channel
    
    Args:
        file_handle - file handle
        number_of_start_stop_events - c_ulonglong class instance
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """
    
    result = c_int(0)
    result = dll.PL2_GetStartStopChannelInfo(c_int(file_handle), byref(number_of_start_stop_events))
    
    return result
    
def lib_get_start_stop_channel_data(file_handle, num_events_returned, event_timestamps, event_values):
    """
    Retrieve digital channel data
    
    Args:
        file_handle - file handle
        num_events_returned - c_ulonglong class instance
        event_timestamps - c_longlong class instance
        event_values - point to c_ushort class instance
    
    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled with values
    """
    
    result = c_int()
    result = dll.PL2_GetStartStopChannelData(c_int(file_handle), byref(num_events_returned), byref(event_timestamps), byref(event_values))
    
    return result
    
def lib_get_comments_info(file_handle, num_comments, total_number_of_comments_bytes):
    """
    Retreive recording comments information

    Args:
        file_handle - file handle
        num_comments - c_ulonglong class instance
        total_number_of_comments_bytes - c_ulonglong class instance

    Returns:
        1 - Success
        0 - Failure
        The class instances passed to the function are filled in with values
    """
    result = c_int()
    result = dll.PL2_GetCommentsInfo(c_int(file_handle), byref(num_comments), byref(total_number_of_comments_bytes))

    return result

def lib_get_comments(file_handle, timestamps, comment_lengths, comments):
    """
    Retreive recording comments

    Args:
        file_handle - file handle
        timestamps - c_longlong class instance
        comment_lengths - c_ulonglong class instance
        comments - c_char array
    """
    result = c_int()
    result = dll.PL2_GetComments(c_int(file_handle), byref(timestamps), byref(comment_lengths), byref(comments))

def lib_read_first_data_block(file_handle):
    """
    Seek to the start of data in pl2 file and read first data block

    Args:
        file_handle - file handle

    Returns:
        1 - Success
        0 - Failure
    """
    return dll.PL2_ReadFirstDataBlock(c_int(file_handle))
    
def lib_read_next_data_block(file_handle):
    """
    Read next data block. PL2_ReadFirstDataBlock must be called before calling this method.

    Args:
        file_handle - file handle

    Returns:
        1 - Success
        0 - Failure
    """
    return dll.PL2_ReadNextDataBlock(c_int(file_handle))
    
def lib_get_data_block_info(file_handle, block_info):
    """
    Retrieve information about current data block
    
    Args:
        file_handle - file handle
        info - PL2BlockInfo class instance

    Returns:
        1 - Success
        0 - Failure
    """
    return dll.PL2_GetDataBlockInfo(c_int(file_handle), byref(block_info))
    
def lib_get_spike_data_block_timestamps(file_handle):
    """
    Retrieve pointer to timestamps for a current data block (if data block is a spike data block)
    The number of timestamps is PL2BlockInfo.m_NumberOfItems

    Args:
        file_handle - file handle

    Returns:
        non-NULL - Success
        NULL - Failure
    """
    func = dll.PL2_GetSpikeDataBlockTimestamps
    func.restype = POINTER(c_ulonglong)
    return func(c_int(file_handle))


def lib_get_spike_data_block_units(file_handle):
    """
    Retrieve pointer to units for a current data block (if data block is a spike data block).
    The number of unit values is PL2BlockInfo.m_NumberOfItems

    Returns:
        non-NULL - Success
        NULL - Failure
    """
    func = dll.PL2_GetSpikeDataBlockUnits
    func.restype = POINTER(c_ushort)
    return func(c_int(file_handle))
    
def lib_get_spike_data_block_waveforms(file_handle):
    """
    Retrieve pointer to waveforms for a current data block (if data block is a spike data block)
    The number of waveforms is PL2BlockInfo.m_NumberOfItems, 
    each waveform contains PL2SpikeChannelInfo.m_SamplesPerSpike values.
    So the total number of values is (PL2BlockInfo.m_NumberOfItems * PL2SpikeChannelInfo.m_SamplesPerSpike).

    Returns:
        non-NULL - Success
        NULL - Failure
    """
    func = dll.PL2_GetSpikeDataBlockWaveforms
    func.restype = POINTER(c_short)
    return func(c_int(file_handle))
    
def lib_get_analog_data_block_timestamp(file_handle):
    """
    Retrieve timestamp of the first data point for a current data block (if data block is an analog data block)

    Returns:
        Returns timestamp of the first data point in the analog data block
    """
    func = dll.PL2_GetAnalogDataBlockTimestamp
    func.restype = c_longlong
    return func(c_int(file_handle))
    
def lib_get_analog_data_block_values(file_handle):
    """
    Retrieve pointer to values for a current data block (if data block is an analog data block)
    The number of values is PL2BlockInfo.m_NumberOfItems
    """
    func = dll.PL2_GetAnalogDataBlockValues
    func.restype = POINTER(c_short)
    return func(c_int(file_handle))
    
def lib_get_digital_data_block_timestamps(file_handle):
    """
    Retrieve pointer to timestamps for a current data block (if data block is a digital data block)
    The number of timestamps is PL2BlockInfo.m_NumberOfItems.
    """
    func = dll.PL2_GetDigitalDataBlockTimestamps
    func.restype = POINTER(c_longlong)
    return func(c_int(file_handle))

def lib_get_digital_data_block_values(file_handle):
    """
    Retrieve pointer to digital event values for a current data block (if data block is a digital data block)
    The number of values is PL2BlockInfo.m_NumberOfItems
    """
    func = dll.PL2_GetDigitalDataBlockValues
    func.restype = POINTER(c_ushort)
    return func(c_int(file_handle))

def lib_get_start_stop_data_block_timestamps(file_handle):
    """
    Retrieve pointer to timestamps for a current data block (if data block is a start/stop data block)
    The number of timestamps is PL2BlockInfo.m_NumberOfItems
    """
    func = dll.PL2_GetStartStopDataBlockTimestamps
    func.restype = POINTER(c_longlong)
    return func(c_int(file_handle))
    
def lib_get_start_stop_data_block_values(file_handle):
    """
    Retrieve pointer to start/stop event values for a current data block (if data block is a start/stop data block)
    The number of values is PL2BlockInfo.m_NumberOfItems
    The values are the following:
    #define PL2_STOP (0)
    #define PL2_START (1)
    #define PL2_PAUSE (2)
    #define PL2_RESUME (3)
    """
    func = dll.PL2_GetStartStopDataBlockValues
    func.restype = POINTER(c_ushort)
    return func(c_int(file_handle))