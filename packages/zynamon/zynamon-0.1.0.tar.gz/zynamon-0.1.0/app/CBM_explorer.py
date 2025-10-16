"""
Streamlit GUI "Explorer" application.
"""

import os
import sys
import time
import streamlit as st

from CBM_explorer_helpers import init_memory, init_sources, ltxstr, mdstr
from zynamon.zeit import *
from zynamon.imex import read_ts_file
from zdev.parallel import duration_str
from zdev.plot import qplotly


# INTERNAL PARAMETERS & DEFAULTS
_PATH_CONFIGS = r'..\cfg'
_PATH_DATA = r'S:\DB\CBM_data'
_MULTIPLE_FILES = False # allow selection of signals to be plotted from more than one file
_FILE_EXTENSION = '.pk'
_NUM_FIGURES = 2 # Note: Maximum number of figures is hard-coded to 5 in 'app_helpers.init_memory()'!
_LIMITS = { 'val': 2000, 'min': 250, 'step': 250, 'max': 25000 }
_FILT_MODE = {
    'Low-pass (FIR)': 'FIR_LP_MA',
    'Low-pass (IIR)': 'IIR_1pole',
    'Flex-pole (IIR)': 'IIR_flexpole',
    'Nonlinear': 'NL_'
    }
#
# todo !!!!!!!!!!!
#
_FILT_NL = { 'Maximum': 'max', 'Median': 'median', 'Minimum': 'min' }
_FILT_SMOOTH = { '3%': 0.03, '5%': 0.05, '10%': 0.10, '15%': 0.15, '20%': 0.20 }
_AGG_TIME = { '5sec': 5, '1min': 60, '5min': 5*60, '1hour': 60*60 }
_AGG_MODE = { 'Maximum': 'max', 'Average': 'avg', 'Minimum': 'min' }


#-----------------------------------------------------------------------------------------------
# GENERAL INIT
#-----------------------------------------------------------------------------------------------

# session state
MEM = init_memory(st.session_state)
MEM.path_old = _PATH_DATA
MEM.cnt += 1

# config files for data sources / projects
SRC = init_sources(os.path.join(os.path.dirname(__file__), _PATH_CONFIGS))

# app page
st.set_page_config(page_title='CBM Explorer', layout='wide', initial_sidebar_state='auto')

# layout
UI_SIGNALS, UI_DISPLAY = st.columns([30,70])


#-----------------------------------------------------------------------------------------------
# SIDEBAR (widgets for settings)
#-----------------------------------------------------------------------------------------------

