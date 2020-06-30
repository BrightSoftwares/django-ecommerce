#! /home/gregmcshane/anaconda3/bin/python3.6

import re
import json
import requests
import uuid
import time
# import logging

# # These two lines enable debugging at httplib level (requests->urllib3->http.client)
# # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# # The only thing missing will be the response.body which is not logged.
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1

# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


class Vinted():
    '''wrap a logged in session to vinted
       you have to enter a valid user name/password'''

    def __init__(self, creds={'login': 'xxxx',
                              'password': 'yyyy'}):

        self.creds = creds
        self.sess = None  # requests session
        # print("Init with credentials", self.creds)

    def get_page(self, url, params={}):
        '''fetch a page using current session'''
        print("Getting page", url)
        return self.sess.get(
            url,
            params=params,
            headers=dict(referer=url))

    def login(self):
        '''login to vinted using the credentials in creds'''

        print("Login with creds", self.creds)
        self.sess = requests.session()
        login_url = 'https://www.vinted.fr/member/general/login?ref_url='

        print('Login to url', login_url)
        tt = self.sess.get(login_url).content.decode('utf-8')
        # print('Login result', tt)

        pp = re.compile('name="csrf-token" content="(.*?)"')
        mm = pp.search(tt)

        payload = self.creds
        payload["authenticity_token"] = mm.group(1)
        print('authenticity payload', payload["authenticity_token"])

        # Get the fingerprint
        pp2 = re.compile('name="fingerprint" content="(.*?)"')
        mm2 = pp2.search(tt)
        payload["fingerprint"] = uuid.uuid4().hex  # mm2.group(1)
        print("fingerpring payload", payload["fingerprint"])

        login_json_url = 'https://www.vinted.fr/member/general/login.json'
        print("Session", self.sess)
        print("Payload", payload)

        headers = {'referer': login_url}

        result = self.sess.post(
            login_json_url, data=payload, headers=headers)
        # json=json.dumps(payload),
        # headers=dict(referer=login_url)
        # )
        # print("Result", result)

        f = open("login.html", "w")
        f.write(result.content.decode('utf-8'))
        f.close()

        r = self.get_page('https://www.vinted.fr')

        return result

    def get_items4member(self, member_id='36544471'):
        '''get all the items for the member
        do not attempt to decode the json
        return user_info as json and items as list of json'''

        base_url = 'https://www.vinted.fr/api/v2/users/'
        print("Getting items for member", member_id)

        r = self.get_page(base_url + '%s/' % member_id)
        print("Items for member", r.json())
        member_info = r.json()['user']

        num_items = member_info['item_count']
        if num_items == 0:
            return member_info, []

        url = base_url + '%s/items' % member_id
        all_items = []

        for k in range(1, num_items // 48 + 2):
            print('page', k)
            r = self.get_page(url,
                              params={'page': k, 'per_page': 48})
            all_items.extend(r.json()['items'])

        return member_info, all_items

    def get_friends4member(self, member_id='20263980'):
        '''get all the friends for the member
        return a list of pairs (member_id, pseudo)'''

        r = self.get_page(
            'https://www.vinted.fr/member/general/followers/' + member_id)
        px = re.compile('class="follow__name".*?(\d+).*?>(.*?)<')
        return list(set(px.findall(r.content.decode('utf-8'))))

# from vinted_creds import creds

# session = Vinted(creds=creds)
# session.login().content.decode('utf-8')

# #friends = session.get_friends4member('36544471')
# friends = session.get_friends4member('12813951')
# for friend in friends:
#     print("Friend: ", friend)
#     friend_id = friend[0]

#     time.sleep(3)
#     print("Re fetching data for friend", friend_id)
#     i_member_info, i_all_items = session.get_items4member(friend_id)
#     print("Member info", i_member_info['real_name'])

# edem_member_info, edem_items = session.get_items4member('12813951')
# print("Edem member info", edem_member_info)
