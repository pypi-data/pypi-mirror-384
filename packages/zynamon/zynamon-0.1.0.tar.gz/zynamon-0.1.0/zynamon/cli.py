"""
Main application functions to be used as CLI tools.
"""

import os
import json
import time
import typer
import shutil
import subprocess as sub
from itertools import product
from typing import Annotated

from zynamon.imex import batch_import_files, batch_merge_files, read_ts_file, pack_ts_file, summarize  
from zynamon.zeit import TS_SAVE_FORMATS
from zdev.core import anyfile
from zdev.parallel import duration_str
from zdev.validio import force_remove


# EXPORTED DATA
app = typer.Typer()
arg = lambda h: typer.Argument(help=f"{h}")
opt = lambda h: typer.Option(help=f"{h}")
opt_secure = lambda h,cb: typer.Option(help=f"{h}", prompt=f"{cb}")

# INTERNAL PARAMETERS & DEFAULTS
_FMT_TIME = 'stamp'
_FMT_FILES = 'json'
_FMT_COLL = 'pk'


def set_folder_env(root, assets='', periods='', cfg_file=''):
    """ Internal helper to get folder environment in a "greedy way" or use settings from a config file. """
    
    if cfg_file:
        with open(cfg_file, mode='r') as jf:
            cfg = json.load(jf)
        root_path = os.path.join(cfg['path'], cfg['root'])
        all_assets = [ast for ast in cfg['assets'] if os.path.isdir(os.path.join(root_path, ast))]
        all_periods = [per for per in cfg['periods'] if any([os.path.isdir(os.path.join(root_path, ast, per)) for ast in all_assets])] 
    
    else:       
        root_path = root       
        if not assets:
            all_assets = [ast for ast in os.listdir(root) if os.path.isdir(os.path.join(root, ast))]
        elif assets.startswith('['):
            all_assets = assets[1:-1].split(',')
        else:
            all_assets = [assets]
        if not periods:
            periods = []
            for ast in all_assets:
                folder = os.path.join(root, ast)
                more_periods = [per for per in os.listdir(folder) if os.path.isdir(os.path.join(folder, per))]
                periods.extend(more_periods)
            tmp = set(periods)
            all_periods = list(tmp)
        elif periods.startswith('['):
            all_periods = periods[1:-1].split(',')
        else:
            all_periods = [periods]
    
    return root_path, all_assets, all_periods