with st.sidebar:
    st.title("CBM Explorer")
    SB_SRC, SB_DISP, SB_MOD, SB_DBG = st.tabs(['Source','Display','Modification','DBG'])

    # DATA SOURCE SETTINGS
    with SB_SRC:

        # path definition
        path_opt = st.radio("Base path:", options=('Default','User defined'), index=0)

        hide_widget = (path_opt != 'User defined')
        path_user = st.text_input(r"Path (use \\\\):", MEM.path_old, disabled=hide_widget)
        if (path_opt == 'User defined'):
            MEM.path = path_user
            MEM.path_old = path_user
        else:
            MEM.path = _PATH_DATA

        # select all options based on available files / folders
        p = st.selectbox("Project (JSON config):", options=tuple(SRC.keys()), index=2) 
        MEM.project = p
        with open(SRC[p]) as jf:
            cfg = json.load(jf)
        avail_assets = [item.name for item in os.scandir(os.path.join(cfg['path'],cfg['root'])) if item.is_dir()] 
        ast = st.selectbox("Asset:", options=avail_assets)
        MEM.asset = ast 
        avail_periods = [item.name for item in os.scandir(os.path.join(cfg['path'],cfg['root'],ast)) if item.is_dir()] 
        per = st.selectbox("Period:", options=avail_periods)
        MEM.period = per
        MEM.datafolder = os.path.join(MEM.path, MEM.project, MEM.asset, MEM.period)    
        print(MEM.datafolder)

        # data file selection
        pk_files = []
        for item in os.listdir(MEM.datafolder):
            if (item.endswith(_FILE_EXTENSION)):
                pk_files.append(item)
        if (_MULTIPLE_FILES):
            fnames = st.multiselect("Data Container:", options=pk_files)
            MEM.datafile = []
            for item in fnames:
                MEM.datafile.append(os.path.join(MEM.datafolder, item))
        else:
            fname = st.selectbox("Which SIGNAL CLASS to use?", options=pk_files)
            MEM.datafile = os.path.join(MEM.datafolder, fname)

        # data loading (only if source settings have changed)
        if ((MEM.datafolder == MEM.datafolder_old) and (MEM.datafile == MEM.datafile_old)):
            st.write(f"###### Data in memory...")
        else:
            st.write(f"###### Loading from...")
            t0 = time.perf_counter()
            if (_MULTIPLE_FILES):
                MEM.data = {}
                for item in MEM.datafile:
                    slim_src = item.strip(MEM.path)
                    st.write(f"###### {slim_src}")
                    tmp = read_ts_file(item, target=dict)
                    MEM.data.update(tmp)
            else:
                slim_src = MEM.datafile.strip(MEM.path)
                st.write(f"###### {slim_src}")
                MEM.data = read_ts_file(MEM.datafile, target=dict)
            t1 = time.perf_counter()
            MEM.data_load_dur = duration_str(t1-t0, sep=' ')
            st.write(f"###### ...loaded in {MEM.data_load_dur}")
            MEM.data_loaded = True
            MEM.sig_list = list(MEM.data.keys())
            MEM.sig_list.sort()


    # DISPLAY SETTINGS
    with SB_DISP:
        # st.write("_Note: These settings will only apply to *newly* plotted traces! (i.e. after the button has been clicked again)_")
        st.markdown(mdstr(1, "_Note: These settings will only apply to *newly* plotted traces! (i.e. after the button has been clicked again)_"), help="I am your markdown!")

        disp_time_str = st.checkbox("Show readable time? (ISO)")

        do_limit = st.checkbox("Limit signals?")

        # limit type
        lim_type = st.radio("Limit signals by...?", ("last samples","interval"), 
            disabled=(not do_limit))

        # number of samples
        crop_samples = st.slider("Number of most recent samples:", value=_LIMITS['val'], min_value=_LIMITS['min'], step=_LIMITS['step'], max_value=_LIMITS['max'],
                                 disabled=(not (do_limit and (lim_type == 'last samples'))))

        # time interval
        SB_DISP_L, SB_DISP_R = st.columns((1,1))
        day_now = dt.date.today()
        day_past = day_now - dt.timedelta(days=30)
        with SB_DISP_L:
            t_start = st.date_input('Start date:', day_past, 
                                    disabled=(not (do_limit and (lim_type == 'interval'))))
        with SB_DISP_R:
            t_end = st.date_input('End date:', day_now, 
                                  disabled=(not (do_limit and (lim_type == 'interval'))))


    # SIGNAL MODIFICATIONS
    with SB_MOD:

        # FILTERING
        do_filt = st.checkbox("Filter signals?")

        filt_mode = st.selectbox("Filter mode:", options=_FILT_MODE.keys(), 
                                 disabled=(not do_filt))

        filt_N = st.slider("Filter size/window:", value=10, min_value=2, step=1, max_value=25,
                           disabled=(not (do_filt and filt_mode in ('Low-pass (FIR)','Nonlinear'))))

        # nonlinear window type
        hide_widget = (not (do_filt and filt_mode in ('Nonlinear')))
        filt_NL = st.selectbox("Sliding-window type:", 
                               options=('Maximum','Median','Minimum'),)           

        # # pole(s) & smoothing range
        # SB_MOD_L, SB_MOD_R = st.columns((1,1))
        # with SB_MOD_L:
        #     hide_widget = (not (do_filt and filt_mode in ('Flex-pole (IIR)')))
        #     filt_poledyn = st.slider("Pole (dynamic):", disabled=hide_widget,
        #         value=0.3, min_value=0.1, step=0.001, max_value=0.5)
        # with SB_MOD_R:
        #     hide_widget = (not (do_filt and filt_mode in ('Low-pass (IIR)','Flex-pole (IIR)')))
        #     filt_pole = st.slider("Pole:", disabled=hide_widget,
        #         value=0.9, min_value=0.5, step=0.001, max_value=0.999)
        # filt_smooth = st.selectbox("Smoothing range:", disabled=hide_widget,
        #     options=_FILT_SMOOTH.keys(), index=2)

        # # COMPRESSION
        # do_agg = st.checkbox("Aggregate signals?")

        # # mode & time
        # hide_widget = (not do_agg)
        # agg_mode = st.selectbox("Aggregation mode:", disabled=hide_widget,
        #     options=('Maximum','Average','Minimum'), index=1)
        # agg_time = st.radio("Aggregation time frame:", disabled=hide_widget,
        #     options=_AGG_TIME.keys(), index=2, horizontal=True)

    # debugging
    with SB_DBG:
        dbg = st.checkbox('Show debug info?')
        if (dbg):
            st.write(f"##### Session # {MEM.cnt}")
            with st.expander("[st.session_data]"):
                st.write(MEM)
            with st.expander("[sys.path]"):
                st.write(sys.path)
            with st.expander("[dir()]"):
                st.write(dir())



