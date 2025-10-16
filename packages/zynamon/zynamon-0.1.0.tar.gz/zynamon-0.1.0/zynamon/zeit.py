"""
Time-series for managing datapoint objects w/ samples from arbitrary time instants.
"""

import os
import re
import h5py
import json
import numpy as np
import pickle as pk
import pandas as pd
import datetime as dt
from scipy.signal import lfilter

from zdev.core import local_val
from zdev.indexing import get_num_digits
from zdev.searchstr import S_NUMBER
from zdev.validio import valid_prec, valid_str_name


# EXPORTED DATA
TS_ISO_FORMAT = '%Y-%m-%d %H:%M:%S'
TS_SAVE_FORMATS = ('pk', 'h5', 'json')
TS_INDEX_LIMIT = int(1e12)
# Note: The 'TS_INDEX_LIMIT' is used to enable & differentiate a NORMAL, "DIRECT" INDEXING for
# time arrays.That is, integer values < 'TS_INDEX_LIMIT' are *not* interpreted as 'stamp_ns' but
# as actual array indices. This implies the following (negligible ;) restrictions:
#   (i) direct indexing is limited to arrays up to ~ 1 trillion samples length
#   (ii) very small times of type 'stamp_ns' cannot be represented by 'TimeSeries', however:
#        int(1e12) as 'stamp_ns'  ==>  '1970-01-01 00:16:40.000000' as 'iso'

# INTERNAL PARAMETERS & DEFAULTS
_JSON_INDENT = 4        # define JSON export (options: [int]|'None' -> one line, very small!)
_HDF5_STR_ENC = 'utf-8' # encoding for HDF5 export w/ string arrays (options 'ascii'|'utf-8')
_HDF5_ZIP_LEVEL = 4     # compression level for 'gzip' (default: 4, 0=min to 9=max)
_HDF5_SHUFFLE = True    # switch for data shuffeling (Note: May improve data compression!)
_PRINT_ONELINE = True   # switch to print preview on single line (otherwise: vertically)
_TIME_TYPE = {
    float: 'stamp', np.float32: 'stamp', np.float64: 'stamp',
    int: 'stamp_ns',
    str: 'iso',
    dt.datetime: 'obj_dt',
    pd.Timestamp: 'obj_pd'
    }
_VALUE_TYPE = {
    float: 'float', np.float32: 'float', np.float64: 'float',
    int: 'int', np.int32: 'int', np.int64: 'int',
    bool: 'bool',
    str: 'str'
    }
_FILTER_MODES = [
    'FIR_LP_MA',
    'IIR_1pole', 'IIR_flexpole',
    'NL_max', 'NL_min', 'NL_median',
    'box_avg', 'box_max', 'box_min', 'box_median',
    ]
_DF_TIME = 't'  # !! DO NOT CHANGE !! internal dataframe's time label !! DO NOT CHANGE !!
_DF_VALUE = 'x' # !! DO NOT CHANGE !! internal dataframe's values label !! DO NOT CHANGE !!

# regex search patterns for COMMON DATE/TIME SETTINGS (e.g. 'YYYY-mm-dd HH:MM:SS:usec')
# (SET) -> dates
_RX_SET_DATE_HYPH_Y4F_MNUM = re.compile(r'%Y-%m-%d')    # 'YYYY-mm-dd'
_RX_SET_DATE_HYPH_Y2F_MNUM = re.compile(r'%y-%m-%d')    # 'yy-mm-dd'
_RX_SET_DATE_HYPH_Y4F_MNAME = re.compile(r'%Y-%b-%d')   # 'YYYY-bbb-dd'
_RX_SET_DATE_HYPH_Y2F_MNAME = re.compile(r'%y-%b-%d')   # 'yy-bbb-dd'
_RX_SET_DATE_DASH_Y4F_MNUM = re.compile(r'%Y/%m/%d')    # 'YYYY/mm/dd'
_RX_SET_DATE_DASH_Y2F_MNUM = re.compile(r'%y/%m/%d')    # 'yy/mm/dd'
_RX_SET_DATE_DASH_Y4F_MNAME = re.compile(r'%Y/%b/%d')   # 'YYYY/bbb/dd'
_RX_SET_DATE_DASH_Y2F_MNAME = re.compile(r'%y/%b/%d')   # 'yy/bbb/dd'
# (SET) -> times
_RX_SET_TIME_USEC_DOT = re.compile(r'%H:%M:%S.%f')      # HH:MM:SS.usec
_RX_SET_TIME_USEC_COMMA = re.compile(r'%H:%M:%S,%f')    # HH:MM:SS,usec
_RX_SET_TIME_SEC = re.compile(r'%H:%M:%S')              # HH:MM:SS
_RX_SET_TIME_MIN = re.compile(r'%H:%M')                 # HH:MM
# (DAT) -> dates
_RX_DAT_DATE_HYPH_Y4F_MNUM = re.compile(r'\d{4}-\d{2}-\d{2}')           # 'YYYY-mm-dd'
_RX_DAT_DATE_HYPH_Y2F_MNUM = re.compile(r'\d{2}-\d{2}-\d{2}')           # 'yy-mm-dd'
_RX_DAT_DATE_HYPH_Y4F_MNAME = re.compile(r'\d{4}-[a-zA-Z]{3}-\d{2}')    # 'YYYY-bbb-dd'
_RX_DAT_DATE_HYPH_Y2F_MNAME = re.compile(r'\d{2}-[a-zA-Z]{3}-\d{2}')    # 'yy-bbb-dd'
_RX_DAT_DATE_DASH_Y4F_MNUM = re.compile(r'\d{4}/\d{2}/\d{2}')           # 'YYYY/mm/dd'
_RX_DAT_DATE_DASH_Y2F_MNUM = re.compile(r'\d{2}/\d{2}/\d{2}')           # 'yy/mm/dd'
_RX_DAT_DATE_DASH_Y4F_MNAME = re.compile(r'\d{4}/[a-zA-Z]{3}/\d{2}')    # 'YYYY/bbb/dd'
_RX_DAT_DATE_DASH_Y2F_MNAME = re.compile(r'\d{2}/[a-zA-Z]{3}/\d{2}')    # 'yy/bbb/dd'
_RX_DAT_DATE_DASH_Y4L_MNUM = re.compile(r'\d{2}/\d{2}/\d{4}')           # 'dd/mm/YYYY'
_RX_DAT_DATE_DASH_Y2L_MNUM = re.compile(r'\d{2}/\d{2}/\d{2}')           # 'dd/mm/yy'
# (DAT) -> times
_RX_DAT_TIME_USEC_DOT = re.compile(r'\d{2}:\d{2}:\d{2}[.]{1}\d')    # 'HH:MM:SS.usec'
_RX_DAT_TIME_USEC_COMMA = re.compile(r'\d{2}:\d{2}:\d{2}[,]{1}\d')  # 'HH:MM:SS,usec'
_RX_DAT_TIME_SEC = re.compile(r'\d{2}:\d{2}:\d{2}')                 # 'HH:MM:SS'
_RX_DAT_TIME_MIN = re.compile(r'\d{2}:\d{2}')                       # 'HH:MM'
# (DAT) -> time-zone
_RX_DAT_TZONE = re.compile(r'[+,-]\d{4}')                 # +0130'
_RX_DAT_TZONE_COLONS = re.compile(r'[+,-]\d{2}[:]\d{2}')  # -01:30'
# Notes: 
# (1) The available options above cover
#   - "European-style dates" (using hyphens, 4/2-digit years first, numeric/named months)
#   - "US-style dates" (using dashes, 4/2-digit years, year first/last, numeric/named months)
#   - "times" (w/ various precisions)
# (2) Further differentiation has to be made w.r.t. to operating regime, i.e. if applied to
#   - parameter 'settings' to define the format (SET)
#   - or given 'data' (DAT) / time values
# (3) For the date, it is emphasized that the "all-two-digits" formats cannot be fully 
#     differentiated when inferring from data! (i.e. 'yy/mm/dd' ~ 'dd/mm/yy' might be confused)
# (4) For time zones, the special "Z" (zulu) notation is captured as well but will be suppressed
#     during conversions.


