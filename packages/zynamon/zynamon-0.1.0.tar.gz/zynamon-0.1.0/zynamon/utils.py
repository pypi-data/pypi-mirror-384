"""
Utility functions for 'TimeSeries' objects, e.g. import scripts and operators for two objects.
"""

import numpy as np

from zynamon.zeit import convert_time, TS_SAVE_FORMATS
from zdev.core import local_val
from zdev.parallel import duration_str

# todo --> check if "istimeseries" is really required here? where to put check for colelctions?

# EXPORTED DATA
TS_OPERATIONS = {
    '+': '__plus__', # added
    '-': '__minus__', # subtracted
    '*': '__times__', # multiplied
    '/': '__over__' # divided
 }

# INTERNAL PARAMETERS & DEFAULTS
# n/a


def list_of_segments(ts, seg_def):
    """ Creates a list of consistent 'segments' for block-wise processing functions.

    This is a robust convenience function, ensuring that all segments based on 'seg_def' are
    wrapped in a valid list for consumption by 'TimeSeries.samples_crop()'. Hence, it will 
    typically be used to prepare calculations operating on several different blocks of time.
    Segments can be defined in any format supported by 'zynamon.TimeSpec()' as follows:
        scalar              -> single limit, i.e. interval "from the end"
        2-tuple             -> interval limits [A,B] within the time-series
        list of segments    -> list of limits (i.e. scalars / intervals may be mixed)

    Args:
        ts (:obj:): TimeSeries object from which segments are to be used.
        seg_def (various): Definition of segments to be extracted from 'ts'.

    Returns:
        seg_list (list): Consistent list of segments (for cropping).

    Examples: Segment definition vs. interpretation by 'TimeSeries.samples_crop()'
              (Note: First two cases employ "direct indexing"!)

        'seg_def':                                  | Resolved intervals:
        ---------------------------------------------------------------------------------------
        1000                                        | [*now*-1000, *now*]
        [200, 300, 500]                             | [*now*-200,*now*], [*now*-300,*now*],
                                                      [*now*-500,*now*]
        ['2022-04-07 12:10','2022-04-07 12:30']     | ['2022-04-07 12:10', *now*],
                                                      ['2022-04-07 12:30', *now*]
        [['2022-04-07 12:10','2022-04-07 12:30']]   | ['2022-04-07 12:10', '2022-04-07 12:30']
        [datetime.datetime(2022, 4, 7, 12, 21, 24), | ['2022-04-07 12:21:24', *now*],
         ['2022-04-07 12:10', 1649334600.0]]          ['2022-04-07 12:10','2022-04-07 12:30']
        ----------------------------------------------------------------------------------------
    """
    from zynamon.zeit import _TIME_TYPE

    # (single) scalar limit
    if (type(seg_def) not in (list,tuple)):
        if (type(seg_def) not in _TIME_TYPE.keys()):
            raise ValueError("Wrong definition of scalar limit! {seg_def}")
        else:
            seg_list = [seg_def]

    # (single) interval limit
    elif ((len(seg_def) == 2) and
          (type(seg_def[0]) not in (list,tuple)) and (type(seg_def[1]) not in (list,tuple))):
        if ((type(seg_def[0]) not in _TIME_TYPE.keys()) or (type(seg_def[1]) not in _TIME_TYPE.keys())):
            raise ValueError(f"Wrong definition of interval limits! {seg_def}")
        else:
            seg_list = seg_def

    # list of scalar or interval limits (Note: Entries may be mixed!)
    else:
        for s, seg in enumerate(seg_def):
            if (type(seg) not in (list,tuple)):
                if (type(seg) not in _TIME_TYPE.keys()):
                    raise ValueError("Wrong definition of segments!")
            elif (len(seg) != 2):
                raise ValueError(f"Wrong definition of segments! {seg}")
            elif ((type(seg[0]) not in _TIME_TYPE.keys()) or (type(seg[1]) not in _TIME_TYPE.keys())):
                raise ValueError(f"Wrong definition of segments! {seg}")
        seg_list = seg_def

    return seg_list   