#-----------------------------------------------------------------------------------------------
# UI_SIGNALS column
#-----------------------------------------------------------------------------------------------

with UI_SIGNALS:
    st.write("##### Signals")

    # selection of signals / time-series
    if (MEM.data_loaded):

        fig_graphs = list(np.arange(1, 1+_NUM_FIGURES, 1))
        MEM.active_fig = st.radio("Active figure:", options=fig_graphs, horizontal=True)

        selected = st.multiselect("Select time-series to plot:", options=MEM.sig_list)
        if (len(selected)):
            plot_fig = st.button("Plot / update signals")
        else:
            plot_fig = False
        clear_fig = st.button("Clear active figure")
    else:
       st.write("No time-series found yet! (load source)")

    # Note: The flag 'data_loaded' will become & remain 'True' after 1st loading of data, i.e.
    #       it is  *ONLY* 'False' right after starting...


#-----------------------------------------------------------------------------------------------
# MAIN column
#-----------------------------------------------------------------------------------------------

with UI_DISPLAY:
    # st.write("##### Display")
    # st.markdown("###### Display", help="I am your markdown!")
    st.markdown(mdstr(1, "Display"), help="I am your markdown!")
    # st.latex(lxstr(1, "Display"), help="I am your markdown!")

    for n in range(1, 1+_NUM_FIGURES):
        st.write(f"[Fig {n}]")

        # plot active figure w/ new data & settings
        if ((MEM.active_fig == n) and plot_fig):
            fh = None
            for idx, sig_name in enumerate(selected):
                ts = MEM.data[sig_name]
                if (do_limit):
                    if (lim_type == 'Last samples'):
                        ts_crop = ts.samples_crop(crop_samples, inplace=False)
                    else: # (lim_type == 'time interval')
                        crop_interval = convert_time([t_start,t_end], 'iso')
                        ts_crop = ts.samples_crop(crop_interval, inplace=False)
                        print("after")
                else:
                    ts_crop = ts

                # if (do_filt):
                #     if (filt_mode == 'Nonlinear'):
                #         f_mode = _FILT_MODE[filt_mode]+_FILT_NL[filt_NL]
                #     else:
                #         f_mode = _FILT_MODE[filt_mode]
                #     f_params = {'N': filt_N, 'pole': [filt_pole,filt_poledyn],
                #                 'smooth': _FILT_SMOOTH[filt_smooth]}
                #     ts_filt = ts_crop.values_filter(f_mode, f_params, inplace=False)
                # else:
                #     ts_filt = ts_crop
                # if (do_agg):
                #     ts_agg = ts_filt.samples_pack(_AGG_TIME[agg_time], _AGG_MODE[agg_mode], inplace=False)
                # else:
                #     ts_agg = ts_filt
                # fh = qplotly(ts_agg, fig=fh, info=ts.name, time_iso=disp_time_str, slider=False, renderer=None)


                fh = qplotly(ts_crop, fig=fh, info=ts.name, time_iso=disp_time_str, slider=False, renderer=None)
                # Note: Conversion to 'readable time' is directly done inside 'qplotly()'!

            st.plotly_chart(fh, use_container_width=True)
            exec(f"MEM.fig{n} = fh")

        # reset active figure
        elif ((MEM.active_fig == n) and clear_fig):
            st.write("###### >> cleared!")
            exec(f"MEM.fig{n} = None")

        # restore all other figures w/ previous signals & settings
        else:
            exec(f"fig_not_empty = (MEM.fig{n} is not None)")
            if (fig_not_empty):
                eval(f"st.plotly_chart(MEM.fig{n}, use_container_width=True)")

    # ensure continuity
    MEM.datafolder_old = MEM.datafolder
    MEM.datafile_old = MEM.datafile
    # Note: Above technique is *VERY IMPORTANT* to avoid un-necessary re-loading of data! 
    # Thus, it significantly improves overall speed & user experience! ;)


################################################################################################
# #todo: possible extension to UI_DISPLAY --> automatic re-draw of figures???
#
#   for this:
#   --> track if one of the options has been changed (i.e. no botton re-click required)
#   --> track selected signals and their settings and store this as list (per figure!)
#
#       --> MEM.selected[n][:] --> for figure 'n'
#       --> MEM.fig_def[n] with
#               - selected (list)
#               - do_limit (bool) + crop_samples (int)
#               - do_agg (bool)   + agg_mode (str) + agg_time_sec (int)
#               - disp_time_str (bool)
#
################################################################################################