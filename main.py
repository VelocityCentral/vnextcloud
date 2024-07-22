import argparse
import os.path

import onxtcld
import sys
import logging
from prontoencryption import ProntoEncryption
from logging.handlers import RotatingFileHandler
import configparser

applog = logging.getLogger('applog')
global_url = None
global_nextcloudroot = None
global_applog = None
global_loglevel = 'DEBUG'
global_datalog = None
global_prontourl = None
global_prontoapiwebresource = None
global_prontoapiuser = None
global_prontoapipassword = None
global_users = []


def process_config(configfilename):
    """
    Read the configuration and set global variables.

    ****** Note that logging has not yet been established *********

    :param configfilename:
    :return:
    """
    config = configparser.ConfigParser()
    config.read(configfilename)
    sections = config.sections()
    if 'SETUP' not in sections:
        raise ValueError("Setup section missing from config file (File : {})".format(configfilename))
    if 'USERPASSWORDS' not in sections:
        raise ValueError("User Passwords section missing from config file (File : {})".format(configfilename))
    global global_url
    global global_applog
    global global_datalog
    global global_loglevel
    global global_prontourl
    global global_users
    global global_nextcloudroot
    global global_prontoapiwebresource
    global global_prontoapiuser
    global global_prontoapipassword
    try:
        if 'url' in config['SETUP']:
            global_url = config['SETUP']['url']
        else:
            raise ValueError('Nextcloud URL not specified in Configuration File')
        if 'nextcloudroot' in config['SETUP']:
            global_nextcloudroot = config['SETUP']['nextcloudroot']
        else:
            raise ValueError('Nextcloud data root not specified in Configuration File.')
        if 'applog' in config['SETUP']:
            global_applog = config['SETUP']['applog']
            # do not set the loglevel unless the logfile has also been set.
            if 'loglevel' in config['SETUP']:
                global_loglevel = config['SETUP']['loglevel'].upper()
        else:
            print("WARNING:No Application Logging Defined")
        if 'datalog' in config['SETUP']:
            global_datalog = config['SETUP']['datalog']
        if 'prontourl' in config['SETUP']:
            global_prontourl = config['SETUP']['prontourl']
            if 'prontoapiwebresource' in config['SETUP']:
                global_prontoapiwebresource = config['SETUP']['prontoapiwebresource']
            if 'prontoapiuser' in config['SETUP']:
                global_prontoapiuser = config['SETUP']['prontoapiuser']
            if 'prontoapipassword' in config['SETUP']:
                global_prontoapipassword = passworddecrypt(config['SETUP']['prontoapipassword'])
            if global_prontourl is not None \
                    and ( global_prontoapipassword is None
                          or global_prontoapiwebresource is None
                          or global_prontoapiuser is None):
                applog.error("Pronto API is not configured correctly")
                raise ConnectionError("Pronto API is not configured correctly")
        # Users
        for user in config['USERPASSWORDS']:
            global_users.append({'user': user, 'password': config['USERPASSWORDS'][user]})
    except Exception as err:
        raise ValueError("Error Setting Global Value from Config ({})".format(str(err)))


def setup_ok():
    """
    By the time this is called all the setup should be done.
    Each variable is checked and an error raised if annything looks incorrect
    :return: True (or some error)
    """
    if not isinstance(global_url, str):
        raise ValueError("The nextcloud URL is not a string")
    if len(global_url) == 0:
        raise ValueError("The nextcloud url is not defined")
    if len(global_users) == 0:
        raise ValueError("There are no users defined in the configuration file")
    if global_prontourl is not None:
        if global_prontoapiuser is None or global_prontoapipassword is None:
            raise ValueError("The configuration file must contain a user id and password for the pronto api")
        if len(global_prontoapiuser) == 0:
            raise ValueError("The pronto api user id is empty")
        if len(global_prontoapipassword) == 0:
            raise ValueError("The pronto api password is empty")
    return True


def process_arguments():
    """
    Process program arguments.

    ****** Note that logging has not yet been established *********

    :return: Arguments object
    """
    inifile = "vnextcloud.ini"
    thispath = os.path.dirname(__file__)
    if os.path.exists(thispath + "/vnextcloud.ini"):
        inifile = thispath + "/vnextcloud.ini"
    parser = argparse.ArgumentParser(description="Process new vnextcloud file")
    parser.add_argument('--file', action='store', required=True,
                        help="The path of the file (owned by the user) e.g. Documents/products/EQ100.jpg)")
    parser.add_argument('--owner', action='store', required=True,
                        help="The user name of the person who owns the file")
    parser.add_argument('--configfile', action='store', required=False, default=inifile,
                        help="Configuration file")
    parser.add_argument('--create-public-share', action='store_true', required=False,
                        help='Create a public share for the file')
    parser.add_argument('--public-keyword', action='store', required=False,
                        help='Only create a public share if the public share keyword is found in the path')
    args = parser.parse_args()
    return args


def establish_logging():
    if global_applog is None:
        loghandler = logging.StreamHandler()
    else:
        loghandler = RotatingFileHandler(filename=global_applog, maxBytes=1000000, backupCount=3)
    fmt = '%(asctime)s|%(filename)s|%(funcName)s|%(levelname)s|%(message)s'
    fmt_date = '%Y-%m-%d|%H:%M:%S'
    formatter = logging.Formatter(fmt, fmt_date)
    loghandler.setFormatter(formatter)
    applog.addHandler(loghandler)
    applog.setLevel(logging.ERROR)


