"""
Helper functions for an automatic import, conversion & aggregation of (many) CSV-files.
"""

import os
import re
import csv
import h5py
import json
import time
import pickle as pk
import shutil

from zynamon.zeit import TimeSeries, convert_time, istimeseries, TS_ISO_FORMAT, TS_SAVE_FORMATS
from zdev.core import anyfile, fileparts
from zdev.parallel import duration_str
from zdev.validio import file_clear_strings, valid_encoding, valid_str_name


# EXPORTED DATA
TS_IMPORT_FORMATS = ('csv','txt')
TS_KEYWORDS_NAME = ('name', 'description', 'identifier', 'info', 'label', 'series')
TS_KEYWORDS_TIME = ('time', 'stamp')
TS_KEYWORDS_VALUE = ('data', 'sample', 'val', 'value', 'meas', 'measured', 'measurement')
TS_NAME_REPLACE = {
    '>=': 'gte',
    '<=': 'lte',
    '>': 'gt',
    '<': 'lt',
    '°': 'deg'
    }

# INTERNAL PARAMETERS & DEFAULTS
_BACKUP_ORIG_FILES = True # switch [bool] to store original files in a "_BKP" sub-folder
_HEARTBEAT = 100000 # number of lines after which to display "heartbeat" (if any)
_VERBOSITY = 1 # verbosity level of "low-level" functions (0=off | 1=summary | 2=per-timeseries)

# regex patterns
_RX_AUTOMAP_NAME = re.compile('|'.join(TS_KEYWORDS_NAME))
_RX_AUTOMAP_TIME = re.compile('|'.join(TS_KEYWORDS_TIME))
_RX_AUTOMAP_VALUE = re.compile('|'.join(TS_KEYWORDS_VALUE))


