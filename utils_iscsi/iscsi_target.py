from __future__ import division
from base import utils_cmd


ISCSI_CONFIG_FILE = "/etc/iscsi/initiatorname.iscsi"

def run():
    """
    Export target in localhost for emulated iscsi
    """

    iqn = "iqn.2019-06.com.kvmqe:target0"

    # confirm if the target exists and create iSCSI target
    check_portal = utils_cmd.cmd_output('targetcli ls /iscsi 1',verbose=False)
    if "Targets: 0" not in check_portal:
        utils_cmd.cmd_output('yum install -y targetcli',verbose=False)

    # In fact, We've got two options here
    #
    # 1) Create a block backstore that usually provides the best
    #    performance. We can use a block device like /dev/sdb or
    #    a logical volume previously created,
    #     (lvcreate -name lv_iscsi -size 1G vg)
    # 2) Create a fileio backstore,
    #    which enables the local file system cache.

    # Create a fileio backstore
    utils_cmd.cmd_output('targetcli /backstores/fileio/ create file_or_dev=/home/osd0 name=osd0 size=20G'
                         ,verbose=False)

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
                             % iqn,verbose=False)

    # Create lun
    check_luns = utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/luns/ create /backstores/fileio/osd0'
                                      % iqn,verbose=False)
    if "lun0" not in check_luns:
        utils_cmd.cmd_output('targetcli /iscsi/%s/tpg1/ set attribute authentication=0'
                             % iqn,verbose=False)
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
    print('pass')

if __name__ == "__main__":
    iscsi_settest = run()