class TimeSeries():
    """ Time-series based on 'pandas.DataFrame' w/ additional container information. """

    def __init__(self, name, tags=None): #samples=None):
        """ Initializes an empty time-series object.

        Args:
            name (str): Unique name identifying the time-series. This may contain '.' or '_'.
            tags (dict, optional): Dictionary of 'keyword: value' pairs descibring the context
                of the time-series data (e.g. 'location: Erlangen' etc). Defaults to 'None'.            

        Returns:
            --
        """

        # public attributes
        self.df = pd.DataFrame(columns=(_DF_TIME,_DF_VALUE)) # joint container for arrays
        self.name = name        # identifier for the time-series
        self.num_batches = -1   # number of batches (if progressive construction)
        self.meta = {}          # dict for additional "meta" data tags
        if (tags is not None):
            for key in tags:
                self.meta[key] = tags[key]
        self.time = None        # time specification object (incl. type/format)
        self.parent = None      # reference to parent object (in case of non-inplace operations)
        self.history = []       # keep track of important modifications to the object

        # # add initial samples (if any)
        # if (samples is not None):
        #     self.samples_add(samples)
        #fixme -> issue: if are non-default keys are used for sample dicts, these would have 
        # #              to be provided here as well... 

        return

    def __repr__ (self): # -> used for direct statement in console
        return f"TimeSeries '{self.name}' w/ {len(self)} samples (and {len(self.meta.keys())} tags)"

    def __str__(self): # -> used for 'print()'
        name = f"TimeSeries '{self.name}':"
        if (_PRINT_ONELINE):
            if (len(self) < 5):
                return name+"  [ not enough samples (yet) ]  "+"\n"
            else:
                if (self.time.type == 'stamp'):
                    str_t = f"  t: [ {self[0].t:8.3f}, {self[1].t:8.3f}, ...  {self[-2].t:8.3f}, {self[-1].t:8.3f}]"
                elif ((self.time.type == 'stamp_ns') or (self.time.type == 'iso')):
                    str_t = f"  t: [ {self[0].t}, {self[1].t}, ...  {self[-2].t}, {self[-1].t}]"
                else: # 'obj' ?
                    str_t = "  t: [ unknown ]"
                if (self.get_type_x() == 'str'):
                    str_x = f"  x: [ {self[0].x}, {self[1].x}, ...  {self[-2].x}, {self[-1].x}]"
                else:
                    str_x = f"  x: [ {self[0].x:8.3f}, {self[1].x:8.3f}, ...  {self[-2].x:8.3f}, {self[-1].x:8.3f}]"               
                return name+"\n"+str_t+"\n"+str_x
        else:
            if (len(self) < 5):
                return name+"\n"+self.df.to_string()+"\n"
            else:
                head = self.df.head(2).to_string()
                tail = self.df.tail(2).to_string(header=False)
                return name+"\n"+head+"\n"+"..."+"\n"+tail+"\n"

    def __len__(self):
        return len(self.df)

    def __bool__(self):
        return len(self.df) > 0

    def __getitem__(self, n):
        # return self.df.loc[n]
        return self.df.iloc[n]    

    def __setitem__(self, n, item):
        self.df.iloc[n] = item
        return

    def __add__(self, other):
        """ Operation + """
        from zynamon.utils import relate
        return relate(self, other, '+', res=None, mode='avg')

    def __sub__(self, other):
        """ Operation - """
        from zynamon.utils import relate
        return relate(self, other, '-', res=None, mode='avg')

    def __mul__(self, other):
        """ Operation * """
        from zynamon.utils import relate
        return relate(self, other, '*', res=None, mode='avg')

    def __truediv__(self, other):
        """ Operation / """
        from zynamon.utils import relate
        return relate(self, other, '/', res=None, mode='avg')


    def clear(self, keep_history=False):
        """ Clears DataFrame arrays (name & tag attributes are kept).

        Args:
            keep_history (bool, optional): Switch to keep information on operations on the
                time-series. Defaults to 'False'.

        Returns:
            --
        """
        self.df = pd.DataFrame(columns=(_DF_TIME,_DF_VALUE))
        self.num_batches = 0
        self.time = None
        if (not keep_history):
            self.history = []
        return


    def clone(self, new_name=None, keep_history=True):
        """ Creates an exact copy of the object w/ potentially 'new_name'.

        Args:
            new_name (str, optional): New name for TimeSeries object, otherwise this will be
                set to 'self.name'+'_'. Defaults to 'None'.
            keep_history (bool, optional): Switch to keep information on operations on the
                time-series. Defaults to 'False'.

        Returns:
            ts_out (:obj:): Cloned 'TimeSeries' object (w/ batch counter reset).
        """

        # copy basic structure
        ts_out = TimeSeries('')
        for key in ts_out.__dict__:
            if (key == 'name'):
                # set new name?
                if (new_name is None):
                    ts_out.name = self.name+'_'
                else:
                    ts_out.name = new_name
            elif (key == 'df'):
                exec(f"ts_out.{key} = self.{key}.copy()")
            else: # all other members
                try:
                    exec(f"ts_out.{key} = self.{key}.copy()")
                except:
                    exec(f"ts_out.{key} = self.{key}") # no true copy! (will have *same* 'id')

        # update
        ts_out.num_batches = 1
        ts_out.parent = id(self)
        if (not keep_history):
            ts_out.history = []

        return ts_out


    def print(self, num_samples=None, end='tail'):
        """ Prints 'num_samples' items of time-series from 'end'.

        Args:
            num_samples (int, optional): Number of lines to print. Defaults to 'None' (= all).
            mode (str, optional): Indicate if data should be printed from 'head' or 'tail'.
                Defaults to 'tail' (i.e. most recent samples from the end).

        Returns:
            --
        """
        name = f"TimeSeries '{self.name}':"
        if (num_samples is None):
            body = eval(f"self.df.{end}(len(self)).to_string()")
        else:
            body = eval(f"self.df.{end}({num_samples}).to_string()")
        print("\n"+name+"\n"+body+"\n")
        return


    def stats(self, content='all'):
        """ Prints some statistics of time-series.

        Args:
            content (str, optional): Select which content to be shown w/ available options
                'all'|'size'|'time'. Defaults to 'all'.
        Returns:
            --
        """
        print("-"*64)
        print(f"Statistics on TimeSeries '{self.name}':")
        if (not len(self)):
            print("[ still empty ]")
            return print("-"*64)
        
        if (content in ('all','size')):            
            print(f" [Size]")
            print(f" - # samples: {len(self)}")
            print(f" - interval: [{self[0].t}, {self[-1].t}]")

        if (content in ('all','time')):
            print(f" [Time]")
            self.time_analyse()
            print(f" - Ts avg:     {self.time.Ts}")
            print(f" - Ts range:   [{self.time.stat['Ts_min']}, {self.time.stat['Ts_max']}]")
            print(f" - Ts quality: {self.time.stat['quality']}")
            print(f" - Ts std dev: ~ {self.time.stat['Ts_sigma']:.3f}")
        else:
            pass

        return print("-"*64)


    def samples_add(self, new_samples, time_key=_DF_TIME, value_key=_DF_VALUE, analyse=True, 
                    incognito=False):
                    # hysteresis=False, hyst_rel=0.01,
                    # hyst_params={'mode': 'suppress', 'min_dev': 0.001, 'max_silence': '60sec'})
                    # #### TODO!
        """ Adds new samples to TimeSeries object.

        New samples may be presented in many formats and will be consumed accordingly. In
        addition, some internal analyses may be carried out as well. However, it should be
        noted that for calling loops w/ "one-sample-at-a-time" behaviour, the overall import
        procedure will perform significantly faster if 'analyse=False'. In this way, no updating
        is carried out in each step, but could be triggered on demand later on...

        Note: In contrast to other methods 'samples_add()' is INHERENTLY INPLACE only!

        Args:
            new_samples (dict or list): Object containing new samples for the object. These may
                be given in one of the following formats/structures:
                + existing 'TimeSeries' object
                + existing 'DataFrame' object
                + dict w/ {time_key: [...], value_key: [...]}
                + zip of 2-tuples where each item represents [time, value]
                + list/tuple/np.ndarray of 2-tuples as [time, value]
                + list/tuple/np.ndarray of dicts w/ scalar items as {time_key: ..., value_key: ...}
                + flat list/np.ndarray (time is created as "natural" 0-based index then)
            time_key (str, optional): If required, this defines the key by which time instants
                are recognised. Defaults to _DF_TIME.
            value_key (str, optional): If required, this defines the key by which sample values
                are recognised. Defaults to _DF_VALUE.
            analyse (bool, optional): Switch to update internal indicators (at the cost of
                slower imports if done sample-wise). Defaults to 'True'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.

        ### TODO!
        # hysteresis stuff?
        ### TODO!

        Returns:
            --
        """

        # init
        kt = time_key if (time_key is not None) else _DF_TIME
        kv = value_key if (value_key is not None) else _DF_VALUE

        # auto-detect format of input samples
        if (istimeseries(new_samples)):
            mode = 'ts'
        elif ((type(new_samples) is pd.DataFrame) and
              (set([kt,kv]).issubset(new_samples.columns))):
            mode = 'df'
        elif (type(new_samples) is dict):
            mode = 'dict'
        elif (type(new_samples) is zip):
            mode = 'zip'
        elif (type(new_samples) in (list, tuple, np.ndarray)):
            if (type(new_samples[0]) in (list, tuple, np.ndarray)):
                mode = 'list-of-tuples'
            elif (type(new_samples[0]) is dict):
                mode = 'list-of-dicts'
            else:
                mode = 'list-values'
        else:
            raise ValueError('Unknown format of new samples')
        
        # ingest new samples by preparing a dataframe (acc. to mode)
        if (mode == 'ts'):
            df_new = new_samples.df

        elif (mode == 'df'):
            df_new = new_samples[[kt,kv]]

        elif (mode == 'dict'):
            if (not set([kt,kv]).issubset(new_samples.keys())):
                raise KeyError(f"Missing time/value keys '{kt}'/'{kv}' in dict")
            if (len(new_samples[kt]) != len(new_samples[kv])):
                raise ValueError('Inconsistent number of time/value items')
            df_new = pd.DataFrame( data={_DF_TIME: new_samples[kt], _DF_VALUE: new_samples[kv]} )

        elif (mode in ('zip', 'list-of-tuples')):
            unzipped = list(zip(*new_samples))
            df_new = pd.DataFrame(data={_DF_TIME: unzipped[0], _DF_VALUE: unzipped[1]})

        elif (mode == 'list-of-dicts'):
            new_unwrapped = { key: [item[key] for item in new_samples] for key in (kt,kv) }
            df_new = pd.DataFrame( data={_DF_TIME: new_unwrapped[kt], _DF_VALUE: new_unwrapped[kv]} )

        else: # mode == 'list-values'
            time_unknown = -1 * np.ones_like(new_samples)
            df_new = pd.DataFrame(data={_DF_TIME: time_unknown, _DF_VALUE: new_samples})
            # Note: Setting 'time_unknown' to NaN values yields trouble when serializing! :(

        #
        # TODO: include hysteresis here...
        #

        # ensure same time format & extend object by current batch
        if (self.df.empty): # initial batch (get spec from data)
            self.time = TimeSpec(df_new.t)
            self.df = df_new
        else: # auto-convert (if required)
            df_new.t = convert_time(df_new.t, self.time.get())
            self.df = pd.concat([self.df, df_new], ignore_index=True)
        self.num_batches += 1

        # perform internal analyses?
        if (analyse or not self.time.Ts):
            self.time_analyse()

        if (not incognito):
            self.history.append(('@samples_add', len(df_new)))

        return


    def samples_crop(self, selected, incognito=False, inplace=True, addon='_cropped'):
        """ Crops matching time frame of 'selected' data & creates new 'TimeSeries'.

        If the time instants referred to by 'selected' are not directly found in the object's
        time array (e.g. due to limits exceeding array range), the effective selection is
        shrinked accordingly such that only parts inside the interval are returned. If no valid
        range is found at all, 'selected' is either in the "future" or in "past".

        For simplicity and intuitive use, a direct indexing is provided as well. That is, if
        'selected' contains integers less than 'TS_INDEX_LIMIT', these are interpreted as normal
        indices of the time array rather than 'stamp_ns' defined by 'zynamon.zeit.TimeSpec'.

        Note: Unexpected behaviour may occur if the time-series is not sorted as "causal"!

        Args:
            selected (2-tuple or scalar): Frame definition by interval or scalars in *any form*
                supported by 'zynamon.zeit.TimeSpec'. Note that intervals '[A,B]' are *inclusive* 
                (i.e. both 'df.iloc[A]' and 'df.iloc[B]' will be present) whereas scalars are 
                resolved into the range '[len(df)-selected:]', i.e. cropping is done from the end.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series. Defaults to '_cropped'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' as frame of original w/ only 'selected' samples
                (unless 'inplace' operation).
        """

        # ensure "usable" format
        orig_spec = self.time.get()
        arr_t = convert_time(self.df.t, 'stamp')

        # determine mode of selection
        direct_indexing = False
        try:
            len(selected)
            if (type(selected) is str):
                raise # Note: dummy to jump to "except" branch ;)
            else:
                mode = 'interval'
                if (((type(selected[0]) is int) and (type(selected[1]) is int)) and
                    (selected[0] <= selected[1] < TS_INDEX_LIMIT)):
                    direct_indexing = True
        except:
            mode = 'scalar'
            if ((type(selected) is int) and (selected < TS_INDEX_LIMIT)):
                direct_indexing = True        

        # evaluate condition
        if (direct_indexing):
            if (mode == 'scalar'):
                cond_tmp = (self.df.index > len(self)-(selected+1))
            else: # == 'interval'
                cond_tmp = ((self.df.index >= selected[0]) & (self.df.index <= selected[1]))
            condition = pd.Series(cond_tmp)
        else:
            if (mode == 'scalar'): # i.e. interval "from the end"
                t_sel = convert_time(selected, 'stamp')
                condition = (arr_t >= arr_t.iloc[-1]-t_sel)
            else: # == 'interval'
                tmp = TimeSpec(selected[0])
                selected[1] = convert_time(selected[1], target=tmp.get()) # support "mixed intervals"??? ;)
                # selected[1] = tmp.force_spec(selected[1]) # supports "spec-mixed" intervals!
                # print(selected)                
                t_sel = convert_time(selected, 'stamp')
                condition = ((arr_t >= t_sel[0]) & (arr_t <= t_sel[1]))

        # actual frame cropping
        if (inplace):
            self.df.where(condition, inplace=True)
            self.df.dropna(inplace=True)
            self.num_batches = 1
            if (not incognito):
                self.history.append(('@samples_crop', selected))
            return
        else:
            df_cond = self.df.where(condition)
            df_crop = df_cond.dropna()
            ts_out = self.clone(self.name+addon)
            ts_out.clear(keep_history=True)
            ts_out.samples_add(df_crop, incognito=True)
            ts_out.time_convert(orig_spec, incognito=True)
            if (not incognito):
                ts_out.history.append(('@samples_crop', selected))
            return ts_out


    def samples_pack(self, agg_time=(5*60), agg_mode='avg',
                     incognito=False, inplace=True, addon='_packed'):
        """ Compresses the time-series samples acc. to the chosen aggregation mode.

        This method essentially performs a call to 'values_filter()' w/ a time-boxed filter
        mode and a subsequent call to 'time_align()' w/ the same time window. By this, the
        number of samples can be considerably reduced and the whole time-series is replaced by
        a downsampled version representing the desired compression.

        Args:
            agg_time (float, optional): Time interval [s] used for aggregation, i.e. resolution
                after downsampling. Defaults to 5 minutes, i.e. '300' sec.
            agg_mode (str, optional): Mapping mode for aggregation. Defaults to 'avg'.
                Available options comply with the 'box_' modes of the 'values_filter()' method,
                i.e. options are 'avg'|'max'|'min'|'median'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_packed'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' object (unless 'inplace' operation).
        """

        if (inplace):
            self.values_filter('box_'+agg_mode, {'box_time': agg_time}, incognito=True)
            self.time_align(agg_time, shift='center', recon='nearest', incognito=True)
            if (not incognito):
                self.history.append(('@samples_pack', f"agg_time={agg_time}, agg_mode={agg_mode}"))
            return
        else:
            ts_out = self.clone(self.name+addon)
            ts_out.values_filter('box_'+agg_mode, {'box_time': agg_time}, incognito=True)
            ts_out.time_align(agg_time, shift='center', recon='nearest', incognito=True)
            if (not incognito):
                ts_out.history.append(('@samples_pack', f"agg_time={agg_time}, agg_mode={agg_mode}"))
            return ts_out

     #------------------------------------------------------------------------------------------
     # TODO: How to implement a "filter/compress" mode for string values?
     #       --> e.g. do NOT repeat same string until next 'box_time' ????
     #      --> i.e. check on 'has_string_values' or get type??
     #------------------------------------------------------------------------------------------

    # def samples_crucialize(self, hyst_level_rel=0.01, hyst_time_max=5*60, incognito=False):
    #                 # hysteresis=False, hyst_rel=0.01,
    #                 # hyst_params={'mode': 'suppress', 'min_dev': 0.001, 'max_silence': '60sec'})
    #                 # #### TODO!
    #     """ Re-interprets samples of TimeSeries object by keeping only relevant ones.

    #     # TODO;: This is an 'hysteresis' function on the existing object.
    #     #       --> TO BE ADDED also to "samples_add"

    #         --
    #     """
    #     # mylocals = hist_locals(locals())
    #     pass
    #     return


    def samples_unique(self, array=None, keep='first', causalise=False,
                       incognito=False, inplace=True, addon='_unique'):
        """ "Streamlines" time-series by removing duplicates and retaining only unique data.

        Args:
            array (str, optional): Switch to select either _DF_TIME or _DF_VALUE to check for
                duplicates. Otherwise, only samples where both time & value are identical are 
                counted. Defaults to 'None' (i.e. check both).
            keep (str, optional): Which occurrences to keep w/ options 'first'|'last'. Defaults
                to 'first'.
            causalise (bool, optional): Switch to sort time array in ascending order (after
                removing duplicates). Defaults to 'False'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_unique'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' object (unless 'inplace' operation).
        """
        if (inplace):
            self.df.drop_duplicates(array, keep=keep, inplace=True, ignore_index=True)
            if (causalise):
                self.time_causalise(inplace=True, incognito=True)
            if (not incognito):
                self.history.append(('@samples_unique', f"array={array}, keep='{keep}', causalise={causalise}"))
            return
        else:
            ts_out = self.clone(self.name+addon)
            ts_out.df.drop_duplicates(array, keep=keep, inplace=True, ignore_index=True)
            if (causalise):
                ts_out.time_causalise(inplace=True, incognito=True)
            if (not incognito):
                ts_out.history.append(('@samples_unique', f"array={array}, keep='{keep}', causalise={causalise}"))
            return ts_out


    def time_align(self, res=1.0, shift='bwd', recon='avg', allow_expand=True,
                   interpol='linear', incognito=False, inplace=True, addon='_aligned'):
        """ Aligns time-series samples by temporally quantising to 'res' intervals.

        This method essentially applies an "anti-jitter" mechanism to the time-series samples.
        That is, all samples are strictly aligned to multiples of the given temporal resolution
        such that a perfect equi-distant sampling rate is generated while the associated values
        have to be mapped. For this reconstruction / interpolation scheme, two fundamental
        effects should be kept in mind:

        Notes:
        (1) The resulting NUMBER OF SAMPLES will generally be different from the original!
            For 'res > Ts', an aggregation is performed where the arrays are COMPRESSED due to
            the inherent "many-to-one" mapping, whereas for 'res < Ts' the amount of samples may
            be kept the same, but will increase if 'expand' is enabled!
        (2) The resulting time-series may represent a NON-CAUSAL VERSION of the original!
            For the default 'bwd' shift, this is the case as the samples are "pulled back"
            compared to the original time axis whereas the "fwd" will shift these to the future
            of the data stream. For reasonably small resolutions (< 1s) and typical applications
            (e.g. IoT sensors w/ larger 'Ts'), implications may still be considered negligible.
            However, the output of the "bwd" mode *could* be interpreted as a "faster response"
            e.g. for generating alarms etc. ;)

        Args:
            res (float, optional): Desired resolution [s] to which mapping should occur.
                Defaults to 1.0 (one sample each sec).
            shift (str, optional): Direction of mapping. Defaults to 'bwd'. Available options:
                 + 'bwd'    -> backwards, i.e. towards the most recent time instant
                 + 'fwd'    -> forwards, i.e. to the future time instant.
                 + 'center' -> centered, only useful when "packing" data where 'res > Ts'
                               (Note: Expansion will be disabled in this case!)
            recon (str, optional): Reconstruction / assignment method for time-series values.
                Defaults to 'avg'. Available options:
                + 'nearest'  -> use only first/last value in mapping (dep. on 'shift')
                + 'avg       -> use arithmetic average of values in mapping
                + 'weighted' -> use weighted averaging w/ contributions proportional to the
                                distance between original and mapped time instants
            allow_expand (bool, optional): Switch to allow expansion of the time-series if
                required (i.e. if 'res' < 'Ts') along with a suitable interpolation method to
                fill the missing values. Defaults to 'True'.
            interpol (str, optional): Interpolation mode to be used in case of time-series
                expansion. All methods supported by 'pd.DataFrame.interpolate' could be chosen,
                however, currently only 'pad'|'linear' are supported. If set to 'None', values
                will not be filled but remain marked as 'np.NaN'. Defaults to 'linear'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_aligned'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' object (unless 'inplace' operation).

        Example: Illustration of alignment for 'res=1.0', shift='bwd' and recon='avg':

            ORIGINAL:
            t:  0.0   0.5    1.0 1.3    2.1    2.8    3.4   4.0               5.7   6.2      7.1
                  |     |      |   |      |      |      |     |                 |     |        |
            x:    1     2      3   4      5      6      7     8                 9    10       11

            ALIGNED w/ "coarser" resolution: 'res=1.0' --> aggregation
            t:  0.0        1.0         2.0       3.0        4.0        5.0        6.0        7.0
                  |          |           |         |          |          |          |          |
            x:  1.5        3.5         5.5       7.5         8          9         10        11.0

            ALIGNED w/ "finer" resolution: 'res=0.2' --> and only "padding" of values
            t:  0.0 .2 .4 .6 .8 1.0 .2 .4 .6 .8 2.0 .2 .4 .6 .8 3.0 .2 .4 .6 .8 4.0    (...)
                  |               |               |               |               |    (...)
            x:    1  1  2  2  2   3  4  4  4  4   5  5  5  5  6   6  6  7  7  7   8    (...)
        """

        # TODO: Apply "causalise" as well?
        # --> introduce this? flag set, until "breaking" operation is triggered! ;)

        # init processing arrays
        orig_spec = self.time.get()
        arr_t, arr_x, _ = self.to_numpy(float)

        # init
        Nd = get_num_digits(res)
        map_idx, map_dist = {}, {}
        if (shift == 'bwd'):
            bit_more = 0
        elif (shift == 'fwd'):
            bit_more = 1
        elif (shift == 'center'):
            bit_more = 0.5
            allow_expand, interpol = False, False # disabled (see above for explanation)

        # track mapping of sample values onto new time instants (which indices & distance?)
        for n in range(len(self)):
            tmp = float( res * (int(arr_t[n]/res) + bit_more) )
            tn = valid_prec(tmp, Nd)
            if (tn not in map_idx.keys()):
                map_idx[tn] = [n,]
                map_dist[tn] = [arr_t[n]-tn,]
            else:
                map_idx[tn].append(n)
                map_dist[tn].append(arr_t[n]-tn)
        t_new = list(map_idx.keys())

        # generate values for new samples (using desired reconstruction mode)
        x_new = np.zeros_like(t_new, dtype=float)
        for n, tn in enumerate(t_new):
            if (tn not in map_idx.keys()):
                continue
            else:
                tmp = 0.0

                if (recon == 'nearest'): # use only first/last value of mapping
                    if (shift == 'bwd'):
                        x_new[n] = arr_x[map_idx[tn][0]]
                    else: # shift == 'fwd'
                        x_new[n] = arr_x[map_idx[tn][-1]]

                elif (recon == 'avg'): # use simple arithmetic average
                    N = len(map_idx[tn])
                    for t_map in map_idx[tn]:
                        tmp += arr_x[t_map]
                    x_new[n] = tmp/N

                elif (recon == 'weighted'): # use weighted average (acc. to time distance)
                    W = 0.0
                    for n_map, t_map in enumerate(map_idx[tn]):
                        weight = 1.0 - (abs(map_dist[tn][n_map])/res)
                        tmp += arr_x[t_map] * weight
                        W += weight
                    x_new[n] = tmp/(W + 1e-9) # Note: 1e-9 for regulation!

                # elif (recon == 'sinc'): # TODO? other?
                #     pass

                else:
                    raise NotImplementedError(f"Unknown reconstruction '{recon}' specified")

        # expansion of time-series? (in case of finer resolution)
        if (allow_expand):

            # init "full ranged" temporal resolution
            tA = float( res * (int(arr_t[0]/res) + bit_more) )
            tB = float( res * (int(arr_t[-1]/res) + 1) )
            t_res = np.arange(tA, tB, res, dtype=float)
            x_res = np.empty(len(t_res))
            x_res[:] = np.nan

            # (a) find support values
            for nr, tr in enumerate(t_res):
                try:
                    nn = t_new.index( valid_prec(tr, Nd) )
                    x_res[nr] = x_new[nn]
                except:
                   continue

            # (b) create DataFrame w/ final time (incl. offset)
            df_aligned = pd.DataFrame({_DF_TIME: np.array(t_res), _DF_VALUE: x_res})

            # (c) interpolate remaining missing values (acc. to mode)
            if (interpol is not None):
                if (interpol == 'pad'):
                    exec(f"df_aligned.ffill(axis=0, inplace=True)")
                elif (interpol in ('linear',)):
                    exec(f"df_aligned.interpolate('{interpol}', axis=0, inplace=True)")
                else:
                    raise NotImplementedError(f"Unknown interpolation '{interpol}' specified")

        else:
            df_aligned = pd.DataFrame({_DF_TIME: np.array(t_new), _DF_VALUE: x_new})

        # update or create new (time-aligned) object
        if (inplace):
            self.clear(keep_history=True)
            self.samples_add(df_aligned, incognito=True)
            self.time_convert(orig_spec, incognito=True)
            if (not incognito):
                self.history.append(('@time_align', f"res={res}, shift='{shift}', recon='{recon}', allow_expand={allow_expand}, interpol='{interpol}'"))
            return
        else:
            ts_out = self.clone(self.name+addon)
            ts_out.clear(keep_history=True)
            ts_out.samples_add(df_aligned, incognito=True)
            ts_out.time_convert(orig_spec, incognito=True)
            if (not incognito):
                ts_out.history.append(('@time_align', f"res={res}, shift='{shift}', recon='{recon}', allow_expand={allow_expand}, interpol='{interpol}'"))
            return ts_out


    def time_analyse(self):
        """ Analyse time array-specific parameters of time-series data. 
        
        Note that this will cover the (average) sampling rate and statistics of the array 
        whereas 'scale' and 'shift' modifiers are only to be set by the 'set_mods()' method!
        """

        # init container for advanced statistics (if not yet existing)
        if (not self.time.stat):
            self.time.stat = {
                'quality': 'too-few-samples',   # general quality of time array
                'Ts_max': -1,         # maxiumum time difference between consecutive samples
                'Ts_min': -1,         # minimum time difference between consecutive samples
                'Ts_sigma': -1,       # standard deviation (of time differences)
                'Ts_sigma_norm': -1,  # normalized standard deviation (of time differences)
                'dev_fac_Ts_max': -1, # maximum sampling rate deviation factor
                'dev_fac_Ts_min': -1, # minimum sampling rate deviation factor
                }        

        # ensure "usable" format for analysis & check basic suitability
        arr_t = convert_time(self.df.t, float)        
        if (len(arr_t) == 1): # single sample (yet)?
            self.time.Ts = -1
            return
        elif (arr_t.iloc[0] == arr_t.iloc[-1]): # samples w/o time? (i.e. mode 'list-values')
            self.time.Ts = -1
            return
        
        # determine (average) sampling rate
        delta_t = arr_t.diff()
        idx = (delta_t != 0.0) # exclude all "0.0" entries (i.e. duplicate time instants!)
        self.time.Ts = round(delta_t[idx].mean(), 9)
        
        # compute additional statistics
        self.time.stat['Ts_max'] = round(delta_t[idx].max(), 9)
        self.time.stat['Ts_min'] = round(delta_t[idx].min(), 9) # Note: Robustify due to division below!
        self.time.stat['Ts_sigma'] = round(delta_t[idx].std(), 9)
        self.time.stat['Ts_sigma_norm'] = round(self.time.stat['Ts_sigma']/self.time.Ts, 9)
        self.time.stat['dev_fac_Ts_max'] = round(self.time.stat['Ts_max']/self.time.Ts, 9)
        self.time.stat['dev_fac_Ts_min'] = round(self.time.Ts/self.time.stat['Ts_min'], 9)

        # assess quality of time array
        if (self.time.stat['Ts_sigma_norm'] <= 0.001): # i.e. < 0.1%
            self.time.stat['quality'] = 'equidistant'
        elif (self.time.stat['Ts_sigma_norm'] <= 0.1): # i.e. < 10%
            self.time.stat['quality'] = 'jittered'
        else: # i.e. > 10%
            self.time.stat['quality'] = 'dispersed'

        return


    def time_causalise(self, incognito=False, inplace=True, addon='_causal'):
        """ Ensures all samples are stored in ascending temporal order.

        Args:
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_causal'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' object (unless 'inplace' operation).
        """
        if (inplace):
            self.df.sort_values(_DF_TIME, ascending=True, inplace=True)
            self.time_analyse()
            if (not incognito):
                self.history.append(('@time_causalise', None))
            return
        else:
            tmp = self.df.sort_values(_DF_TIME, ascending=True)
            ts_out = self.clone(self.name+addon)
            ts_out.clear(keep_history=True)
            ts_out.samples_add(tmp, analyse=True, incognito=True)
            if (not incognito):
                ts_out.history.append(('@time_causalise', None))
            return ts_out


    def time_convert(self, target, factor=None, offset=None, incognito=False):
        """ Converts time array to 'target' w/ optional scaling 'factor' and/or 'offset'.

        Notes:
        (1) Modifications (scaling / offset) are only available for 'stamp'-type inputs!
        (2) Both operations work "in-place" and in the order of arguments.
        (3) For more infos on 'TimeSeries' time formats, refer to 'TimeSpec()'.

        Args:
            target (scalar): Desired time specification.
            factor (float, optional): Scaling factor for all times. Defaults to 'None'.
            offset (scalar, optional): Additional offset (in *any* supported timespec) to be
                applied for all times.  Defaults to 'None'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.

        Returns:
            --
        """

        # anticipate change in sampling rate (if any)
        if ((self.time.Ts != -1) and (factor is not None)):
            new_Ts = self.time.Ts * factor
        else:
            new_Ts = None

        # array conversion
        self.df.t = convert_time(self.df.t, target, factor, offset)

        # update parameters
        self.time = TimeSpec(target)
        self.time.set(scale=factor, shift=offset, Ts=new_Ts)
        if (not incognito):
            self.history.append(('@time_convert', f"'{target}', factor={factor}, offset={offset}"))
        
        return


    def time_reset(self, incognito=False):
        """ Resets time array to original values (i.e. re-format w/o offset).

        Args:
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.

        Returns:
            --
        """
        if ((self.time.scale != 1.0) or (self.time.shift != 0.0)):
            # ensure timespec is determined & "usable" format
            orig_spec = self.time.get()
            self.time_convert('stamp')
            # reverse modifications
            rev_scaling = 1./self.time.scale
            rev_offset = -self.time.shift
            self.time_convert(orig_spec, scaling=rev_scaling, offset=rev_offset,
                              incognito=incognito)
        else:
            pass # nothing to do ;)
        return


    def values_filter(self, mode='FIR_LP_MA',
                      params={'N': 10, 'pole': [0.9,0.3], 'smooth': 0.15, 'box_time': (5*60)},
                      init=True, incognito=False, inplace=True, addon='_filtered'):
        """ Filters the values array 'df.x' acc. to a desired 'mode'.

        The default mode provides a moving-average over N=10 samples, realising a "lazy" FIR
        low-pass filter. For a better preservation of peaks while still smoothing less dynamic
        segments, use the sophisticated IIR-type filter w/ "flexible pole".

        Args:
            mode (str, optional): Type of filter implementation. Defaults to 'FIR_LP_MA'.
                Available options & sub-options areas follows:
                + 'FIR': Transversal finite impulse response filtering w/ fixed length 'N'.
                    - '_LP_MA'    -> rectangular shape (i.e. "moving average")
                + 'IIR': Recursive filtering acc. to given poles.
                    - '_1pole'    -> single pole (e.g. "forgetting factor")
                    - '_flexpole' -> flexible-pole approach (e.g. for preserving peaks during
                                    dynamic phases while smoothing otherwise)
                + 'NL': Sample-wise nonlinear filtering based on length 'N' sliding window.
                    - '_max'      -> select maximum within window
                    - '_min'      -> select minimum within window
                    - '_median'   -> select median value within window
                + 'box': Time-boxed filtering operation, based on the actual durations
                    found in the time array 'df.t'. All values within the box are replaced
                    by this filtered value.
                    - '_avg'      -> block-wise averaging (= arithmetic mean)
                    - '_max'      -> use maximum within t-box
                    - '_min'      -> use minimum within time-box
                    - '_median'   -> use median value within time-box
            params (dict, optional): Dictionary of filter parameters. Note that this depends on
                the chosen 'mode', i.e. not all parameters are required for every filter mode.
                Defaults to {'N': 10, 'pole': [0.9,0.3], 'smooth': 0.15, 'box_time': (5*60) },
                where the individual entries refer to:
                + 'N' (int): Filter length in case of 'FIR' or 'NL' modes.
                + 'pole' (float(s)): Pole(s) in case of 'IIR' modes.
                + 'smooth' (float): Relative distance between successive sample values to
                                    distinguish between "dynamic" and "smoothing" phases.
                + 'box_time' (float): Fixed time window in [s] in case of 'box_' modes.
            init (bool, optional): Switch to keep original values as long as filter is being
                filled in order to avoid ramp-up effects. Defaults to 'True'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_filtered'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' object (unless 'inplace' operation).

        Example:
            Using a "flexible pole" (i.e. toggeling between two significantly different
            forgetting factors) in order to preserve peaks while also apply smoothing in less
            dynamic phases. That is:
                y[n] = pole * y[n-1] + (1-pole) * x[n]
            where
                pole = val_smooth   if  (1-smooth)*y[n] <= x[n] <= (1+smooth)*y[n]
                pole = val_dynamic  else
            and
                0.0 < val_dynamic << val_smooth < 1.0
        """

        # check availability (Note: Done here in order to prevent checking in loops!)
        if (mode not in _FILTER_MODES):
            raise NotImplementedError(f"Unknown filtering '{mode}' specified")

        # init processing arrays
        arr_t, arr_x, _ = self.to_numpy(float)
        xf = np.zeros_like(self.df.x)

        # FIR types
        if (mode.startswith('FIR')):
            # init
            N = params['N']
            buffer = 0.0
            for k in range(N):
                buffer += arr_x[k]
                if (init):
                    xf[k] = arr_x[k]
                else:
                    xf[k] = buffer/(1+k)
            # main phase
            if (mode == 'FIR_LP_MA'):
                tmp = lfilter(np.ones(N), [1], arr_x)
                xf[N:] = (1./N) * tmp[N:]
            else:
                pass #TODO: implement more variants?

        # IIR types
        elif (mode.startswith('IIR')):

            if (mode == 'IIR_1pole'):
                pole = params['pole'][0]
                if (init):
                    xf, _ = lfilter([(1-pole)], [1,-pole], arr_x, zi=[pole*arr_x[0]])
                else:
                    xf = lfilter([(1-pole)], [1,-pole], arr_x)

            elif (mode == 'IIR_flexpole'):
                pole_smooth = params['pole'][0]
                pole_dynamic = params['pole'][1]
                smoothing_range = params['smooth']
                if (init):
                    xf[0] = arr_x[0]
                else:
                    xf[0] = pole_smooth*0.0 + (1-pole_smooth)*arr_x[0]
                for n in range(1, len(self)):
                    if (abs((arr_x[n]/xf[n-1])-1.0) <= smoothing_range):
                        xf[n] = pole_smooth*xf[n-1] + (1-pole_smooth)*arr_x[n]
                    else:
                        xf[n] = pole_dynamic*xf[n-1] + (1-pole_dynamic)*arr_x[n]
            else:
                pass #TODO: implement more variants?

        # NL types
        elif (mode.startswith('NL')):
            # init
            N = params['N']
            if (init):
                buffer = arr_x[0] * np.ones(N)
            else:
                buffer = np.zeros(N)
            # main phase
            for k in range(len(self)):
                for n in range(N-1):
                    buffer[n] = buffer[n+1]
                buffer[N-1] = arr_x[k]
                if (mode == 'NL_max'):
                    xf[k] = np.max(buffer)
                elif (mode == 'NL_min'):
                    xf[k] = np.min(buffer)
                elif (mode == 'NL_median'):
                    xf[k] = np.median(buffer)

        # box types
        elif (mode.startswith('box')):

            # init
            Tb = params['box_time']
            v = int(arr_t[0]/Tb) # boundaries w.r.t. *absolute* time -> large frame numbers!
            t_start = v * Tb
            t_end = t_start + Tb
            timebox = []
            k = 0

            # block processing w/ strict time checking
            for n, tn in enumerate(arr_t):

                # buffer samples in "timebox"
                if (tn < t_end):
                    timebox.append( arr_x[n] )
                    continue # with next sample

                # compute respective value...
                if (mode == 'box_avg'):
                    val = np.mean(timebox)
                elif (mode == 'box_max'):
                    val = np.max(timebox)
                elif (mode == 'box_min'):
                    val = np.min(timebox)
                elif (mode == 'box_median'):
                    val = np.median(timebox)
                else:
                    val = 0.0 #TODO: implement more variants? (e.g. weighted?)

                # ...and assign to whole timebox
                N_box = len(timebox)
                xf[k:k+N_box] = val * np.ones(N_box)

                # determine next frame (i.e. timebox of sample that has already been "touched")
                v = int(tn/Tb)

                # reset buffer & update counters
                timebox = [ arr_x[n] ]
                t_start = v * Tb
                t_end = t_start + Tb
                k += N_box

        # update or create new (filtered) object
        if (inplace):
            self.df.x = list(xf)
            if (not incognito):
                self.history.append(('@values_filter', f"mode='{mode}', params={params}"))
            return
        else:
            ts_out = self.clone(self.name+addon)
            ts_out.values_set(xf, incognito=True)
            if (not incognito):
                ts_out.history.append(('@values_filter', f"mode='{mode}', params={params}"))
            return ts_out


    def values_purge(self, mode='patch_local', params={'N': 3}, outliers=None,
                     incognito=False, inplace=True, addon='_purged'):
        """ Purges values of "outlier" samples (if any) acc. to 'mode' and 'params'.

        Args:
            mode (str, optional): Correction mode for outliers (if any). Defaults to
                'patch_local'. Available options:
                + 'remove'       -> delete outlier samples
                + 'patch_local'  -> patch outlier values by local average around position
                + 'patch_global' -> patch outliers by global mean value
            params (dict, optional): Parameters for correction (if required at all). Defaults
                to {'N': 3} where the individual entries refer to:
                + 'N' (int): (One-sided) width of local window to perform averaging
            outliers (list, optional): List of outlier samples w/ items (n, ts.t[n], ts.x[n]).
                Defaults to 'None' (i.e. automatic detection w/ default settings).
                Note: This allows to use a specific configuration of 'ts_find_outliers()'!
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_purged'.

        Returns:
            ts_out (:obj:): New 'TimeSeries' object (unless 'inplace' operation).
        """
        from zynamon.utils import find_outliers
        
        # init
        df_new = self.to_pandas()

        # perform outlier detection? (w/ default settings)
        if (outliers is None):
            outliers, _ = find_outliers(self)

        # handle all outlier values (if any)
        if (len(outliers)):

            if (mode == 'remove'):
                for item in outliers:
                    df_new.iloc[item[0]] = {_DF_TIME: np.nan, _DF_VALUE: np.nan}
                df_new.dropna(inplace=True)

            elif (mode == 'patch_local'):
                for item in outliers:
                    df_new.loc[item[0],_DF_VALUE] = local_val(self.df.x, item[0], params['N'], mode='avg')
                
            elif (mode == 'patch_global'):
                global_patch = self.df.x.mean()
                for item in outliers:
                    df_new.loc[item[0],_DF_VALUE] = global_patch                  

            else:
                raise NotImplementedError(f"Unknown outlier purge '{mode}' specified")

        # update or create new (filtered) object
        if (inplace):
            self.df = df_new
            if (not incognito):
                self.history.append(('@values_purge', f"mode='{mode}', params={params}"))
            return
        else:
            ts_out = self.clone(self.name+addon)
            ts_out.clear(keep_history=True)
            ts_out.samples_add(df_new, incognito=True)
            if (not incognito):
                ts_out.history.append(('@values_purge', f"mode='{mode}', params={params}"))
            return ts_out


    def values_set(self, new_values, incognito=False, inplace=True, addon='_'):
        """ Directly sets 'new_values' for all samples while keeping the time array.

        Note: Although this method may seem useless at first glance, it is in fact a convenience
        function that may come in handy when comparing modified value arrays of the same
        (original) time-series next to other modified versions (e.g. in the same plot).

        Args:
            new_values (list or np.ndarray): Array of values that should be used instead. Note
                that 'len(new_values)' has to match the current 'len(self.df.x)'!
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.
            inplace (bool, optional): Switch for in-place operation. Defaults to 'True'.
            addon (str, optional): String that will be appended to the original name of the
                time-series (*only* in case a new object is returned). Defaults to '_'.

        Returns:
            ts_out (:obj:): 'TimeSeries' object w/ new values (unless 'inplace' operation).
        """

        # check consistency
        if (len(new_values) != len(self)):
            raise ValueError(f"New values do not match size of existing array! {len(new_values)}")

        # directly replace sample values
        if (inplace):
            self.df.x = list(new_values)
            self.num_batches = 1
            if (not incognito):
                self.history.append(('@values_set', None))
            return
        else:
            ts_out = self.clone(self.name+addon)
            ts_out.values_set(list(new_values), incognito=True, inplace=True)
            # Note: No more settings required due to recursion (see above)) ;)
            return ts_out


    def tags_register(self, tags, overwrite=False, incognito=False):
        """ Adds one or more tags to internal meta data.

        Args:
            tags (dict): Dict of tags to be added as key-value pairs.
            overwrite (bool, optional): Switch to force updating of tag values if key already
                exists. Defaults to 'False'.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.

        Returns:
            --
        """
        existing = list(self.meta.keys())
        for key in list(tags.keys()):
            if (key in existing):
                if (overwrite):
                    self.meta[key] = tags[key]
                else:
                    print(f"Warning: Tag '{key}' already exists in meta data! (skipping)")
                    continue
            else:
                self.meta[key] = tags[key]
        if (not incognito):
            self.history.append(('@tags_register', list(tags.keys())))
        return


    def tags_delete(self, tags, incognito=False):
        """ Remove tag(s) under 'keys' from internal meta data (if present).

        Args:
            tags (list): List of tag keys that should be removed from time-series meta data.
            incognito (bool, optional): Switch to avoid history tracking. Defaults to 'False'.

        Returns:
            --
        """
        for key in list(tags):
            if (key in self.meta.keys()):
                del self.meta[key]
        if (not incognito):
            self.history.append(('@tags_delete', tags))
        return


    def to_numpy(self, type_t=None, type_x=None):
        """ Converts both _DF_TIME & _DF_VALUE columns to NumPy arrays (for heavy-lifting ;).

        Args:
            type_t (type or str, optional): Convert time array to any desired type supported by
                'zynamon.zeit.TimeSpec'. Defaults to 'None' (i.e. no conversion).
            type_x (type or str, optional): Convert value array.

        Returns:
            arr_t (np.array): NumPy array representation of 'self.df.t' (pandas Series).
            arr_x (np.array): NumPy array representation of 'self.df.x' (pandas Series).
            types (2-tuple): Original types of contents in time/value arrays (which may be
                required in order to enforce these after processing).
        """
        types = (self.get_type_t(), self.get_type_x())
        arr_t = self.df.t.to_numpy()
        arr_x = self.df.x.to_numpy()
        if (type_t is not None):
            arr_t = convert_time(arr_t, type_t)
        #
        #todo: conversion for values???
        #
        return arr_t, arr_x, types


    def to_pandas(self):
        """ Converts time-series to plain pandas 'DataFrame' type (e.g. for new objects).

        Returns:
            df_out (:obj:): Plain pandas 'DataFrame' object containing only columns _DF_TIME
                and _DF_VALUE (w/o any meta information).
        """
        df_out = self.df.copy()
        return df_out


    def export_to_file(self, fname=None, overwrite=False, combine=False, keep_history=False,
                       fmt='json'):
        """ Exports the 'TimeSeries' object to a text-based or binary-file.

        This method exports the 'TimeSeries' object to one of the file formats supported by
        'TS_SAVE_FORMATS'. This may be either:
            + JSON:     human readable / dictionary-like (text-based)
            + HDF5:     hierarchical data format (binary)
            + PK:       serialized, "pickled" Python object (binary)
        While the "core" data of the time-series is always stored, information on recent
        operations to the object are only kept if the respective switch is set 'True' as well.
        Note that such information is inherently stored if objects are "pickled" (PK).

        If desired, several 'TimeSeries' objects can be merged into a single file by using the
        'combine' option. This may be useful for the first import of data from CSV-files which
        contain more than one time-series data at once, since this will reflect the hierarchical
        assignment. However, for these scenarios, the following aspects have to be considered:
            (i) The calling application must ensure that 'fname' remains the same for all
                consecutive calls / objects to be stored
            (ii) Switch 'overwrite' has no effect, as file existence is managed internally
            (iii) Consequently, any existing files need to be deleted by the caller before!

        Moreover it needs to be emphasized that the function 'zynamon.imex.write_file()'
        PROVIDES A MUCH HIGHER SPEED FOR LARGE TIME-SERIES COLLECTIONS, since it avoids repeated
        open/write cycles on the files!

        Args:
            fname (str, optional): Desired name to be used for the export file. If none is
                given, this is created from the time-series' name. Defaults to 'None'.
            overwrite (bool, optional): Switch to overwrite existing files. Defaults to 'False'.
            combine (bool, optional): Switch to combine several time-series into one file.
                See above description for notes on usage. Defaults to 'False'.
            keep_history (bool, optional): Switch to keep information on operations on the
                time-series. Defaults to 'False'.
            fmt (str, optional): File format to be stored to w/ available options as in
                'TS_SAVE_FORMATS'. This will also be applied as extension. Defaults to 'json'.

        Returns:
            --
        """

        # core time-series information
        ts_item = _ts_to_dict(self, keep_history)

        # configure filename
        if (fname is None):
            ts_name = valid_str_name(self.name) # Note: This will remove special chars
            the_file = os.path.join(os.getcwd(), ts_name+'.'+fmt)
        else:
            the_file = fname

        # check consistency
        if (fmt not in TS_SAVE_FORMATS):
            raise NotImplementedError(f"Unknown file export type '{fmt}' specified")

        # write time-series to own/single file?
        if (not combine):
            if (os.path.isfile(the_file)):
                if (not overwrite):
                    raise FileExistsError(f"'TimeSeries' file '{the_file}' exists")
            if (fmt == 'json'):
                with open(the_file, mode='w') as jf:
                    json.dump(ts_item, jf, sort_keys=True, indent=_JSON_INDENT)
            elif (fmt in 'h5'):
                with h5py.File(the_file, mode='w') as hf:
                    _ts_to_h5grp(hf, ts_item)
            elif (fmt == 'pk'):
                with open(the_file, mode='wb') as pf:
                     itsme = self # HACK: Required to prevent "It's not the same object" error!
                     pk.dump(itsme, pf)

        # write combination of time-series?
        else:

            if (not os.path.isfile(the_file)): # -> start in 1st call
                if (fmt == 'json'):
                    with open(the_file, mode='w') as jf:
                        json.dump({ts_item['name']: ts_item}, jf, indent=_JSON_INDENT)
                elif (fmt in 'h5'):
                    with h5py.File(the_file, mode='w') as hf:
                        _ts_to_h5grp(hf, ts_item)
                elif (fmt == 'pk'):
                    with open(the_file, mode='wb') as pf:
                        pk.dump({self.name: self}, pf)

            else: # -> actual "combine" for any other times
                if (fmt == 'json'):
                    with open(the_file, mode='r+') as jf:
                        all_data = json.load(jf)
                        all_data[ts_item['name']] = ts_item
                        jf.seek(0)
                        json.dump(all_data, jf, sort_keys=True, indent=_JSON_INDENT)
                elif (fmt in 'h5'):
                    with h5py.File(the_file, mode='a') as hf:
                        _ts_to_h5grp(hf, ts_item)
                elif (fmt == 'pk'):
                    with open(the_file, mode='rb+') as pf:
                        all_data = pk.load(pf)
                        all_data[self.name] = self
                        pf.seek(0)
                        pk.dump(all_data, pf)

        return


    def export_pk(self, fname=None, overwrite=False, combine=False, keep_history=False):
        """ Exports the 'TimeSeries' object to a PK-file (Python "pickle").

        This is an alias method for 'export_to_file(fmt="pk")'. See respective base function
        for description of call signature.
        """
        self.export_to_file(fname, overwrite, combine, keep_history, fmt='pk')
        return


    def export_hdf5(self, fname=None, overwrite=False, combine=False, keep_history=False):
        """ Exports the 'TimeSeries' object to a HDF5-file.

        This is an alias method for 'export_to_file(fmt='h5')'. See respective base function
        for description of call signature.
        """
        self.export_to_file(fname, overwrite, combine, keep_history, fmt='h5')
        return


    def export_json(self, fname=None, overwrite=False, combine=False, keep_history=False):
        """ Exports the 'TimeSeries' object to a JSON-file.

        This is an alias method for 'export_to_file(fmt="json")'. See respective base function
        for description of call signature.
        """
        self.export_to_file(fname, overwrite, combine, keep_history, fmt='json')
        return
    

    def get_time_range(self):
        """ Returns numeric time range/span covered by whole array.

        Note: The result will only be meaningful if the time-series *is causal*. However, this
        is only assumed, but *not checked* by this method!
        """
        if (self.time.type == 'stamp'):
            return (self[-1].t - self[0].t)
        else:
            tmp = convert_time([self[0].t, self[-1].t], 'stamp')
            return (tmp[1] - tmp[0])


    def get_type_t(self, check_array=False):
        """ Returns type of DataFrame column _DF_TIME.

        Args:
            check_array (bool, optional): Switch to check whole array, otherwise only the first
                item is checked and this result is assumed for all. Defaults to 'False'.
        Returns:
            type_t (str): Time type found as an element of 'set(_TIME_TYPE.values())', i.e.
                'stamp_ns'|'stamp'|'iso'|'obj_dt'|'obj_pd'.
        """
        return self.time.type

        #fixme: old stuff, what was the purpose? -> delete?
        # # # get type of 1st time instant
        # # dummy = TimeSpec(self.df.t.iloc[0])

        # # check all other elements?
        # if (not check_array):
        #     return self.time.type
        # else:
        #     for item in self.df.t.iloc[1:]:
        #         dummy = TimeSpec(item)
        #         if (dummy.type != self.time.type):
        #             return None # i.e. array data not consistent
        #     return self.time.type


    def get_type_x(self, check_array=False):
        """ Returns type of DataFrame column _DF_VALUE.

        Args:
            check_array (bool, optional): Switch to check whole array, otherwise only the first
                item is checked and this result is assumed for all. Defaults to 'False'.

        Returns:
            type_x (str): Value type found as an element of 'set(_VALUE_TYPE.values())', i.e.
                'float'|'int'|'bool'|'str'.
        """

        # get type of 1st sample value
        type_x = _VALUE_TYPE[type(self.df.x.iloc[0])]

        # check all other elements?
        if (not check_array):
            return type_x
        else:
            for item in self.df.x.iloc[1:]:
                chk_type = type(item)
                if (chk_type != type_x):
                    return None # i.e. array data not consistent #fixme: what to do?
            return type_x


    def is_type_t(self, chk_type, check_array=False):
        """ Validates that DataFrame column _DF_TIME contains (only) values matching 'chk_type'.

        Args:
            chk_type (str): Type of values to be checked for in 'self.df.t' w/ options acc. to
                'set(_TIME_TYPE.values())' (can be provided by type or as string).
            check_array (bool, optional): Switch to check whole array, otherwise only the first
                item is checked and this result is assumed for all. Defaults to 'False'.
        Returns:
            res (bool): Result of type checking acc. to above settings.
        """

        # convert type to 'timespec' string (if required)
        if (type(chk_type) is type):
            chk_type = _TIME_TYPE[chk_type]

        # get existing type & compare w/ check
        the_type = self.get_type_t(check_array)
        if (the_type == chk_type):
            return True
        else:
            return False


    def is_type_x(self, chk_type, check_array=False):
        """ Validates that DataFrame column _DF_VALUE contains values matching 'chk_type'.

        Args:
            chk_type (str): Type of values to be checked for in 'self.df.x' w/ available
                options 'float'|'int'|'bool'|'str' (*must be* indicated as string).
            check_array (bool, optional): Switch to check whole array, otherwise only the first
                item is checked and this result is assumed for all. Defaults to 'False'.

        Returns:
            res (bool): Result of type checking acc. to above settings.
        """

        # get existing type & compare w/ check
        the_type = self.get_type_x(check_array)
        if (the_type == chk_type):
            return True
        else:
            return False


    def close(self):
        """ Deletes memory of objects. """
        del self.df
        return


