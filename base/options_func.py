#-*-coding:utf-8-*-
import os
import sys
from platform import machine
from base import utils_misc, utils_cmd
import re
from base.utils_misc import waiting_procesor_bar, waiting_spin_procesor_bar
from multiprocessing import Process
import time
import socket
from utils_iscsi import iscsi_target
import string
import configparser


color = utils_misc.Colored()
def create_extra_repo():
    pass


def install_qemu_package(nvr):
    found = False
    download_file = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))),'downloads')
    if os.path.exists(download_file):
        for pkg in os.listdir(download_file):
            if pkg == (nvr + '.' + machine()):
                found = True
                break
        if found:
            utils_cmd.cmd_output('yum remove -y qemu-*')
            utils_cmd.cmd_output('cd %s;yum install -y *' %
                                 (os.path.join(download_file, pkg)))
        else:
            download_dir, ret = utils_brew.brew_download_rpms(rpm_nvr=nvr,
                                                              arch=machine())
            if not ret:
                return  False
            utils_cmd.cmd_output('yum remove -y qemu-*')
            utils_cmd.cmd_output('cd %s;yum install -y *' % download_dir)
    else:
        download_dir, ret = utils_brew.brew_download_rpms(rpm_nvr=nvr,
                                                          arch=machine())
        if not ret:
            return False
        utils_cmd.cmd_output('yum remove -y qemu-*')
        utils_cmd.cmd_output('cd %s;yum install -y *' % download_dir)
    s, o = utils_cmd.cmd_status_output('/usr/libexec/qemu-kvm --version')
    print(o)
    if s !=0:
        print(color.red('Failed to install qemu package.'))
        return False
    else:
        return True


def option_1():
    net_thread = Process(target=waiting_spin_procesor_bar,
                         args=('Configuring bridge network ....', 0.2))
    net_thread.daemon = True
    net_thread.start()

    #get localhost IP
    def get_host_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    #setup bridge
    nic_ip = get_host_ip()
    nic_status = utils_cmd.cmd_output('ip addr | grep %s' % nic_ip, verbose=False)
    nic_name = nic_status.split(" ")[-1].strip('\n')
    connection = utils_cmd.cmd_output('nmcli device show %s | grep GENERAL.CONNECTION'
                         % nic_name, verbose=False)
    conid = re.split(r'\s{2,}',connection)[-1].strip('\n')

    utils_cmd.cmd_output('nmcli con add type bridge ifname switch con-name switch stp no'
                         , verbose=False)
    utils_cmd.cmd_output('nmcli con modify \'%s\' master switch' % conid
                         , verbose=False)
    utils_cmd.cmd_output('nmcli con up \'%s\'' % conid
                         , verbose=False)
    if utils_cmd.cmd_output('[ $? -ne 1 ]', verbose=False):
        print('NetworkManager Command failed')

    #check_bridge
    def check_bridge_dev_ip():
        start = time.time()
        # get_ip = False
        while time.time() - start <= 120:
             if utils_cmd.cmd_output('ifconfig switch | grep inet| awk {print\$2}'
                                     , verbose=False).split("\n")[0] is None:
                 time.sleep(5)
                 continue
             else:
                 get_ip = True
                 break

        if not get_ip:
             print('Fail to get ip address of bridge device in 2 mins')
    check_bridge_dev_ip()


    #write configuration file
    utils_cmd.cmd_output('echo \"#!/bin/sh\nswitch=switch\nip link set \$1 up\n'
                         'ip link set dev \$1 master \${switch}\n'
                         'ip link set \${switch} type bridge forward_delay 0\n'
                         'ip link set \${switch} type bridge stp_state 0\" > /etc/qemu-ifup'
                         , verbose=False)

    utils_cmd.cmd_output('echo \"#!/bin/sh\nswitch=switch\nip link set \$1 down\n'
                         'ip link set dev \$1 nomaster\" > /etc/qemu-ifdown'
                         , verbose=False)

    utils_cmd.cmd_output('chmod a+rx /etc/qemu-if*',verbose=False)
    net_thread.terminate()
    sys.stdout.write('\b')
    sys.stdout.flush()
    print(color.yellow('Done'))


def option_2():
    iscsi_target.run()


def option_3():
    s, o = utils_cmd.cmd_status_output('which ceph')
    if s:
        pack_list = []
        rel_ver = utils_cmd.cmd_output(cmd='cat /etc/redhat-release | '
                                           'grep -oE \'[0-9]+\.[0-9]+\'| '
                                           'cut -d\'.\' -f1', verbose=False)

        lttng_ust_list = utils_brew.brew_search('lttng-ust')
        leaste_lttng_ust = sorted(
            [lttng_ust for lttng_ust in lttng_ust_list
             if re.match(r'^lttng-ust-\d.*\.el%s$'
                         % rel_ver.strip('\n'), lttng_ust)])[-1]
        print(leaste_lttng_ust)
        pack_list.append(leaste_lttng_ust)

        python_flask_list = utils_brew.brew_search('python-flask')
        leaste_python_flask = sorted(
            [python_flask for python_flask in python_flask_list
             if re.match(r'^python-flask-\d.*\.el%s'
                         % rel_ver.strip('\n'), python_flask)])[-1]
        print(leaste_python_flask)
        pack_list.append(leaste_python_flask)

        python_werkzeug_list = utils_brew.brew_search('python-werkzeug')
        leaste_python_werkzeug = sorted(
            [python_werkzeug for python_werkzeug in python_werkzeug_list
             if re.match(r'^python-werkzeug-\d.*\.el%s'
                         % rel_ver.strip('\n'), python_werkzeug)])[-1]
        print(leaste_python_werkzeug)
        pack_list.append(leaste_python_werkzeug)

        python_itsdangerous_list = utils_brew.brew_search('python-itsdangerous')
        leaste_python_itsdangerous = sorted(
            [python_itsdangerous for python_itsdangerous in python_itsdangerous_list
             if re.match(r'^python-itsdangerous-\d.*\.el%s'
                         % rel_ver.strip('\n'), python_itsdangerous)])[-1]
        print(leaste_python_itsdangerous)
        pack_list.append(leaste_python_itsdangerous)

        userspace_rcu_list = utils_brew.brew_search('userspace-rcu')
        leaste_userspace_rcu = sorted(
            [userspace_rcu for userspace_rcu in userspace_rcu_list
             if re.match(r'^userspace-rcu-\d.*\.el%s'
                         % rel_ver.strip('\n'), userspace_rcu)])[-1]
        print(leaste_userspace_rcu)
        pack_list.append(leaste_userspace_rcu)

        ceph_list = utils_brew.brew_search('ceph')
        leaste_ceph = sorted(
            [ceph for ceph in ceph_list
             if re.match(r'^ceph-\d.*\.el%scp$'
                         % rel_ver.strip('\n'), ceph)])[-1]
        print(leaste_ceph)
        pack_list.append(leaste_ceph)

        for pak in pack_list:
            download_dir, ret = utils_brew.brew_download_rpms(rpm_nvr=pak,
                                                              arch=machine())
            if not ret:
                print(color.red('Please check package NVR or '
                                'search it before download.'))


def option_4():
    print('TODO')
    pass


if __name__ == "__main__":
    # create_qemu_ifdown_script('switch')
    # create_qemu_ifup_script('switch')
    print(utils_cmd.cmd_output('ifconfig switch | grep inet', verbose=False).splitlines()[0].split()[1])
