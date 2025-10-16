"""
Utilities for X-tools CSV-export files.
This module contains helpers for the modification of CSV-files as exported by "CMS X-Tools". 
For example, it provides a helper to present the spectra (FFT) as a regular time-series w/ 
faked timestamps for ease of import by e.g. PI system tools. 
"""

import os
import csv
import shutil

from zynamon.zeit import convert_time
from zdev.core import massfileop


# INTERNAL PARAMETERS & DEFAULTS
# n/a


def x_read_spectrum(fname):
    """ Reads an FFT spectrum from the CSV-file 'fname'. 
    
    Args:
        fname (str): Filename of original CSV-file by X-Tools containing spectral data.
        
    Returns:
        spectrum (dict): Dict describing the collected spectral data (FFT) w/ keys:
            - time: Time reference of spectral snapshot (i.e. last sample in sample batch)
            - freq: Frequency grid in "Frequency Unit" (see "meta" information)
            - magnitude: Magnitude values of FFT 
            - phase: Phase values of FFT
            - meta: Dict of "meta" information colelcting from first two lines in the file
        orig_header (list): List of first two lines (str) from the original CSV-file. This may
            be required to save a modified CSV-file.
    """
    
    # init output dict
    spectrum = {
        'time': -1,
        'freq': [],
        'magnitude': [],
        'phase': [],
        'meta': {}
        }

    # read original CSV-file & extract data
    with open(fname, mode='r') as tf:
        meta_info = {}
        
        # init format parsing (Note: Proper format is determined from 1st line)
        first_line = tf.readline()
        tf_format = csv.Sniffer().sniff( first_line )
        
        # get meta info from first two lines
        second_line = tf.readline()   
        k_meta = first_line.split(tf_format.delimiter)
        v_meta = second_line.split(tf_format.delimiter)
        for n, key in enumerate(k_meta):
            k_meta[n] = key.strip() # clean whitespaces (incl. newline)
            meta_info.update({k_meta[n]: v_meta[n].strip()})
        spectrum['meta'] = meta_info   
        
        # get end point time reference & frequencies from third line
        third_line = tf.readline()
        fields = third_line.split( tf_format.delimiter )
        for n, item in enumerate(fields):
            fields[n] = item.strip() # clean whitespaces (incl. newline)
        spectrum['time'] = fields[0] # 1st column = time reference (assigned directly)
        spectrum['freq'] = fields[2:-1] # 3rd to last column = all frequency values
        
        # read spectral data 
        fourth_line = tf.readline()
        fields = fourth_line.split( tf_format.delimiter )
        for n, item in enumerate(fields):
            fields[n] = item.strip() # clean whitespaces (incl. newline)
        # spectrum['time'] = fields[0] # 1st column = time reference (assigned directly)
        spectrum['time'] = convert_time(fields[0], str) 
        spectrum['magnitude'] = fields[2:-1]
        
        fifth_line = tf.readline()
        fields = fifth_line.split( tf_format.delimiter )
        for n, item in enumerate(fields):
            fields[n] = item.strip() # clean whitespaces (incl. newline)
        spectrum['phase'] = fields[2:-1]
                        
        # keep header lines for output file
        orig_header = [first_line, second_line]
        
    return spectrum, orig_header

 
def x_write_spectrum(fname, spectrum, orig_header=None, spread=0.1):
    """ Writes 'spectrum' to 'fname' where the FFT is "faked" as a regular time-series. 
    
    Args:
        fname (str): Filename of output CSV-file.
        spectrum (dict): Spectral data as extracted by "x_read_file_spectra()".
        orig_header (list, optional): 2-element list containing the first two original lines 
            (str) to create a fully modified CSV-file. Defaults to 'None'.
        spread (float, optional): Distance [s] between two faked timestamps for the frequency 
            entries. This effectively determines how much time is covered by the whole FFT 
            spectrum on the time axis. Defaults to 0.1 (i.e. 100ms).
            
    Returns:
        time_span (2-tuple of str): Time covered by the batch of spectral values. 
    """

    # create output file
    with open(fname, mode='wt') as tf:
        
        # replicate original header?
        if (orig_header is not None):
            tf.write(orig_header[0])
            tf.write(orig_header[1])
       
        # init actual data header & timestamp faking
        tf.write("Timestamp [ns]; Frequency [Hz]; Amplitude; Phase;\n")
        T0 = convert_time(spectrum['time'], int) 
        Tsp = int(spread * 1e9) # spread in [ns]
        
        # write whole spectrum
        for n, f in enumerate(spectrum['freq']):
            t_fake = T0 + n*Tsp
            my_line = f"{t_fake}; {f}; {spectrum['magnitude'][n]}; {spectrum['phase'][n]};\n"
            tf.write(my_line)
         
    time_span = (convert_time(T0, str), 
                 convert_time(T0+int(len(spectrum['freq']))*Tsp, str))    
    
    return time_span


def x_convert_spectrum(fname, spread=0.1, ext='mod_csv'):
    """ Converts original FFT spectrum from 'fname' and converts to file w/ fake time 'spread'.
    
    Note: This is just a convenience function w/ sequential calls to 'x_read_spectrum()' and
    'x_write_spectrum()'!
    
    Args:
        fname (str): Filename of original CSV-file by X-Tools containing spectral data.
        spread (float, optional): Distance [s] between two faked timestamps for the frequency 
            entries. This effectively determines how much time is covered by the whole FFT 
            spectrum on the time axis. Defaults to 0.1 (i.e. 100ms).
        ext (str, optional): File extension for converted files. Note: This should be different
            from '.csv' in order for modified files not to be found. Defaults to 'mod_csv'.
        
    Returns:
        fname_conv (str): Filename of converted CSV-file.
    """
    spectrum, orig_header = x_read_spectrum(fname)
    fname_conv = fname[:-4]+'.'+ext
    x_write_spectrum(fname_conv, spectrum, orig_header, spread)
    return fname_conv