#-----------------------------------------------------------------------------------------------


class TimeSpec():
    """ Basic time specification (e.g. used w/ class 'TimeSeries'). """
   
    def __init__(self, x=None):
        """ Initializes a 'TimeSpec' instance (i.e. an empty one or for input 'x').

        The main purpose of this class is to provide a unified handling fro the different ways
        of describing time contents by a *MAPPING* to the definitions acc. to '_TIME_TYPE'!

        Specification (str|type|example)                  => Description
        ----------------------------------------------------------------------------------------
        'stamp_ns'|int         |1657186852027276032       => Integer timestamp [ns], e.g. InfluxDB
        'stamp'   |float       |1657186852.027276         => POSIX timestamp [s], e.g. 'datetime'
        'iso'     |str         |'2022-10-20 19:02:44'     => String in default '_TS_ISO_FORMAT'
        'obj_dt'  |dt.datetime |dt.datetime(2025 [,...])  => Object 'dt.datetime' (w/ fields)
        'obj_pd'  |pd.Timestamp|Timestamp('2025-...')     => Object 'pd.Timestamp' (w/ fields)

        ...or...
        detailed formats e.g.  |'%y/%b/%d %H:%M:%S.%z'    => arbitrary string formats
        ----------------------------------------------------------------------------------------
        """

        # general attributes
        self.orig_type = None   # Python type of original input (e.g. pd.Series or list)
        self.type = None        # defined  type [str] ('stamp'|'stamp_ns'|'iso'|'obj_dt'|'obj_pd')
        self.fmt = ''           # detailed time format/precision [str] (only for 'iso' type)

        # array-specific attributes (only reasonable for associated array)
        self.Ts = None      # sampling interval [s] (will typically be averaged)
        self.scale = 1.0    # scaling factor [float]
        self.shift = 0.0    # temporal offset [float]
        self.stat = None    # advanced statistics [dict]
        # Note: The 'stat' is initialized to 'None' to indicate that no analysis has been done.

        # apply proper mapping on input 'x' (if already provided)
        if (x is not None):
            if ((type(x) in (int, float, dt.datetime, pd.Timestamp, # scalar data...
                             list, np.ndarray, pd.Series))          # ...array data...  
                or ((type(x) is str) and re.search(S_NUMBER, x))):  # ...or string w/ actual numbers
                self.from_data(x)
            
            elif ((x in _TIME_TYPE.keys())                             # 'x' matches some type
                  or ((type(x) is str) and (x in _TIME_TYPE.values())) # 'x' matches a "typename" string
                  or ((type(x) is str) and (True))):    # 'x' matches a string w/ detailed format ;) 
                self.from_param(x)

        return
    
    def __repr__ (self): # -> used for direct statement in console
        return f"TimeSpec '{self.type}' w/ fmt='{self.fmt}'"
    
    def __str__(self): # -> used for 'print()'
        return f"TimeSpec '{self.type}' w/ fmt='{self.fmt}'"

    def __eq__(self, other):
        """ Checks equality of own properties with those of 'other'. """
        return ((self.type == other.type) and (self.fmt == other.fmt)) 
    

    def get(self):
        """ Returns basic type/format (e.g. as "target" to enforce onto other objects). """
        if (self.fmt != ''):
            return self.fmt
        else:
            return self.type


    def set(self, scale=None, shift=None, Ts=None):
        """ Sets none or more parameters for the interpretation of the time array.
         
        Notes: 
        (1) Modifiers 'scale' and 'shift' should be exclusively set in this way!
        (2) Both of these values are applied "accumulatively", i.e.:
                any 'scale' will be *multiplied* w/ the existing one
                any 'shift' will be *added* to the existing one (using proper sign)
        (3) Setting 'Ts' through the method should only be used for imports (in order to avoid
            re-conversion operations in case of string-based time formats)

        Args: 
            scale (float, optional): Scaling factor (for compression of stretching of axis).
            shift (float, optional): Offset (for shifting to past/future time instants).
            Ts (float, optional): Sampling time as previously determined by a call to 
                'TimeSeries.time_analyse()'.

        Returns:
            --
        """       
        if (scale is not None):
            self.scale *= scale
        if (shift is not None):
            self.shift += shift   
        if (Ts is not None):
            self.Ts = Ts # hard over-write!
        return


    def from_param(self, t_par, check_known=False):
        """ Sets time specification acc. to a desired in 't_par' (i.e. either type or strings).

        Arg:
            t_par (type or str): Time specification to be set w/ possible ways of parametric 
                definition acc. to type|str|formatted string (see examples below).
            check_known (bool, optional): Switch to check if the provided format matches *any*
                known pattern, only applicable for 'iso'. Defaults to 'False'.

        Returns:
            --

        Note: If no other/detailed format is given 'TS_ISO_FORMAT' is used for string types/'iso'!

        Examples:
            (type)     't_par':   int       |float  |str  |dt.datetime
            (string)   't_par':   'stamp_ns'|'stamp'|'iso'|'obj_dt'|'obj_pd'
            (detailed) 't_par':   '%Y-%m-%d %H:%M:%S.%f' (acc. to ISO 8601 / RFC3339)
        """
        self.orig_type = type(t_par)

        # determine internal type
        if (self.orig_type is type):
            self.type = _TIME_TYPE[t_par]
        elif (t_par in set(_TIME_TYPE.values())):
            self.type = t_par
        elif (self.orig_type is str):
            self.type = 'iso'
        else:
            raise ValueError(f"Unknown parameter input '{t_par}'")

        # determine (detailed) format
        if (self.type == 'iso'):
            if ((t_par is str) or (t_par == 'iso')):
                self.fmt = TS_ISO_FORMAT
            else:
                if (check_known):
                    # try to match w/ known DATE patterns...
                    if ((_RX_SET_DATE_HYPH_Y4F_MNUM.match(t_par) is not None) or
                        (_RX_SET_DATE_HYPH_Y2F_MNUM.match(t_par) is not None) or
                        (_RX_SET_DATE_HYPH_Y4F_MNAME.match(t_par) is not None) or
                        (_RX_SET_DATE_HYPH_Y2F_MNAME.match(t_par) is not None) or
                        (_RX_SET_DATE_DASH_Y4F_MNUM.match(t_par) is not None) or
                        (_RX_SET_DATE_DASH_Y2F_MNUM.match(t_par) is not None) or
                        (_RX_SET_DATE_DASH_Y4F_MNAME.match(t_par) is not None) or
                        (_RX_SET_DATE_DASH_Y2F_MNAME.match(t_par) is not None)): # -> date ok
                        # ...then try to match w/ known TIME pattern / precision
                        if ((_RX_SET_TIME_USEC_DOT.search(t_par) is not None) or
                            (_RX_SET_TIME_USEC_COMMA.search(t_par) is not None) or
                            (_RX_SET_TIME_SEC.search(t_par) is not None) or
                            (_RX_SET_TIME_MIN.search(t_par) is not None)): # -> time ok
                            self.fmt = t_par
                        else:
                            raise ValueError(f"Unknown time pattern in '{t_par}'")
                    else:
                        raise ValueError(f"Unknown date pattern in '{t_par}'")
                else:
                    self.fmt = t_par # i.e. apply w/o checking
        else:
            self.fmt = ''

        return


    def from_data(self, t_dat):
        """ Sets time specification acc. to time data in 't_dat' (i.e. scalar or array).

        Args:
            t_dat (scalar or array): Data sample or array from which to derive the infomration. 
                For arrays, only the 1st item is analysed sicne assuming a "homogeneous" structure.

        Returns:
            --

        Examples:
            (scalar) 't_dat':   '2022-10-20 19:02'  or '2025-07-07T19:02:44.123456Z'
            (array)  't_dat':   [1657186852.027276, 1657188744.037128, ... ]
        """
        self.orig_type = type(t_dat)

        # get 1st element (= prototype) for further analysis
        if (self.orig_type in (list, np.ndarray)):
            t_chk = t_dat[0]
        elif (self.orig_type is pd.Series):
            t_chk = t_dat.iloc[0]
        else:
            if (self.orig_type is str):
                try:
                    t_chk = int(t_dat)
                except:
                    try:
                        t_chk = float(t_dat)
                    except:
                        t_chk = t_dat
            else:
                t_chk = t_dat
        # Note: Even if input data is a string, try to map it to a number (int? / float?).
        # This is done for more robust importing of CSV-data where read items may often be 
        # surrounded by superfluous '' or "" ;)

        # determine internal type
        if (type(t_chk) in (int, np.int64)): # Note: 'np.int32' can't hold 'stamp_ns' precision!
            self.type = 'stamp_ns'
        elif (type(t_chk) in (float, np.float32, np.float64)):
            self.type = 'stamp'
        elif (type(t_chk) in (dt.date, dt.datetime)):
              self.type = 'obj_dt'
        elif (type(t_chk) is pd.Timestamp):
            self.type = 'obj_pd'
        elif (type(t_chk) is str):
            if (t_chk.find('.') >= 0):
                try:
                    t_chk = float(t_chk)
                    self.type =  'stamp'
                except:
                    try:
                        t_chk = int(t_chk)
                        self.type =  'stamp_ns'
                    except:
                        self.type = 'iso'
            else: # if no decimal point
                try: 
                    t_chk = int(t_chk)
                    self.type =  'stamp_ns'
                except:
                    self.type = 'iso'
        else:
            raise ValueError(f"Unknown data input '{t_dat}'")

        # determine (detailed) format
        if (self.type == 'iso'):
            self.fmt = _infer_iso_format_from_data_str(t_chk)
        else:
            self.fmt = ''

        return


    # def force_spec(self, ts):
    #     """ Force same TimeSpec as represented by 'self' onto TimeSeries 'ts'.

    #     Args:
    #         ts (:obj:): TimeSeries object ("slave").

    #     Returns:
    #         ts_mod (:obj:): Output object w/ converted time representation (if required).
    #     """

    #     if (self == ts.time):
    #         return ts
    #     else: # i.e. time-specs are different
    #         if (self.fmt != ''):
    #             return convert_time(ts, self.fmt)
    #         else:
    #             return convert_time(ts, self.type)   



