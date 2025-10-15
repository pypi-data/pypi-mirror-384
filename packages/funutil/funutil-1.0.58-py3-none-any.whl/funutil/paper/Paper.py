import demjson
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 显示所有列
pd.set_option("display.max_columns", None)
# 显示所有行
pd.set_option("display.max_rows", None)
# 设置value的显示长度为100，默认为50
pd.set_option("max_colwidth", 500)

# 显示所有列
pd.set_option("display.max_columns", None)
# 显示所有行
pd.set_option("display.max_rows", None)
# 设置value的显示长度为100，默认为50
pd.set_option("max_colwidth", 500)


def get_list():
    cookies = {
        "dotmatics.elementalKey": "SLsLWlMhrHnTjDerSrlG",
        "bm_sz": "3BF93D7B71A744D350FF28590058D6D3~YAAQVVcyuAWtrnxuAQAA8y78pwWLrEY9j+J+r9sK0nfw/MjUdbYHRu9nC30obskQRbhdTnxQaEN4Q4zsABCBmzNOEJI2X8DhLTwfCnM4QtbuylOxmjJ2A906YWxuE/zMHshwYlnrbHrywp3j4LJ8l3+bgAjO4o6DC/o2ooWAGQht87xCASC+3em2g+aNMMp8PYQtivGgpQw=",
        "SID": "5Bk2kUNVevpPxhkgdgD",
        "CUSTOMER": "China Jiliang University",
        "E_GROUP_NAME": "China Jiliang University",
        "ak_bmsc": "258744D0E96907D177F984229A3C181617C2BBF6271100009338DD5DFA9A5659~plRgekuhVPntsAMA+BEtCJTyxww2rt5hIb6isw9ZizLKcTGofnqQ5BRQuCRt2D6MxvKB66JBmGnOIBW5lBGk5vZq4J1SkqCf1nvsEVqaHax0yCK0Zfu2JlZ0Bz/DIngPKeubLKBwPP5z1cN4Ii4Oe/z0MJjWWgqZpgER/5LhicSmqPc3k1lWUBZ2v1z+j8KFBMErwe3ef8ntIyDgodmSYzV98J8M9GErk/O9wYksFr4ewjKOKwNH8+JrnYCKabO8+0",
        "_sp_ses.630e": "*",
        "_abck": "41A499AC1838C7AFC94C2840BB494EAD~0~YAAQFDwxF04c2KJuAQAAN1YsqAI4KLEmyo28+OC6QOT1vyWGAQrCE4fClJV5Y5SSj0MS6GPcKtsuEeYSpVqxCJDqqdbvJ6G/ICmJZJXHVVXsAImt38KQG6F58a4ZUk6Ed9bl3wLDZcaN2gbDeyVmewiZPV3vV5n9KNndV0Iyli04MOPu50HWoqYQEHtQCH+h6XlxOcpvCAkH3Q6Zpd7ACN8cSJp9uMnnfhRnaO3owHQpDudeuwSKdayas23zCRH7J1U+jGdA1Gegdj7djj+yONA9PZ4C95xzsnVGbYBBkQcNS6LPz0Vbs8OjrrjZfavKldiIL18hQfB4RKXh/6Ru~-1~-1~-1",
        "bm_sv": "46C2AD419DA15E55DAF2A48C4DEDDD78~/OFdYg2OzCNYDMdm3nlikSMlO8RrWYQuocJeZaBEAKcC9VA6L0ZeB1MMYiyTkNS7rUIiDFG4Eyceb17eK6HCkhyBUlGX+c4pPUWfOmpNbH08wsidqi/VgGye4Fah7WhmrFrBRaB3ubRGLlZO3b2JnkV5Mzu1Q/JCx60uBNe3gbs=",
        "_sp_id.630e": "16a7684c-a7ce-4223-820c-616e3c2b0ad3.1573358376.6.1574779640.1574776360.f784709b-7763-4265-b7b7-b8255a1da1ed",
    }

    headers = {
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "X-1P-WOS-SID": "5Bk2kUNVevpPxhkgdgD",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Mobile Safari/537.36",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Referer": "https://app.webofknowledge.com/author/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    params = (
        ("authorId", "29481976"),
        ("batch", "true"),
        ("limit", "50"),
        ("offset", "0"),
        ("order", "desc"),
        ("sort", "year"),
    )
    url = "https://app.webofknowledge.com/api/rrc/author/publications"
    response = requests.get(url, headers=headers, params=params, cookies=cookies)

    res = demjson.decode(response.text)
    return res["hits"]


