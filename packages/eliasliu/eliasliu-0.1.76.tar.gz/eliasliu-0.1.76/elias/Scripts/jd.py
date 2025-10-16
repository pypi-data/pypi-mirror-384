# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 09:12:05 2023

@author: nlsm
"""

from selenium import webdriver
import time
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys

class jd: 
    
    def __init__(self):    
        chromedriver = 'C:\Program Files\Google\Chrome\Application\chromedriver'
        self.driver = webdriver.Chrome(chromedriver)
    
    def get_url(self,url = 'https://www.jd.com'):
        self.driver.get(url) 
    
    def head_check(self): # 防止登录页面（京东-欢迎登录）
        from bs4 import BeautifulSoup
        pageSource = self.driver.page_source # 获取Elements中渲染完成的网页源代码
        soup = BeautifulSoup(pageSource,'html.parser')  # 使用bs解析网页
        head = soup.find("title").text
        return head
    
    
    def check_error(self):
        # 首个商品图片背后链接
        from bs4 import BeautifulSoup
        pageSource = self.driver.page_source # 获取Elements中渲染完成的网页源代码
        soup = BeautifulSoup(pageSource,'html.parser')  # 使用bs解析网页
        
        # 确认搜索结果(汪~没有找到搜索词相关商品)
        result = soup.find('div',class_ = "check-error")
        
        if result != None:
            # result_key_codelist = result.find_all('a',class_ = "key2")
            # result_key_list = []
            # for k in result_key_codelist:
            #     result_key  = k.text
            #     result_key_list.append(result_key)
            result_key  = result.find('a',class_ = "key2").text
        else:
            result_key = None
        return result_key
    
    
    
    def search(self,query):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        try:
            search_box = self.driver.find_element(By.XPATH,"/html/body/div[1]/div[4]/div/div[2]/div/div[2]/input") 
        except:
            search_box = self.driver.find_element(By.XPATH,"/html/body/div[3]/div[2]/div/input")
        
        search_box.clear()
        # search_box.send_keys('0123')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        # assert query in self.driver.title, f"The title of the webpage does not contain the string '{query}'"
        
        import time
        time.sleep(1)
        
    def href_get(self,n=0):
        # 首个商品图片背后链接
        from bs4 import BeautifulSoup
        pageSource = self.driver.page_source # 获取Elements中渲染完成的网页源代码
        soup = BeautifulSoup(pageSource,'html.parser')  # 使用bs解析网页       
        
        goods_list = soup.find('div',id = "J_goodsList").find_all('li',class_='gl-item')
        goods_list = goods_list[n:]
        # i = goods_list[0]
        # 跳过广告标识
        for j in range(len(goods_list)):
            try:
                isadd_ = goods_list[j].find('span',class_ = "p-promo-flag").text
            except:
                isadd_ = None
            if isadd_ == "广告":
                pass
            else:
                break
                
        good = goods_list[j].find("div",class_="p-img")
        # print(good)
        # title = good.find("a")["title"]
        href = good.find("a")["href"].replace('//',"https://")
        return href
    
    
    def item_get(self,href):
        from bs4 import BeautifulSoup
        self.driver.get(href) 
        
        pageSource = self.driver.page_source # 获取Elements中渲染完成的网页源代码
        soup = BeautifulSoup(pageSource,'html.parser')  # 使用bs解析网页
        
        item = soup.find("div",class_="crumb fl clearfix").text.replace('\n',"")
        spu_list = soup.find("ul",class_="parameter2 p-parameter-list").find_all('li')
        spu = spu_list[0]['title']
        spu_no = spu_list[1]['title']
        # spu_no = spu_list[6]['title']
        brand = soup.find("ul",class_="p-parameter-list").find('li')['title']
        return item,spu,spu_no,brand
    
    
    def close(self):
        self.driver.close()
        
    # ---------------------------
class key_words:
    
    def hla(goods='HLA-短袖T恤 IP款-HNTBJ2D423A-EB-深蓝花纹-175/92A(50)'):
        import re
        ls = re.findall('[\da-zA-Z]+', goods)
        gid = [i for i in ls if len(i)>8][0]
        
        p = goods.replace('-','+').split('+')[1].replace(" ","")
        print(p,gid)
        return p,gid
        










if __name__ == '__main__':
    driver = jd()
    driver.get_url(url = 'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F')
    retry = 3
    while driver.head_check()=='京东-欢迎登录' and retry>1:
        driver.close()
        time.sleep(5)
        driver = jd()
        driver.get_url()
        retry = retry-1
    href = driver.search(query = 'iphone')
    item = driver.item_get(href = href)
    driver.close()