#-----------------------------------------------------------------------------------------------
# PRIVATE FUNCTIONS (only to be used from internal methods, but not to be exposed!)
#-----------------------------------------------------------------------------------------------

def _infer_iso_format_from_data_str(t_str):
    """ todo 
    
    Note: Although the (powerful) pandas call 'pd.to_datetime(t_str, format='ISO8601)' works
    perfectly, it will *NOT* provide information on the actually used format.

    Args:
        todo

    Returns:
        todo
    """

    full_fmt = ''

    # step 1: try to match w/ known DATE patterns
    if (_RX_DAT_DATE_HYPH_Y4F_MNUM.match(t_str) is not None):
        fmt_date = '%Y-%m-%d'
    elif (_RX_DAT_DATE_HYPH_Y2F_MNUM.match(t_str) is not None):
        fmt_date = '%y-%m-%d'
    elif (_RX_DAT_DATE_HYPH_Y4F_MNAME.match(t_str) is not None):
        fmt_date = '%Y-%b-%d'
    elif (_RX_DAT_DATE_HYPH_Y2F_MNAME.match(t_str) is not None):
        fmt_date = '%y-%b-%d'
    elif (_RX_DAT_DATE_DASH_Y4F_MNUM.match(t_str) is not None):
        fmt_date = '%Y/%m/%d'
    elif (_RX_DAT_DATE_DASH_Y2F_MNUM.match(t_str) is not None):
        fmt_date = '%y/%m/%d'
    elif (_RX_DAT_DATE_DASH_Y4F_MNAME.match(t_str) is not None):
        fmt_date = '%Y/%b/%d'
    elif (_RX_DAT_DATE_DASH_Y2F_MNAME.match(t_str) is not None):
        fmt_date = '%y/%b/%d'
    elif (_RX_DAT_DATE_DASH_Y4L_MNUM.match(t_str) is not None):
        fmt_date = '%d/%m/%Y'
    elif (_RX_DAT_DATE_DASH_Y2L_MNUM.match(t_str) is not None):
        fmt_date = '%d/%m/%y'
    else:
        fmt_date = ''        
    # Note: The last one actually cannot be reached since "all-two-digits" formats may
    # be mixed up --> i.e. 'yy/mm/dd' ~ 'dd/mm/yy'!
     
    # step 2: try to match w/ known TIME pattern & precision           
    if (_RX_DAT_TIME_USEC_DOT.search(t_str) is not None):
        fmt_time = '%H:%M:%S.%f'
    elif (_RX_DAT_TIME_USEC_COMMA.search(t_str) is not None):
        fmt_time = '%H:%M:%S,%f'
    elif (_RX_DAT_TIME_SEC.search(t_str) is not None):
        fmt_time = '%H:%M:%S'
    elif (_RX_DAT_TIME_MIN.search(t_str) is not None):
        fmt_time = '%H:%M'
    else:
        fmt_time = ''

    # step 3: combining things...
    if ((fmt_date == '') or (fmt_time == '')):
        sep = '' # no separator required
    elif ('T' in t_str):
        sep = 'T'
    else:
        sep = ' '
    full_fmt = fmt_date + sep + fmt_time
    # Note that the above data and/or time detection allows for both "date-only" 
    # ('2022-10-08') as well as "time-only" ('12:07:32') formats to be ingested...

    # step 4: handling of time-zones
    if (_RX_DAT_TZONE.search(t_str) is not None):
        full_fmt += '%z'
    elif (_RX_DAT_TZONE_COLONS.search(t_str) is not None):
        full_fmt += '%z'
    elif (t_str[-1] == 'Z'):
        full_fmt += '%Z' # catch & signal special "zulu" notation
    else:
        pass

    return full_fmt