def get_relative_path(root, owner, path):
    """
    Strip off the leading components of the path
    :param root: The leading part of the path to the nextcloud data directory.
                e.g. "/var/www/html/nextcloud/data/
    :param owner: The name of the file owner.
    :param path: The full path to the file
        eg: :/var/www/html/nextcloud/data/noddy/files/Documents/TESTFLOW/timesheet.json
    :return: The remaining part
        eg: Documents/TESTFLOW/timesheet.json
    """
    relative_path = ""
    if root == path[:len(root)]:
        relative_path = path[len(root) + 1:]
    if relative_path[0] == "/":
        relative_path = relative_path[1:]
    if owner == relative_path[:len(owner)]:
        relative_path = relative_path[len(owner) + 1:]
    if relative_path[0] == "/":
        relative_path = relative_path[1:]
    if "files" == relative_path[:len("files")]:
        relative_path = relative_path[len("files") + 1:]
    if relative_path[0] == "/":
        relative_path = relative_path[1:]
    return relative_path


def set_logging_level(level):
    if level == 'CRITICAL':
        applog.setLevel(logging.CRITICAL)
    elif level == 'ERROR':
        applog.setLevel(logging.ERROR)
    elif level == 'WARNING':
        applog.setLevel(logging.WARNING)
    elif level == 'INFO':
        applog.setLevel(logging.INFO)
    elif level == 'DEBUG':
        applog.setLevel(logging.DEBUG)
    elif level == 'NOTSET':
        applog.setLevel(logging.NOTSET)


def setup_to_log(args):
    # Parameters
    applog.info('Parameter File:{}'.format(args.file))
    applog.info('Parameter Owner:{}'.format(args.owner))
    applog.info('Parameter Config:{}'.format(args.configfile))
    if args.create_public_share:
        applog.info('Called with create-public-share')
    if 'public_keyword' in args:
        applog.info('Parameter Public Keyword:{}'.format(args.public_keyword))
    # Globals
    applog.info('Config Nextcloud URL:{}'.format(global_url))
    applog.info('Config Logfile:{}'.format(global_applog))
    applog.info('Config Logging Level:{}'.format(global_loglevel))
    applog.info('Config datalog:{}'.format(global_datalog))
    applog.info('Config Pronto URL:{}'.format(global_prontourl))
    applog.info('Config Pronto API User:{}'.format(global_prontoapiuser))
    #applog.info('Config Pronto API Password:{}'.format(global_prontoapipassword))
    # Users
    for udict in global_users:
        applog.info('Config User :{}/{}'.format(udict['user'], udict['password']))


def ownerpassword(owner):
    passwordlist = [p['password'] for p in global_users if p['user'] == owner]
    if len(passwordlist) == 0:
        raise ConnectionError("No Password for this owner ({})".format(owner))
    try:
        return passworddecrypt(passwordlist[0])
    except Exception as e:
        raise ConnectionError("Invalid password for owner ({}) {}".format(owner,str(e)))


def passworddecrypt(password):
    # we have a password.  The contents of the text are either a single item
    # in which case we consider this to be a plain text password, or a pair
    # of values, in which case we assume that the first value is an AES256 CTR
    # encrypted password and the second value is an initialisation vector
    # for the encrypted password.  The Secret key for the encryption is
    # 'QuicklinksIsHandyToolInProntoOften'.  This secret key is embedded
    # in the Velocity quicklinks program vglmntauto.  They MUST match
    secretkey = 'QuicklinksIsHandyToolInProntoOften'
    thispasswd = password.split(",")
    if len(thispasswd) == 1:
        # it is a clear text password.
        return thispasswd[0]
    elif len(thispasswd) == 2:
        # it is encrypted.
        cleartxt = ProntoEncryption.decrypt(thispasswd[0],secretkey,thispasswd[1])
        return cleartxt
    else:
        raise ConnectionError("Invalid password - More than 2 comma spearated entries")


if __name__ == '__main__':
    try:
        print("Application Start")
        pgm_args = process_arguments()
        print("Arguments Processed")
        process_config(pgm_args.configfile)
        print("Configuration Loaded")
        establish_logging()
        print("Logging Established")
        applog.info("App Started")
        if setup_ok():
            set_logging_level(global_loglevel)
            setup_to_log(pgm_args)
            thiscloud = onxtcld.NxtCld(global_url, pgm_args.owner, ownerpassword(pgm_args.owner))
            #remove the root
            prefixlength = len(global_nextcloudroot) + len(pgm_args.owner) + 1 + 6
            thiscloud.file_path = pgm_args.file[prefixlength:]
            if pgm_args.create_public_share:
                thiscloud.optionally_create_public_share = True
            if pgm_args.public_keyword is not None:
                thiscloud.public_share_keyword = pgm_args.public_keyword
            if global_datalog is not None:
                thiscloud.add_to_csv_file(global_datalog)
            if global_prontourl is not None:
                thiscloud.add_pronto_quicklink(global_prontourl, global_prontoapiwebresource,
                                               global_prontoapiuser, global_prontoapipassword)
            if isinstance(thiscloud.messages,list):
                for m in thiscloud.messages:
                    print(m)
            else:
                print("No messages logged from object")
    except Exception as e:
        applog.error("Error occured: {}".format(str(e)))
        print(str(e))
        sys.exit(1)