def get_detail(meta):
    import requests

    cookies = {
        "dotmatics.elementalKey": "SLsLWlMhrHnTjDerSrlG",
        "bm_sz": "3BF93D7B71A744D350FF28590058D6D3~YAAQVVcyuAWtrnxuAQAA8y78pwWLrEY9j+J+r9sK0nfw/MjUdbYHRu9nC30obskQRbhdTnxQaEN4Q4zsABCBmzNOEJI2X8DhLTwfCnM4QtbuylOxmjJ2A906YWxuE/zMHshwYlnrbHrywp3j4LJ8l3+bgAjO4o6DC/o2ooWAGQht87xCASC+3em2g+aNMMp8PYQtivGgpQw=",
        "SID": "5Bk2kUNVevpPxhkgdgD",
        "CUSTOMER": "China Jiliang University",
        "E_GROUP_NAME": "China Jiliang University",
        "ak_bmsc": "258744D0E96907D177F984229A3C181617C2BBF6271100009338DD5DFA9A5659~plRgekuhVPntsAMA+BEtCJTyxww2rt5hIb6isw9ZizLKcTGofnqQ5BRQuCRt2D6MxvKB66JBmGnOIBW5lBGk5vZq4J1SkqCf1nvsEVqaHax0yCK0Zfu2JlZ0Bz/DIngPKeubLKBwPP5z1cN4Ii4Oe/z0MJjWWgqZpgER/5LhicSmqPc3k1lWUBZ2v1z+j8KFBMErwe3ef8ntIyDgodmSYzV98J8M9GErk/O9wYksFr4ewjKOKwNH8+JrnYCKabO8+0",
        "_sp_ses.630e": "*",
        "_abck": "41A499AC1838C7AFC94C2840BB494EAD~0~YAAQFDwxF04c2KJuAQAAN1YsqAI4KLEmyo28+OC6QOT1vyWGAQrCE4fClJV5Y5SSj0MS6GPcKtsuEeYSpVqxCJDqqdbvJ6G/ICmJZJXHVVXsAImt38KQG6F58a4ZUk6Ed9bl3wLDZcaN2gbDeyVmewiZPV3vV5n9KNndV0Iyli04MOPu50HWoqYQEHtQCH+h6XlxOcpvCAkH3Q6Zpd7ACN8cSJp9uMnnfhRnaO3owHQpDudeuwSKdayas23zCRH7J1U+jGdA1Gegdj7djj+yONA9PZ4C95xzsnVGbYBBkQcNS6LPz0Vbs8OjrrjZfavKldiIL18hQfB4RKXh/6Ru~-1~-1~-1",
        "JSESSIONID": "2B1C4D8ED4EDFD737AA372B4B4ABE3DC",
        "bm_sv": "46C2AD419DA15E55DAF2A48C4DEDDD78~/OFdYg2OzCNYDMdm3nlikSMlO8RrWYQuocJeZaBEAKcC9VA6L0ZeB1MMYiyTkNS7rUIiDFG4Eyceb17eK6HCkhyBUlGX+c4pPUWfOmpNbH08wsidqi/VgGye4Fah7Whm9vmpN/StBbh5j6ie7PZHIw36A/tzo52CwPHhfY+LzMg=",
        "_sp_id.630e": "16a7684c-a7ce-4223-820c-616e3c2b0ad3.1573358376.6.1574780163.1574776360.f784709b-7763-4265-b7b7-b8255a1da1ed",
    }

    headers = {
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Mobile Safari/537.36",
        "Sec-Fetch-User": "?1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "navigate",
        "Referer": "https://app.webofknowledge.com/author/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    params = (
        ("customersID", "RRC"),
        ("mode", "FullRecord"),
        ("IsProductCode", "Yes"),
        ("product", "WOS"),
        ("Init", "Yes"),
        ("Func", "Frame"),
        ("DestFail", "http://www.webofknowledge.com"),
        ("action", "retrieve"),
        ("SrcApp", "RRC"),
        ("SrcAuth", "RRC"),
        ("SID", "5Bk2kUNVevpPxhkgdgD"),
        ("UT", meta["ut"]),
    )
    times = 5
    while times > 0:
        times -= 1
        try:
            response = requests.get(
                "https://apps.webofknowledge.com/InboundService.do",
                headers=headers,
                params=params,
                cookies=cookies,
            )
            break
        except Exception as e:
            print(f"error:{e} try again {times}")

    soup = BeautifulSoup(response.text, "lxml")

    def get_value(soup, key1, key2=None):
        res = soup.find("div", class_=key1)
        if key2 is not None:
            res = soup.find("p", class_=key2)

        value = ""
        if res is not None:
            value = res.text or ""
        value = value.replace("\n", "")
        value = value.strip(" ")
        return value

    meta["sourceTitle"] = get_value(
        soup, "block-record-info block-record-info-source", "sourceTitle"
    )

    # s1 = soup.find('div',class_='block-record-info block-record-info-source').find_all('p',class_='FR_field')
    s1 = soup.find_all("p", class_="FR_field")

    for line in s1:
        key = None
        value = None
        for i in line.find_all():
            text = i.text
            text = text.strip("\n")
            text = text.strip(":")
            text = text.strip()
            if key is None:
                key = text
            else:
                value = text
        if value is not None:
            meta[key] = value
    return response.text


meta_list = get_list()
print("size {}".format(len(meta_list)))
index = 0
for meta in meta_list:
    index += 1
    print(index)
    res = get_detail(meta)
    pass
df = pd.DataFrame.from_dict(meta_list)

# df.to_excel('result.xls')
