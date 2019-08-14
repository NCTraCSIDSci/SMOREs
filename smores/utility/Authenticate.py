from requests import Session

from smores.utility import util

'''Retrieves Ticket Granting Ticket for the user (must be replaced every 8 hours but can be used multiple for 
multiple API requests) '''


def Authenticate(auth_url, auth_endpoints):
    session = Session()
    response = session.post(
        url=auth_url + auth_endpoints['apikey'],
        data={
             'apikey': util.get_api_key('UMLS').strip('\'')
        },
        headers={
            'content-type': 'application/x-www-form-urlencoded'
        }
    )
    begin = response.text.index("TGT-")
    end = response.text.index("-cas")
    TGT = response.text[begin:end + 4]
    return TGT


'''Gets the UMLS service ticket (needed to make API calls) which expires after one use or after 5 min and can be used to 
make API calls 
'''


def get_service_ticket(auth_url, st_service, TGT):
    session = Session()
    response = session.post(
        url=st_service + TGT,
        data={
            'service': 'http://umlsks.nlm.nih.gov'
        },
        headers={
            'content-type': 'application/x-www-form-urlencoded'
        }
    )
    SGT = response.text
    return SGT
