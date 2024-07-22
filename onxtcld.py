from nextcloud import NextCloud
from nextcloud import NextCloud
from nextcloud.codes import ShareType
import os
import decimal
import csv
import datetime
import logging
import requests
import xml.etree.ElementTree as ET
import urllib3

urllib3.disable_warnings()

applog = logging.getLogger('applog')


class NxtCld:
    class NxtCldError(Exception):
        pass

    def __init__(self, url, user, password, filepath=None):
        """
        The class must be instantiated with a URL to the next Cloud server, a user id to connect with
        and a password for that user.  Optionally a path can be added to the instantiation or set via the setter.

        Essentially the oject is instantiated with the url, username and password.  Other variables that control the
        behaviour of the class should then be set.

        It is MOST important to note that the determination of the shares is done by __process_shares.  Each getter
        of the readonly variables (share_url, public_share_id and file_id) will invoke __process_shares if it has
        not already been executed.  The two methods that do things with the shares (add_to_csv_file and add_pronto_quicklink)
        will also invoke the process_shares function if it has not already been done.
        Therefore, all the object consumer has to do is to access a property or invoke a mehthod for the share processing
        to execute.

        The Object then does three essential functions:
            a) A share url is determined.  This could be a public share, or a private share. If so configured
               the object will create a public share and return the url or, if no public share exists and the
               no option has been taken to create one, then a private url is returned.  A file id is always
               available, but the public_share_id is only available if a public share already exists or
               has been newly created.  The boolean variable __shares_processed is set when the object has completed
               this task

            b) An entry is made in a log file.

            c) A pronto API is called to add the quicklink.

        Usage :
        Try:
            # Instantiate the class with user
            thiscloud = onxtcld.NxtCld(global_url, pgm_args.owner, ownerpassword(pgm_args.owner))
            # Set critical properties
            # public shares are created only if optionally_create_public_share is true or
            # a keyword has been defined.  If a keyword has been defined then the public share
            # is created if the keyword is found in the path or filename.
            thiscloud.optionally_create_public_share = TRUE
            # or
            thiscloud.public_share_keyword = 'shared'
            # Finally set the file path.  This invokes the processing.
            thiscloud.file_path = Fullpathtofile

            # Access the properties
            # The determination of returned properties is in the property getter itself.  The object keeps track
            # of whether the determination of the values has already been done.
            print(thiscloud.first_public_share_url)
            print(thiscloud.first_public_share_id)
            # create publicshare:
            thiscloud.create_public_share()
            # access URL
            print(thiscloud.url)
            print(thiscloud.fileid)
            print(thiscloud.shareid)
            # add to logfile
            thiscloud.add_to_log_file('/tmp/logfile.log')
            # or
            thiscloud.log_file = '/tmp/logfile.log'
            thiscloud.add_to_log_file()
            # Call pronto API
            thiscloud.add_pronto_quicklink(url,user,password)

        :param url:  The url of the nexcloud server
        :param user: The name of the user who owns the file
        :param password: The password of the user who owns the file.
        """
        # todo: validate parameters.

        self.__public_share_keyword = None
        self.__optionally_create_public_share = False
        self.__log_file = None
        self.__pronto_url = None
        self.__url = None
        self.__user = None
        self.__password = None
        # Set the following variables using the appropriate setter to ensure validation is done.
        self.url = url
        self.user = user
        self.password = password
        # Establish connection
        self.__nxc = NextCloud(self.__url, self.__user, self.__password,
                               session_kwargs={'verify': False}
                               )
        ci = self.__nxc.get_connection_issues()  # execution time for this function is VERY Slow
        if ci is not None:
            applog.error("Failed to Connect : {}".format(self.__url))
            raise self.NxtCldError("Failed to Connect : {}".format(self.__url))
        applog.info("Successful Connection to URL")
        # initialise private variables.
        self._initialise_internal_variables()
        if filepath is not None:
            # use setter to ensure validation and ALSO PROCESSING.
            self.file_path = filepath

    # -------------------Property setters and getters ----------------------------------

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, value):
        if self.__url is not None:
            raise TypeError('You cannot change the URL after it has been set.  Create a new object')
        if not self.__isstr(value):
            raise TypeError('Invalid URL')
        if len(value) == 0:
            raise TypeError('Invalid URL (must not be blank)')
        self.__url = value

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, value):
        if self.__user is not None:
            raise TypeError('You cannot change the User after it has been set.  Create a new object')
        if not self.__isstr(value):
            raise TypeError('Invalid user')
        if len(value) == 0:
            raise TypeError('Invalid user (must not be blank)')
        self.__user = value

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value):
        if self.__password is not None:
            raise TypeError('You cannot change the Password after it has been set.  Create a new object')
        if not self.__isstr(value):
            raise TypeError('Invalid Password')
        if len(value) == 0:
            raise TypeError('Invalid Password (must not be blank)')
        self.__password = value

    @property
    def file_path(self):
        return self.__file_path

    @file_path.setter
    def file_path(self, value):
        if self.__file_path is not None:
            raise TypeError('You cannot change the filename after it has been set.  Create a new object.')
        if not self.__isstr(value):
            raise TypeError('Invalid file_path')
        if len(value) == 0:
            raise TypeError('Invalid File Path (must not be blank)')
        self.__file_path = value
        if self.__fileid is None:
            self.__set_fileid_from_path()

    @property
    def log_file(self):
        return self.__log_file

    @log_file.setter
    def log_file(self, value):
        if not self.__isstr(value):
            raise TypeError('Invalid log_file')
        if len(value) == 0:
            raise TypeError('Invalid log_file (must not be blank)')
        self.__log_file = value

    @property
    def pronto_url(self):
        return self.__pronto_url

    @pronto_url.setter
    def pronto_url(self, value):
        if not self.__isstr(value):
            raise TypeError('Invalid pronto_url')
        if len(value) == 0:
            raise TypeError('Invalid Pronto Url (must not be blank)')
        self.__pronto_url = value

    @property
    def optionally_create_public_share(self):
        return self.__optionally_create_public_share

    @optionally_create_public_share.setter
    def optionally_create_public_share(self, value):
        if not self.__isbool(value):
            raise TypeError('Invalid value for this variable (must be true or false')
        self.__optionally_create_public_share = value

    @property
    def public_share_keyword(self):
        return self.__public_share_keyword

    @public_share_keyword.setter
    def public_share_keyword(self, value):
        if not self.__isstr(value):
            raise TypeError('Public Share Keyword must be a string')
        self.__public_share_keyword = value


    #  --------------------------  Read Only Properties ------------------------------

    @property
    def share_url(self):
        if not self.__shares_processed:
            self.__process_shares()
        return self.__share_url

    @property
    def public_share_id(self):
        if not self.__shares_processed:
            self.__process_shares()
        return self.__public_share_id

    @property
    def file_id(self):
        if self.__fileid is None:
            self.__set_fileid_from_path()
        return self.__fileid

    @property
    def messages(self):
        return self.__messages

    # @file_id.setter
    # def file_id(self, value):
    #     if self.__fileid is not None:
    #         raise TypeError('You cannot change the file id after it has been set.  Create a new object')
    #     if not self.__isint(value):
    #         raise TypeError('Invalid file_id')
    #     if value == 0:
    #         raise TypeError('Invalid file id (must not be zero)')
    #     self.__fileid = value

    # ---------------------------  Methods for type validation---------------------------------

    @staticmethod
    def __isstr(para):
        if para is None:
            return False
        if not isinstance(para, str):
            return False
        return True

    @staticmethod
    def __isint(para):
        if para is None:
            return False
        if not isinstance(para, int):
            return False
        return True

    @staticmethod
    def __isbool(para):
        if para is None:
            return False
        if not isinstance(para, bool):
            return False
        return True

    @staticmethod
    def __islist(para):
        if para is None:
            return False
        if not isinstance(para, list):
            return False
        return True

    @staticmethod
    def __isnum(para):
        if para is None:
            return False
        if not isinstance(para, (int, float, decimal.Decimal)):
            return False
        return True

    # ---------------------------- Public Methods ---------------------------------------

    # def get_create_public_share(self, filepath=None):
    #     """
    #     returns the url for a public share.  It is EITHER the first public share in the
    #     list or a new public share
    #     :return: URL of a public share
    #     """
    #     applog.debug("Starting get/create public share")
    #     if filepath is None:
    #         if self.file_path is None:
    #             raise self.NxtCldError("No file specified")
    #         else:
    #             filepath = self.file_path
    #     else:
    #         self.file_path = filepath  # will validate the variable as well
    #     fps = self.__get_first_public_share()
    #     if fps is None:
    #         self.__create_public_share()
    #     else:
    #         applog.info('Existing Public Share Returned {}'.format(fps))
    #         return fps

    def add_to_csv_file(self, logfile=None):
        if not self.__shares_processed:
            self.__process_shares()
        applog.debug('Adding file to data log.')
        if logfile is None and self.__log_file is None:
            raise self.NxtCldError("Log file is not set")
        if logfile is not None:
            self.log_file = logfile
        if self.log_file is None:
            raise self.NxtCldError("log file not set")
        if self.__file_path is None:
            raise self.NxtCldError("No filepath set to log.")
        flds = ['date', 'time', 'file', 'owner', 'url', 'shareid', 'fileid']
        # if not os.path.isfile(self.__log_file):
        try:
            f = open(self.__log_file, 'a')
            filesize = os.stat(f.fileno()).st_size
            wrtr = csv.DictWriter(f, fieldnames=flds, delimiter="|")
            if filesize == 0:
                # write the header
                wrtr.writeheader()
            # add next record here
            wrtr.writerow({
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'time': datetime.datetime.now().strftime("%H:%M:%S"),
                'file': self.__file_path,
                'owner': self.__user,
                'url': self.__share_url,
                'shareid': self.__public_share_id,
                'fileid': self.__fileid
            })
            f.close()
        except Exception as e:
            applog.debug("Error adding log entry:{}".format(str(e)))
            raise self.NxtCldError("Error adding log entry:{}".format(str(e)))

    def add_pronto_quicklink(self, apiurl, apiwebresource, apiuser, apipassword):
        """
        Call the pronto api to add a quicklink
        :param apiurl:
        :param apiwebresource:
        :param apiuser:
        :param apipassword:
        :return:
        """
        # Verify we have the necessary data
        if not self.__shares_processed:
            self.__process_shares()
        applog.info("Create Quicklink via API")
        if not self.__isstr(self.file_path):
            raise self.NxtCldError("The file path must be set before calling the pronto api")
        if not self.__isstr(self.user):
            raise self.NxtCldError("The owner of the file must be set before calling the pronto api")
        if not self.__isstr(self.share_url):
            raise self.NxtCldError("The public share  must be set before calling the pronto api")
        #
        # build the header
        headers = {'Content-Type': 'application/xml',
                   'X-Pronto-Token': self.__get_pronto_token(apiurl, apiwebresource, apiuser, apipassword)}
        # build the API Body
        root = ET.Element('Data')
        ET.SubElement(root, 'filename').text = self.file_path
        applog.info('API Parameter Filename :{}'.format(self.file_path))
        ET.SubElement(root, 'owner').text = self.user
        applog.info('API Parameter owner :{}'.format(self.user))
        ET.SubElement(root, 'shareurl').text = self.share_url
        applog.info('API Parameter shareurl :{}'.format(self.share_url))
        if self.public_share_id != 0:
            ET.SubElement(root, 'publicshareid').text = str(self.public_share_id)
            applog.info('API Parameter publicshareid :{}'.format(self.public_share_id))
        if self.file_id != 0:
            ET.SubElement(root, 'fileid').text = str(self.file_id)
            applog.info('API Parameter fileid :{}'.format(self.file_id))
        body = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
        # set the url for the api call
        url = apiurl + "/pronto/rest/" + apiwebresource + "/api/vapi-ql"
        # call the api
        applog.info('Calling Pronto API')
        resp = requests.request("POST", url, headers=headers, data=body)
        if resp.status_code != 200:
            applog.error("Call to API Failed ({} - {})".format(resp.status_code, resp.text))
            raise self.NxtCldError("Call to API Failed ({} - {})".format(resp.status_code, resp.text))
        # The api ran - check the result
        applog.debug('Call Successful')
        root = ET.fromstring(resp.text)
        applog.debug(resp.text)
        applog.debug("API Response Code: {}".format(root.findall("./APIResponseStatus/Code")[0].text))
        responsecode = root.findall("./APIResponseStatus/Code")[0].text
        if responsecode != '0':
            applog.error("API Response Error: {}".format(root.findall("./APIResponseStatus/Code")[0].text))
            applog.error("API Response Message: {}".format(root.findall("./APIResponseStatus/Message")[0].text))
            raise self.NxtCldError(root.findall('./APIResponseStatus/Message')[0].text)
        else:
            applog.info("Company {}".format(root.findall("./ResponseFields/company")[0].text))
            applog.info("Pronto Object : {}".format(root.findall("./ResponseFields/object")[0].text))
            applog.info("Keys {}".format(root.findall("./ResponseFields/keys")[0].text))
            applog.info("Sequence {}".format(root.findall("./ResponseFields/seq")[0].text))
            self.__messages.append("Quicklink Added")
            self.__messages.append("Company {}".format(root.findall("./ResponseFields/company")[0].text))
            self.__messages.append("Pronto Object {}".format(root.findall("./ResponseFields/object")[0].text))
            self.__messages.append("Keys {}".format(root.findall("./ResponseFields/keys")[0].text))
            self.__messages.append("Sequence {}".format(root.findall("./ResponseFields/seq")[0].text))
        applog.info("Quicklinks API Successful")

    # ---------------------------- Private Methods ---------------------------------------

    def _initialise_internal_variables(self):
        """
        Generally only called by init.  Changing the file path is generally not possible but
        it may be useful (especially in unit tests or batch processes) to establish a connection and reset
        the internal variables
        :return:
        """
        self.__fileid = None
        self.__file_path = None
        self.__log_file = None
        self.__pronto_url = None
        self.__share_url = None
        self.__public_share_id = None
        self.__public_share_keyword = None
        self.__optionally_create_public_share = False
        self.__shares_processed = False
        self.__messages = []

    def __process_shares(self):
        if self.__shares_processed:
            return  # shares already processed.
        if self.__file_path is None:
            raise self.NxtCldError("No File Specified")
        if self.__fileid is None:
            self.__set_fileid_from_path()
        # If a public share exists then use it.
        fps = self.__get_first_public_share()
        if fps is None:
            # do we need to create one?  If optionally_create_public_share exists or the keyword is in the path
            if self.__public_share_keyword is not None:
                if self.__public_share_keyword.upper() in self.__file_path.upper():
                    self.__optionally_create_public_share = True
            if self.__optionally_create_public_share:
                self.__create_public_share()
        else:
            applog.info('Existing Public Share Returned {}'.format(fps))
        # use a private share if no public one is available
        if self.__public_share_id is None:
            self.__share_url = self.__url + '/index.php/f/' + str(self.__fileid)
        self.__shares_processed = True

    def __create_public_share(self):
        applog.info("New public share required")
        try:
            lnk = self.__nxc.create_share(self.__file_path, share_type=ShareType.PUBLIC_LINK)
            # self.__messages.append('lnk.data in get_create_public_share {}'.format(lnk.data))
            applog.info('New Public Share Created {}'.format(lnk.data['url']))
            self.__share_url = lnk.data['url']
            self.__public_share_id = lnk.data['id']
            self.__messages.append("New public share created:")
            self.__messages.append("Share Link Id : {}".format(self.__public_share_id))
            self.__messages.append("URL: {}".format(self.__share_url))
            return lnk.data['url']
        except Exception as e:
            applog.error("Error in create public share : {} ".format(str(e)))
            self.NxtCldError("Error in create public share : {} ".format(str(e)))

    def __get_first_public_share(self):
        """
        Return the url of the first public share for the file path.
        If there are no shares then return None.
        :return: url of first public share
        """
        applog.debug("Getting First Public Share")
        if len(self.__file_path) == 0:
            applog.error("The file path is blank")
            raise self.NxtCldError("The file path is blank")
        theseshares = self.__nxc.get_shares_from_path(self.__file_path)
        for d in theseshares.data:
            if d['share_type'] == ShareType.PUBLIC_LINK:
                self.__share_url = d['url']
                self.__public_share_id = d['id']
                applog.debug('Existing Public share found for file.')
                self.__messages.append("Existing public share located:")
                self.__messages.append("Share Link Id : {}".format(self.__public_share_id))
                self.__messages.append("URL: {}".format(self.__share_url))
                return d['url']
        # if we get to here then none have been found
        applog.debug('No public shares found for file.')
        return None

    def __get_pronto_token(self, apiurl, apiwebresource, apiuser, apipassword):
        # validate
        if None in (apiurl, apiwebresource, apiuser,apipassword):
            raise ConnectionError("One of the parameters to __get_pronto_token is None")
        # set url and headers
        applog.debug('Getting Pronto Authorization Token')
        url = apiurl + "/pronto/rest/" + apiwebresource + "/login"
        applog.debug('url: {}'.format(url))
        #applog.debug('api user /password: {}/{}'.format(apiuser,apipassword))
        applog.debug('api user /password: {}/{}'.format(apiuser,"Password not shown"))
        headers = {
            'X-Pronto-Username': apiuser,
            'X-Pronto-Password': apipassword,
            'Content-Type': 'application/xml'
        }
        try:
            # call the api to get a token
            resp = requests.request("POST", url, headers=headers)
            if resp.status_code != 200:
                applog.error('Attempt to get token resulted in a {} response'.format(resp.status_code))
                applog.error('url was {}'.format(url))
                raise self.NxtCldError("Unable to get token")
            # xml = ET.ElementTree(ET.fromstring(resp.text))
            # root = xml.getroot()
            root = ET.fromstring(resp.text)
            for node in root.iter('token'):
                applog.debug('Token Successfully Retrieved : {}'.format(node.text))
                return node.text
        except Exception as e:
            raise self.NxtCldError(str(e))

    def __set_fileid_from_path(self):
        if self.__fileid is not None:
            raise self.NxtCldError("file Id already set")
        try:
            thisfile = self.__nxc.get_file(self.__file_path)
            if thisfile is None:
                applog.error(
                    "Could not determine File id.  get_file returned None for path {}".format(self.__file_path))
                raise self.NxtCldError(
                    "Could not determine File id.  get_file returned None for path {}".format(self.__file_path))
            self.__fileid = thisfile['file_id']
        except Exception as e:
            raise self.NxtCldError("Could not determine file id: {}".format(e))
