#!/usr/bin/env python3
"""
Simple example script for running notebooks and reporting exceptions.

Usage: `run-ipynb.py foo.ipynb [bar.ipynb [...]]`

Each cell is submitted to the kernel, and checked for errors.

Source: https://gist.github.com/AliMirlou/11143323b2bbfe3f5207c63bdc31db00
"""

import os
import sys
from queue import Empty

from jupyter_client.manager import KernelManager

from nbformat import read, current_nbformat


def run_notebook(nb):
    km = KernelManager()
    km.start_kernel(stderr=open(os.devnull, 'w'))

    kc = km.client()
    kc.start_channels()

    cells = failures = 0
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue

        kc.execute(cell.source)

        # Wait to finish, maximum for 3 hour
        try:
            reply = kc.get_shell_msg(timeout=10800)['content']
        except Empty:
            reply = {'status': 'error', 'traceback': ["Cell execution timed out!"]}
        if reply['status'] == 'error':
            failures += 1
            print("\nFAILURE:")
            print(cell.source)
            print('-----')
            print("Raised:")
            print('\n'.join(reply['traceback']))
        cells += 1
        sys.stdout.write('.')

    kc.stop_channels()

    km.shutdown_kernel()

    return cells, failures


if __name__ == '__main__':
    for ipynb in sys.argv[1:]:
        print('Running notebook "%s"...' % ipynb)

        nb = read(ipynb, current_nbformat)
        cells, failures = run_notebook(nb)

        print("    Cells ran: %i" % cells)
        print("    Cells raised exception: %i" % failures)
