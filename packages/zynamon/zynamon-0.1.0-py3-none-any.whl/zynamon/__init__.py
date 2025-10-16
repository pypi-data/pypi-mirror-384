""" Generalized & powerful time-series class and related functions """

__author__ = 'Dr. Marcus Zeller (dsp4444@gmail.com)'
__version__ = '0.1.0'
__all__ = []

#from zynamon.cli import importer

def demo():
    print("This is a demo for the 'zynamon' package.")
    print("")
    print("Usage example:")
    print(">>> from zynamon.zeit import TimeSeries")
    print("")
    print(">>> ts.tags_register({'location': 'Erlangen', 'reason': 'Just-a-test'})")
    print(">>> apples = [0.1, 1.1, 2.9, 2.5, 3.4, 4, 3.1, 5.2]")
    print(">>> pears  = [10, 20, 30, 40, 50, 60, 70, 80]")
    print(">>> ts.samples_add(zip(apples, pears))")
    print(">>> ts.time_causalise()")
    print(">>> ts.time_align(res=1.0, shift='bwd', recon='mean')")
    print(">>> ts.print_items(25)")
    print(">>> print(ts.time.stat)")

# def demo_run():    
#     from zynamon.zeit import TimeSeries
#     ts = TimeSeries('MyTest')
#     return ts
