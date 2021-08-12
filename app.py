#!/usr/bin/env python

import os
import re
import sys
import requests as rq
from bs4 import BeautifulSoup

# Random User-Agent
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from creds import *

# Login Details
__username = username
__password = password

# Hacks
__expected_off = expected_off
__bike_brand_id = bike_brand_id
__expected_discount = expected_discount

# User Session
__session = rq.Session()

# Base URL
__base = 'https://aleshamart.com/'

def user_agent() -> str:
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

    # Get Random User Agent String.
    agent = user_agent_rotator.get_random_user_agent()

    return agent

def token(page: str=None) -> str:
  if page:
    res = __session.get(page, headers={'user-agent': user_agent()})
  else:
    res = rq.get(__base, headers={'user-agent': user_agent()})
  pattern = re.compile(r'c.{8}n\"\s.{8}\"([A-z0-9_]{10,})\"')
  matches = pattern.findall(res.text)
  if len(matches) > 0:
    return matches[0]

def login() -> str:
  # https://aleshamart.com/login
  csrf_token = token('https://aleshamart.com/login')
  data = {
    '_token': csrf_token,
    'email': __username,
    'password': __password,
  }

  res = __session.post(__base + 'loginsubmit', data=data, headers={
    'user-agent': user_agent(),
    'origin': 'https://aleshamart.com',
    'referer': 'https://aleshamart.com/login',
    'X-CSRF-TOKEN': csrf_token,
    'x-requested-with': 'XMLHttpRequest'
  })

  if res.url == 'https://aleshamart.com/account':
    return 'SUCCESS'

def search_bikes(brand: str) -> list:
  # All found Bikes
  bikes = list()

  # Search for Bikes
  target = f'{__base}category/automobiles-biking?csearch=&brand%5B%5D={brand}&sort=0' # &_token=GxygobpRGFPqsnK3kMu4H2B7Z5hZXu0Uvlv6Jtu7'
  res = rq.get(target, headers={'user-agent': user_agent()})
  soup = BeautifulSoup(res.text, 'html.parser')
  soup_prod = soup.find_all('div', {'class': 'product_single'})

  for prod in soup_prod:
    bike = dict()
    string_reps = str(prod)
    bike['name'] = re.findall(r'\>([A-z0-9\-_\s]{3,})\<', string_reps)[0]
    bike['price'] = re.findall(r'Tk.\s([0-9,.]{3,})\<', string_reps)[1]
    bike['final_price'] = re.findall(r'Tk.\s([0-9,.]{3,})\<', string_reps)[0]
    bike['off'] = re.findall(r'([0-9]{1,}%)\sOFF', string_reps)[0]
    bike['link'] = BeautifulSoup(string_reps, 'html.parser').find_all('a')[0]['href']
    bikes.append(bike)

  # print(bikes)
  return bikes

def buy(link: str) -> str:
  product_id = link.split('/')[4]
  cart_url = 'https://aleshamart.com/carts/addtocart/' + product_id
  csrf_token = token(link)

  data = {
    '_method': 'PATCH',
    '_token': csrf_token,
    'quantity': '1',
    'variation_id': '0',
    'usedattributes': '',
    'buy_now': 'buy_now'
  }

  res = __session.post(cart_url, data=data, headers={
    'user-agent': user_agent(),
    'origin': 'https://aleshamart.com',
    'referer': link,
    'X-CSRF-TOKEN': csrf_token,
  })

  if res.status_code == 200:
    return 'SUCCESS'

def checkout() -> None:
  link = 'https://aleshamart.com/quickcheckout'
  csrf_token = token(link)

  data = {
    '_token': csrf_token,
    'billing': '249460',
    'shipping': '249460',
    'sameasbilling': '1',
    'payment_method': '2',
    'payable_total_amount': '0',
    'note': '',
    'shipping_cost': '0',
    'discount_amount': str(__expected_discount),
    'is_flat_shipping': '0',
    'appliedDiscountIdsWithAmount': 'a: 0: {}'
  }

  res = __session.post(link, data=data, headers={
    'user-agent': user_agent(),
    'origin': 'https://aleshamart.com',
    'referer': link,
    'X-CSRF-TOKEN': csrf_token,
  })

  if res.status_code == 200:
    return 'SUCCESS'

def main() -> None:
  if login():
    print(f'[+] LOGIN SUCCESSFULL!')
    while True:
      for bike in search_bikes(__bike_brand_id):
        if int(bike.get('off')[:-1]) >= __expected_off and buy(bike.get('link')):
          print(f'[+] Trying to buy: {bike.get("name")}')
          if checkout():
            print(f'[+] {bike.get("name")} buy: SUCCESS!')
          else:
            print(f'[+] {bike.get("name")} buy: FAILED!')


if __name__ == '__main__':
  # https://aleshamart.com/carts
  # https://aleshamart.com/checkout
  main()
