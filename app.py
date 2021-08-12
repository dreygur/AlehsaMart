#!/usr/bin/env python

import os
import re
import sys
import requests as rq
from bs4 import BeautifulSoup

# Random User-Agent
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

# Base URL
__base = 'https://aleshamart.com/'
__username = 'rakib'
__password = 'rakib'
__bike_brand_id = 42

# User Session
__session = rq.Session()

def user_agent() -> str:
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

    # Get Random User Agent String.
    agent = user_agent_rotator.get_random_user_agent()

    return agent

def token(page: str=None) -> str:
  if page:
    res = rq.get(page, headers={'user-agent': user_agent()})
  res = rq.get(__base, headers={'user-agent': user_agent()})
  pattern = re.compile(r'c.{8}n\"\s.{8}\"([A-z0-9_]{10,})\"')
  matches = pattern.findall(res.text)
  if len(matches) > 0:
    return matches[0]

def cookie() -> str:
  # https://aleshamart.com/login
  csrf_token = token('https://aleshamart.com/login')
  data = {
    '_token': csrf_token,
    'email': __username,
    'password': __password,
  }

  res = rq.post(__base + 'loginsubmit', data=data, headers={
    'user-agent': user_agent(),
    'origin': 'https://aleshamart.com',
    'referer': 'https://aleshamart.com/login',
    'X-CSRF-TOKEN': csrf_token
  })
  print(res.status_code)
  print(res.request.body)

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

def buy(link: str) -> None:
  product_id = link.split('/')[4]
  cart_url = 'https://aleshamart.com/carts/addtocart/' + product_id

  data = {
    '_method': 'PATCH',
    '_token': token(),
    'quantity': '1',
    'variation_id': '0',
    'usedattributes': '',
    'buy_now': 'buy_now'
  }

  print(product_id)

def main() -> None:
  # token()
  # print(search_bikes(__bike_brand_id))
  cookie()
  # for bike in search_bikes(__bike_brand_id):
  #   buy(bike.get('link'))
  #   if int(bike.get('off')[:-1]) > 15:
  #     buy(bike.get('link'))


if __name__ == '__main__':
  main()
