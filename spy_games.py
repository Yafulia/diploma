import os
import json
import time
import requests

def get_token():
    with open(os.path.join(os.path.dirname(__file__), 'config.json')) as f:
        token = json.load(f)['token']
    return token

TOKEN = get_token()
VERSION = '5.67'
URL_VK = 'https://api.vk.com/method/'
REQUESTS_TIMEOUT = 0.3
TOO_MANY_REQUESTS_PER_SECOND_ERROR_CODE = 6

params = {
    'access_token': TOKEN,
    'v': VERSION
}

class Client:
    common_params = {
        'v': VERSION,
        'access_token': TOKEN
    }

    def send_request(self, method, params=None):
        params = params or {}
        params.update(self.common_params)
        while True:
            response = requests.get(url=URL_VK + method, params=params)
            print('-')

            response.raise_for_status() #requests raises an exception for error codes 4xx or 5xx
            response = response.json()
            if 'error' in response and response['error']['error_code'] == TOO_MANY_REQUESTS_PER_SECOND_ERROR_CODE:
                print('Ошибка: "{}", повторяю запрос.'.format(response['error']['error_msg']))
                time.sleep(REQUESTS_TIMEOUT)
            else:
                break
        return response

class User(Client):
    def __init__(self, user_id=None):
        self.id = user_id
        self.groups_id = []
        self.groups_count = 0
        self.friends_id = []
        self.friends_count = 0

    def get_groups(self):
        response = self.send_request('groups.get', params={'user_id': self.id, 'filter': ['publics']})
        if 'error' in response: #User was deleted or banned and other
            print('Ошибка: "{}".'.format(response['error']['error_msg']))
        else:
            self.groups_id = response['response']['items']
            self.groups_count = response['response']['count']

    def get_friends(self):
        response = self.send_request('friends.get', params={'user_id': self.id})
        if 'error' in response:
            print('Ошибка: "{}".'.format(response['error']['error_msg']))
        else:
            self.friends_id = response['response']['items']
            self.friends_count = response['response']['count']

if __name__ == '__main__':
    C = Client()
    while True:
        input_value = input('Введите идентификатор или имя пользователя: ')
        response = C.send_request('users.get', params={'user_ids': input_value})
        if 'error' in response:
                print('Ошибка: "{}".\n'.format(response['error']['error_msg']))
        else:
            if type(input_value == str):
                input_value = response['response'][0]['id']

            user_obj = User(input_value)
            user_obj.get_groups()
            user_obj.get_friends()

            target_groups_id = set(user_obj.groups_id)

            for user_friend_id in user_obj.friends_id:
                user_friend_obj = User(user_friend_id)
                user_friend_obj.get_groups()
                target_groups_id -= set(user_friend_obj.groups_id)

            if len(list(target_groups_id)) > 0:
                tmp = ', '.join(list(map(str, list(target_groups_id))))
                groups = user_obj.send_request('groups.getById',
                                               params={'group_ids': tmp, 'fields': ['members_count']})['response']
                answer = []
                for group in groups:
                    answer.append({'name': group['name'], 'gid': group['id'], 'members_count': group['members_count']})

                with open('groups.json', 'w', encoding='utf-8') as f:
                    json.dump(answer, f, indent=2, ensure_ascii=False)
            else:
                print('Индивидуальных групп нет!')

            break