def import_csv(csv_file, col_time=None, col_data=None, col_meta=[],
               headers=None, encoding=None, enforce=None, 
               ensure_causal=True, keep_meta=True, save_file=True, save_fmt='json',
               max_ts=int(99), max_lines=int(1e9), verbosity=_VERBOSITY):
    """ Import samples of one (or more) time-series from a CSV-file w/ a common time reference.

    The files are assumed to contain samples from one (or more) time-series in a "line-by-line"
    manner, i.e. each line yields ONE NEW SAMPLE of all series acc. to the SAME TIME REFERENCE.
    Multiple measurements up to 'max_ts' may be represented in the file and will be imported 
    altogether. If desired, any other columns are considered as "meta" information and may be 
    kept as well. Since these are assumed to have repeating contents, a compression of the 
    resulting objects is likely, as such tags are extracted acc. to the first line of occurrence 
    and will be stored only once (per time-series).

    For all of the columns, information on the contents of the CSV-file may also be detected
    *automagically* based on a keyword approach. The operational precedence is as follows:
        (i) map 'time' reference (as specified / auto-detect otherwise)
        (ii) map 'data' and 'meta' columns (as specified)
        (iii) map remaining columns (acc. to  auto-detection)

    Notes on the "auto-detection" feature:
    (1) 'time' will only consider the first matching column!
    (2) 'meta=[]' effectively implies that ALL COLUMNS are interpreted as 'data'! (ease of use)
    (3) auto-detection rules for 'data' may also catch certain meta information (careful!)

    Args:
        csv_file (str): Absolute filename to "CSV-like" file (w/ or w/o headers).
        col_time (str, optional): Header of column containing the time reference. Defaults to
            'None' (i.e. auto-detect).
        col_data (list of str, optional): Header of one or more columns containing data.
            Defaults to 'None' (i.e. auto-detect).
        col_meta (list of str, optional): One or more columns containing meta data. Defaults to
            empty list '[]' (i.e. meta information disabled).        
            Note: Use 'xtools' as SPECIAL CASE to indicate that first two lines in CSV-files
            carry additional meta information and have to be treated separately!
        headers (list, optional): Headers of all columns if not in the file. Defaults to 'None'.
        encoding (str, optional): Encoding of CSV-file. Defaults to 'None' (i.e. auto mode).
        enforce (list, optional): Enforce conversions while extracting data. If the types in the
            CSV-source are known, this may be particularly required for 'datetime' formats. If
            multiple time-series are contained, each one requires an "enforce" item of its own.
            Defaults to 'None' (i.e. plain data is copied).
        keep_meta (bool, optional: Switch for storing the meta information in the 'TimeSeries',
            otherwise it will be discarded. Defaults to 'None'.
        ensure_causal (bool, optional): Switch for ensuring that all samples of a time-series
            are sorted in ascending time and computing some statistics. Defaults to 'True'.
        save_file (bool, optional): Switch to save all imported 'TimeSeries' to file. Otherwise,
            conversion results will only be available in memory. Defaults to 'True'.       
        save_fmt (str, optional): File format in which converted data is saved (options
            'json' and 'pk'). Defaults to 'json'.
        max_ts (int, optional): Maximum number of time-series to consider. Defaults to '99'.
        max_lines (int, optional): Maximum number of lines to scan for. Defaults to '1e9'. 
        verbosity (int, optional): Verbosity level of function. Defaults to '0' (= silent).
            level 1 -> shows only a short summary (at the end)
            level 2 -> shows a detailed summary (at the end)            
            level 3 -> generates a "heartbeat"

    Returns:
        objects (list): List of all 'TimeSeries' objects imported from the CSV-file.

    Example:
        Timestamp, Humidity, Pressure, Temperature,
        2020-04-01 00:01:54, 10.022, 992.2, 37.1875, 
        2020-04-01 00:01:55, 10.018, 992.3, 37.2123,
        ...
        2020-04-01 00:14:12, 10.172, 994.8, 37.0625
        --> First column is common reference for 3 different time-series!
    """

    # configure file
    fpath, fname, _ = fileparts(csv_file)
    file_clear_strings(csv_file, '"', verbose=False) # Note: This will remove unnessary quotes
    if (encoding is None):
        enc = valid_encoding(csv_file)
    else:
        enc = encoding   

    # check consistency
    if (col_time is not None):
        if (type(col_time) != str):
            print(f"(warning: unknown time column format '{col_time}' specified, setting to auto)")
            col_time = None
    if ((col_data is None) and (col_meta is None)):
        print("(warning: meta data cannot be differentiated, may be mapped to time-series?)")
    if (save_fmt not in TS_SAVE_FORMATS):
        raise NotImplementedError(f"Unknown save format '{save_fmt}' specified")

    # read CSV-file in proper encoding
    with open(csv_file, mode='r', encoding=enc) as tf:

        # init format parsing (Note: First line will always be checked)
        meta_info = {}
        meta_is_filled = True
        first_line = tf.readline()
        tf_format = csv.Sniffer().sniff( first_line )

        # parse format & columns configuration
        if (col_meta == 'xtools'): # SPECIAL case
            # Note: Special case for "CMS X-Tools" file exports, as these carry additional
            # "meta information" already in their first two lines. Hence, the column format will
            # be changing afterwards, i.e. starting with the third line.

            # get meta info from first two lines
            second_line = tf.readline()
            if (keep_meta):
                k_meta = first_line.split(tf_format.delimiter)
                v_meta = second_line.split(tf_format.delimiter)
                for n, key in enumerate(k_meta):
                    k_meta[n] = key.strip() # clean whitespaces (incl. newline)
                    meta_info.update({k_meta[n]: v_meta[n].strip()})

            # get regular time reference & data column(s) from third line
            third_line = tf.readline()
            fields = third_line.split( tf_format.delimiter )
            for n, item in enumerate(fields):
                fields[n] = item.strip() # clean whitespaces (incl. newline)
            col_time = fields[0] # 1st column == time reference (directly assigned)
            k_data = []
            for n, item in enumerate(fields[1:], start=1):
                k_data.append( fields[n] ) # later columns == values (one or more)

        else: # NORMAL case
            # Note: For the "normal" case, the column headers are parsed and the mapping as
            # specified is done OR an auto-detection (based on typical keywords) is carried out.

            if (headers is None):
                fields = first_line.split( tf_format.delimiter )
                for n, item in enumerate(fields):
                    fields[n] = item.strip() # clean whitespaces (incl. newline)
            else:
                fields = headers
                tf.seek(0)

            # (1) get time reference (as specified, or via auto-detection)
            col_time = _assign_columns(col_time, fields, _RX_AUTOMAP_TIME)[0]
      
            # (2) get data & meta columns (as specified) 
            k_data = _assign_columns(col_data, fields) 
            k_meta = _assign_columns(col_meta, fields)  

            # (3) auto-detection: map all remaining columns based on keywords (if not specified)
            for item in fields:
                # -> data was specified, map any other to meta
                if ((col_data is not None) and (col_meta is None)):
                    if (item not in (col_time, k_data)):
                        k_meta.append(item)
                # -> meta was specified, map any other to data
                elif ((col_data is None) and (col_meta is not None)):
                    if (item not in (col_time, k_meta)):
                        k_data.append(item)
                # -> neither data nor meta were specified, map matching to data, rest to meta
                elif ((col_data is None) and (col_meta is None)):                    
                    if (_RX_AUTOMAP_VALUE.search(item.lower())):
                        k_data.append(item)
                    elif (item not in (col_time, k_data)):
                        k_meta.append(item)

            # init extraction of meta information (if desired)
            if (keep_meta):
                for item in k_meta:
                    meta_info.update({item: ''})
                meta_is_filled = False
            # Note: Flag is reset here to enforce filling for 1st line!

        # check limitations
        if (len(k_data) > max_ts):
            print(f"(warning: found max # of time-series (={max_ts}) -> ignoring rest)")
            k_data[max_ts:] = []

        # init time-series collection
        buffers = []
        objects = []
        for n, item in enumerate(k_data):
            if (col_meta == 'xtools'):
                ts_name = meta_info['Data Name']+'_'+item
            else:
                ts_name = fname+'_'+item
            buffers.append([])
            objects.append( TimeSeries(ts_name, tags=meta_info) )

        # line-wise processing
        stream = csv.DictReader(tf, fieldnames=fields, dialect=tf_format)
        m = 0
        while (True):
            try: # Note: Safe approach in case NULL is found in files!
                m += 1
                line = stream.__next__()
                if (m == max_lines):
                    print(f"(warning: reached max # of lines (={int(max_lines)}) -> skipping)")
                    break
                elif (verbosity and (not m%_HEARTBEAT)):
                    print(f"(read {m} lines)")

                # extract meta information (only for first line!)
                if (not meta_is_filled):
                    for n, item in enumerate(k_data):
                        for key in objects[n].meta.keys():
                            objects[n].tags_register({key: line[key]}, overwrite=True)           
                    meta_is_filled = True

                # copy time-series data
                for n, item in enumerate(k_data):
                    if (enforce is None): # use plain data...
                        sample = [line[col_time], line[item]]
                    else: # ... or enforce type conversion
                        # time
                        if (enforce[0] is not None):
                            the_time = convert_time(line[col_time], target=enforce[0])
                        else:
                            the_time = line[col_time]
                        # data
                        if (len(enforce) > 1+n): # 1st entry == always time!
                            if (enforce[1+n] is float):
                                try:
                                    the_data = float(line[item])
                                except:
                                    the_data = 0.0
                            elif (enforce[1+n] is int):
                                try:
                                    the_data = int(line[item])
                                except:
                                    the_data = 0
                            elif (enforce[1+n] is str):
                                try:
                                    the_data = str(line[item])
                                except:
                                    the_data = ''
                        else:
                            the_data = line[item]
                        sample = [the_time, the_data]
                    buffers[n].append(sample)

            except: # reached EOF or NUll
                break

    # add batch of samples to time-series & ensure causality (if desired)
    for n, ts in enumerate(objects):
        ts.samples_add(buffers[n], analyse=(not ensure_causal))
        if (ensure_causal):
            ts.time_causalise()
            ts.time_analyse()

    # save time-series to file(s)
    if (save_file):
        the_file = os.path.abspath(os.path.join(fpath,fname+'.'+save_fmt))
        if (os.path.isfile(the_file)):
            os.remove(the_file)
        for ts in objects:
            ts.export_to_file(the_file, combine=True, fmt=save_fmt)

    # display summary
    if (verbosity):
        print(f"(registered {len(objects)} individual time-series)")
        if (verbosity >= 2):
            for ts in objects:
                print(f"( - '{ts.name}' w/ {len(ts)} samples )")
        if (save_file):
            print(f"(stored all data in '{fname}.{save_fmt}')")

    return objects


