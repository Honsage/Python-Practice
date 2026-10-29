import requests


URL = 'https://api.thecatapi.com/v1/images/search'


def get_cat_photo():
    url = ''
    is_succeed = False
    response = requests.get(URL)

    if response.status_code == 200:
        response = response.json()
        url = response[0].get('url')
        is_succeed = True

    return {
        'is_succeed': is_succeed,
        'url': url
    }