def _ts_to_dict(ts, keep_history=False):
    """ Creates a dict item out of a 'TimeSeries' object (e.g. for storing to JSON-files).

    Args:
        ts (:obj:): 'TimeSeries' object from which to create a dict item w/ core information.
            Note that this excludes information that can be recreated once again.
        keep_history (bool, optional): Switch to keep information on operations on the
            time-series. Defaults to 'False'.

    Returns
        ts_item (dict): Corresponding dict (item).
    """

    ts_item = {
        'name': ts.name,
        'arr_t': list(ts.df.t),
        'arr_x': list(ts.df.x),
        'meta': ts.meta,
        # 'time': vars(ts.time), #fixme: will not work due to types (e.g. in 'orig_type'!)
        'time': {
            'type': ts.time.type,
            'fmt': ts.time.fmt,
            'Ts': ts.time.Ts,
            'shift': ts.time.shift,
            'scale': ts.time.scale,
            #'stat': None, # fixme: or don't use?
            } 
    }  

    if (keep_history):
        ts_item['num_batches'] = ts.num_batches
        ts_item['history'] = ts.history

    return ts_item


def _ts_to_h5grp(hf, ts_item):
    """ Creates a group inside an HDF5-file for representing a 'TimeSeries' object.

    This convenience function just "bundles" the necessary writing operations for the HDF5-file.
    Special care needs to be taken for 'str' types in the 'df' arrays, since they have to be
    converted to 'bytes'. All operations are based on a previous conversion to the 'ts_item'
    acc. to the details of '_ts_to_dict()'.

    Args:
        hf (:obj:): Opened HDF5-file.
        ts_item (dict): A dictionary item representing the 'TimeSeries' object.

    Returns
        --
    """

    ts_grp = hf.create_group(name=ts_item['name'])
    for key in ts_item.keys():
        if (key in ('arr_t','arr_x')):
            if (type(ts_item[key][0]) is str):
                data_arr = [ s.encode(_HDF5_STR_ENC, errors='ignore') for s in ts_item[key] ]
            else:
                data_arr = ts_item[key]
            ts_grp.create_dataset(name=key, data=data_arr, chunks=True, compression='gzip',
                                  compression_opts=_HDF5_ZIP_LEVEL, shuffle=_HDF5_SHUFFLE)
        elif (key in ('name','num_batches')):
            ts_grp.attrs[key] = ts_item[key]
        elif (key in ('meta','time')):
            sub_dict = ts_grp.create_group(name=key)
            for k,v in ts_item[key].items():
                sub_dict.attrs[k] = str(v)
        elif (key in ('history')):
            sub_list = ts_grp.create_group(name=key)
            for n, item in enumerate(ts_item[key]):
                sub_list.attrs[str(n)] = str(item)

    return