@app.command()
def importer(
    root: Annotated[str, arg("Root folder for hierarchical file search (may be overwritten by cfg-file setting)")],
    assets: Annotated[str, arg("Subfolders of assets")] = '',
    periods: Annotated[str, arg("Subfolders of time ranges")] = '',
    cfg_file: Annotated[str, opt("Config file for specific mappings (otherwise *automagic* assumptions)")] = '',
    causalise: Annotated[bool, opt("Ensure all time-series are causal")] = True,
    save_files: Annotated[bool, opt("Save all files after conversion (PK)")] = False,
    save_series: Annotated[bool, opt("Save all time-series to separate files (JSON)")] = True,
    add_summaries: Annotated[bool, opt("Create summary files for all collections")] = True,
    delete_backups: Annotated[bool, opt("Delete backup folders after conversion")] = True,
    verbosity: Annotated[int, opt("Level of progress tracking (0=OFF | 1=folders | 2=files | 3=time-series)")] = 2,
    ) -> None:
    """ 
    Mass import of time-series data from CSV-like files.
    """    
    print("#"*80+"\n"+"MASS-IMPORTING ... [started @ "+time.strftime('%Y-%m-%d %H:%M:%S')+"]\n")
    ta = time.perf_counter()

    # determine folders for import process
    root_path, the_assets, the_periods = set_folder_env(root, assets, periods, cfg_file)

    # traverse asset & period combinations and convert/import all single files 
    for ast in the_assets:
        folder_asset = os.path.join(root_path, ast)
        print("@"*64+f"\n@ ASSET '{ast}'\n")

        for per in the_periods:
            folder_period = os.path.join(folder_asset, per)
            print("="*48+f"\n= PERIOD '{per}'\n")

            if not os.path.isdir(folder_period):
                print(f"Folder does not exist (skipping)")
                continue
            
            if not cfg_file: # simple interpret *all* CSV files in the subfolders as *log* files ;)

                batch_import_files(
                    folder_period,
                    os.listdir(folder_period),
                    'async', 
                    None,
                    None,
                    None,
                    enforce = [_FMT_TIME, None],
                    causalise = causalise,
                    save_files = save_files,
                    save_series = save_series,
                    save_fmt=(_FMT_FILES,_FMT_COLL),
                    fname_out = '_ALL_COLLECTION',
                    verbosity=verbosity)

            else: # do it properly acc. to configuration ;)

                with open(cfg_file, mode='r') as jf:
                    cfg = json.load(jf)

                print("+"*32)
                if ('sub_logs_enum' not in cfg.keys()) or (not len(cfg['sub_logs_enum'])): 
                    print("+ NO event LOGS (ENUM) data specified\n")
                else:
                    print("+ event LOGS (ENUM) data\n")
                    batch_import_files(
                        folder_period,
                        cfg['sub_logs_enum'],
                        'async',
                        cfg['def_logs_enum']['name'],
                        cfg['def_logs_enum']['time'],
                        cfg['def_logs_enum']['data'],
                        enforce = [_FMT_TIME, None], # Note: No data-type is enforced here -> strings? (e.g. 'DIS')
                        causalise = causalise,
                        save_files = save_files, 
                        save_series = save_series, 
                        save_fmt=(_FMT_FILES,_FMT_COLL),
                        fname_out = '_ALL_LOGS_enum', 
                        verbosity=verbosity)
                    
                
                print("+"*32)
                if ('sub_logs_real' not in cfg.keys() or not len(cfg['sub_logs_real'])): 
                    print("+ NO event LOGS (REAL) data specified\n")
                else:
                    print("+ event LOGS (REAL) data\n")
                    batch_import_files(
                        folder_period,
                        cfg['sub_logs_real'],
                        'async',
                        cfg['def_logs_real']['name'],
                        cfg['def_logs_real']['time'],
                        cfg['def_logs_real']['data'],
                        enforce = [_FMT_TIME, float], 
                        causalise = causalise,
                        save_files = save_files, 
                        save_series = save_series, 
                        save_fmt=(_FMT_FILES,_FMT_COLL),
                        fname_out = '_ALL_LOGS_real',
                        verbosity=verbosity)
                        
                print("+"*32)
                if ('sub_streams' not in cfg.keys() or not len(cfg['sub_streams'])): 
                    print("+ NO STREAMS data specified\n")
                else:

                    enforce_for_all = [_FMT_TIME]
                    for st in cfg['def_streams']['data']:
                        enforce_for_all.append(float) # Note: Add as many "float" conversion as streams! ;)

                    print("+ STREAMS data\n")
                    batch_import_files(
                        folder_period,
                        cfg['sub_streams'],
                        'stream',
                        None,
                        cfg['def_streams']['time'],
                        cfg['def_streams']['data'],
                        enforce = enforce_for_all,
                        causalise = causalise,
                        save_files = save_files, 
                        save_series = save_series,
                        save_fmt=(_FMT_FILES,_FMT_COLL),
                        fname_out = '_ALL_STREAMS',
                        verbosity=verbosity)
                        
                print("+"*32)
                if ('sub_streams_xt' not in cfg.keys() or not len(cfg['sub_streams_xt'])): 
                    print("+ NO X-TOOLS STREAMS data specified\n")
                else:
                    print("+ X-TOOLS STREAMS data\n")
                    batch_import_files(
                        folder_period, 
                        cfg['sub_streams_xt'],
                        'stream-xt',
                        None,
                        cfg['def_streams_xt']['time'],
                        cfg['def_streams_xt']['data'],
                        enforce = [_FMT_TIME, float],
                        causalise = causalise,
                        save_files = save_files,
                        save_series = save_series,
                        save_fmt=(_FMT_FILES,_FMT_COLL),
                        fname_out = '_ALL_STREAMS_XT',
                        verbosity=verbosity)
                        
            if add_summaries:
                summarizer(folder_period, ignore_ext=True, overwrite=True, verbosity=0)

    if delete_backups:
        print("@"*64+f"\n\nDeleting backup files...\n")
        for ast in the_assets:
            for per in the_periods:
                folder_period = os.path.join(root_path, ast, per)
                if os.path.isdir(folder_period):
                    for item in os.listdir(folder_period):
                        if item == '_BKP':
                            shutil.rmtree(os.path.join(folder_period, item), onexc=force_remove)              
        
    print("... MASS-IMPORTING! [finished @ "+time.strftime('%Y-%m-%d %H:%M:%S')+"]\n"+"#"*80)
    tb = time.perf_counter()

    print(f"Total duration ~ {duration_str(tb-ta, sep=' ')}")
    return