def import_csv_async(csv_file, col_name=None, col_time=None, col_data=None,
                     headers=None, encoding=None, enforce=None, 
                     keep_meta=True, ensure_causal=True, save_file=True, save_fmt='json',
                     max_ts=int(1e5), max_lines=int(1e9), verbosity=_VERBOSITY):
    """ Imports a "mixed sequence" of time-series data samples from a CSV-file.

    The files are assumed to contain samples from many different time-series that are generated
    in an asynchronous manner such that NO COMMON TIME REFERENCE is available. In particular,
    EACH LINE CONTAINS ONE NEW SAMPLE OF A (NEW or EXISTING) TIME-SERIES, THAT IS RELATED TO A
    SPECIFIC TIME INSTANT / EVENT. For efficient processing, all samples of the same series are
    collected first in a buffered manner before finally adding them in a single batch.

    In order to determine the structure of the file, the first line is expected to contain the
    required column headers. Otherwise, 'headers' needs to provide the respective fields and the
    1st line in the file is then assumed to start w/ data.

    Each time-series is defined by information from the following columns:
        (1) col_name = unique name of time-series (may also be created from several parts)
        (2) col_time = time information of time-series
        (3) col_data = sample values of time-series
    Any other columns not covered by the above will be considered as "meta" information, but may
    be kept as well. Since these information are assumed to have repeating contents, the
    resulting 'TimeSeries' data structures will exhibit a significant compression in size, since
    these tags are extracted acc. to the first line of occurrence and will be stored only once
    (per time-series).

    Args:
        csv_file (str): Absolute filename to "CSV-like" file (w/ headers in first line).

        col_name (str or list): Column referring to the time-series names. If several columns
            are required to create unique identifiers, this is expected to be a list (of str)
            and the name parts will be concatenated by '_'.

        col_time (str): Column containing times of time-series (e.g. 'meas_time').
            Defaults to 'None' (i.e. auto-detect).
        col_data (str): Column containing the samples values of time-series (e.g. 'value').
            Defaults to 'None' (i.e. auto-detect).
        headers (list, optional): Headers of all columns if not in the file. Defaults to 'None'.
        encoding (str, optional): Encoding of CSV-file. Defaults to 'None' (i.e. auto mode).
        enforce (list, optional): 2-tuple specifying conversions that should be enforced on
            'time' and 'data' entries. Defaults to 'None' (i.e. plain data is copied).
        keep_meta (bool, optional): Switch for storing all "static" meta information only once.
            Defaults to 'True'.
        ensure_causal (bool, optional): Switch for ensuring that all samples of a time-series
            are sorted in ascending time and computing some statistics. Defaults to 'True'.
        save_file (bool, optional): Switch to save all imported 'TimeSeries' to file. Otherwise,
            conversion results will only be available in memory. Defaults to 'True'.        
        save_fmt (str, optional): File format in which converted data is saved w/ options
            'TS_SAVE_FORMATS'. Defaults to 'json'.
        max_ts (int, optional): Maximum number of time-series to consider. Defaults to '1e5'.
        max_lines (int, optional): Maximum number of lines to scan for. Defaults to '1e9'.
        verbosity (int, optional): Verbosity level of function. Defaults to '0' (= silent).
            Level 1 -> shows only a short summary (at the end)
            Level 2 -> shows a detailed summary (at the end)
            Level 3 -> generates a "heartbeat"
            Level 4 -> generates infos on each NEW time-series that is found
            Note: Level 4 may produce *many* lines, depending on the contents of the file!

    Returns:
        objects (list): List of all 'TimeSeries' ojects imported from the CSV-file.

    Example:
        SIGNAL_NAME,      SIGNAL_DESCRIPTION,   SIG_CLASS, UNIT, VALUE, INSERT_TIME
        =10QA12/CB_STAT,  Stat 1 CB open/close, STAT,      NULL, 0,     2020-04-16 20:59:42.5
        =My_own_signal,   Anything else,        MES,       NULL, 14.75, 2020-04-16 21:02:19.2
        ...
        =21UF44/PAC_EST,  Not enough AC power!, WARN,      NULL, 1,     2020-05-03 08:40:17.3
        ...
        =My_own_signal,   Anything else,        MES,       NULL, 12.33, 2020-06-07 09:48:08.6
    """

    # configure file & check consistency
    fpath, fname, _ = fileparts(csv_file)
    file_clear_strings(csv_file, '"', verbose=False) # Note: This will remove unnessary quotes
    if (encoding is None):
        enc = valid_encoding(csv_file)
    else:
        enc = encoding    
    if (save_fmt not in TS_SAVE_FORMATS):
        raise NotImplementedError(f"Unknown save format '{save_fmt}' specified")

    # read CSV-file in proper encoding
    with open(csv_file, mode='r', encoding=enc) as tf:

        # parse format & configuration
        first_line = tf.readline()
        tf_format = csv.Sniffer().sniff(first_line)
        if (headers is None):
            fields = first_line.split(tf_format.delimiter)
            for n, item in enumerate(fields):
                fields[n] = item.strip() # clean whitespaces (incl. newline)
        else:
            fields = headers
            tf.seek(0)

        # check consistency (proper columns available?)
        col_name = _assign_columns(col_name, fields, _RX_AUTOMAP_NAME)
               
        # get time & data columns (as specified or via auto-detection) 
        col_time = _assign_columns(col_time, fields, _RX_AUTOMAP_TIME)[0]
        col_data = _assign_columns(col_data, fields, _RX_AUTOMAP_VALUE)[0]   
       
        # get meta information (if desired)
        k_meta = []
        if (keep_meta):
            for item in fields:
                if (item not in (col_name, col_data, col_time)):
                    k_meta.append(item)

        # init time-series collection
        buffers = {}
        objects = []        

        # copy data of all time-series from file...
        stream = csv.DictReader(tf, fieldnames=fields, dialect=tf_format)
        m = 0
        while (True):
            try:
                m += 1
                line = stream.__next__() # Note: Safe approach in case NULL is found in files!
                if (m >= max_lines):
                    print(f"(warning: reached max # of lines (={int(max_lines)}) -> skipping)")
                    break
                elif (verbosity and (not m%_HEARTBEAT)):
                    print(f"(read {m} lines)")

                # get/create time-series name & ensure "safe" usage (i.e. remove special chars)
                if (len(col_name) >= 2):
                    tmp = ''
                    for name_part in col_name:
                        tmp += line[name_part]+'_'
                    ts_name = tmp[:-1]
                else:
                    ts_name = line[col_name[0]]
                ts_name = valid_str_name(ts_name, repl_str='_', repl_dict=TS_NAME_REPLACE)

                # create new time-series & buffer?
                if (ts_name not in buffers.keys()):
                    if (len(objects) >= max_ts):
                        print(f"(warning: found max # of time-series (={int(max_ts)}) -> ignoring rest)")
                        continue
                    elif (verbosity >= 3):
                        print(f"(line #{m}: found time-series '{ts_name}')")
                    ts = TimeSeries(ts_name)
                    if (keep_meta):
                        meta_info = {}
                        for item in k_meta:
                            meta_info.update({item: line[item]})
                        ts.tags_register(meta_info)
                    buffers[ts_name] = []
                    objects.append(ts)

                # add sample to proper buffer
                if (enforce is None): # use plain data...
                    sample = [line[col_time], line[col_data]]
                else: # ... or enforce type conversion
                    # time
                    if (enforce[0] is not None):
                        the_time = convert_time(line[col_time], enforce[0])
                    else:
                        the_time = line[col_time]
                    # data
                    if (enforce[1] is float):
                        try:
                            the_data = float(line[col_data])
                        except:
                            the_data = 0.0
                    elif (enforce[1] is int):
                        try:
                            the_data = int(line[col_data])
                        except:
                            the_data = 0
                    elif (enforce[1] is str):
                        try:
                            the_data = str(line[col_data])
                        except:
                            the_data = ''
                    else:
                        the_data = line[col_data]
                    sample = [the_time, the_data]
                buffers[ts_name].append(sample)

            except: # reached EOF or NUll
                break

    # add batch of samples to time-series & ensure causality (if desired)
    for ts in objects:
        ts.samples_add(buffers[ts.name], analyse=(not ensure_causal))
        if (ensure_causal):
            ts.time_causalise()
            ts.time_analyse()

    # save imported time-series to file?
    if (save_file):
        the_file = os.path.join(fpath,fname+'.'+save_fmt)
        if (os.path.isfile(the_file)):
            os.remove(the_file)
        for ts in objects:
            ts.export_to_file(the_file, combine=True, fmt=save_fmt)

    # display summary
    if (verbosity):
        print(f"(registered {len(objects)} individual time-series)")
        if (verbosity >= 2):
            for ts in objects:
                print(f"( - '{ts.name}' w/ {len(ts)} samples )")
        if (save_file):
            print(f"(stored all data in '{fname}.{save_fmt}')")

    return objects


