# -*- coding: utf-8 -*-
"""
Created on Tue May  7 00:05:37 2019

@author: ksuboch
"""

import pandas as pd
import requests
import urllib.parse as urlparse
from bs4 import BeautifulSoup
import time


def getMainUrl(base_url, add_url):
    return urlparse.urljoin(base_url, add_url)


def getBeautifulSoup(url):
    r  = requests.get(url)
    if r.status_code == 200:
        return BeautifulSoup(r.text, features="lxml")
    

def getLastPageNum(bs, base_url):
    page_links = bs.find_all('a', class_='pagination-page')
    if len(page_links) > 0:
        last_page_href = page_links[-1].get('href')
        last_page_url = urlparse.urljoin(base_url, last_page_href)
        parsed = urlparse.urlparse(last_page_url)
        return int(urlparse.parse_qs(parsed.query)['p'][0])
    else:
        return 0


def getPagesDataFrame(bs, base_url, main_url):
    lastPageNum = getLastPageNum(bs, base_url)    
    df = pd.DataFrame(columns = ['Link'])
    for i in range(lastPageNum):
        params = {'p' : i + 1}
        pr = requests.PreparedRequest()
        pr.prepare_url(main_url, params)
        df.loc[i] = pr.url
    return df


def getFloorNum(bs):
    tag = bs.find('span', class_='item-params-label', text='Этаж: ')
    if tag != None:
        data = tag.next_sibling
        if data != None:
            return int(data)


def getFloorCnt(bs):
    tag = bs.find('span', class_='item-params-label', text='Этажей в доме: ')
    if tag != None:
        data = tag.next_sibling
        if data != None:
            return int(data)


def getHouseTyp(bs):
    tag = bs.find('span', class_='item-params-label', text='Тип дома: ')
    if tag != None:
        data = tag.next_sibling
        if data != None:
            return str(data)


def getRoomsCnt(bs):
    tag = bs.find('span', class_='item-params-label', text='Количество комнат: ')
    if tag != None:
        data = tag.next_sibling.split('-')[0]
        if data != None:
            return int(data)


def getSpaceCnt(bs):
    tag = bs.find('span', class_='item-params-label', text='Общая площадь: ')
    if tag != None:
        data = tag.next_sibling.split()[0]
        if data != None:
            return float(data)


def getAddress(bs):
    tag = bs.find('span', itemprop='streetAddress')
    if tag != None:
        data = tag.string.strip()
        if data != None:
            return str(data)


def getLatLon(bs):
    mapDiv = bs.find('div', class_='item-map-wrapper')
    if mapDiv != None:
        return (float(mapDiv.attrs['data-map-lat']), float(mapDiv.attrs['data-map-lon']))


def getPageItemsDataFrame(main_url, url):
    bs = getBeautifulSoup(url)
    if bs != None:
        links = bs.find_all('a', class_='item-description-title-link')
        df = pd.DataFrame({'Link' : pd.Series(map(lambda x: urlparse.urljoin(main_url, x.get('href')), links))})
    return df


def getItemsDataFrame(base_url, main_url):
    bs = getBeautifulSoup(main_url)
    if bs != None:
        pages_df = getPagesDataFrame(bs, base_url, main_url)
        items_df = pd.DataFrame(columns = ['Link'])
        for index, page in pages_df.iterrows():
            items_df = items_df.append(getPageItemsDataFrame(main_url, page['Link']), ignore_index=True)
    return items_df


def getItemData(items_df):
    df = pd.DataFrame(columns = ['Link', 'Floor Num', 'Floor Cnt', 'House Type', 'Rooms Cnt', 'Space Cnt', 'Address', 'Lat', 'Lon'])
    for index, item in items_df.iterrows():
        print(f'Link: {item["Link"]}; Ind: {index}')
        time.sleep(20)
        bs = getBeautifulSoup(item['Link'])
        if bs != None:
            df.loc[index, 'Link']       = item['Link']
            df.loc[index, 'Floor Num']  = getFloorNum(bs)
            df.loc[index, 'Floor Cnt']  = getFloorCnt(bs)
            df.loc[index, 'House Type'] = getHouseTyp(bs)
            df.loc[index, 'Rooms Cnt']  = getRoomsCnt(bs)
            df.loc[index, 'Space Cnt']  = getSpaceCnt(bs)
            df.loc[index, 'Address']    = getAddress(bs)
            df.loc[index, 'Lat'], df.loc[index, 'Lon'] = getLatLon(bs)
            print(df.head())
    return df


if __name__ == '__main__':
    base_url = 'https://www.avito.ru' 
    add_url = '/balakovo/kvartiry/prodam/1-komnatnye'
    main_url = getMainUrl(base_url, add_url)
    itemdata = getItemData(getItemsDataFrame(base_url, main_url))
    itemdata.to_excel("output.xls")