@app.command()
def summarizer(
    folder: Annotated[str, arg("Folder of collection files (in either format 'pk'|'h5'|'json')")],
    ignore_ext: Annotated[bool, opt("Create only single summary file for collection (even if stored in multiple file formats)")] = True,
    overwrite: Annotated[bool, opt("Force creation of summary file (even if a '.tsinfo' of similiar basename already exists)")] = False,    
    verbosity: Annotated[int, opt("Level of progress tracking (0=OFF | 1=files | 2=details)")] = 1,
    ) -> None:
    """ 
    Generate summary information on collection files.
    """

    all_files = [item for item in os.scandir(folder) if item.is_file()]
    all_fnames = [item.name for item in all_files]

    for file in all_files:
        if (file.name.endswith(TS_SAVE_FORMATS)):

            info_file = file.name.split('.')[0]+'.tsinfo' if ignore_ext else '_'.join(file.name.split('.'))+'.tsinfo'

            if not overwrite and info_file in all_fnames:
                print(f"Skipping {file.name} -> *.tsinfo file exists!")
                continue

            print(f"Summarizing {file.path}")
            collection = read_ts_file(file.path, target=dict, verbose=(verbosity>1))
            summarize(
                collection,
                print_out=False, 
                print_file=os.path.join(folder, info_file),
                show_meta=True,
                show_series=True,
                time_iso=True)
            
    return


@app.command()
def compresser(
    root: Annotated[str, arg("Root folder of hierarchical file search (will be overwritten if config file is used)")],
    assets: Annotated[str, arg("Subfolders of assets (restrict seach)")] = '',
    periods: Annotated[str, arg("Subfolders of time ranges (restrict search)")] = '',
    cfg_file: Annotated[str, opt("Config file for specific mappings (otherwise *automagic* assumptions)")] = '',
    agg_time: Annotated[str, opt("Aggregation time(s) [s] to use for compression")] = '300',
    agg_mode: Annotated[str, opt("Aggregation mode(s) to use for compression (options: 'avg'|'max'|'min'|'median')")] = 'avg',
    verbosity: Annotated[int, opt("Level of progress tracking (0=OFF | 1=files | 2=compressions | 3=time-series)")] = 2  
    ) -> None:    
    """ 
    Compression of time-series collections to one or more aggregation levels.
    Note that this is restricted to real-valued data!
    """    
    print("#"*80+"\n"+"COMPRESSING COLLECTIONS ... [started @ "+time.strftime('%Y-%m-%d %H:%M:%S')+"]\n")
    ta = time.perf_counter()
        
    # determine folders for import process (Note: This is a "greedy" approach if no config is used!)
    root_path, the_assets, the_periods = set_folder_env(root, assets, periods, cfg_file)

    # handle compression settings & create permutations
    if agg_time.startswith('['):
        tmp = agg_time[1:-1].split(',')
        all_times = [float(item) for item in tmp]
    else:
        all_times = [float(agg_time)]
    if agg_mode.startswith('['):
        all_modes = agg_mode[1:-1].split(',')
    else:
        all_modes = [agg_mode]
    compressions = product(all_times, all_modes)
    
    # traverse asset & period combinations and convert/import all single files 
    for ast in the_assets:
        folder_asset = os.path.join(root_path, ast)
        print("@"*64+f"\n@ ASSET '{ast}'\n")

        for per in the_periods:
            folder_period = os.path.join(folder_asset, per)
            print("="*48+f"\n= PERIOD '{per}'\n")

            for sig_class in ('LOGS_real', 'STREAMS', 'STREAMS_XT'):
                coll_file = anyfile(folder_period, '_ALL_'+sig_class, TS_SAVE_FORMATS)
                if (coll_file is not None):
                    print(f"+ '{sig_class}' data")
                    pack_ts_file(
                        coll_file,
                        compressions,
                        save_fmt = _FMT_COLL, 
                        overwrite = True,
                        verbosity = verbosity)
                else:
                    print(f"+ NO {sig_class} data storage found")
                print("")
            # Note: Compressions can *only* be applied for *real-valued* data!

    return