def read_ts_file(the_file, target=dict, read_limit=None, verbose=False):
    """ Reads 'TimeSeries' objects collected in 'the_file' and return as desired 'target'.

    This routine works for all supported files acc. to 'zynamon.zeit.TS_SAVE_FORMATS' that have
    been saved e.g. during previous imports from CSV-files. Contained objects may either be 
    placed in a list or a dictionary structure. Since 'TimeSeries' objects cannot be used 
    directly (except for Python's "pickle", PK), an intermediate step is to convert their 
    information to a 'dict' item and then recreate all contained 'TimeSeries' objects in the 
    given 'target' structure by this function.

    Args:
        the_file (str): Name of storage file to read from in either format of 
            'zynamon.zeit.TS_SAVE_FORMATS'.
        target (type, optional): Target structure if several objects have been combined in one
            single file, options are 'list|dict'. Defaults to 'dict'.
        read_limit (int, optional): Maximum number of objects to read from file. Defaults to
            'None' (i.e. extract all).
        verbose (bool, optional): Switch to show infos on loaded contents. Defaults to 'False'.

    Returns:
        collection (list or dict): Collection of all 'TimeSeries' objects found in the file
            w/ type acc. to 'target'. These are created from the all entries in the JSON-file.
    """
    from zynamon.zeit import _ts_from_dict, _ts_from_h5grp

    # determine format of storage file & init
    fext = the_file.split('.')[-1]
    if (target is dict):
        collection = {}
    elif (target is list):
        collection = []
    else:
        raise ValueError(f"Unknown target structure '{target}' specified")

    if (read_limit is not None):
        limit = read_limit
    else:
        limit = int(1e9)

    # load or re-create 'TimeSeries' objects & arrange collection (dep. on source/target type)
    t0 = time.process_time()
    if (fext == 'pk'):
        with open(the_file, mode='rb') as pf:
            objects = pk.load(pf)

        # single 'TimeSeries' object...
        if (istimeseries(objects)):
            if (target is dict):
                collection = { objects.name: objects }
            else:
                collection.append(objects)

        # ...or actual collection?
        elif (type(objects) is dict):
            if (target is dict):
                for n, name in enumerate(objects.keys(), start=1):
                    collection[name] = objects[name]
                    if (n == limit):
                        break
            else:
                for n, name in enumerate(objects.keys(), start=1):
                    collection.append(objects[name])
                    if (n == limit):
                        break
        elif (type(objects) is list):
            if (target is dict):
                for n, ts_item in enumerate(objects, start=1):
                    collection[ts_item.name] = ts_item
                    if (n == limit):
                        break
            else:
                collection = objects[:limit]

        else:
            print(f"Error: Unknown contents in '{the_file}'! (aborting)")

    elif (fext == 'json'):
        with open(the_file, mode='r') as jf:
            objects = json.load(jf)

        if (type(objects) is dict):
            # pre-processing (only required for single "export_json()" files)...
            tmp = list(objects.keys())
            single_item = all((item in tmp) for item in ('name','arr_t','arr_x','meta','time'))
            if (single_item):
                objects = {objects['name']: objects}
            # assign dict items to target structure
            for n, name in enumerate(objects.keys(), start=1):
                ts = _ts_from_dict(objects[name])
                if (target is dict):
                    collection[name] = ts
                else:
                    collection.append(ts)
                if (n == limit):
                    break

        elif (type(objects) is list):
            for n, ts_item in enumerate(objects, start=1):
                ts = _ts_from_dict(ts_item)
                if (target is dict):
                    collection[ts.name] = ts
                else:
                    collection.append(ts)
                if (n == limit):
                    break

        else:
            print(f"Error: Unknown contents in '{the_file}'! (aborting)")

    elif (fext in ('h5','hdf5')):
        with h5py.File(the_file, mode='r') as hf:
            for n, name in enumerate(hf.keys(), start=1):
                ts = _ts_from_h5grp(hf[name])                
                if (target is dict):
                    collection[name] = ts
                else:
                    collection.append(ts)
                if (n == limit):
                    break
    else:
        raise NotImplementedError(f"Unknown format '{fext}' found")
    t1 = time.process_time()

    # display basic infos
    if (verbose):
        coll_size = len(collection.keys()) if (target is dict) else len(collection)    
        print(f"(loaded {coll_size} items in {duration_str(t1-t0)})")

    return collection


def write_ts_file(collection, the_file, save_fmt='h5', target=dict, enforce=None, 
                  overwrite=False, verbose=False):
    """ Exports all 'TimeSeries' objects in 'collection' to 'the_file'.

    Args:
        collection (list or dict): All 'TimeSeries' objects to be written to the file.
        the_file (str): Filename to write to (proper extension will be enforced).
        save_fmt (str or list, optional): Output format(s) to write w/ available options as in
            'zynamon.zeit.TS_SAVE_FORMATS'. Defaults to 'h5'.
        target (type, optional): File structure to be used within the storage (if applicable) 
            w/ options 'list|dict'. Defaults to 'dict'.
            Note: This setting e.g. has *no effect* on HDF5-files! (= always "dict-like")
        enforce (list, optional): When transcoding data, this might be used as a 2-tuple,
            specifying time & value target formats in the new save format. Defaults to 'None'.
        overwrite (bool, optional): Switch to overwrite existing files. Defaults to 'False'.
        verbose (bool, optional): Switch to show infos on written contents. Defaults to 'False'.

    Returns:
        --
    """
    from zynamon.zeit import _ts_to_dict, _ts_to_h5grp    

    # check consistency
    fpath, fname, _ = fileparts(the_file)
    save_file = os.path.join(fpath, fname)
    if (type(save_fmt) is str):
        save_fmt = [save_fmt]
    for fmt in save_fmt:
        if (fmt not in TS_SAVE_FORMATS):
            raise NotImplementedError(f"Unknown save format '{fmt}' specified")
        elif (os.path.isfile(save_file+'.'+fmt)):
            if (overwrite):
                print(f"Warning: Overwriting time-series collection '{save_file+'.'+fmt}")
            else:
                raise FileExistsError(f"Time-series collection '{save_file+'.'+fmt}' exists")           

    # init outputs
    if (target is dict):
        objects = {}
    elif (target is list):
        objects = []
    else:
        raise NotImplementedError(f"Unknown target file structure '{target}' specified")
    
    t0 = time.process_time()  
    
    # modify collection (if enforce) & create output collection (acc. to target)
    for ts in (collection.values() if (type(collection) is dict) else collection):
        if (enforce is not None):
            ts.time_convert(enforce[0])
            if (enforce[1] is not None):
                eval(f"ts = {enforce[1]}(ts)") #todo: use 'try' ... 'except' if conversion fails?!?           
        if (target is dict):
            objects[ts.name] = ts
        else: 
            objects.append(ts)
    
    # save as Python 'pickle' (special case = can use objects directly)
    if ('pk' in save_fmt):
        with open(save_file+'.pk', mode='wb') as pf:
            pk.dump(objects, pf)
        save_fmt.remove('pk')
        
    # save in any other file format (convert to 'dict-like' items)
    if (save_fmt):

        if (target is dict):
            object_items = {}
            for name, ts in objects.items():
                object_items[name] = _ts_to_dict(ts)
        else:
            object_items = []
            for ts in objects:
                object_items.append(_ts_to_dict(ts))
        
        for fmt in save_fmt:

            if (fmt.lower() == 'json'):
                with open(save_file+'.'+fmt, mode='w') as jf:
                    json.dump(object_items, jf, indent=4, sort_keys=(target is dict))

            if (fmt.lower() in ('h5','hdf5')):
                with h5py.File(save_file+'.'+fmt, mode='w') as hf:
                    for ts in (object_items.values() if (target is dict) else object_items):
                        _ts_to_h5grp(hf, ts)

            # 
            # todo: extend list of formats?
            #  

    t1 = time.process_time()

    # display basic infos
    if (verbose):
        coll_size = len(collection.keys()) if (type(collection) is dict) else len(collection)        
        print(f"(saved {coll_size} items in {duration_str(t1-t0)})")

    return