def find_in_history(ts, operation):
    """ Checks whether 'operation' has been applied in the past of 'ts' and returns entries.

    Note that not all time-series operations are stored to the history, but only the ones
    "actually modifying". For more info on the individual operations see "zynamon.zeit".

    Args:
        ts (:obj:): TimeSeries object to investigate.
        operation (str): Operation to be checked for in the history. Available options:
            'samples_'  +   'add'| 'crop' | 'pack' | 'unique'
            'time_'     +   'align' | 'causalise' | 'convert' | 'reset'
            'values_'   +   'filter' | 'purge' | 'set'
            'tags_'     +   'register' | 'delete'

    Returns:
        res (bool): Confirmation if 'operation' had been applied in the past.
        idx (list): List containing the indices of all matching operations (if any, else []).
    """
    chk = []
    for n, item in enumerate(ts.history):
        if (item[0] == f'@{operation}'):
            chk.append((n, item[1]))
    return chk


#todo: Use the following as easy-to-read abbreviations for common operations?!?!?

def is_filtered(ts):
    return (len(find_in_history(ts, 'values_filter')) > 0)

# def is_modified_in_value(ts):
#     return (ts_find_in_history(ts, 'values_filter')[0]
#             or ts_find_in_history(ts, 'values_purge')[0]
#             or ts_find_in_history(ts, 'values_set')[0])

# def is_time_altered(ts):
#     return (ts_find_in_history(ts, 'time_align')[0]
#             or ts_find_in_history(ts, 'time_causalise')[0])


def find_outliers(ts, cmp_with='avg', excess_mode='relative', params={'N': 10, 'excess': 0.3}):
    """ Detects possible outliers in 'ts' acc. to 'mode' and detection 'params'.

    Args:
        ts (:obj:): 'TimeSeries' object for which to identify outliers.
        cmp_with (str, optional): Computation of comparison level within a sliding window of
            2*N+1 samples centered around current instant (non-causal!). Defaults to 'avg'.
            Avilable options are 'avg'|'max'|'min'|'sum'|'median' as provided by the options 
            of function 'zdev.core.local_val()'.
        excess_mode (str, optional): Mode of comparing the "excess" of outliers against the 
            computed level as either 'relative' or 'absolute'. Defaults to 'relative'.
        params (dict, optional): Parameters for tuning the detection. Defaults to
            {'N': 10, 'excess': 0.3} where the individual entries refer to:
            + 'N' (int): (one-sided) width for computation of comparison level
            + 'excess' (float): Depending on the corresponding mode, this is either
                -> a factor for how much a value has to exceed or fall short w.r.t. its 
                   surrounding to be declared as outlier (if 'relative')
                -> or an absolute distance to the computed comparison level (if 'absolute')

    Returns:
        outliers (list): List of all outlier samples w/ 3-tuple items as (n, ts.t[n], ts.x[n]).
        cmp (:obj:): Comparator object ('TimeSeries' w/ same time array).

    Example: If comparison is done w.r.t. value 'cmp[n] = 3.0' (computed by either 'cmp_with'
             mode) and if a 'relative' mode was chosen w/ a factor 'excess' = 1.0, 
             i.e. any "outliers" are required to be 100% larger or smaller, then:

                                | x[n] - cmp[n] |
             Definition:  xs := -----------------
                                    | x[n] |

             Case 1: x[n] > cmp[n]
                 x[n] = 4.5  --> xs[n] = 0.5  (ok)
                 x[n] = 6.10 --> xs[n] ~ 1.03 (outlier! -> value more than twice 'cmp')

             Case 2: x[n] < cmp[n]
                 x[n] = 1.5  --> xs[n] = 0.5  (ok)
                 x[n] = 1.49 --> xs[n] ~ 1.01 (outlier! -> 'cmp' more than twice the value)
    """

    # create comparator
    cmp = ts.clone(ts.name+'_cmp_'+cmp_with)    
    tmp = np.zeros(len(ts))
    for k in range(len(ts)):
        tmp[k] = local_val(ts.df.x, k, params['N'], mode=cmp_with)
    cmp.values_set(tmp)

    # find & collect outlier samples
    outliers = []
    if (excess_mode == 'relative'):
        for n in range(len(ts)):
            xs = abs(ts[n].x - cmp[n].x) / abs(cmp[n].x)
            if (xs >= params['excess']):
                outliers.append((n, ts[n].t, ts[n].x))
    else: # threshold == 'absolute'
        for n in range(len(ts)):
            xs = abs(ts[n].x - cmp[n].x)
            if (xs >= params['excess']):
                outliers.append((n, ts[n].t, ts[n].x))

    return outliers, cmp