@app.command()
def merger(
    root: Annotated[str, arg("Root folder of hierarchical file search (will be overwritten if config file is used)")],
    assets: Annotated[str, arg("Subfolders of assets (restrict seach)")] = '',
    periods: Annotated[str, arg("Subfolders of time ranges (restrict search)")] = '',
    cfg_file: Annotated[str, opt("Config file for specific mappings (otherwise *automagic* assumptions)")] = '',
    verbosity: Annotated[int, opt("Level of progress tracking (0=OFF | 1=files | 2=time-series)")] = 1 
    ) -> None:
    """ Merge several different time periods into a single collection file. """
    print("#"*80+"\n"+"MERGING COLLECTIONS ... [started @ "+time.strftime('%Y-%m-%d %H:%M:%S')+"]\n")
    ta = time.perf_counter()
        
    # determine folders for import process (Note: This is a "greedy" approach if no config is used!)
    root_path, the_assets, the_periods = set_folder_env(root, assets, periods, cfg_file)

    # traverse asset & period combinations and convert/import all single files 
    for ast in the_assets:
        folder_asset = os.path.join(root_path, ast)
        print("@"*64+f"\n@ ASSET '{ast}'\n")
            
        # check on available storage files (Note: Assume the same are present in all folders)
        avail_types = set()
        avail_comps = set()
        for item in os.listdir(os.path.join(folder_asset, the_periods[0])):
            if item.endswith(TS_SAVE_FORMATS):
                for data_type in ('_ALL_LOGS_real','_ALL_STREAMS','_ALL_STREAMS_XT'):
                    if item.startswith(data_type):
                        avail_types.add(data_type)
                        tmp = item.removeprefix(data_type+'_')
                        if (tmp != item):
                            data_comp = tmp.split('.')[0]
                            avail_comps.add(data_comp)
        # Note: Full-length data is excluded on purpose -> use only compressed versions!        

        # perform merging of all periods for all base files
        for at in avail_types:
            for ac in avail_comps:
                basename = at+'_'+ac
                batch_merge_files(
                    folder_asset, 
                    the_periods, 
                    basename,
                    allow_overwrite = True,
                    save_fmt = _FMT_COLL,
                    fname_out = '',
                    verbosity=verbosity)
            
    return


@app.command()
def explorer(
    root: Annotated[str, arg("Root folder to start exploring ;)")]
    ) -> None:
    """ Start a GUI implemented in streamlit. """

    app_file = os.path.join(os.path.dirname(__file__), r'..\app\CBM_explorer.py') 
    cmd_list = ['streamlit', 'run', app_file]
    proc = sub.Popen(cmd_list)#, stdin=sub.PIPE, stdout=sub.PIPE, stderr=sub.PIPE, text=True)

    return


if __name__ == '__main__':
    app()      



################################################################################################
# NOTES:
# (1) Typcial usage for COMMAND:
#
#   py app.py importer . --cfg-file T:\Python\ZynAMon\cfg\data_BMTE.json --save-series
#   py app.py compresser S:/DB/CBM_data/DW6_DolWin6 [CWC,Tafo] 2020-05 --agg-time [10,60,300,3600] --agg-mode [avg,min,max]
#   py app.py merger S:/DB/CBM_data/DW6_DolWin6 [CWC,Tafo]
#
#   py app.py summarizer {path_to_folder} --ignore-ext --overwrite --verbosity 1
#
# Note: In most cases, using configuration files for projects is recommended which then removes
#       the need to provide the underlying subfolders (i.e. asset/periods)!
#
#
# (2) Expected HIERARCHY OF FOLDER storage:
#
#       [PROJECT]
#       |
#       +-- [ASSET A1]
#       |   |
#       |   +-- [PERIODS P1]
#       |   |   +-- Subfolders "log_enum" (zero or more)
#       |   |   +-- Subfolders "log_real" (zero or more)
#       |   |   +-- Subfolders "streams" (zero or more)
#       |   |   +-- Subfolders "streams_xt" (zero or more)
#       |   |   
#       |   +-- [PERIOD P2]
#       |     ...
#       |
#       +--  [ASSET A2]
#         ...
#
#
# (3) Nesting of FUNCTION CALLS:
#
#       > import_process()              --> traverse various assets, periods and data types
#
#           > batch_import_files()      --> traverse set of subfolders for specific settings (from above)
#
#               > import_csv_async()    --> convert CSV-files with log/event-based data
#               > import_csv()          --> convert CSV-files with regularly sampled data
#
#
# (4) Relationship of SUBFOLDER DEFINITION (in config files) and CSV-TYPES:
#
#       folder          | csv_type
#       ---------------------------------------
#       logs_enum       | 'async'
#       logs_real       | 'async'
#       streams         | 'stream'
#       streams_xt      | 'stream-xt'
#
#
# (5) General usage recommendations:
#
# - Depending on the (size of the) CSV file dumps, converting each file alone (save_files=True) 
#   may be useful. For typical event lists, however, the whole subfolder should be converted to 
#   one file.  
#
# - For the time target setting, using 'stamp' or 'stamp_ns' is highly recommended! 
#   That is, DO NOT USE ISO-STRINGS DIRECTLY in stored 'TimeSeries' representations!
#   (will cause a significantly larger storage size, i.e. long 'str' vs. single 'float'/'int')
#
# - Regardless of both 'save' settings, the overall collections are always stored in the
#   parent folder, i.e. at Project > Asset > Period level.
#
################################################################################################