def pack_ts_file(the_file, agg_params=[(5*60, 'avg')], save_fmt='h5', overwrite=False, verbosity=2):
    """ Compresses all time-series of collection stored in 'the_file'.

    Args:
        the_file (str): Location of input file w/ collection of (uncompressed) time-series.
        agg_params (list, optional): List of 2-tuples as (agg_time, agg_mode) acc. to
            'TimeSeries.samples_pack()'. Note that applying several compression settings at once
            avoids re-loading the storage file! Defaults to [(300, 'avg')].
        save_fmt (str, optional): Output format w/ options from 'TS_SAVE_FORMATS'.
            Defaults to HDF5 ('h5').
        overwrite (bool, optional): Switch to allow overwrite of existing files, i.e.
            compression process will be repeated. Defaults to 'False'.        
        verbosity (int, optional): Level of displayed information. Defaults to '1'.
            level 0 = OFF (not recommended!)
            level 1 = per file information
            level 2 = per compression setting information
            level 3 = per time-series information

    Returns:
        coll_compressed: Collection in compressed format (acc. to last parameters, if several).
    """

    # load collection & perform desired aggregation (in-place)
    if (verbosity): print(f"Loading '{os.path.basename(the_file)}'")
    coll = read_ts_file(the_file, target=dict)

    # init output filename
    fpath, fname, _ = fileparts(the_file)

    # apply all different compression settings
    for (agg_time, agg_mode) in agg_params:
        fname_out = fname+'_'+duration_str(agg_time, sep='')+'_'+f'{agg_mode}'

        # check for existence (Note: Necessary to avoid work if overwrite is *not* desired!)
        file_out = os.path.join(fpath, fname_out+'.'+save_fmt)
        if (not overwrite):
            existing_file = anyfile(fpath, fname_out, TS_SAVE_FORMATS)
            if (not existing_file):
                print(f"Compressed file '{fname_out}' already exists! (enforce 'overwrite')")
                return None

        if (verbosity >= 2): print(f"+ Compressing w/ {agg_time} sec in mode '{agg_mode}'")
        coll_compressed = {}
        for n, ts_name in enumerate(coll):
            if (verbosity >= 3): print(f"  - Aggregating '{ts_name}'")
            coll_compressed[ts_name] = coll[ts_name].samples_pack(agg_time, agg_mode, inplace=False)

        # save compressed collection
        if (verbosity): print(f"Saving '{fname_out+'.'+save_fmt}'")
        write_ts_file(coll_compressed, file_out, save_fmt, dict, overwrite=overwrite)

    return coll_compressed


