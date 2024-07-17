import base64
import unittest
import xml.etree.ElementTree as ET
from pprint import pprint
import logging
import configparser
import os
from logging.handlers import RotatingFileHandler
import inspect

import main
#import onxtcld

from onxtcld import NxtCld

from prontoencryption import ProntoEncryption


from nextcloud import NextCloud
from nextcloud.codes import ShareType, Permission

applog = logging.getLogger('applog')
global_applog = 'testlog.log'


class RegressionSet(unittest.TestCase):
    """
    This is the main set of test cases for program.

    To make the test work, review setUpClass and change accordingly

    Prior to Execution:
        Clear the logfile (see Establish logging in this file)
        Remove all API based quicklinks from Pronto (Should only be customer C0002)
        Remove all sharing from Nextcloud - rayb/Documents/PythonAppTestCases EXCEPT: Existing Public Share.pdf
            Sign into nextcloud, navigate to the folder.  For each file, click on the word "shared", a panel opens on the RHS.
            Any item that has three dots horizontally, click on the dots.  Delete share

    """

    @classmethod
    def setUpClass(cls):
        cls.NC_URL = "https://nextcloud189.velocityglobal.co.nz"
        cls.NC_USER = "rayb"
        cls.NC_PASSWORD = "sillypassword"
        cls.PRONTO_URL = "https://raydemo.velocityglobal.co.nz:8440"
        cls.PRONTO_WEBRESOURCE = 'sat.vapiql'
        cls.PRONTO_USER = "rayb"
        cls.PRONTO_PASSWORD = "zkgbu"
        cls.FILE_WITH_EXISTING_PUBLIC_SHARE = \
            '/Documents/PythonAppTestCases/Existing Public Share.pdf'
        cls.URL_FOR_EXISTING_PUBLIC_SHARE = 'https://nextcloud189.velocityglobal.co.nz/index.php/s/fo5nfiqGp5dABpQ'
        cls.ID_FOR_EXISTING_PUBLIC_SHARE_FILE = 2278
        cls.FILE_WITH_NO_PUBLIC_SHARE = \
            '/Documents/PythonAppTestCases/No Public Share.pdf'
        cls.KNOWN_FILEID = 'Documents/PythonAppTestCases/File2281.pdf'
        cls.ID_FOR_KNOWN_FILEID = 2281
        cls.NXC = NxtCld(cls.NC_URL,
                         user=cls.NC_USER,
                         password=cls.NC_PASSWORD)
        cls.FILE_WITH_NO_SHARES = \
            '/Documents/PythonAppTestCases/No Shares.pdf'
        cls.FILE_WITH_NO_PRIVATE_SHARES = \
            '/Documents/PythonAppTestCases/Private Share.pdf'
        cls.FILE_API_KEYWORD = \
            '/Documents/PythonAppTestCases/C0002_shared_via_public_keyword.pdf'
        cls.FILE_API_CREATE_SHARE_VIA_FLAG = \
            '/Documents/PythonAppTestCases/C0002_shared_via_create_share_flag.pdf'
        cls.FILE_API_NO_PRIVATE_SHARE = \
            '/Documents/PythonAppTestCases/C0002_no_share.pdf'
        cls.FILE_DOES_NOT_EXIST = \
            '/Documents/PythonAppTestCases/CompleteCrap.pdf'
        cls.FOLDER_DOES_NOT_EXIST = \
            '/Documents/CompleteCrap/No Shares.pdf'

    def setUp(self) -> None:
        self.NXC._initialise_internal_variables()

    def test001(self):
        """ Test Invalid URL"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        with self.assertRaises(self.NXC.NxtCldError):
            n = NxtCld("badurl", self.NC_USER, self.NC_PASSWORD)

    def test002(self):
        """ Test Invalid user"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        with self.assertRaises(self.NXC.NxtCldError):
            n = NxtCld(self.NC_URL, "zaphod", self.NC_PASSWORD)

    def test003(self):
        """ Test Invalid password"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        with self.assertRaises(self.NXC.NxtCldError):
            n = NxtCld(self.NC_URL, self.NC_PASSWORD, "zaphod", )

    def test004(self):
        """ Test existing share - there will be output from the pgm listed below"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test004 File: {}".format(self.FILE_WITH_EXISTING_PUBLIC_SHARE))
        self.NXC.file_path = self.FILE_WITH_EXISTING_PUBLIC_SHARE
        self.assertEqual(self.NXC.share_url, self.URL_FOR_EXISTING_PUBLIC_SHARE, "Incorrect URL")

    def test005(self):
        """ Test new share - remove share in NExtcloud first """
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test005 File: {}".format(self.FILE_WITH_NO_PUBLIC_SHARE))
        self.NXC.optionally_create_public_share = True
        self.NXC.file_path = self.FILE_WITH_NO_PUBLIC_SHARE
        self.assertNotEqual(self.NXC.public_share_id, 0, "No public share")
        self.assertRegex(self.NXC.share_url, "https://nextcloud189.velocityglobal.co.nz/index.php/s/")

    def test006(self):
        """ Test writing to csv file - check /tmp/testlog.log """
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test006 File: {}".format(self.FILE_WITH_EXISTING_PUBLIC_SHARE))
        try:
            thisnxc = NxtCld(self.NC_URL,
                             user=self.NC_USER,
                             password=self.NC_PASSWORD)
            thisnxc.log_file = "/tmp/testlog.log"
            thisnxc.file_path = self.FILE_WITH_EXISTING_PUBLIC_SHARE
            thisnxc.add_to_csv_file()
        except NxtCld.NxtCldError as e:
            self.fail("NxtCld error raised: {}".format(str(e)))
        except Exception as e:
            self.fail("Some other error occurred: {}".format(str(e)))

    def test007(self):
        """ Test Invalid Filename """
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        with self.assertRaises(self.NXC.NxtCldError):
            self.NXC.file_path = '/unknownfolder/unkownfile.pdf'

    def test008(self):
        """Test correct fileid returned"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        self.NXC.file_path = self.KNOWN_FILEID
        self.assertEqual(self.NXC.file_id, self.ID_FOR_KNOWN_FILEID, "Invalid file id returned")

    def test009(self):
        """Test object initialisation with filename"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        thisnxc = NxtCld(self.NC_URL, self.NC_USER, self.NC_PASSWORD, self.KNOWN_FILEID)
        self.assertEqual(thisnxc.file_id, self.ID_FOR_KNOWN_FILEID, "Incorrect File Id")

    def test010(self):
        """Test Private Shares"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test010 File: {}".format(self.FILE_WITH_NO_SHARES))
        self.NXC.file_path = self.FILE_WITH_NO_SHARES
        self.assertRegex(self.NXC.share_url, 'https://nextcloud189.velocityglobal.co.nz/index.php/f',
                         "Public share where private share should be")

    def test011(self):
        """Test No Share"""
        # This should return a share.  It is just that nextcloud has no one sharing it.  Doesn't matter.
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test011 File: {}".format(self.FILE_WITH_NO_PRIVATE_SHARES))
        self.NXC.file_path = self.FILE_WITH_NO_PRIVATE_SHARES
        self.assertRegex(self.NXC.share_url, 'https://nextcloud189.velocityglobal.co.nz/index.php/f',
                         "Public share where private share should be")

    def test012(self):
        """Test Creating public share with public share keyword"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test012 File: {}".format(self.FILE_WITH_NO_PUBLIC_SHARE))
        self.NXC.public_share_keyword = "public"
        self.NXC.file_path = self.FILE_WITH_NO_PUBLIC_SHARE
        self.assertNotEqual(self.NXC.public_share_id, 0, "Public share not created")

    def test020(self):
        """Test calling pronto API - create public share via Flag"""
        # Test cases for the api require the automatic quicklinks shares to have the following parameters:
        #   Unix Path = /Documents/PythonAppTestCases
        #   Quicklinks Path = API
        #   object = deb-master
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test020 File: {}".format(self.FILE_API_CREATE_SHARE_VIA_FLAG))
        self.NXC.file_path = self.FILE_API_CREATE_SHARE_VIA_FLAG
        self.NXC.optionally_create_public_share = True
        self.NXC.add_pronto_quicklink(self.PRONTO_URL, self.PRONTO_WEBRESOURCE ,self.PRONTO_USER, self.PRONTO_PASSWORD)
        # for m in self.NXC.messages:
        #     print(m)

    def test021(self):
        """Test invalid quicklink"""
        # this test case should result in an error because the api should raise an error - no
        # quicklink target can be determined from the filename.
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test021 File: {}".format(self.FILE_WITH_NO_PUBLIC_SHARE))
        with self.assertRaises(self.NXC.NxtCldError):
            self.NXC.file_path = self.FILE_WITH_NO_PUBLIC_SHARE
            self.NXC.optionally_create_public_share = True
            self.NXC.add_pronto_quicklink(self.PRONTO_URL,self.PRONTO_WEBRESOURCE, self.PRONTO_USER, self.PRONTO_PASSWORD)
            for m in self.NXC.messages:
                print(m)

    def test022(self):
        """Test adding quicklink for file with a keyword in the name"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test022 File: {}".format(self.FILE_API_KEYWORD))
        self.NXC.file_path = self.FILE_API_KEYWORD
        self.NXC.public_share_keyword = "public"
        self.NXC.add_pronto_quicklink(self.PRONTO_URL, self.PRONTO_WEBRESOURCE, self.PRONTO_USER, self.PRONTO_PASSWORD)
        for m in self.NXC.messages:
            print(m)

    def test023(self):
        """Test adding file that has no private share"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        print("test023 File: {}".format(self.FILE_API_NO_PRIVATE_SHARE))
        self.NXC.file_path = self.FILE_API_NO_PRIVATE_SHARE
        self.NXC.add_pronto_quicklink(self.PRONTO_URL,self.PRONTO_WEBRESOURCE, self.PRONTO_USER, self.PRONTO_PASSWORD)
        for m in self.NXC.messages:
            print(m)


