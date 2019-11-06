from __future__ import division
import re
import sys
from multiprocessing import Process
from base import options_func, utils_cmd, utils_misc, utils_numeric
from base.utils_misc import waiting_spin_procesor_bar


ISCSI_CONFIG_FILE = "/etc/iscsi/initiatorname.iscsi"
color = utils_misc.Colored()

def run():
    """
    Basic iscsi support for Linux host with the help of commands
    iscsiadm and tgtadm:

    1) Create a fileio backstore,
       which enables the local file system cache.
    2) Check fileio backstore
    3) Create a target name: /etc/iscsi/initiatorname.iscsi
    4) Create a iscsi lun and check
    5) Set initiatorname with local initiatorname
    6) Set firewall add tcp port=3260, if it's enabled
    7) initiator iSCSI login
    """

    def _exist_lun():
        output = utils_cmd.cmd_output(
            'targetcli ls /backstores/fileio/', verbose=False)
        searched = re.search(r'(\d+\d?)', output)
        return searched.group(1)

    def _check_rpm():
        check_portal = utils_cmd.cmd_output('targetcli ls /iscsi 1', verbose=False)
        if "Targets: 0" not in check_portal:
            utils_cmd.cmd_output('yum install -y targetcli', verbose=False)

    def _check_localhost_space():
        folder_list = ((utils_cmd.cmd_output('df /home'
                                             , verbose=False)).split())
        int_size = int(folder_list[-3]) / 1024
        if float(image_size_all) >= int_size:
            net_thread.terminate()
            sys.stdout.write('\b')
            sys.stdout.flush()
            print(color.yellow('Done'))
            print(color.red("There is not enough space on /home"))
        else:
            return True

    def _create_backstore():
            status, output = utils_cmd.cmd_status_output(
                'targetcli /backstores/fileio/ create file_or_dev=/home/osd%s '
            'name=osd%s size=%sM'% (exist_lun, exist_lun, image_size2), verbose=False)
            if status !=0:
                net_thread.terminate()
                sys.stdout.write('\b')
                sys.stdout.flush()
                print(color.yellow('Done'))
                print(color.red('Command Error: %s.' % output))
            else:
                return True

    def _create_iqn():
        # Create an IQN with a target named target_name
        utils_cmd.cmd_output('targetcli /iscsi/ create %s'
                             % iqn,verbose=False)
        check_portal = utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/portals ls'
                                            % iqn,verbose=False)
        if "0.0.0.0:3260" not in check_portal:
            # Create portal
            # 0.0.0.0 means binding to INADDR_ANY
            # and using default IP port 3260
            utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/portals/ '
            'create 0.0.0.0 3260'% iqn, verbose=False)

    def _create_lun():
        # Create lun and check
        check_luns = utils_cmd.cmd_output(
            'targetcli /iscsi/%s/tpg1/luns/ create /backstores/fileio/osd%s'
                                          % (iqn,exist_lun), verbose=False)
        if ('lun%s' % exist_lun) not in check_luns:
            utils_cmd.cmd_output(
                'targetcli /iscsi/%s/tpg1/ set attribute authentication=0'
                                 % iqn, verbose=False)
            utils_cmd.cmd_output(
                'targetcli /iscsi/%s/tpg1/ set attribute demo_mode_write_protect=0'
                                 % iqn, verbose=False)
            utils_cmd.cmd_output(
                'targetcli /iscsi/%s/tpg1/ set attribute generate_node_acls=1'
                                 % iqn, verbose=False)

    def _set_initname():
        # Set initiatorname
        check_init = utils_cmd.cmd_output('cat /etc/iscsi/initiatorname.iscsi'
                                          , verbose=False)
        init_name = check_init.split("=")[-1]
        utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/acls/ create %s'
                             % (iqn,init_name.strip('\n')), verbose=False)

    def _add_firewall_port():
        # Set firewall if it's enabled
        firewall_sta = utils_cmd.cmd_output("firewall-cmd --state", verbose=False)
        if "^running" in firewall_sta:
            utils_cmd.cmd_output("firewall-cmd --permanent --add-port=3260/tcp",
                                 verbose=False)
            utils_cmd.cmd_output("firewall-cmd --reload", verbose=False)

    def _save_config():
        # Save configuration
        utils_cmd.cmd_output('targetcli / saveconfig', verbose=False)
        # Restart iSCSI service
        utils_cmd.cmd_output('systemctl restart target.service', verbose=False)

    def _login_iscsi():
        # initiator iSCSI and login
        iscsi_login = utils_cmd.cmd_output(
            'iscsiadm -m discovery -t st -p 0.0.0.0:3260', verbose=False)
        targ_name = iscsi_login.split(" ")[-1]
        utils_cmd.cmd_output(
            'iscsiadm -m node -T %s -u' % (targ_name.strip('\n')),verbose=False)
        utils_cmd.cmd_output(
            'iscsiadm -m node -T %s -l' % (targ_name.strip('\n')),verbose=False)

    iqn = "iqn.2019-06.com.kvmqe:target0"
    net_thread = Process(target=waiting_spin_procesor_bar,
                         args=('Configuring iscsi ....', 0.2))
    net_thread.daemon = True
    image_size = input('please input the lun size : ')
    image_size1 = (utils_numeric.normalize_data_size(image_size))
    image_size2 = re.search(r'(\d{1,10})+(\.)?',image_size1).group(1).rstrip('.')
    image_size_all = float(utils_numeric.normalize_data_size(image_size))

    if int(image_size2) == 0:
        print(color.yellow('Configuring iscsi ...Done'))
        print(color.red('The lun size setting error, please enter again.'))
        options_func.option_2()
    else:
        net_thread.start()
        _check_rpm()
        exist_lun = _exist_lun()
        if _check_localhost_space():
            if _create_backstore():
                _create_iqn()
                _create_lun()
                _set_initname()
                _add_firewall_port()
                _save_config()
                _login_iscsi()
                net_thread.terminate()
                sys.stdout.write('\b')
                sys.stdout.flush()
                print(color.yellow('Done'))
                print(color.green('create lun%s: %sM' % (exist_lun, image_size2)))
                info_iscsi = utils_cmd.cmd_output('targetcli ls /iscsi',
                                                  verbose=False)
                print(
                    color.green(re.search(r'(.*)iscsi(.*)]', info_iscsi).group(0)))
                print(color.green(re.search(r'(.*)iqn(.*)]', info_iscsi).group(0)))
                print(
                    color.green(re.search(r'(.*)tpg1(.*)]', info_iscsi).group(0)))
                print(color.green(
                    re.search(r'(.*) acls (.*)]', info_iscsi).group(0)))
                print(
                    color.green(re.search(r'(.*)LUNs:(.*)]', info_iscsi).group(0)))
                print(color.green(
                    re.search(r'(.*)lun%s(.*)]' % exist_lun, info_iscsi).group(0)))
                print(color.green(
                    re.search(r'(.*)portals(.*)]', info_iscsi).group(0)))
                print(
                    color.green(re.search(r'(.*)3260(.*)]', info_iscsi).group(0)))
            else:
                options_func.option_5()
        else:
            options_func.option_5()


if __name__ == "__main__":
    iscsi_settest = run()