def batch_import_files(path, sub_folders, csv_type, col_name, col_time, col_value,
                       enforce=None, causalise=False, allow_transcode=True,
                       save_files=False, save_series=False, save_fmt=('json','pk'), 
                       fname_out='_ALL_COLLECTION', verbosity=1):
    """ Imports time-series data from CSV-files in all 'sub_folders' below 'path'.

    This helper will go into 'path', check for all CSV-like files in all 'sub_folders', extract
    all time-series data that are found and convert/store them acc. to the given settings. Since
    data in different files may also refer to the same time-series (i.e. identical in name) the
    converted data has to be combined. Therefore, causality may have to be enforced at every
    "save stage" (in order to present time-series w/ monotonously increasing time instants).

    Regarding the 'csv_type', there are three general types of structure that may be found:

        'async': Each line contains a NEW SAMPLE for A SINGLE time-series such that contributing
            samples can appear in a mixed, asynchronous order. "Meta information" can be taken
            from all other columns (not referred to by the respective arguments).
            Typical examples for such files are log/event recordings.

        'stream': Each line contains a NEW SAMPLE for ONE OR MORE time-series w/ SAME, COMMON
            TIME REFERENCE. The names of all series are identified by the headers of the
            'col_data' columns (Note: 'col_name' setting will be ignored). 
            Typical examples are equidistantly sampled measurement signals of high resolution.

        'stream-xt': In these files, only a SINGLE STREAM is given, but w/ data starting only 
            in the 3rd line of the file. The first two lines indicate the signal name as well as
            dedicated meta information. Therefore, these lines have to be extracted first. 
            This special type is used for CSV-file exports from SIMATIC "CMS X-Tools".

    Notes on naming:
    (i) For the 'async' type, names are taken from column 'col_name' entries (per line). 
        Note that several items can be concatenated (by '_') if 'col_name' refers to a list!
    (ii) In case of the other CSV types, the setting in 'col_name' is actually ignored!
        For 'stream', names are taken from 'col_value' (header from 1st line).
        For 'stream-xt', names are directly inferred from the 'Data Name' field in the files.

    Args:
        path (str): Parent location of all data locations listed in 'sub_folders'.
        sub_folders (list of str): List of sub-folders to check for CSV-files containing more
            time-series data. If empty, i.e. [], the parent folder in 'path' will be searched.
        csv_type (str): Structure of CSV-files, either 'async'|'sampled'|'xstream'.
        col_name (str or list): Column(s) indicating datapoint name. If more than one columns
            are required to create a unique identifier, the items are concatenated by '_'.
            Note: This setting is only used for 'async' types!
        col_time (str): Column indicating the timestamps of the datapoint samples.
        col_value (str): Column indicating the values of the datapoint samples.
            Note: This setting defines signal names for 'sampled' types!
        enforce (list, optional): 2-tuple specifying conversions that should be enforced on
            'time' and 'data' entries. Defaults to 'None' (i.e. plain data is copied).
        causalise (bool, optional): Ensure that a "causal" timeline is represented. This may be
            required if samples have a non-monotonous ordering. Defaults to 'True'.
        allow_transcode (bool, optional): Switch to allow a "trans-coding" of storage files,
            i.e. if such file exist in the sub-folders but do not match the currently desired
            setting in 'save_fmt[1]', they will still be loaded an the collection will be saved
            to the desired (new) format. Defaults to 'True'.
        save_files (bool, optional): Switch to save each file after import, resulting in a
            "1-to-1"" conversion of all CSV-files. Otherwise, all contents imported from each
            subfolder are stored in a single file (as for the parent). Defaults to 'False'.
        save_series (bool, optional): Switch to save each single time-series found in its
            separate file. This can only be applied as final step since samples of (the same)
            time-series *might* be distributed over several subfolders. Defaults to 'False'.        
        save_fmt (list, optional): 2-tuple of file formats [str] to which converted data shall
            be stored to w/ options 'TS_SAVE_FORMATS'. Defaults to ('json', 'pk').
            Note: The two different levels are applied as follows:
                item [0]    -> single time-series and/or files ("1-to-1" conversion)
                item [1]    -> sub-folders & main path & collections (e.g. time periods, assets)
                Defaults to ('json', 'pk').        
        fname_out (str, optional): Filename for storing the full collection at parent level w/o
            file extension. Defaults to '_all'.        
        verbosity (int, optional): Level of displayed information. Defaults to '1'.
            level 0 = OFF (not recommended!)
            level 1 = only basic progress information (i.e. steps & traversed folders)
            level 2 = per file information
            level 3 = per time-series information (new & existing)

    Returns:
        collected (dict): Dict of collected & combined 'TimeSeries' objects from all files
            in all 'sub_folders' of 'path'.
    """    
    back = os.getcwd()
    os.chdir(path)

    # check for special meta format
    if (csv_type == 'stream-xt'):
        col_meta = 'xtools'
    else:
        col_meta = None

    # init & sub-folder checks (which are actually existing)
    collected = {}
    the_folders = sub_folders.copy()
    for chk in sub_folders:
        path_chk = os.path.join(path, chk)
        if (not os.path.isdir(path_chk)):
            the_folders.remove(chk)
    if (the_folders == []):
        return collected

    # init backup folder (to keep original files)
    if (_BACKUP_ORIG_FILES):
        folder_backup = os.path.join(path, '_BKP')
        if (not os.path.isdir(folder_backup)):
            os.mkdir(folder_backup)

    # parse ALL SUB-FOLDERS...
    for sub in the_folders:
        if (verbosity): print(f"o SUB-FOLDER '{sub}'")
        path_sub = os.path.join(path, sub)
        collected[sub] = []

        # check for existing (sub-folder) store file
        file_store, fext_store = None, None        
        chk = os.path.join(path_sub, f'_{sub}.{save_fmt[1]}')        
        if (os.path.isfile(chk)):
            file_store = chk
        elif (allow_transcode):            
            file_store = anyfile(path_sub, f'_{sub}', TS_SAVE_FORMATS)
            if (file_store):
                fext_store = file_store.split('.')[-1]

        # retrieve stored sub-folder data (if any)...
        if (file_store):
            if (verbosity): print(f"  Loading storage <{file_store}> ...")
            loaded = read_ts_file(file_store, target=list, verbose=(verbosity >= 2)) 
            for ts in loaded:
                collected[sub].append(ts)
        
        else: # ...or actually parse & import data from all files in sub-folder
            if (verbosity): print("  Importing files ... ")

            for fname in os.listdir(sub):
                fext = fname.split('.')[-1]
                if (fext not in TS_IMPORT_FORMATS):
                    continue # skip any other file formats

                # ensure backup folder (if any)
                if (_BACKUP_ORIG_FILES):
                    path_bkp = os.path.join(folder_backup, sub)
                    if (not os.path.isdir(path_bkp)):
                        os.mkdir(path_bkp)

                # data import & conversion
                if (verbosity >= 2): print(f"  + Converting <{fname}>")

                if (csv_type == 'async'):
                    objects = import_csv_async(os.path.join(path_sub, fname),
                        col_name, col_time, col_value,
                        enforce=enforce, ensure_causal=False,
                        save_file=save_files, save_fmt=save_fmt[0], verbosity=0)

                else: # (csv_type == 'stream'|'stream-xt'):
                    objects = import_csv(os.path.join(path_sub, fname),
                        col_time, col_value, col_meta,
                        enforce=enforce, ensure_causal=False,
                        save_file=save_files, save_fmt=save_fmt[0], verbosity=0)

                # move file to backup folder (if any)
                if (_BACKUP_ORIG_FILES):
                    try:
                        shutil.move(os.path.join(path_sub, fname), os.path.join(path_bkp, fname))
                    except:
                        print("    (file backup failed, check if existing)")

                # determine if new or existing time-series (within same sub-folder)
                for ts in objects:
                    idx = get_ts_list_index(collected[sub], ts.name)
                    if (idx is None):
                        if (verbosity >= 3): print(f"    - (new) '{ts.name}'")
                        collected[sub].append(ts)
                    else:
                        if (verbosity >= 3): print(f"    - (existing) -> add samples to '{ts.name}'")
                        collected[sub][idx].samples_add(ts, analyse=False)
                        collected[sub][idx].samples_unique()

        # save sub-folder collection
        if (collected[sub]):
            if (causalise):
                if (verbosity): print("  Ensuring causality of all time-series")
                for ts in collected[sub]:
                    ts.time_causalise()
            fname_sub = os.path.join(path_sub, f'_{sub}.'+save_fmt[1])
            # if (allow_transcode and (fext_store is not None) and (save_fmt[1] != fext_store)): # nur nach "file_store" testen, da transcdoing auch nur auf enforce
            if (allow_transcode and file_store):
                if (verbosity): print(f"  Transcoding sub-folder to <{fname_sub}>")
                trans_enforce = [enforce[0],None] if (enforce is not None) else None
                write_ts_file(collected[sub], fname_sub, save_fmt[1], dict, enforce=trans_enforce, overwrite=True)
            else:
                if (verbosity): print(f"  Saving sub-folder to <{fname_sub}>")
                write_ts_file(collected[sub], fname_sub, save_fmt[1], dict, overwrite=True)
                # Note: 'enforce' has already been applied during calls to 'import_...()' so save processing here!

        print("")

    # combine collections @ parent folder (i.e. from all existing sub-folders)
    if (verbosity): print(f"o PARENT folder")
    collected_all = []
    collected_names = []

    # ensure uniqueness
    if (verbosity): print("  Ensuring unique time-series (= possible merge of objects)")
    for sub in the_folders:
        for ts in collected[sub]:
            if (ts.name not in collected_names): # first appearance...
                collected_all.append(ts)
                collected_names.append(ts.name)
            else: # ...existing, append samples
                idx = get_ts_list_index(collected_all, ts.name)
                obj = collected_all[idx]
                obj.samples_add(ts, analyse=True)
                collected_all.pop(idx)
                collected_all.append(obj)

    # ensure causality
    if (causalise):
        if (verbosity): print("  Ensuring causality of all time-series")
        for ts in collected_all:
            if (verbosity >= 3): print(f"  - '{ts.name}'")
            ts.time_causalise()

    # save whole collection
    if (collected_all):
        file_all = os.path.join(path, fname_out+'.'+save_fmt[1])
        if (verbosity): print(f"  Saving WHOLE COLLECTION to <{file_all}>")
        write_ts_file(collected_all, file_all, save_fmt[1], dict, overwrite=True)

    # save all time-series to individual files
    if (save_series):
        if (verbosity): print(f"  Saving ALL COLLECTED TIME-SERIES (w/ individual filenames)")
        path_series = os.path.join(path, '_ALL_TS_'+save_fmt[0])
        if (not os.path.isdir(path_series)):
            os.mkdir(path_series)
        for ts in collected_all:
            fname_ts = os.path.join(path_series, ts.name+'.'+save_fmt[0])
            ts.export_to_file(fname_ts, True, fmt=save_fmt[0])

    print("")
    os.chdir(back)
    return collected


