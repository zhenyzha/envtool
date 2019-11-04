from __future__ import division
import re
import sys
from multiprocessing import Process
from base import utils_cmd, utils_misc, utils_numeric, user_exception
from base.utils_misc import waiting_spin_procesor_bar


ISCSI_CONFIG_FILE = "/etc/iscsi/initiatorname.iscsi"
color = utils_misc.Colored()

def run():
    """
    Export target in localhost for emulated iscsi
    """

    iqn = "iqn.2019-06.com.kvmqe:target0"
    net_thread = Process(target=waiting_spin_procesor_bar,
                         args=('Configuring iscsi ....', 0.2))
    net_thread.daemon = True

    # confirm if the target exists and create iSCSI target
    check_portal = utils_cmd.cmd_output('targetcli ls /iscsi 1',verbose=False)
    if "Targets: 0" not in check_portal:
        utils_cmd.cmd_output('yum install -y targetcli',verbose=False)

    # In fact, We've got two options here
    #
    # 1) Create a block backstore that usually provides the best
    #    performance. We can use a block device like /dev/sdb or
    #    a logical volume previously created,
    #     (lvcreate -name lv_iscsi -size size __G vg)
    # 2) Create a fileio backstore,
    #    which enables the local file system cache.

    #new lun number
    img_number = input('please input the lun number: ')

    #Detect the number of luns that already exist
    def exist_lun():
        output = utils_cmd.cmd_output(
            'targetcli ls /backstores/fileio/', verbose=False)
        searched = re.search(r'(\d+\d?)', output)
        return searched.group(1)

    #the number of all luns
    exist_lun = exist_lun()
    all_lun_number = (int(img_number) + int(exist_lun))

    #image size
    image_size = input('please input the lun size __G: ')
    folder_list = ((utils_cmd.cmd_output('df /home'
                                         , verbose=False)).split())
    int_size = int(folder_list[-3]) / 1024
    image_size1 = (utils_numeric.normalize_data_size(image_size))
    image_size2 = re.search(r'(\d{1,10})+(\.)?',image_size1).group(1).rstrip('.')
    image_size_all = (float(utils_numeric.normalize_data_size(image_size)) * int(all_lun_number))

    net_thread.start()

    for i in list(range(int(exist_lun) + 1, int(all_lun_number) + 1)):
        if float(image_size_all) >= int_size:
            print(color.red("space overflow"))
        else:
            status, output = utils_cmd.cmd_status_output(
                'targetcli /backstores/fileio/ create file_or_dev=/home/osd%s name=osd%s size=%sM'
                 % (i, i, image_size2), verbose=False)
            if status !=0:
                print(color.red('Command Error: %s.' % output))

    # Check backstore
    for i in list(range(int(exist_lun) + 1, int(all_lun_number) + 1)):
        pattern = ('osd%s' % i)
        check_return = utils_cmd.cmd_output('targetcli ls /backstores/fileio/', verbose=False)
        match = re.search(pattern, check_return).group(0)
        if pattern not in match:
            print(color.red('create backstore failed'))
            sys.exit(0)
        else:
            print(color.yellow('create backstore success'))

    # Create an IQN with a target named target_name
    utils_cmd.cmd_output('targetcli /iscsi/ create %s'
                         % iqn,verbose=False)

    check_portal = utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/portals ls'
                                        % iqn,verbose=False)
    if "0.0.0.0:3260" not in check_portal:
        # Create portal
        # 0.0.0.0 means binding to INADDR_ANY
        # and using default IP port 3260
        utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/portals/ create 0.0.0.0 3260'
                             % iqn, verbose=False)

    # Create lun
    for i in list(range(int(exist_lun) + 1 , int(all_lun_number) + 1)):
        check_luns = utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/luns/ create /backstores/fileio/osd%s'
                                          % (iqn,i), verbose=False)
        if "lun0" not in check_luns:
            utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/ set attribute authentication=0'
                                 % iqn, verbose=False)
            utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/ set attribute demo_mode_write_protect=0'
                                 % iqn,verbose=False)
            utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/ set attribute generate_node_acls=1'
                                 % iqn,verbose=False)

    # Set initiatorname
    check_init = utils_cmd.cmd_output('cat /etc/iscsi/initiatorname.iscsi',verbose=False)
    init_name = check_init.split("=")[-1]
    utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/acls/ create %s'
                         % (iqn,init_name.strip('\n')),verbose=False)

    # Set firewall if it's enabled
    firewall_sta = utils_cmd.cmd_output("firewall-cmd --state",verbose=False)
    if "^running" in firewall_sta:
        # firewall is running
        process.system("firewall-cmd --permanent --add-port=3260/tcp",verbose=False)
        process.system("firewall-cmd --reload",verbose=False)

    # Save configuration
    utils_cmd.cmd_output('targetcli / saveconfig',verbose=False)

    # Restart iSCSI service
    utils_cmd.cmd_output('systemctl restart target.service',verbose=False)

    # initiator iSCSI login
    iscsi_login = utils_cmd.cmd_output('iscsiadm -m discovery -t st -p 0.0.0.0:3260',verbose=False)
    targ_name = iscsi_login.split(" ")[-1]
    utils_cmd.cmd_output('iscsiadm -m node -T %s -l' % (targ_name.strip('\n')),verbose=False)
    net_thread.terminate()
    sys.stdout.write('\b')
    sys.stdout.flush()
    print(color.yellow('Done'))

if __name__ == "__main__":
    iscsi_settest = run()