def _ts_from_dict(ts_item):
    """ Recreates a 'TimeSeries' object from dict item.

    Args:
        ts_item (dict): A dictionary representing the former (core) 'TimeSeries' object as
            typically read from JSON-files. If information on previous operations has been saved
            previously, this data will be enforced as well (see "_ts_to_dict()" for details).

    Returns:
        ts (:obj:): Recreated 'TimeSeries' object.
    """

    # recreate core data (arrays & additional time parameters)
    ts = TimeSeries(ts_item['name'], tags=ts_item['meta'])
    ts.samples_add(zip(ts_item['arr_t'], ts_item['arr_x']), analyse=True)
    # Note: Above call has implicitly created the proper 'TimeSpec'!
    if ('time' in ts_item.keys()):
        for k,v in ts_item['time'].items():
            if (k in ('Ts','shift','scale')): 
                eval(f"ts.time.set({k}={v})")                
    # else: #fixme?
    #     # raise ValueError("No proper time information found in dict item")
    
    # enforce additional, historic information (if present)
    if ('num_batches' in ts_item.keys()):
        ts.num_batches = ts_item['num_batches']
    if ('history' in ts_item.keys()):
        ts.history = []
        for n, item in enumerate(ts_item['history']):
            ts.history.append(tuple(item))

    return ts