def cohere(ts1, ts2, res=None, mode='avg'):
    """ Cohere 'ts1' and 'ts2', i.e. determine & pack to a common time basis.

    This function brings two different time-series to a common, equidistant time reference. As
    such, it is used as an inherent pre-processing step for most arithmetic operations, since
    arbitrary time-series may generally exhibit different time references and/or even gaps in
    samples.

    Args:
        ts1 (:obj:): First time-series.
        ts2 (:obj:): Second time-series.
        res (float, optional): Desired common resolution (if specified). Note that this will 
            only be  applied if the sampling intervals of both 'ts1' and 'ts2' are below that
            value. Otherwise the (integer) maximum of the sampling intervals is used which is
            also the default behaviour. Defaults to 'None'.
        mode (str, optional): Desired aggregation mode for the time-series w/ options:
            'avg'|'max'|'min'|'median' (see 'TimeSeries.samples_pack()' for details). 
            Defaults to 'avg'.

    Returns:
        ts1_coherent (:obj:): Packed version of 'ts1' w/ time matching 'ts2_coherent'.
        ts2_coherent (:obj:): Packed version of 'ts2' w/ time matching 'ts1_coherent'.
    """

    # update sampling infos
    ts1.time_analyse()
    ts2.time_analyse()

    # determine common ("coherent") sampling basis
    if ((res is not None) and ((res >= ts1.time.Ts) and (res >= ts2.time.Ts))):
        Ts_max = None
        Ts_res = res
    else: # (res is None)        
        Ts_max = max(ts1.time.Ts, ts2.time.Ts)
        Ts_res = int(Ts_max)+1 # round to next integer [s]

    # check if already coherent w/ desired rate (if specified)
    if ((ts1.time.stat['quality'] == ts2.time.stat['quality'] == 'equidistant') and
        ((res is not None) and (ts1.time.Ts == ts2.time.Ts == res))):
        ts1_coh = ts1.clone()
        ts2_coh = ts2.clone()
    else:
        # pack / resample time-series
        ts1_coh = ts1.samples_pack(Ts_res, mode, inplace=False)
        ts2_coh = ts2.samples_pack(Ts_res, mode, inplace=False)

    return ts1_coh, ts2_coh, Ts_res