def batch_merge_files(path, sub_folders, basename, 
                      allow_overwrite=False, save_fmt='pk', fname_out='', verbosity=1):
    """ Merges data from storage files in 'sub_folders' below 'path'.

    This helper will go into 'path', check for all storage files (e.g. 'pk'|'json') and combine
    their collections on a 'TimeSeries' basis. In a typical usage, 'sub_folders' should refer
    to different periods of time (e.g. months), such that the resulting output storage files
    will then contain data of a longer (contiguous) interval w/ ensured causality.

    Args:
        path (str): Parent location of all data locations listed in 'sub_folders'.
        sub_folders (list of str): List of sub-folders to check for storage files ('pk'|'json').
        basename (str): Basic filename of storage file on which to performing the merge 
            operation w/o file extension (e.g. '_all_real_5min_avg').       
        save_fmt (str, optional): File format for merged storage file w/ options 'pk'|'json'.
            Defaults to 'pk'.
        fname_out (str, optional): Filename w/o file extension for merged storage file at
            parent level. Defaults to '' (i.e. filename is created from 'basename' + all items
            from 'sub_folders').
        allow_overwrite (bool, optional): Switch to allow overwriting of existing files, i.e. merging
            process will be repeated. Defaults to 'False'.
        verbosity (int, optional): Verbosity level of function. Defaults to '0'.
            level 0 = OFF (not recommended!)             
            level 1 = basic progress information (i.e. steps & folders/files)      
            Level 2 = per time-series information (i.e. merging of batches)

    Returns:
        collected_all (dict): Dict of collected & combined 'TimeSeries' objects from all 
            'basename' storage files in all 'sub_folders'.
    """
    back = os.getcwd()
    os.chdir(path)

    # init output filename
    if (fname_out == ''):
        fname_out = basename
        for item in sub_folders:
            fname_out += '_'+item

    # check for existence (Note: Necessary to avoid work if overwrite is *not* desired!)
    if (not allow_overwrite):
        existing_file = anyfile(path, fname_out, TS_SAVE_FORMATS)
        if (existing_file is not None):
            print(f"Merged file <{fname_out}> already exists! (enforce overwrite if required)")
            return None
    file_out = os.path.join(path, fname_out+'.'+save_fmt)

    # parse all sub-folders
    collected = {}
    for sub in sub_folders:
        if (verbosity): print(f"o SUB-FOLDER '{sub}'")
        collected[sub] = []

        # retrieve stored data (in any format)
        file_existing = anyfile(os.path.join(path, sub), basename, TS_SAVE_FORMATS)
        if (file_existing is not None):
            if (verbosity): print(f"  Loading storage <{os.path.basename(file_existing)}>")
            collected[sub] = read_ts_file(file_existing, target=list)
        else:
            if (verbosity): print(f"  No storage file <{basename}> found (skipping sub-folder)")
        print("")

    # combine full collection @ parent folder (i.e. asset level)
    collected_all = []
    collected_names = []

    # ensure uniqueness
    if (verbosity): print("Ensuring unique time-series (= merging batches)...")
    for sub in sub_folders:
        for ts in collected[sub]:
            if (ts.name not in collected_names): # first appearance...
                collected_all.append(ts)
                collected_names.append(ts.name)
            else: # ...existing, append samples
                idx = get_ts_list_index(collected_all, ts.name)
                obj = collected_all[idx]
                obj.samples_add(ts, analyse=True)
                collected_all.pop(idx)
                collected_all.append(obj)

    # ensure causality    
    if (verbosity): print("Ensuring causality of all time-series...")
    for ts in collected_all:
        if (verbosity >= 2): print(f"  - Sorting '{ts.name}'")
        ts.time_causalise()

    # save whole collection
    if (verbosity): print(f"Saving MERGED COLLECTION as <{file_out}>")
    write_ts_file(collected_all, file_out, save_fmt, dict, overwrite=True)

    print("")
    os.chdir(back)
    return collected_all