class misc(unittest.TestCase):

    def test001(self):
        """Test an encryption produces the correct result"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        secretkey = "iliketoflylittleaeroplaneswithorwithoutengines"
        initialization_vector = "poy8R^Sj#)4LAvvR"
        encrypted = ProntoEncryption.encrypt('Cessna172', secretkey, initialization_vector)
        expected = bytes('5RYJGQDtJUEn',"UTF-8")
        self.assertEqual(encrypted,expected,"Encrypted text failed.")

    def test002(self):
        """Test an decryption produces the correct result"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        encoded_text = '5RYJGQDtJUEn'
        secretkey = "iliketoflylittleaeroplaneswithorwithoutengines"
        initialization_vector = "poy8R^Sj#)4LAvvR"
        clear_text = ProntoEncryption.decrypt(encoded_text, secretkey, initialization_vector)
        self.assertEqual(clear_text,"Cessna172","Decryption Failed.")

    def test003(self):
        """ Test encryption of passwords with special characters"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__, inspect.stack()[0][3]))
        encoded_text = '4acRgnGMW0rI3F79lQzeKE4='
        secretkey = "iliketoflylittleaeroplaneswithorwithoutengines"
        initialization_vector = "oSHUR#j/cKhN@eLH"
        clear_text = ProntoEncryption.decrypt(encoded_text, secretkey, initialization_vector)
        self.assertEqual(clear_text, "Grate4848Piezzo##", "Decryption Failed.")

    def test010(self):
        """ Test ini file reading"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        from main import process_config
        thispath = os.path.dirname(__file__)
        if os.path.exists(thispath + "/vnextcloud.ini"):
            inifile = thispath + "/vnextcloud.ini"
        main.process_config(inifile)
        self.assertEqual(main.global_prontourl,"https://raydemo.velocityglobal.co.nz:8440",
                         "Did not get global variable correctly")
        self.assertEqual(main.global_prontoapiuser,"rayb","Invalid API User")

    def test011(self):
        """ Test ini file passwords"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__,inspect.stack()[0][3]))
        from main import process_config
        thispath = os.path.dirname(__file__)
        if os.path.exists(thispath + "/vnextcloud.ini"):
            inifile = thispath + "/vnextcloud.ini"
        main.process_config(inifile)
        self.assertEqual(main.ownerpassword("rayb"),"sillypassword","Encrypted Password Incorrect")
        self.assertEqual(main.ownerpassword("raysharee"),"sillypassword","Clear Password Incorrect")
        self.assertEqual(main.global_prontoapipassword,"zkgbu","Api Password incorrect")
        self.assertEqual(main.global_url ,"https://nextcloud189.velocityglobal.co.nz","Config incorrect")
        self.assertEqual(main.global_nextcloudroot,"/var/www/html/nextcloud/data","Config incorrect")
        self.assertEqual(main.global_applog,"/var/www/html/nextcloud/vnextcloud.log","Config incorrect")
        self.assertEqual(main.global_datalog,"/tmp/vnextcloud.csv","Config incorrect")
        self.assertEqual(main.global_loglevel,"DEBUG","Config incorrect")
        self.assertEqual(main.global_prontourl,"https://raydemo.velocityglobal.co.nz:8440","Config incorrect")
        self.assertEqual(main.global_prontoapiwebresource,"sat.vapiql","Config incorrect")
        self.assertEqual(main.global_prontoapiuser,"rayb","Config incorrect")
        self.assertEqual(main.global_prontoapipassword,"zkgbu","Config incorrect")

class temptests(unittest.TestCase):
    def test003(self):
        """ Test encryption of passwords with special characters"""
        applog.debug('start of Test {}.{}'.format(self.__class__.__name__, inspect.stack()[0][3]))
        encoded_text = '4acRgnGMW0rI3F79lQzeKE4='
        secretkey = "iliketoflylittleaeroplaneswithorwithoutengines"
        initialization_vector = "oSHUR#j/cKhN@eLH"
        clear_text = ProntoEncryption.decrypt_ctr(encoded_text, secretkey, initialization_vector)
        self.assertEqual(clear_text, "Grate4848Piezzo##", "Decryption Failed.")


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
    applog.setLevel(logging.DEBUG)


if __name__ == '__main__':
    #
    # establish logs.
    establish_logging()
    applog.info("Test Cases initiated")
    # Case 1 is the main test class that should be used for regression testing
    case1 = unittest.TestLoader().loadTestsFromTestCase(RegressionSet)
    # Case 2 test the other miscellaneous features
    case2 = unittest.TestLoader().loadTestsFromTestCase(misc)
    tempcase = unittest.TestLoader().loadTestsFromTestCase(temptests)
    # thissuite = unittest.TestSuite([case1,case2])
    thissuite = unittest.TestSuite([case1,case2])
    unittest.TextTestRunner(verbosity=2).run(thissuite)