def _ts_from_h5grp(ts_item):
    """ Recreates a 'TimeSeries' object from a corresponding group in a HDF5 file.

    Args:
       ts_item (:obj:): A group of an opened HDF5-file, representing 'TimeSeries' data (e.g.
           from a previous saving operation).

    Returns:
        ts (:obj:): Recreated 'TimeSeries' object.
    """

    # decode HDF5 datasets to useable arrays
    if (type(ts_item['arr_t'][0]) is bytes):
        time_arr = [ b.decode(_HDF5_STR_ENC, errors='ignore') for b in ts_item['arr_t'] ]
    else:
        time_arr = np.array( ts_item['arr_t'] )
    if (type(ts_item['arr_x'][0]) is bytes):
        data_arr = [ b.decode(_HDF5_STR_ENC, errors='ignore') for b in ts_item['arr_x'] ]
    else:
        data_arr = np.array( ts_item['arr_x'] )

    # Note: The 'h5py._hl.dataset.Dataset' should either refer to a NumPy-like array (default)
    # or to a 'bytes' from which the original string (as "char-array") needs to be recreated!

    # recreate core data (dict structures)
    meta_dict = {}
    for k,v in ts_item['meta'].attrs.items():
        meta_dict[k] = v
    time_dict = {}
    for k,v in ts_item['time'].attrs.items():
        if (k in ('Ts','scale','shift')):
            time_dict[k] = float(v)

    # recreate core data (arrays & additional time parameters)
    ts = TimeSeries(ts_item.attrs['name'], tags=meta_dict)
    ts.samples_add(zip(time_arr, data_arr), analyse=True)
    for k,v in time_dict.items():
        eval(f"ts.time.set({k}={float(v)})")

    # enforce additional, historic information (if present)
    if ('num_batches' in ts_item.attrs.keys()):
        ts.num_batches = ts_item.attrs['num_batches']
    if ('history' in ts_item.keys()):
        ts.history = []
        for n, (k,v) in enumerate(ts_item['history'].attrs.items()):
            ts.history.append(eval(v))

    return ts