def relate(ts1, ts2, op, res=None, mode='avg'):
    """ Apply sample-wise 'operation' (e.g. '+'|'-'|'*'|'/') onto time-series 'ts1' and 'ts2'.

    Args:
        ts1 (:obj:): First time-series operand, will be made coherent with 2nd one.
        ts2 (:obj:): Second time-series operand, will be made coherent with 1st one.
        op (str): Operation to be applied sample-wise for each matching time instant of coherent
            versions of 'ts1' and 'ts2' w/ available options '+'|'-'|'*'|'/'.
        res (float, optional): Desired common resolution (if any). Note that this will only be
             applied if the sampling intervals of both 'ts1' and 'ts2' are below that value.
             Otherwise the (integer) maximum of the sampling intervals is used as resolution
             which is also the default setting (for 'None').
        mode (str, optional): Desired aggregation mode for the time-series w/ options 'avg'|
            'max'|'min'|'median' (see 'TimeSeries.samples_pack' for details). 
            Defaults to 'avg'.

    Returns:
        ts_op (:obj:):
    """

    # check consistency
    if (op not in TS_OPERATIONS.keys()):
        raise NotImplementedError("Unknown time-series operation {op}")

    # prepare inputs (i.e. ensure coherence & extract processing arrays)
    ts1c, ts2c, _ = cohere(ts1, ts2, res, mode)
    at1, ax1, _ = ts1c.to_numpy()
    at2, ax2, _ = ts2c.to_numpy()

    # prepare output
    ts_op = ts1c.clone(ts1.name+TS_OPERATIONS[op]+ts2.name, keep_history=False)

    # apply (sample-wise) operation
    new_values = []
    for n1, instant in enumerate(at1):
        try:
            n2 = int( np.where(at2 == instant)[0] )
            val = eval(f"ax1[n1] {op} ax2[n2]")
            new_values.append( val )
        except:
            new_values.append( np.nan )

    # write operation's result to output & smooth NaN values ;)
    ts_op.values_set(new_values)
    ts_op.df.interpolate('linear', inplace=True)

    return ts_op


def regression(ts, segments=None, accuracy=False, orig_spec=True, model='linear'):
    """ Estimates a regression 'model' for 'ts' based on the samples in the 'segments'.

    In the simplest case, the best parameters for the linear model "y = b1*x+ b0" for any given
    segment are computed acc. to [ https://de.wikipedia.org/wiki/Lineare_Einfachregression ]

                SUM_i=0^i=N-1  (x_i - x_avg) * (y_i - y_avg)
        b1  =  ----------------------------------------------
                SUM_i=0^i=N-1  (x_i - x_avg)**2

        b0  =  y_avg - b1 * x_avg

    Note: The center of these piecewise-linear curves is located at the origin (0,0), whereas
    timestamps are based on "Linux epoch", i.e. '1970-01-01 00:00:00'. Thus, the shift
    parameters (b0) are often numerically quite large so as to "reach" the values in typical
    today's time ranges (i.e. years of 2020+).

    Args:
        ts (:obj:): 'TimeSeries' object for which to perform regression analysis.
        segments (various, optional): Definition of intervals of 'ts' which should be analysed.
            See 'list_segments()' for details. Defaults to 'None' (i.e. full range is used).
        accuracy (bool, optional): Switch to key 'accuracy' to 'section' to provide measures
            (MAE, MSE) to judge the estimation quality. Defaults to 'False'.
        orig_spec (bool, optional): Switch to enforce same "timespec" for the time instants in
            key 'points' of 'sections' as in object 'ts'. Defaults to 'True'.
        model (str, optional): Estimation model. Defaults to 'linear'.

    Returns:
        sections (list of dict): List of dicts for all sections acc. to regression analysis.
            The number of entries corresponds to the defined 'segments' whereas the number of
            parameters depends on the used 'model'. Each dict item is given by:
                {
                    'params':   [b1,b0],            # if model = 'linear'
                    'points':   [[xA,xB],[yA,yB]],  # point coordinates (start "A" / end "B")
                    'accuracy': { 'MAE': <float>,   # MAE = mean absolute error
                                  'MSE': <float> }  # MSE = mean squared error
                }
            Note: The 'points' can be used for a simple comparative plotting!
    """

    # gather all segments
    if (segments is None): # default mode (use whole signal)
        segments_list = [ [0, len(ts)], ]
    else:
        segments_list = list_of_segments(ts, segments)

    # linear regression analysis
    sections = []
    for s, seg in enumerate(segments_list):
        sec_item = { 'params': [], 'points': [], 'accuracy': {'MAE': 0.0, 'MSE': 0.0} }

        # get respective frame of data
        ts_seg = ts.samples_crop(seg, inplace=False)
        ts_seg.time_convert('stamp') # Note: Ensure "usable" format

        if (model == 'linear'):

            # compute mean values
            t_avg = ts_seg.df.t.mean()
            x_avg = ts_seg.df.x.mean()

            # compute parameters (i.e. slope (b1) & shift (b0))
            num, den = 0.0, 0.0
            for n in range(len(ts_seg)):
                num += (ts_seg[n].t - t_avg) * (ts_seg[n].x - x_avg)
                den += (ts_seg[n].t - t_avg)**2

            b1 = num / den
            b0 = x_avg - (b1*t_avg)
            sec_item['params'] = [b1,b0]

            # compute start/end points
            yA = b1*ts_seg[0].t + b0
            yB = b1*ts_seg[-1].t + b0
            if (orig_spec):
                t_range = convert_time([ts_seg[0].t, ts_seg[-1].t], ts.time.get())
            else:
                t_range = [ts_seg[0].t, ts_seg[-1].t]
            sec_item['points'] = [t_range, [yA,yB]]

            # compute accuracy measures?
            if (accuracy):
                tmp_ae, tmp_se = 0.0, 0.0
                for n in range(len(ts_seg)):
                    error = (b1*ts_seg[n].t + b0) - ts_seg[n].x
                    tmp_ae += abs(error)
                    tmp_se += error**2
                sec_item['accuracy']['MAE'] = tmp_ae/len(ts_seg)
                sec_item['accuracy']['MSE'] = tmp_se/len(ts_seg)
            else:
                sec_item['accuracy'] = None

        else:
            raise NotImplementedError(f"Unknown regression '{model}' specified")
            # TODO: have more sophisticated regressions?

        sections.append( sec_item )

    return sections


