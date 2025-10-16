# -*- coding: utf-8 -*-
"""
Environment settings for the "CBM Explorer" streamlit GUI application.
"""

import os
import json


# INTERNAL PARAMETERS & DEFAULTS
# n/a


def init_memory(mem):
    """ Add variables to "persistent memory "container if not yet present (= 1st run). """

    # session counter
    if ('cnt' not in mem):
        mem.cnt = 1

    # data administration
    if ('path' not in mem):
        mem.path = ''
    if ('path_old' not in mem):
        mem.path_old = ''
    if ('project' not in mem):
        mem.project = ''
    if ('asset' not in mem):
        mem.asset = ''
    if ('period' not in mem):
        mem.period = ''

    if ('datafolder' not in mem):
        mem.datafolder = ''
    if ('datafolder_old' not in mem):
        mem.datafolder_old = mem.datafolder

    if ('datafile' not in mem):
        mem.datafile = ''
    if ('datafile_old' not in mem):

        mem.datafile_old = ''
    if ('data_load_dur' not in mem):
        mem.data_load_dur = 0
    if ('data_loaded' not in mem):
        mem.data_loaded = False
    if ('data' not in mem):
        mem.data = None

    if ('sig_list' not in mem):
        mem.sig_list = None

    # plot config (Note: 'figN' == figure N incl. all traces!)
    if ('active_fig' not in mem):
        mem.active_fig = None
    if ('plot_fig' not in mem):
        mem.plot_fig = False
    if ('clear_fig' not in mem):
        mem.clear_fig = False
    if ('fig1' not in mem):
        mem.fig1 = None
    if ('fig2' not in mem):
        mem.fig2 = None
    if ('fig3' not in mem):
        mem.fig3 = None
    if ('fig4' not in mem):
        mem.fig4 = None
    if ('fig5' not in mem):
        mem.fig5 = None

    return mem


def init_sources(folder):
    """ Lists all available JSON configs. """    
    sources = {}
    for file in os.scandir(folder):
        if file.name.startswith('data_') and file.name.endswith('json'):
            with open(file.path) as jf:
                tmp = json.load(jf)
            sources[tmp['root']] = file.path
    return sources


def mdstr(fontsize, text):
    """ Creates a string text for a 'st.markdown' body field with proper font size.
     
    Args:
        size (int): Integer fontsize w/ levels 1 (smallest) -> 6 (largest). """
    sized_str = '#'*(7-fontsize)
    sized_str += ' '+text
    return sized_str


def ltxstr(text, size):
    """ Set LaTeX body with proper fontsize from 1-10 (small -> large). """
    
    match size:
        case 1: sized_str = r'\tiny'
        case 2: sized_str = r'\scriptsize'
        case 3: sized_str = r'\footnotesize'
        case 4: sized_str = r'\small'
        case 5: sized_str = r'\normalsize'
        case 6: sized_str = r'\large'
        case 7: sized_str = r'\Large'
        case 8: sized_str = r'\LARGE'
        case 9: sized_str = r'\huge'
        case 10: sized_str = r'\Huge'

    sized_str += r' \fontfamily{helvet} '
    sized_str += text

    return sized_str

