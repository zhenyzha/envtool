#-*-coding:utf-8-*-
import os
import sys
import logging
from base import utils_cmd, utils_misc
from sys import version_info
from collections import OrderedDict
from platform import machine
from base import options_func
from base.utils_guest import Guest
from multiprocessing import Process
from base.utils_misc import waiting_procesor_bar, waiting_spin_procesor_bar
from base.utils_misc import py3_get_terminal_size, py2_get_terminal_size


color = utils_misc.Colored()
def create_opt_desc():
    dict = OrderedDict()
    dict['1'] = 'Setup bridge network.'
    dict['2'] = 'Setup iSCSI server.'
    dict['3'] = 'Setup Ceph server.(TODO)'
    dict['4'] = 'Download and bootstrap ipa.(TODO)'
    dict['l'] = 'List menu.'
    dict['q'] = 'Quit.'
    return dict


def main_loop(dict):
    brew = Brew()
    init_thread = Process(target=waiting_spin_procesor_bar,
                          args=('Initializing VMT ....', 0.1, ))
    init_thread.daemon = True
    init_thread.start()
    guest = Guest()
    init_thread.terminate()
    sys.stdout.write('\b')
    sys.stdout.flush()
    print(color.yellow('Done'))
    while 1:
        opt = utils_misc.py2_and_py3_input()
        # Setup bridge network
        if opt == '1':
            options_func.option_1()
        # Setup iSCSI server
        elif opt == '2':
            options_func.option_2()
        # Setup Ceph server.
        elif opt == '3':
            options_func.option_3()
        # Download and bootstrap ipa
        elif opt == '4':
            options_func.option_4()
        elif opt == 'l':
            utils_misc.usage(dict)
        elif opt not in opt_dict:
            print(color.yellow('No this option, please check it again.'))
        elif opt == 'q':
            break

if __name__ == "__main__":
    opt_dict = create_opt_desc()
    utils_misc.usage(opt_dict)
    main_loop(opt_dict)
    try:
        sys.exit(0)
    except:
        print(color.yellow('Quit Env Deployment Toolkit.'))
    finally:
        print(color.yellow('Bye bye !!!'))
