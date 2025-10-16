#!/usr/bin/env python3
"""Analyze data from more than one plane."""

import sys
from argparse import ArgumentParser
from pathlib import Path
from vdaq_ana import VDaqData, Progress

def main(fname):
    inp_file_path = Path(fname)
    if not inp_file_path.exists():
        print("Input file ", inp_file_path, " does not exist")
        return

    # open the vdaq file
    vdaq = VDaqData(fname)
    vdaq.show_info(show_modules=True)

    last_stamp = 0
    for ievt, evt in enumerate(vdaq):
        mid = evt.mod_id
        if mid != 999:
            print("Mod {:3d}, evtno {:6d}".format(mid, evt.evtcnt))
            data = vdaq.modules[mid].process_event(evt)
            if data is not None:
                for C in data:
                    print("  Ch {:.1f}: E {:.1f}".format(C.chan, C.E))
                    
            continue

        time_stamp = evt.time_stamp
        if last_stamp > 0:
            if time_stamp > last_stamp :
                delta_time = time_stamp-last_stamp
            else:
                delta_time = time_stamp + 0xffffffffffffffff - last_stamp


        else:
            delta_time = 1e-12

        high = time_stamp >> 32
        low  = time_stamp & 0xffffffff
        print("Mod {:3d}: evtno {:6d} Hig: {:8x} Low: {:8x} trigger: {:.3f}".format(mid, evt.evtcnt, high, low, 1.0e9/delta_time))
        last_stamp = time_stamp


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('files', nargs='*', help="Input files")

    options = parser.parse_args()
    if len(options.files) == 0:
        print(sys.argv[0])
        print("I need an input file")
        sys.exit()

    main(options.files[0])
