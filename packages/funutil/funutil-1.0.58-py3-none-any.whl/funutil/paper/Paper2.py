#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    keywords = "通信"  ### 查询的主题
    n = 0
    target = (
        "http://search.cnki.net/search.aspx?q="
        + str(keywords)
        + "&rank=relevant&cluster=all&val=CJFDTOTAL&p={}"
    )
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
    headers = {"User-Agent": user_agent}
    for i in range(10):
        i = i * 15
        target = target.format(i)
        req = requests.get(url=target)
        html = req.text
        html = html.replace("<br>", " ").replace("<br/>", " ").replace("/>", ">")
        bf = BeautifulSoup(html, "html.parser")
        texts = bf.find("div", class_="articles")
        texts_div = texts.find_all("div", class_="wz_content")
        for item in texts_div:
            item_name = item.find("a").text
            item_href = item.find("a")["href"]
            item_refer2 = item.find("span", class_="count").text
            print("{} {} {}\n".format(item_name, item_href, item_refer2))
    print(n)
