# pypl2api.py - High level functions for accessing
# .pl2 files. Mimics Plexon's Matlab PL2 SDK
#
# (c) 2016 Plexon, Inc., Dallas, Texas
# www.plexon.com
#
# This software is provided as-is, without any warranty.
# You are free to modify or share this file, provided that the above
# copyright notice is kept intact.

from . import pypl2lib as pl2
import re
from collections import defaultdict
from argparse import ArgumentError
from ctypes import c_short, c_ushort, c_longlong, c_ulonglong, c_char
import numpy as np
from datetime import datetime
from pypixelmapdump import get_pixel_map_dump

class PL2FileReader(object):

    _PROBE_MAP = {
        "PROBE_MODEL_R1_256_1S": "1S256",
        "PROBE_MODEL_R1_512_1S": "1S512",
        "PROBE_MODEL_R1_512_1S_NHP": "1S512-N",
        "PROBE_MODEL_R1_1024_4S": "4S1024",
        "PROBE_MODEL_R1_1024_8S": "8S1024",
    }


    def __init__(self, filename:str):
        self.filename = filename
        self.handle = pl2.lib_open_file(filename)
        file_info = self.get_file_info()

        # map channel identifiers
        self._map = {}
        source_channel_pattern = re.compile("([A-z]+)([0-9]+)")
        self._source_names = set()
        self._source_ids = set()
        self._source_to_type = {}
        self._source_channel_names = defaultdict(list)
        self._source_type_channel_names = defaultdict(list)

        ## map analog channels
        for zero_based_channel_index in range(file_info["total_number_of_analog_channels"]):
            analog_channel_info = pl2.AnalogChannelInfo()
            _ = pl2.lib_get_analog_channel_info(self.handle, zero_based_channel_index, analog_channel_info)
            channel_name = analog_channel_info.m_Name.decode("utf-8")
            source_id = analog_channel_info.m_Source
            source_name, one_based_channel_index_str = source_channel_pattern.search(channel_name).groups()
            self._source_to_type[source_id] = "analog"
            self._source_to_type[source_name] = "analog"
            one_based_channel_index = int(one_based_channel_index_str)
            self._source_names.add(source_name)
            self._source_ids.add(source_id)
            self._source_channel_names[source_name].append(channel_name)
            self._source_type_channel_names["analog"].append(channel_name)
            tuple_ = (zero_based_channel_index, channel_name, (source_id, one_based_channel_index), (source_name, one_based_channel_index))
            self._map[zero_based_channel_index] = tuple_
            self._map[channel_name] = tuple_
            self._map[(source_id, one_based_channel_index)] = tuple_
            self._map[(source_name, one_based_channel_index)] = tuple_

        ## map spike channels
        for zero_based_channel_index in range(file_info["total_number_of_spike_channels"]):
            spike_channel_info = pl2.SpikeChannelInfo()
            _ = pl2.lib_get_spike_channel_info(self.handle, zero_based_channel_index, spike_channel_info)
            channel_name = spike_channel_info.m_Name.decode("utf-8")
            source_id = spike_channel_info.m_Source
            source_name, one_based_channel_index_str = source_channel_pattern.search(channel_name).groups()
            self._source_to_type[source_id] = "spike"
            self._source_to_type[source_name] = "spike"
            one_based_channel_index = int(one_based_channel_index_str)
            self._source_names.add(source_name)
            self._source_ids.add(source_id)
            self._source_channel_names[source_name].append(channel_name)
            self._source_type_channel_names["spike"].append(channel_name)
            tuple_ = (zero_based_channel_index, channel_name, (source_id, one_based_channel_index), (source_name, one_based_channel_index))
            self._map[zero_based_channel_index] = tuple_
            self._map[channel_name] = tuple_
            self._map[(source_id, one_based_channel_index)] = tuple_
            self._map[(source_name, one_based_channel_index)] = tuple_

        ## map digital event channels
        for zero_based_channel_index in range(file_info["number_of_digital_channels"]):
            digital_channel_info = pl2.DigitalChannelInfo()
            _ = pl2.lib_get_digital_channel_info(self.handle, zero_based_channel_index, digital_channel_info)
            channel_name = digital_channel_info.m_Name.decode("utf-8")
            source_id = digital_channel_info.m_Source
            try:
                source_name, one_based_channel_index_str = source_channel_pattern.search(channel_name).groups()
                self._source_to_type[source_id] = "digital"
                self._source_to_type[source_name] = "digital"
            except:
                self._source_to_type[source_id] = "digital"
                self._source_to_type[channel_name] = "digital"
            one_based_channel_index = int(one_based_channel_index_str)
            self._source_names.add(source_name)
            self._source_ids.add(source_id)
            self._source_channel_names[source_name].append(channel_name)
            self._source_type_channel_names["digital"].append(channel_name)
            tuple_ = (zero_based_channel_index, channel_name, (source_id, one_based_channel_index), (source_name, one_based_channel_index))
            self._map[zero_based_channel_index] = tuple_
            self._map[channel_name] = tuple_
            self._map[(source_id, one_based_channel_index)] = tuple_
            self._map[(source_name, one_based_channel_index)] = tuple_

    def close(self):
        pl2.lib_close_file(self.handle)

    def get_file_info(self):
        file_info = pl2.FileInfo()
        _ = pl2.lib_get_file_info(self.handle, file_info)
        return DotDict({
            "creator_comment": file_info.m_CreatorComment.decode("utf-8"),
            "creator_software_name": file_info.m_CreatorSoftwareName.decode("utf-8"),
            "creator_software_version": file_info.m_CreatorSoftwareVersion.decode("utf-8"),
            "creator_date_time": convert_to_datetime_object(file_info.m_CreatorDateTime),
            "creator_date_time_milliseconds": file_info.m_CreatorDateTimeMilliseconds,
            "timestamp_frequency": file_info.m_TimestampFrequency,
            "number_of_channel_headers": file_info.m_NumberOfChannelHeaders,
            "total_number_of_spike_channels": file_info.m_TotalNumberOfSpikeChannels,
            "number_of_recorded_spike_channels": file_info.m_NumberOfRecordedSpikeChannels,
            "total_number_of_analog_channels": file_info.m_TotalNumberOfAnalogChannels,
            "number_of_recorded_analog_channels": file_info.m_NumberOFRecordedAnalogChannels,
            "number_of_digital_channels": file_info.m_NumberOfDigitalChannels,
            "minimum_trodality": file_info.m_MinimumTrodality,
            "maximum_trodality": file_info.m_MaximumTrodality,
            "number_of_non_omni_plex_sources": file_info.m_NumberOfNonOmniPlexSources,
            "unused": file_info.m_Unused,
            "reprocessor_comment": file_info.m_ReprocessorComment.decode("utf-8"),
            "reprocessor_software_name": file_info.m_ReprocessorSoftwareName.decode("utf-8"),
            "reprocessor_software_version": file_info.m_ReprocessorSoftwareVersion.decode("utf-8"),
            "reprocessor_date_time": convert_to_datetime_object(file_info.m_ReprocessorDateTime),
            "reprocessor_date_time_milliseconds": file_info.m_ReprocessorDateTimeMilliseconds,
            "start_recording_time": file_info.m_StartRecordingTime,
            "duration_of_recording": file_info.m_DurationOfRecording,
        })

    def get_analog_channel_info(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        analog_channel_info = pl2.AnalogChannelInfo()
        _ = pl2.lib_get_analog_channel_info(self.handle, zero_based_channel_index, analog_channel_info)
        return DotDict({
            "name": analog_channel_info.m_Name.decode("utf-8"),
            "source": analog_channel_info.m_Source,
            "channel": analog_channel_info.m_Channel,
            "channel_enabled": analog_channel_info.m_ChannelEnabled,
            "channel_recording_enabled": analog_channel_info.m_ChannelRecordingEnabled,
            "units": analog_channel_info.m_Units.decode("utf-8"),
            "samples_per_second": analog_channel_info.m_SamplesPerSecond,
            "coeff_to_convert_to_units": analog_channel_info.m_CoeffToConvertToUnits,
            "source_trodality": analog_channel_info.m_SourceTrodality,
            "one_based_trode": analog_channel_info.m_OneBasedTrode,
            "one_based_channel_in_trode": analog_channel_info.m_OneBasedChannelInTrode,
            "number_of_values": analog_channel_info.m_NumberOfValues,
            "maximum_number_of_fragments": analog_channel_info.m_MaximumNumberOfFragments,
        })
    
    def get_analog_channel_data(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        analog_channel_info = self.get_analog_channel_info(zero_based_channel_index)
        num_fragments_returned = c_ulonglong(0)
        num_data_points_returned = c_ulonglong(0)
        fragment_timestamps = (c_longlong * analog_channel_info["maximum_number_of_fragments"])()
        fragment_counts = (c_ulonglong * analog_channel_info["maximum_number_of_fragments"])()
        values = (c_short * analog_channel_info["number_of_values"])()
        _ = pl2.lib_get_analog_channel_data(self.handle, zero_based_channel_index, num_fragments_returned, num_data_points_returned, fragment_timestamps, fragment_counts, values)

        # recast returned values and remove extra zeros
        num_fragments_returned = num_fragments_returned.value
        num_data_points_returned = num_data_points_returned.value
        fragment_timestamps = np.asarray(fragment_timestamps)[:num_fragments_returned]
        fragment_counts = np.asarray(fragment_counts)[:num_fragments_returned]
        values = np.asarray(values)

        return DotDict({
            "num_fragments_returned": num_fragments_returned,
            "num_data_points_returned": num_data_points_returned,
            "fragment_timestamps": fragment_timestamps,
            "fragment_counts": fragment_counts,
            "values": values,
        })
    
    def get_analog_channel_data_subset(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None, zero_based_start_value_index:int=None, num_subset_values:int=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        analog_channel_info = self.get_analog_channel_info(zero_based_channel_index)

        if zero_based_start_value_index is None:
            zero_based_start_value_index = 0
        elif zero_based_start_value_index < 0:
            zero_based_start_value_index = 0
        elif zero_based_start_value_index > analog_channel_info.number_of_values - 1:
            zero_based_start_value_index = analog_channel_info.number_of_values - 1
        
        if num_subset_values is None \
            or (zero_based_start_value_index + num_subset_values) > analog_channel_info.number_of_values:
            num_subset_values = analog_channel_info.number_of_values - zero_based_start_value_index

        num_fragments_returned = c_ulonglong(0)
        num_data_points_returned = c_ulonglong(0)
        fragment_timestamps = (c_longlong * analog_channel_info["maximum_number_of_fragments"])()
        fragment_counts = (c_ulonglong * analog_channel_info["maximum_number_of_fragments"])()
        values = (c_short * num_subset_values)()
        _ = pl2.lib_get_analog_channel_data_subset(self.handle, zero_based_channel_index, zero_based_start_value_index, num_subset_values, num_fragments_returned, num_data_points_returned, fragment_timestamps, fragment_counts, values)

        # recast returned values
        num_fragments_returned = num_fragments_returned.value
        num_data_points_returned = num_data_points_returned.value
        fragment_timestamps = np.asarray(fragment_timestamps)[:num_fragments_returned]
        fragment_counts = np.asarray(fragment_counts)[:num_fragments_returned]
        values = np.asarray(values)

        return DotDict({
            "num_fragments_returned": num_fragments_returned,
            "num_data_points_returned": num_data_points_returned,
            "fragment_timestamps": fragment_timestamps,
            "fragment_counts": fragment_counts,
            "values": values,
        })
    
    def get_spike_channel_info(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        spike_channel_info = pl2.SpikeChannelInfo()
        _ = pl2.lib_get_spike_channel_info(self.handle, zero_based_channel_index, spike_channel_info)
        return DotDict({
            "name": spike_channel_info.m_Name.decode("utf-8"),
            "source": spike_channel_info.m_Source,
            "channel": spike_channel_info.m_Channel,
            "channel_enabled": spike_channel_info.m_ChannelEnabled,
            "channel_recording_enabled": spike_channel_info.m_ChannelRecordingEnabled,
            "units": spike_channel_info.m_Units.decode("utf-8"),
            "samples_per_second": spike_channel_info.m_SamplesPerSecond,
            "coeff_to_convert_to_units": spike_channel_info.m_CoeffToConvertToUnits,
            "samples_per_spike": spike_channel_info.m_SamplesPerSpike,
            "threshold": spike_channel_info.m_Threshold,
            "pre_threshold_samples": spike_channel_info.m_PreThresholdSamples,
            "sort_enabled": spike_channel_info.m_SortEnabled,
            "sort_method": spike_channel_info.m_SortMethod,
            "number_of_units": spike_channel_info.m_NumberOfUnits,
            "sort_range_start": spike_channel_info.m_SortRangeStart,
            "sort_range_end": spike_channel_info.m_SortRangeEnd,
            "unit_counts": np.asarray(spike_channel_info.m_UnitCounts)[:(spike_channel_info.m_NumberOfUnits+1)],
            "source_trodality": spike_channel_info.m_SourceTrodality,
            "one_based_trode": spike_channel_info.m_OneBasedTrode,
            "one_based_channel_in_trode": spike_channel_info.m_OneBasedChannelInTrode,
            "number_of_spikes": spike_channel_info.m_NumberOfSpikes,
        })
    
    def get_spike_channel_data(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        spike_channel_info = self.get_spike_channel_info(zero_based_channel_index)
        num_spikes_returned = c_ulonglong(0)
        spike_timestamps = (c_ulonglong * spike_channel_info["number_of_spikes"])()
        units = (c_ushort * spike_channel_info["number_of_spikes"])()
        values = (c_short * spike_channel_info["number_of_spikes"] * spike_channel_info["samples_per_spike"])()
        _ = pl2.lib_get_spike_channel_data(self.handle, zero_based_channel_index, num_spikes_returned, spike_timestamps, units, values)

        # recast returned values
        num_spikes_returned = num_spikes_returned.value
        spike_timestamps = np.asarray(spike_timestamps)
        units = np.asarray(units)
        values = np.asarray(values).reshape((spike_channel_info["number_of_spikes"], spike_channel_info["samples_per_spike"]))

        return DotDict({
            "num_spikes_returned": num_spikes_returned,
            "spike_timestamps": spike_timestamps,
            "units": units,
            "values": values,
        })
    
    def get_digital_channel_info(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        digital_channel_info = pl2.DigitalChannelInfo()
        _ = pl2.lib_get_digital_channel_info(self.handle, zero_based_channel_index, digital_channel_info)
        
        return DotDict({
            "name": digital_channel_info.m_Name.decode("utf-8"),
            "source": digital_channel_info.m_Source,
            "channel": digital_channel_info.m_Channel,
            "channel_enabled": digital_channel_info.m_ChannelEnabled,
            "channel_recording_enabled": digital_channel_info.m_ChannelRecordingEnabled,
            "number_of_events": digital_channel_info.m_NumberOfEvents
        })
    
    def get_digital_channel_data(self, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None):
        channel_identifier = PL2FileReader._validate_channel_identifiers(zero_based_channel_index, channel_name, source_id_and_1_index)
        zero_based_channel_index, _, _, _ = self._map[channel_identifier]
        digital_channel_info = self.get_digital_channel_info(zero_based_channel_index)
        num_events_returned = c_ulonglong(0)
        event_timestamps = (c_longlong * digital_channel_info["number_of_events"])()
        event_values = (c_ushort * digital_channel_info["number_of_events"])()
        _ = pl2.lib_get_digital_channel_data(self.handle, zero_based_channel_index, num_events_returned, event_timestamps, event_values)

        # recast returned values
        num_events_returned = num_events_returned.value
        event_timestamps = np.asarray(event_timestamps)
        event_values = np.asarray(event_values)

        return DotDict({
            "num_events_returned": num_events_returned,
            "event_timestamps": event_timestamps,
            "event_values": event_values,
        })

    def get_start_stop_channel_info(self):
        number_of_start_stop_events = c_ulonglong(0)
        _ = pl2.lib_get_start_stop_channel_info(self.handle, number_of_start_stop_events)
        
        # recast values
        number_of_start_stop_events = number_of_start_stop_events.value

        return DotDict({
            "number_of_start_stop_events": number_of_start_stop_events,
        })

    def get_start_stop_channel_data(self):
        start_stop_channel_info = self.get_start_stop_channel_info()
        number_of_start_stop_events = start_stop_channel_info["number_of_start_stop_events"]
        num_events_returned = c_ulonglong(0)
        event_timestamps = (c_longlong * number_of_start_stop_events)()
        event_values = (c_ushort * number_of_start_stop_events)()
        _ = pl2.lib_get_start_stop_channel_data(self.handle, num_events_returned, event_timestamps, event_values)

        # recast values
        num_events_returned = num_events_returned.value
        event_timestamps = np.asarray(event_timestamps)
        event_values = np.asarray(event_values)

        return DotDict({
            "num_events_returned": num_events_returned,
            "event_timestamps": event_timestamps,
            "event_values": event_values,
        })

    def get_comments_info(self):
        num_comments = c_ulonglong(0)
        total_number_of_comments_bytes = c_ulonglong(0)
        _ = pl2.lib_get_comments_info(self.handle, num_comments, total_number_of_comments_bytes)

        # recast values
        num_comments = num_comments.value
        total_number_of_comments_bytes = total_number_of_comments_bytes.value

        return DotDict({
            "num_comments": num_comments,
            "total_number_of_comments_bytes": total_number_of_comments_bytes
        })

    def get_comments(self):
        comments_info = self.get_comments_info()
        timestamps = (c_longlong * comments_info["num_comments"])()
        comment_lengths = (c_ulonglong * comments_info["num_comments"])()
        comments = (c_char * comments_info["total_number_of_comments_bytes"])()
        _ = pl2.lib_get_comments(self.handle, timestamps, comment_lengths, comments)

        # recast values
        timestamps = np.asarray(timestamps)
        comment_lengths = np.asarray(comment_lengths)
        comments_ = [None] * comments_info["num_comments"]
        offset = 0
        for index in range(comments_info["num_comments"]):
            comment = comments[offset:(offset+comment_lengths[index])]
            offset += comment_lengths[index]
            comments_.append(comment.decode("utf-8"))
        
        return DotDict({
            "timestamps": timestamps,
            "comment_lengths": comment_lengths,
            "comments": comments_
        })

    def read_first_data_block(self):
        # TODO: implement this function
        pass

    def read_next_data_block(self):
        # TODO: implement this function
        pass

    def get_data_block_info(self):
        # TODO: implement this function
        pass

    def get_spike_data_block_timestamps(self):
        # TODO: implement this function
        pass

    def get_spike_data_block_units(self):
        # TODO: implement this function
        pass

    def get_spike_data_block_waveforms(self):
        # TODO: implement this function
        pass

    def get_analog_data_block_timestamp(self):
        # TODO: implement this function
        pass

    def get_analog_data_block_values(self):
        # TODO: implement this function
        pass

    def get_digital_data_block_timestamps(self):
        # TODO: implement this function
        pass

    def get_digital_data_block_values(self):
        # TODO: implement this function
        pass

    def get_start_stop_data_block_timestamps(self):
        # TODO: implement this function
        pass

    def get_start_stop_data_block_values(self):
        # TODO: implement this function
        pass

    # private methods
    @classmethod
    def _validate_channel_identifiers(cls, zero_based_channel_index:int=None, channel_name:str=None, source_id_and_1_index:tuple=None, source_name_and_1_index:tuple=None):
        if zero_based_channel_index is not None and channel_name is None and source_id_and_1_index is None and source_name_and_1_index is None:
            return zero_based_channel_index
        elif zero_based_channel_index is None and channel_name is not None and source_id_and_1_index is None and source_name_and_1_index is None:
            return channel_name
        elif zero_based_channel_index is None and channel_name is None and source_id_and_1_index is not None and source_name_and_1_index is None:
            return source_id_and_1_index
        elif zero_based_channel_index is None and channel_name is None and source_id_and_1_index is None and source_name_and_1_index is not None:
            return source_name_and_1_index
        else:
            raise ArgumentError("Cannot pass more than one parameter.")

    @property
    def source_names(self):
        return self.get_source_names()
    
    @property
    def source_ids(self):
       return self.get_source_ids()
    
    def get_source_names(self):
        return tuple(self._source_names)
    
    def get_source_ids(self):
        return tuple(self._source_ids)

    def get_source_channel_names(self, source_name, include_disabled=False):
        source_type = self._source_to_type[source_name]
        channel_names = []
        for channel_name in self._source_channel_names[source_name]:
            if source_type == "analog":
                channel_info = self.get_analog_channel_info(channel_name=channel_name)
            elif source_type == "spike":
                channel_info = self.get_spike_channel_info(channel_name=channel_name)
            elif source_type == "digital":
                channel_info = self.get_digital_channel_info(channel_name=channel_name)
            else:
                raise("undefined source type")
        
            if include_disabled or (channel_info["channel_enabled"] and channel_info["channel_recording_enabled"]):
                channel_names.append(channel_name)
        
        return channel_names
    
    def get_source_type_channel_names(self, source_type, include_disabled=False):
        channel_names = []
        for channel_name in self._source_type_channel_names[source_type]:
            if source_type == "analog":
                channel_info = self.get_analog_channel_info(channel_name=channel_name)
            elif source_type == "spike":
                channel_info = self.get_spike_channel_info(channel_name=channel_name)
            elif source_type == "digital":
                channel_info = self.get_digital_channel_info(channel_name=channel_name)

            else:
                raise("undefined source type")
            
            if include_disabled or (channel_info["channel_enabled"] and channel_info["channel_recording_enabled"]):
                channel_names.append(channel_name)

        return channel_names
    
    def get_probe_names(self):
        """
        Returns list of probes used to record .pl2 file.

        Args:
            pl2_file_path - path to .pl2 file from which to extract data
        
        Outputs:
            probe_list - list of probe names
        """

        probes, _ = get_pixel_map_dump(self.filename)
        probes = [PL2FileReader._PROBE_MAP[x] for x in [x.split(" = ")[1] for x in probes] if x !='none']

        return probes



    def _get_channel_out_of_tune_durations(self):
        """
        Returns list of channel out of tune durations for specified .pl2 file.

        Args:
            pl2_file_path - path to .pl2 file from which to extract data
        
        Outputs:
            List of channel out of tune durations
        """
        
        file_info = self.get_file_info()
        recording_duration = file_info.duration_of_recording / file_info.timestamp_frequency
        
        for source_name in self.get_source_names():
            if source_name not in ("WB", "SPKC"):
                continue

            source_channel_names = self.get_source_channel_names(source_name, include_disabled=False)
            if source_channel_names:
                break
        
        channel_indexes = [int(source_channel_name.replace(source_name,""))-1 for source_channel_name in source_channel_names]
        channel_out_of_tune_durations = {channel_index: 0.0 for channel_index in channel_indexes}
        
        # get pixel map dump
        _, timestamp_info = get_pixel_map_dump(self.filename)
        n_timestamps = len(timestamp_info)

        for index, (timestamp, channels) in enumerate(timestamp_info):
            # determine the "next" timestamp and hence the duration of the current block
            if index==n_timestamps - 1:
                next_timestamp = recording_duration
            else:
                next_timestamp = timestamp_info[index+1][0]
            
            block_duration = next_timestamp - timestamp

            # increment the out-of-tune time for the channels included in the current block
            for channel in channels:
                channel_out_of_tune_durations[channel] += block_duration

        return channel_out_of_tune_durations

    def get_bad_channels(self, limit:float, mode:str="absolute"):
        """
        Returns list of bad channels in .pl2 file.

        Args:
            pl2_file_path - path to .pl2 file from which to extract data
            limit - threshold value for determining bad channels
            mode - "absolute" or "relative" (defaults to "absolute")
                - for "absolute", limit specifies the number of seconds a channel 
                can be out of tune before it is deemed "bad."
                - for "relative", limit specifies the fraction (NOT PERCENTAGE) 
                of time a channel can be out of tune before it is deemed "bad" 
                (must be between 0.0 and 1.0).

        Outputs:
            bad_channels - list of bad channels
        """

        if mode not in ("absolute", "relative"):
            raise("Invalid mode specified.")

        file_info = self.get_file_info()
        recording_duration = file_info.duration_of_recording / file_info.timestamp_frequency
        oot_durations_dict = self._get_channel_out_of_tune_durations()
        
        bad_channels = []
        for channel, oot_dur in oot_durations_dict.items():
            if mode=="absolute":
                if oot_dur >= limit:
                    bad_channels.append(channel)

            elif mode=="relative":
                oot_fractional = oot_dur / recording_duration
                if (oot_fractional) >= limit:
                    bad_channels.append(channel)

        return bad_channels

class DotDict(object):
    def __init__(self, dictionary):
        # Store the dictionary as an internal attribute
        self.__dict__["_data"] = dictionary

    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(f'Attribute "{key}" not found')
    
    def __setattr__(self, key, value):
        try:
            self._data[key] = value
        except KeyError:
            raise AttributeError(f'Attribute "{key}" not found')
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __delattr__(self, key):
        try:
            del self._data[key]
        except KeyError:
            raise AttributeError(f'Attribute "{key}" not found')
    
    def __repr__(self):
        return repr(self._data)
    
    def to_dict(self):
        return dict(self._data)

def convert_to_datetime_object(tm_object):
    tm_sec = tm_object.tm_sec
    tm_min = tm_object.tm_min
    tm_hour = tm_object.tm_hour
    tm_mday = tm_object.tm_mday
    tm_mon = tm_object.tm_mon + 1
    tm_year = tm_object.tm_year + 1900
    # tm_wday = tm_object.tm_wday
    # tm_yday = tm_object.tm_yday
    # tm_isdst = tm_object.tm_isdst

    if tm_year > 1900:
        return datetime(year=tm_year, month=tm_mon, day=tm_mday, hour=tm_hour, minute=tm_min, second=tm_sec)
    else:
        return datetime(year=1900, month=1, day=1)