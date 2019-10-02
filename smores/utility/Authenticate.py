import requests
from datetime import datetime, timedelta
from typing import Union
import logging
from lxml.html import fromstring

from smores.utility.errors import smores_error
from smores.utility import util


'''Retrieves Ticket Granting Ticket for the user (must be replaced every 8 hours but can be used multiple for 
multiple API requests) '''

APIlog = logging.getLogger(__name__)

class Authenticate:
    e_class = '#A'
    e_subclass = 'x004'

    def __init__(self, authuri:str, authendpoint:Union[str, dict], authkey=None, authuser=None, authpwd=None):
        self.auth_param = {}
        self.auth_uri = authuri
        self.auth_ticket = None
        self.auth_ticket_expire = None

        if authkey is not None:
            self.auth_method = 'apikey'
            self.auth_param['apikey'] = authkey
        elif authuser is not None:
            if authpwd is None or len(authpwd) == 0:
                smores_error('{0}{1}.{2}'.format(Authenticate.e_class, Authenticate.e_subclass, '2'), logger=APIlog)
            else:
                self.auth_method = 'user'
                self.auth_param['user'] = authuser
                self.auth_param['pwd'] = authpwd
        else:
            self.auth_method = False
            smores_error('{0}{1}.{2}'.format(Authenticate.e_class, Authenticate.e_subclass, '3'), logger=APIlog)
        self.auth_endpoint = authendpoint if type(authendpoint) is str else authendpoint[self.auth_method]

    def get_auth_ticket(self):
        if self.auth_ticket is not None and datetime.now() < self.auth_ticket_expire:
            return self.auth_ticket

        elif self.auth_method:
            if self.auth_method == 'apikey':
                params = {'apikey': self.auth_param['apikey']}
            else:
                params = {'username': self.auth_param['user'], 'password': self.auth_param['pwd']}

            h = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "User-Agent": "python"}
            try:
                r = requests.post(self.auth_uri+self.auth_endpoint, data=params, headers=h)
                response = fromstring(r.text)
                tgt = response.xpath('//form/@action')[0]
                if tgt is not None:
                    self.auth_ticket_expire = datetime.now() + timedelta(hours=8)
                    self.auth_ticket = tgt
                return tgt
            except (requests.ConnectionError, requests.Timeout) as e:
                print(e)
                return False
            except:
                return False
        else:
            return False

    def get_service_ticket(self, service:str):
        tgt = self.get_auth_ticket()
        params = {'service': service}
        h = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "User-Agent": "python"}
        try:
            r = requests.post(tgt, data=params, headers=h)
            st = r.text
            return st
        except (requests.ConnectionError, requests.Timeout) as e:
            print(e)
            return False
        except:
            return False