def predict(ts, thresholds, segments=None, warn_readable=False):
    """ Predicts future violation of 'ts' against 'thresholds' (for all desired 'segments').

    This function uses a linear regression model on the TimeSeries 'ts' in order to compare the
    trending against one or more 'thresholds'. As result, estimates for the remaining times
    (durations) until thresholds are exceeded are provided.

    Args:
        ts (:obj:): 'TimeSeries' object for which predition is to be performed.
        thresholds (list): List of thresholds against which violation is to be compared.
        segments (various, optional): Definition of intervals of 'ts' which should be analysed.
            See 'list_segments()' for details. Defaults to 'None' (i.e. full range is used).
        warn_readable (bool, optional): Switch to use an easy-to-read string representation for
            the pre-warning time. Defaults to 'False' (i.e. float in [s]).

    Returns:
        pre_warn (list): "Pre-warning" time defined as minimum (= most critical!) distance of
            upcoming violation (per threshold) for the various segments.
        ttt (list): Predicted "time-to-threshold" as seen from most recent sample of 'ts'.
            The number of entries corresponds to 'len(sections) x len(thresholds)'.
    """

    # init
    ttt = []
    pre_warn = []
    time_base = convert_time([ts[0].t, ts[-1].t], 'stamp')

    # compute linear regression model
    sections = regression(ts, segments, model='linear')

    # check all sections
    for s, sec in enumerate(sections):
        ttt.append([])

        # compute time of & distance to all thresholds (from last sample)
        for t, th in enumerate(thresholds):
            time_thresh = (th - sec['params'][1]) / sec['params'][0]
            time_dist = time_thresh - time_base[1]
            ttt[s].append(time_dist)
            if (time_dist < 0):
                raise RuntimeError(f"Estimated distance is *NOT* in future! ({time_dist})")

    # determine "pre-warning" time (i.e. minimum distance over all considered sections)
    for t in range(len(thresholds)):
        dist_min = 1e9
        for s in range(len(sections)):
            dist_min = min([dist_min, ttt[s][t]]) # compared w.r.t. unit [s]
        if (warn_readable):
            pre_warn.append(duration_str(dist_min, max_unit='days'))
        else:
            pre_warn.append(dist_min)

    return pre_warn, ttt