def x_batch_conv_spec(root, pattern='.* Spm.*\.csv', target_dir=None, backup_dir=None, 
                      backup=True, verbose=True):
    """ Batch conversion of (new) X-Tools CSV spectrum files (for PI System compatibility).  
    
    This routine converts all spectrum files found and stores their converted versions w/ new
    extension 'mod_csv'. This indicates that these files can then be parsed / imported into 
    the PI system by use of the "UFL adapter" (UFL = Universal File Loader). If desired,
    original files can still be kept and could also be placed in single 'backup_dir' (to be 
    easily deleted later on).
    
    This routine is implemented w/ ROBUST BEAHVIOUR AGAINST POTENTIAL INTERRUPTIONS (such as the
    untimely removal of external USB drives) and WILL THEN PICK UP OPERATION IN THE NEXT RUN! :)
    
    Args:
        root (str): Root folder (absolute path) of subfolder tree that will be searched for 
            files matching the 'pattern'.
        pattern (str): RegEx (regular expression) string to identify proper spectrum files.
            Defaults to '.* Spm.*\.csv' (= standard X-Tools output).
        target_dir (str, optional): Target folder where all converted files will be placed. If 
            omitted, conversion will take place in the individual folders. Defaults to 'None'.        
        backup_dir (str, optional): Backup folder where all originals files will be placed. If 
            omitted, the files will be "hidden" but left in the individual folders. Defaults 
            to 'None'.
        backup (bool, optional): Switch to backup orginal files. Defaults to 'True'.
            Note: Depending on the setting for 'backup_dir', the original CSV files will either
            (i) be kept in the 'target' folder (if any) but "hidden" from next conversion runs 
            by using '.orig_csv' as extension or (ii) will be moved to the common 'backup_dir'.
            Of course, a unique file naming is assumed for the latter. If set to 'False', all 
            files will directly be deleted after conversion - USE THIS WITH CAUTION!!!
        verbose (bool, optional): Switch to display detailed information on converted files.
            Defaults to 'True'.  
    
    Returns:
        msg (int): Return code denoting state of operation (e.g. for signalling exceptions to 
            outside caller).
        success (list of str): List of successfully converted files (absolute filenames).          
    """
    
    if (verbose):
        print(f" + TASK: CONVERSION OF SPECTRUM FILES (=> {root})")
        
    # step 0: check / setup environment
    if ((target_dir is not None) and (not os.path.isdir(target_dir))):
        os.mkdir(target_dir)
    if (backup and (backup_dir is not None) and (not os.path.isdir(backup_dir))):
        os.mkdir(backup_dir)  
          
    # step 1: check for all new files matching the 'pattern' definition
    files_new = massfileop(root, pattern, mode='count', params=[], max_depth=5, 
                           dry=True, verbose=0)     
    
    # early skip (this) run?
    if (files_new == []):
        print(f"    ==> No new files found for conversion (skipping run)")
        return 0, []
   
    # step 2: prepare list of files to work on    
    if (target_dir is None):
        files_work = files_new
    else:
        try:            
            # copy new files to target/working folder
            for src_file in files_new:
                fname = os.path.basename(src_file)
                dest_file = os.path.join(target_dir, fname)
                shutil.move(src_file, dest_file)
                
            # get actual list of files to work on
            files_work = massfileop(target_dir, '\.csv', mode='count', params=[], max_depth=1,
                                    dry=True, verbose=0)
        except:
            print("    ==> !!!! INTERRUPTION during COPYING !!!! (external storage?)")
            return 1, []
            
    # Note: If a special 'target_dir' is used, another search on "original" CSV-files needs
    # to be conducted in order to SAFELY HANDLE POTENTIAL INTERRUPTIONS! Otherwise, any 
    # previously copied CSV-files are "orphaned" and will not get converted...
         
    # step 3: convert all spectrum files
    success = []
    N = len(files_work)   
    for n, the_file in enumerate(files_work, start=1):
        try:            
            if (verbose):
                print(f" {n}/{N} -> Converting {the_file}")
                        
            mod_file = x_convert_spectrum(the_file)
            success.append(mod_file)
            
            if (backup):
                if (backup_dir is None):
                    bkp_file = the_file[:-4]+'.orig_csv'
                else:                    
                    fname = os.path.basename(the_file)
                    bkp_file = os.path.join(backup_dir, fname[:-4]+'.orig_csv')
                shutil.move(the_file, bkp_file)
                if (verbose):
                    print(f"        Backing up to {bkp_file}")
            else:
                os.remove(the_file)
                if (verbose):
                    print(f"        Deleted {the_file}")
                    
        except:
            print("    ==> !!!! INTERRUPTION during CONVERSION !!!! (external storage?)")
            return 2, success            
                
    # summary
    if (not verbose):
        print(f"    ==> Found & successfully converted {N} files")        
         
    return 0, success



################################################################################################
#
# Explanation: "Spectrum format" (in CSV-files created by "CMS X-Tools")
#
#   This special format actually refers only to a SINGLE TIMESTAMP (= last sample of batch from
#   which FFT is computed), but carries the frequency information to the right (i.e. row) of the 
#   files.
#
#   That is:
#       line 1: header fields of "meta" information
#       line 2: values w/ the "meta" information
#       line 3: time of FFT batch; str 'Data'; list of frequency values (0 ... N-1)
#       line 4: FFT amplitude values (for each frequency)
#       line 5: FFT phase values (for each frequency)
#
################################################################################################