def summarize(collection, print_out=True, print_file=None, intro_lines=[],
              show_meta=True, show_series=True, time_iso=True):
    """ Gathers information on the objects in 'collection' for printing and/or saving to file.

    Args:
        collection (list or dict): Collection of 'TimeSeries' objects (either dict or list) for
            which to gather general information.
        print_out (bool, optional): Switch to print found information. Defaults to 'True'.
        print_file (str, optional): File to write to, extension '.tsinfo' will be enforced.
            Defaults to 'None' (i.e. no file output).
        intro_lines (list of str, optional): Introductory text to be placed befor the listings.
            Note that this could be used to insert details about the source of the data (e.g.
            import folders). Defaults to '[]'.
        show_meta (bool, optional): Switch to indicate if all keys of "meta" information
            present in the time-series data should also be listed. Defaults to 'True'.
        show_series (bool, optional): Switch to list all individual time-series by name and
            respective length [samples]. Defaults to 'True'.
        time_iso (bool, optional): Switch to convert [start,end] times for all objects to
            readable ISO 8061 string representation. Defaults to 'True'.

    Returns:
        infos (list): List of (ts_name, ts_length) tuples.
        tags (list): List of all tag strings (i.e. keys).
        totals (2-tuple): Two tuples containing infos on time extent for whole collection, i.e.
            (i) num_samples     -> minimum & maximum number of samples (across *all* objects)
            (ii) joint interval -> overlapping interval (covered by *all* objects)
    """
    infos, tags = [], []

    # parse collection (acc. to type) & sort by time-series names
    if (type(collection) is dict):
        for name in collection.keys():
            infos.append([name, len(collection[name]), [collection[name][0].t, collection[name][-1].t]])
            for tag in collection[name].meta.keys():
                if (tag not in tags):
                    tags.append(tag)
    elif (type(collection) is list):
        for ts in collection:
            infos.append([ts.name, len(ts), [ts[0].t, ts[-1].t]])
            for tag in ts.meta.keys():
                if (tag not in tags):
                    tags.append(tag)
    elif (istimeseries(collection)):
        ts = collection
        infos.append([ts.name, len(ts), [ts[0].t, ts[-1].t]])
        for tag in ts.meta.keys():
            if (tag not in tags):
                tags.append(tag)
    infos.sort(key=lambda x: x[0])

    # derive infos on whole collection
    if (len(infos)):
        get_samples = lambda x: [item[1] for item in x]
        get_start = lambda x: [item[2][0] for item in x]
        get_end = lambda x: [item[2][1] for item in x]
        all_samples = get_samples(infos)
        num_samples = [min(all_samples), max(all_samples)]
        time_start = max(get_start(infos))
        time_end = min(get_end(infos))
        if (time_start > time_end):
            interval = ['!! NOT', 'OVERLAPPING !!']
        else:
            interval = convert_time([time_start, time_end], TS_ISO_FORMAT)
    else:
        num_samples = [0, 0]
        time_start = 0.0
        time_end = 0.0
        interval = ['empty', 'collection']

    # use readable time in infos?
    if (time_iso):
        for item in infos:
            item[2] = convert_time(item[2], TS_ISO_FORMAT)

    # init output display (if any)
    display = []
    if (print_out):
        display.append( dict(eng='print', new='', skip='print("")') )       
    if (print_file):
        fpath, fbase, _ = fileparts(print_file)
        the_file = os.path.join(fpath, fbase+'.tsinfo')

        print(the_file)

        fh = open(the_file, mode='wt')
        display.append( dict(eng='fh.write', new=r'\n', skip=r'fh.write("\n")') )

    # print summary in all displays
    for D in display:   
        for line in intro_lines:
            eval(f'{D['eng']}("{line} {D['new']}")')
        eval(f'{D['skip']}')
        eval(f'{D['eng']}("================= {D['new']}")')
        eval(f'{D['eng']}("TOTAL COLLECTION: {D['new']}")')
        eval(f'{D['eng']}("================= {D['new']}")')
        eval(f'{D['eng']}("Number of time-series: {len(infos)} {D['new']}")')
        eval(f'{D['eng']}("Length minimum: {num_samples[0]:9d} samples {D['new']}")')
        eval(f'{D['eng']}("Length maximum: {num_samples[1]:9d} samples {D['new']}")')
        eval(f'{D['eng']}("Common interval: [ {interval[0]} <=> {interval[1]} ] {D['new']}")')
        eval(f'{D['skip']}')
        if (show_series):
            eval(f'{D['eng']}("============ {D['new']}")')
            eval(f'{D['eng']}("TIME-SERIES: {D['new']}")')
            eval(f'{D['eng']}("============ {D['new']}")')
            eval(f'{D['eng']}("Idx    Name                                                              # Samples  [ Interval ]               {D['new']}")')             
            eval(f'{D['eng']}("{'-'*128} {D['new']}")')
            for n, ts in enumerate(infos):
                eval(f'{D['eng']}("{n+1: 5}  {ts[0]:64}  {ts[1]: 9}  [ {ts[2][0]} <-> {ts[2][1]} ] {D['new']}")')
            eval(f'{D['eng']}("{'-'*128} {D['new']}")')
            eval(f'{D['skip']}')
        if (show_meta):
            eval(f'{D['eng']}("================= {D['new']}")')
            eval(f'{D['eng']}("META INFORMATION: {D['new']}")')
            eval(f'{D['eng']}("================= {D['new']}")')
            eval(f'{D['eng']}("Number of tags: {len(tags)} (union set, i.e. not all may be available for all series!) {D['new']}")')
            eval(f'{D['eng']}("Tag keys: {D['new']}")')
            for key in tags:
                eval(f'{D['eng']}("  o {key} {D['new']}")')
            eval(f'{D['skip']}')

    if (print_file):
        fh.close()

    return infos, tags, (num_samples, interval)


def get_ts_list_index(collection, name):
    """ Returns index of 'TimeSeries' object in list 'collection' w/ matching 'name'.

    Args:
        collection (list): Collection list of 'TimeSeries' objects.
        name (str): Name of object that shall be found.

    Returns:
        idx (int): Index of list object matching 'name'.
    """
    idx = next((n for n, ts in enumerate(collection) if (ts.name == name)), None)
    return idx


def get_ts_by_name(collection, name):
    """ Returns 'TimeSeries' object from 'collection' whose name matches 'name'.

    Note: This is a convenience function to manage list or dict collections in the same way!

    Args:
        collection (dict or list): Collection of 'TimeSeries' objects as either 'dict'|'list'.
        name (str): Name of object that shall be found.

    Returns:
        ts (:obj:): TimeSeries object as retrieved from 'collection'.
    """
    ts = None
    if (type(collection) is dict):
        if (name in collection.keys()):
            ts = collection[name]
    elif (type(collection) is list):
        idx = get_ts_list_index(collection, name)
        if (idx is not None):
            ts = collection[idx]
    else:
        raise NotImplementedError(f"Unknown type '{type(collection)}' for collection")
    return ts



#-----------------------------------------------------------------------------------------------
# PRIVATE FUNCTIONS (only to be used from internal methods, but not to be exposed!)
#-----------------------------------------------------------------------------------------------

def _assign_columns(desired, available, regex_auto=None):
    """ Return list of proper columns for CSV-file extraction.
     
    Note: This is a helper for most convenient use of CSV-file extraction and may include an 
    automatic mapping by checking for 'regex_auto' searches on 'available' if required!

    Args:
        desired (str or list): One or more columns to be found in 'available'.
        available (list of str): Available pool of columns (e.g. CSV-file headers).
        regex_auto (:obj:, optional): An 're' pattern for keyword searches in 'available' if
            'desired' is None. Defaults to 'None' (i.e. auto-mapping disabled).

    Returns:
        out (list of str): List of assigned columns (if any, otherwise '[]').      
    """

    # find as specified
    if (desired is not None):
        if (type(desired) is str):
            desired = [desired,]
        elif (type(desired) is not list):
            desired = []
        out = []
        for item in desired:
            if (item in available):
                out.append(item)
            else:
                raise ValueError(f"No column {item} found!")
        return out
    
    # find automagically? ;)
    if (regex_auto is not None):
        out = []
        for item in available:
            if (regex_auto.search(item.lower())):
                out.append(item)
        if (len(out)):
            return out 
        else:
            raise ValueError(f"No columns could be auto-mapped!")
        
    return []



#===============================================================================================
#===============================================================================================
#===============================================================================================

#%% MAIN
if __name__ == "__main__":
    print("This is the 'zynamon.imex' module.")
    print("See 'help(zynamon.imex)' for proper usage.")


    import_csv( r'S:\DB\CBM_data\VibTest\rpm700\2022-04-07\raw\new 1.txt', 
        col_time='Timestamp [ns]',
        col_data='Value', 
        col_meta='xtools',
        enforce=None,
        ensure_causal=True,
        keep_meta=True, 
        save_file=True, 
        save_fmt='json',
        verbosity=4)