#-----------------------------------------------------------------------------------------------
# MODULE FUNCTIONS
#-----------------------------------------------------------------------------------------------

def istimeseries(obj, accept_type=True):
    """ Checks whether 'obj' is a 'TimeSeries' object and/or the respective type itself.

    Args:
        obj (:obj:): Object (or type) of class 'TimeSeries'.
        accept_type (bool, optional): Switch to indicate that 'obj' may also refer to the *type*
            'class TimeSeries' rather than directly being an object. Defaults to 'True'.

    Returns:
        res (bool): Result of check.
    """
    if (isinstance(obj, TimeSeries)):
        return True
    elif (accept_type and (str(obj).find('zynamon.zeit.TimeSeries') >= 0)):   
        return True
    else:
        return False


def convert_time(t_in, target, factor=None, offset=None):
    """ Converts 't_in' to the given 'target' (w/ optional 'factor' and 'offset').

    Input 't_in' will typically refer to a time array; however, scalar inputs are also handeled
    in the same way (e.g. for representing time intervals). The function works in a "lazy" way,
    trying to avoid conversion work if not required and may thus return quickly if no changes
    apply. Modifications on a time array may be enforced by using the 'factor' (multiplicative)
    and 'offset' (additive) options.

    Notes:
    (1) Modifications (factor / offset) are only available for 'stamp'-type inputs!
    (2) For more information on 'TimeSeries' time formats, refer to 'zynamon.zeit.TimeSpec'.

    Args:
        t_in (array or scalar): Input time value(s). For speed & simplicity, all elements are
            assumed to be of same type such that case-switching needs to be done only once.
        target (scalar): Desired time specification.
        factor (float, optional): Scaling factor for stretching (> 1.0) or squeezing (< 1.0)
            consecutive samples along the time axis. Defaults to 'None'.
        offset (scalar, optional): Additional offset that can be given in *any format* supported
            by 'zynamon.zeit.TimeSpec' and which shall be applied to all array elements before
            conversion (but *after* factor). Defaults to 'None'.

    Returns:
        t_out (list): Array of properly converted time values.
    """

    # determine specifications of input & desired output
    src = TimeSpec(t_in)
    tgt = TimeSpec(target)
    if (src.orig_type is str):
        scalar_input = True
    else:
        try:
            len(t_in)
            scalar_input = False
        except:
            scalar_input = True

    # ensure consistency of scaling & offset (only for 'stamp'/'stamp_ns' inputs)
    off, fac = 0.0, 1.0
    if ((src.type == 'stamp') or (src.type == 'stamp_ns')):
        if (factor is not None):
            try:
                fac = float(factor)
            except:
                raise ValueError(f"Unknown scaling {factor} specified!")
        if (offset is not None):
            try:
                off = convert_time(offset, 'stamp')
            except:
                raise ValueError(f"Unknown offset {offset} specified!")
    # Note: For any other source type, these settings (if any) are ignored!

    # "laziness checks" (i.e. bypass if actually nothing to do ;)
    if (src.type == tgt.type):
        if ((tgt.type in ('stamp', 'stamp_ns')) and (off == 0.0) and (fac == 1.0)):
            return t_in
        elif ((tgt.type == 'iso') and (src.fmt == tgt.fmt)):
            return t_in
        elif (tgt.type in ('obj_dt', 'obj_pd')):
            return t_in
        else:
            pass

    # init conversion (i.e. use temporary lists for consistent processing)
    t_out = []
    if (scalar_input):
        t_in = [t_in]

    # convert to desired output type
    if (src.type == 'stamp'):
        for tn in t_in:
            tmp = tn*fac + off
            if (tgt.type == 'stamp'):
                t_out.append( tmp )
            elif (tgt.type == 'stamp_ns'):
                t_out.append( int(1e9*tmp) )
            elif (tgt.type == 'iso'):
                obj = pd.Timestamp(1e9*tmp)
                t_out.append( obj.strftime(tgt.fmt) )
            elif (tgt.type == 'obj_dt'):
                t_out.append( dt.datetime.fromtimestamp(tmp, tz=dt.timezone.utc) )
            elif (tgt.type == 'obj_pd'):
                t_out.append( pd.Timestamp(1e9*tmp) )

    elif (src.type == 'stamp_ns'):
        for tn in t_in:
            tmp = (float(tn)/1e9)*fac + off
            if (tgt.type == 'stamp'):
                t_out.append( tmp )
            elif (tgt.type == 'stamp_ns'):
                t_out.append( int(1e9*tmp) )
            elif (tgt.type == 'iso'):
                obj = pd.Timestamp(1e9*tmp)
                t_out.append( obj.strftime(tgt.fmt) )
            elif (tgt.type == 'obj_dt'):
                t_out.append( dt.datetime.fromtimestamp(tmp, tz=dt.timezone.utc) )
            elif (tgt.type == 'obj_pd'):
                t_out.append( pd.Timestamp(1e9*tmp) )

    elif (src.type == 'iso'):
        for tn in t_in:
            # handle & suppress special "zulu" time zone (if required)
            if (src.fmt.endswith('%Z')):
                try:
                    tmp = pd.to_datetime(tn[:-1], format=src.fmt[:-2]) # i.e. remove 'Z'
                except:
                    # we have mixed formats?!?
                    tmp = pd.to_datetime(tn) ##, format='mixed')
            else:
                try:
                    tmp = pd.to_datetime(tn, format=src.fmt)
                except: 
                    # we have mixed formats?!?
                    tmp = pd.to_datetime(tn) ##, format='mixed')
            #
            # quick hack as work-around 
            #   -> the above is not nice, as we don't know what's going on! :( 
            #   -> better approach would be to explicitly allow a "mixed-format approach"
            #

            # normal data conversion
            if (tgt.type == 'stamp'):
                t_out.append( tmp.timestamp() )
            elif (tgt.type == 'stamp_ns'):
                t_out.append( int(1e9*tmp.timestamp()) )
            elif (tgt.type == 'iso'):
                t_out.append( tmp.strftime(tgt.fmt) )
            elif (tgt.type == 'obj_dt'):
                t_out.append( dt.datetime.fromtimestamp(tmp.timestamp(), tz=dt.timezone.utc) )
            elif (tgt.type == 'obj_pd'):
                t_out.append( tmp )

    elif (src.type == 'obj_dt'):
        for tn in t_in:
            tmp = tn
            if (tgt.type == 'stamp'):
                t_out.append( tmp.timestamp() )
            elif (tgt.type == 'stamp_ns'):
                t_out.append( int(1e9*tmp.timestamp()) )
            elif (tgt.type == 'iso'):
                t_out.append( tmp.strftime(tgt.fmt) )
            # elif (tgt.type == 'obj_dt'):
            #     t_out.append( tmp ) 
            elif (tgt.type == 'obj_pd'):
                t_out.append( pd.Timestamp(tmp) )
       
    elif (src.type == 'obj_pd'):
        for tn in t_in:
            tmp = tn
            if (tgt.type == 'stamp'):
                t_out.append( tmp.timestamp() )
            elif (tgt.type == 'stamp_ns'):
                t_out.append( int(1e9*tmp.timestamp()) )
            elif (tgt.type == 'iso'):
                t_out.append( tmp.strftime(tgt.fmt) )
            elif (tgt.type == 'obj_dt'):
                t_out.append( dt.datetime.fromtimestamp(tmp.timestamp(), tz=dt.timezone.utc) )
            # elif (tgt.type == 'obj_pd'):
            #     t_out.append( tmp )

    # Note: Missing/commented branches are already covered by the "laziness checks" above! ;)
    
    # return output (matching to input type/shape)
    if (src.orig_type is pd.Series):
        return pd.Series(t_out) # Note: This will inherently convert 'obj_dt' type to 'obj_pd'
    elif (src.orig_type is np.ndarray):
        return np.array(t_out)
    elif (scalar_input):
        return t_out[0]
    else:
        return t_out



#===============================================================================================
#===============================================================================================
#===============================================================================================

#%% MAIN
if __name__ == "__main__":
    print("This is the 'zynamon.zeit' module.")
    print("See 'help(zynamon.zeit)' for proper usage.")



################################################################################################
# EXPLANATIONS
################################################################################################
#
# (1) General difference between 'pandas' vs. 'zynamon' methods:
#           pandas.core.frame.DataFrame     -> creates NEW object (per default)
#           zynamon.zeit.TimeSeries         -> works IN-PLACE (per default)
#
#  Overview for 'zynamon.zeit.TimeSeries':
#
# .clear            = (fixed) inplace
# .copy             = (fixed) create NEW object
#
# .samples_add      = (fixed) inplace
# .samples_crop     = inplace
# .samples_pack     = inplace
# .samples_unique   = inplace
#
# .time_align       = inplace
# .time_analyse     = (fixed) inplace
# .time_causalise   = inplace
# .time_convert     = (fixed) inplace
# .time_reset       = (fixed) inplace
#
# .values_filter    = inplace
# .values_purge     = inplace
# .values_set       = inplace
#
#
# (2) Format Codes for 'strftime()' and 'strptime()'
# [ https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior ]
#
#   %Y      Year with century as a decimal number.              0001, …, 2013, 2014, …, 9999
#   %y      Year w/o century as a zero-padded decimal number.   00, 01, …, 99
#   %m      Month as a zero-padded decimal number.              01, 02, …, 12
#   %d      Day of the month as a zero-padded decimal number.   01, 02, …, 31
#
#
#   %H      Hour (24-hour) as a zero-padded decimal number.     00, 01, …, 23
#   %M      Minute as a zero-padded decimal number.             00, 01, …, 59
#   %S      Second as a zero-padded decimal number.             00, 01, …, 59
#   %f      Microsecond as a decimal number, zero-padded.       000000, 000001, …, 999999
#
#   %b      Month as locale’s abbreviated name.                 Jan, Feb, …, Dec (en_US)
#                                                               Jan, Feb, …, Dez (de_DE)
#
#   %a      Weekday as locale’s abbreviated name.               Sun, Mon, …, Sat (en_US)
#                                                               So, Mo, …, Sa (de_DE)
#
#   %A      Weekday as locale’s full name.                      Sunday, Monday, …, Sat. (en_US)
#                                                               Sonntag, Montag, …, Sam. (de_DE)
#
################################################################################################