# def calc_GENERAL_slope(self):
#     """ todo

#     have same segment-wise decomposition (as "helper" in tsutils???)
#       --> then grow into a general analysis framwork with:
#         - max/min/mean statistics
#         - sigma / variance
#         - RMS values? (where reasonable)
#         - histograms w/ 10 - 50 bin levels, squeezed into |max-min| range
#         - slope (general and also due to sections / time intervals?)

#     general restriction to an "extracetd frame"?
#         (e.g. defaults = last x samples / y seconds?)

#       ...

#     # FIXME: compute different lin regs

#     # create a linear regression (for comparison)
#     inc = slope * dt/len(self)
#     linreg_hit = np.arange(self.x[0], self.x[-1]+(inc/2), inc) # +(inc/2) only to ensure!
#     # Note: This will NOT hit the end-point but be a better approx
#     # End-point including is obtained by "inc = slope * (dt/(len(self)-1)"

#     inc2 = slope * dt/(len(self)-1)
#     linreg_ext = np.arange(self.x[0], self.x[-1]+(inc/2), inc2)

#     avg = np.average(self.x)
#     linreg_avg = np.arange(avg-(dx/2), avg+(dx/2), inc)



#===============================================================================================
#===============================================================================================
#===============================================================================================

#%% MAIN
if __name__ == "__main__":
    print("This is the 'zynamon.utils' module.")
    print("See 'help(zynamon.utils)' for proper usage.")



################################################################################################
# Explanation:
#
#   What is the DIFFERENCE between 'ts_import_csv()' and 'ts_import_csv_mixed()'...
#   ..or: WHEN TO USE WHICH ONE?
#
#   1. 'ts_import_csv()' can import data that...
#       ...represents continuous time-series (probably w/ much redundant meta information)
#
#   (1a) = single time-series:
#   NAME,               DESCRIPTION,          CLASS,    UNIT,   VALUE,  INSERT_TIME
#   =10QA12/CB_STAT,    Stat 1 CB open/close, STAT,     NULL,   0,      2020-04-16 20:59:42.5
#   =10QA12/CB_STAT,    Stat 1 CB open/close, STAT,     NULL,   0,      2020-04-19 04:33:27.1
#   ...
#   =10QA12/CB_STAT,    Stat 1 CB open/close, STAT,     NULL,   1,      2020-05-03 08:40:17.3
#
#   (1b) = several time-series, in multiple columns:
#   TIMESTAMP,              LOCATION_TAG,   VALUE_1,    VALUE_2,    ...     VALUE_N
#   2020-04-16 20:59:42.5,  GER: Erlangen,  14.7,       60,         ...     134683.3
#   2020-04-16 20:59:45.3,  GER: Erlangen,  14.8        59,         ...     136584.45
#   ...
#   2020-04-16 21:06:13.7,  GER: Erlangen,  12.9        64,         ...     140432.8
#
#
#   2. 'ts_import_csv_mixed()' can import...
#       ...non-continuous lists of data, contributing to many time-series (i.e. event sequence)
#
#   NAME,               DESCRIPTION,            CLASS,  UNIT,   VALUE,  INSERT_TIME
#   =10QA12/CB_STAT,    Stat 1 CB open/close,   STAT,   NULL,   0,      2020-04-16 20:59:42.5
#   =20QA11/CB_STAT,    Stat 2 CB open/close,   STAT,   NULL,   1,      2020-04-19 04:33:27.1
#   ...
#   =10/GEN_FLT,        Stat 1 General FAULT!,  ALR,    NULL,   1,      2020-05-03 08:40:17.3
#   ...
#   =20QA11/CB_STAT,    Stat 2 CB open/close,   STAT,   NULL,   0,      2020-05-08 16:03:39.4
#   ...
#
################################################################################################