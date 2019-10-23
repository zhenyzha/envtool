#-*-coding:utf-8-*-
from base.base_vmt import Base, Color
from doctor_python.collection_unit.brew_collection import BrewCollection
from base.utils_misc import py2_and_py3_input, convert_to_str
from base.utils_misc import py2_get_terminal_size, py3_get_terminal_size
import os
from platform import machine
import sys
import re
from collections import OrderedDict
from base.utils_cmd import cmd_status_output, cmd_output
from sys import version_info
from doctor_python.common.shell import doctor_cmd_output
import time
from threading import Thread
from base.utils_misc import waiting_spin_procesor_bar
from multiprocessing import Process
from .options_func import install_update_qemu_plus


if version_info.major == 3:
    from urllib.request import urlopen
elif version_info.major == 2:
    from urllib2 import urlopen


class Guest(object):
    def __init__(self):
        self.color = Color()
        self.server = {}
        self.server['bos_url'] = 'http://download.eng.bos.redhat.com/'
        self.server['pek2_url'] = 'http://download.eng.pek2.redhat.com/'
        self.base_url = self.chose_server()
        if version_info.major == 3:
            _, self.columns = py3_get_terminal_size()
        elif version_info.major == 2:
            _, self.columns = py2_get_terminal_size()

    def convert_to_kb(self, size):
        if 'G' in size:
            return float(size[:-1]) * float(1024) * float(1024)
        elif 'M' in size:
            return float(size[:-1]) * float(1024)

    def download_procesor_bar(self, file, total_size):
        start_time = time.time()
        sys.stdout.write('[')
        long_size = int(self.columns / 2)
        sys.stdout.write(' ' * long_size)
        sys.stdout.write(']')
        sys.stdout.flush()
        cur_pos = 1
        unit_size = self.convert_to_kb(total_size) / float(long_size)
        while cur_pos <= long_size:
            step = 0
            while step <= ((long_size + 1) - cur_pos):
                sys.stdout.write('\b')
                step += 1
            sys.stdout.write('>')
            sys.stdout.write(' ' * (long_size - cur_pos))
            sys.stdout.write(']')

            sys.stdout.flush()
            check_cmd = 'ls -l --block-size=K %s' % file
            while float(
                    re.findall(r'\d+K', cmd_output(check_cmd, 10, False))[0][:-1])\
                    <= float(unit_size * cur_pos):
                pass
            cur_pos += 1
        download_time = time.time() - start_time
        download_size = cmd_output('du -h %s' % file, verbose=False).split()[0]
        self.color.print_yellow(' Total Time: %0.2f sec.' % download_time)
        self.color.print_yellow(' ' * (long_size + 3) + 'Total Size: %s.'
                                % download_size)

    def _get_input_info(self, prompt):
        info = py2_and_py3_input(prompt).strip()
        if info == 'q':
            return 'q'
        return info

    def chose_server(self):
        self.rtt_avg = {}
        rtt_min = 1000
        server_url = ''
        for name, url in self.server.items():
            cmd = 'ping %s -c 2' % url.split('/')[2]
            ping_output = cmd_output(cmd=cmd, verbose=False)
            self.rtt_avg[url] = float(ping_output.splitlines()[-1].split('/')[-3])
            if self.rtt_avg[url] <= rtt_min:
                rtt_min = self.rtt_avg[url]
                server_url = url
        return server_url

    def get_os_list(self, name):
        regex = r'href=\"%s' % name
        version = ['rel-eng', 'nightly']
        for ver in version:
            t = Process(target=waiting_spin_procesor_bar,
                        args=('Searching for \"%s\" in %s ....'
                              % (name, ver), 0.2,))
            t.daemon = True
            t.start()
            url = self.base_url + ver
            html = urlopen(url)
            rhel_list = OrderedDict()
            t.terminate()
            sys.stdout.write('\b')
            sys.stdout.flush()
            self.color.print_yellow('Done')
            division_line = '*' * int((self.columns - len(ver)) / 2) + \
                            '%s' % ver + \
                            '*' * int((self.columns - len(ver)) / 2)
            self.color.print_yellow(division_line)
            for info in html.read().splitlines():
                info = convert_to_str(info)

                if re.search(regex, info, re.IGNORECASE):
                    # print(info)
                    uptime = re.sub(r'\s+-', '',
                                    re.split(r'</a>\s+', info)[-1])
                    os_name = re.sub(r'//\s+', '', info.split('\"')[5]).strip(
                        '/')
                    rhel_list[os_name] = uptime
                    if os_name and uptime:
                        self.color.print_green(
                            '{:<50}| Update time:{}'.format(os_name, uptime))

        if not rhel_list:
            sys.stdout.write('\b')
            sys.stdout.flush()
            self.color.print_yellow('Done')
            self.color.print_red('No found such OS on server.')

    def get_os_list_option(self):
        while 1:
            name = py2_and_py3_input(
                'Please input os name searched:').strip()
            if name == 'q':
                return 'q'
            elif not name:
                continue
            self.get_os_list(name)

    def get_iso_url(self, os_name, arch):
        iso_url = ''
        iso_size = ''
        for version in ['rel-eng', 'nightly']:

            url = self.base_url + '%s/%s/compose/Server/%s/iso/' \
                  % (version, os_name, arch)
            try:
                html = urlopen(url)
                for info in html.read().splitlines():
                    info = convert_to_str(info)
                    if re.search(r'.*dvd1\.iso</a>', info):
                        iso_url = url + info.split('"')[5]
                        iso_size = info.split()[-1]
                        return (iso_url, iso_size)
            except Exception as e:
                url = self.base_url + '%s/%s/compose/BaseOS/%s/iso/' \
                      % (version, os_name, arch)
                try:
                    html = urlopen(url)
                    for info in html.read().splitlines():
                        info = convert_to_str(info)
                        if re.search(r'.*dvd1\.iso</a>', info):
                            iso_url = url + info.split('"')[5]
                            iso_size = info.split()[-1]
                            return (iso_url, iso_size)
                except:
                    continue

        if not iso_url:
            self.color.print_red('No found %s iso for %s.'
                                 % (os_name, arch))

    def download_iso(self, iso_info):
        pattern = re.compile(r'\s*,\s*|\s*;\s*|\s+')
        arch = ''
        os_name = ''
        if len(pattern.split(iso_info)) == 2:
            for param in pattern.split(iso_info):
                if not param:
                    self.color.print_red('Need two arguments.')
                    continue
                else:
                    if re.match(r'^ppc64$|^ppc64le$|^x86_64$|^s390x$', param):
                        arch = param
                    else:
                        os_name = param
        elif len(pattern.split(iso_info)) > 2:
            self.color.print_red('Too many arguments.')
            return None
        elif len(pattern.split(iso_info)) == 1:
            self.color.print_red('Need two arguments.')
            return None
        elif not pattern.search(iso_info):
            return None
        if os_name and arch:
            download_url, download_size = self.get_iso_url(os_name, arch)
            download_file = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))),
                'downloads')
            if not os.path.exists(download_file):
                os.mkdir(download_file)
            isos_dir = os.path.join(download_file, 'isos')
            if not os.path.exists(isos_dir):
                os.mkdir(isos_dir)
            download_cmd = 'cd %s && curl -O %s -s' % (isos_dir, download_url)
            self.color.print_green('Downloading: %s.' % download_url)
            file_name = os.path.join(isos_dir, download_url.split('/')[-1])
            download_thread = Thread(target=doctor_cmd_output,
                                     args=(download_cmd, 3600, False))
            download_thread.daemon = True
            download_thread.start()
            while bool(re.search(
                    r'No such file or directory',
                    cmd_output('ls %s' % file_name, verbose=False))):
                pass

            self.download_procesor_bar(file=file_name,
                                       total_size=download_size)
            self.color.print_yellow('Downloaded files: %s' % isos_dir)

        else:
            self.color.print_red('Please input correct os name and arch.')
            return None

    def download_iso_option(self):
        while 1:
            iso_info = py2_and_py3_input(
                'Please input iso name and arch downloaded:').strip()
            if iso_info == 'q':
                return 'q'
            elif not iso_info:
                continue
            if not self.download_iso(iso_info):
                continue

    def create_iamge(self, image_format, filename, size):
        s, _ = cmd_status_output(cmd='which qemu-img', verbose=False)
        if s:
            self.color.print_red('No found qemu-img.')
            install_update_qemu_plus()
        create_cmd = 'qemu-img create -f %s %s %s' % (image_format, filename, size)
        s, o = cmd_status_output(cmd=create_cmd, verbose=False)
        if s:
            self.color.print_red('Failed to create image')
            print(create_cmd)
            print(o)
            return False
        return True

    def boot_up_guest(self):
        pass

    def start_to_install_guest(self, image_format, filename, size):
        if self.create_iamge(image_format, filename, size):
            self.boot_up_guest()
        else:
            return False

    def install_guest_option(self):
        while 1:
            platform = py2_and_py3_input(
                'Please input platform to install:').strip()
            if platform == 'q':
                return 'q'
            if not platform:
                continue
            if re.match(r'^ppc64$|^ppc64le$|^x86_64$|^s390x$', platform):
                while 1:
                    os_version = py2_and_py3_input(
                        'Please input OS Version to install:').strip()
                    if os_version == 'q':
                        return 'q'
                    if not os_version:
                        continue
                    else:
                        self.get_os_list(os_version)
                        while 1:
                            os_compose = py2_and_py3_input(
                                'Please input OS Compose to install:').strip()
                            if os_compose == 'q':
                                return 'q'
                            if not os_compose:
                                continue
                            else:
                                if not self.download_iso((os_compose + ',' + platform)):
                                    continue
                                else:
                                    while 1:
                                        drive_format = py2_and_py3_input(
                                            'Please input drive format to install:').strip()
                                        if drive_format == 'q':
                                            return 'q'
                                        if not drive_format:
                                            continue
                                        else:
                                            while 1:
                                                iamge_format = py2_and_py3_input(
                                                    'Please input image format to install:').strip()
                                                if iamge_format == 'q':
                                                    return 'q'
                                                if not iamge_format:
                                                    continue
                                                else:
                                                    # self.start_to_install_guest()
                                                    pass
            else:
                self.color.print_red('Please input correct platform.')
                continue


if __name__ == '__main__':
    pass