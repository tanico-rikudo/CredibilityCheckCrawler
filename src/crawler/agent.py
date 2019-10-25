
# -*- coding: utf-8 -*-
###############
#image off
##############
import time,os,json,csv,gzip

# import screenshot_driver as sd #chrome用の独自プラグイン
import scroll as sc #scroll用の独自プラグイン
import crawl_setting as cs #myself用の設定プラグイン

from datetime import datetime as dt
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options #chrome
from selenium.webdriver.common.action_chains import ActionChains

import pandas as pd
import hashlib #ハッシュ化
from numpy.random import *
from bs4 import BeautifulSoup as bs

import copy
import subprocess

import timeout_decorator
import requests
import shutil
import codecs
import urlparse

##############################
### result folder 設定下の方に###
##############################

def check_folder(path):
	if not os.path.exists(path):
		os.makedirs(path)

def check_words_in_list(target , list):
	for word in list:
		if target.find(word) > -1:
			return True
	return False


class Agent():
	###=================###
	###アクセス人の基本設定###
	###=================###
	def __init__ (self,agent_name,convert_url_dict):

		self.agent_name = agent_name
		self.agent_farm = cs.agent_farm

		self.progress_record = {}
		self.progress_record['n_done'] = 0
		self.progress_record['progress'] = 0
		self.progress_record['past_n_done'] = 0

		#使用JSの読み込み(JSを使用する場合)
		with open('checker.js') as f:
			self.checker_js_code = f.read()  # ファイル終端まで全て読んだデータを返す

		with open('linked_link_checker.js') as f:
			self.replace_js_code = f.read()

		#使用Agent群の読み込み
		self.agent_list  = [line[0] for line in csv.reader(open('../asset/chrome_agent_list.csv')) for agent in line ]
		# print self.agent_list

		self.url = {} #型のみ定義
		self.out_time = cs.out_time #制限時間
		self.forbidden_domain_list = cs.forbidden_domain_list
		self.forbidden_word_list   = cs.forbidden_word_list
		self.link_checking_time_out = cs.link_checking_time_out
		self.link_checking = cs.link_checking

		#保存ファイル先を設定(コアの部分)
		self.result_folder =  cs.result_folder
		self.record_path = cs.record_path
		self.data_base_path = cs.data_base_path
		self.image_base_path = cs.image_base_path
		self.wget_base_path = cs.wget_base_path

		check_folder(self.data_base_path)
		check_folder(self.image_base_path)
		check_folder(self.record_path)
		check_folder(self.wget_base_path)

		#自分コンテンツの場合に必要 
		self.allow_xsite= cs.allow_xsite
		self.require_convert_url = cs.require_convert_url
		self.convert_url_dict = convert_url_dict#共有
		self.dump_basepath = cs.dump_basepath

		return 


	###===============###
	###文字列-->JSON関数###
	###===============###
	def replay_text_parser(self,text):
		dict = json.loads(text)
		return dict

	###==================###
	###アクセス毎に設定を変更###
	###==================###
	def ready_browser(self,url):

		#url
		self.url['url'] = url
		self.url['hash'] = str(self.agent_name) + '-' + str(self.progress_record['n_done'])
		self.progress_record['n_done']+=1

		#保存ファイル先
		self.data_path = self.data_base_path + self.url['hash']
		self.image_path = self.image_base_path+self.url['hash']
		# self.wget_base_path


		#ブラウザ設定(chrome)**共通項**
		self.options = Options()
		self.options.add_argument('--headless')
		self.options.add_argument('--disable-gpu')
		self.options.add_argument("--window-size=1920,1080")
		self.now_agent = self.agent_list[int(rand()*len(self.agent_list))]
		self.options.add_argument('--user-agent='+ self.now_agent )#agent変更処理
		if self.allow_xsite:
			self.options.add_argument('--disable-web-security')
			# self.options.add_argument('--user-data-dir')
			# pass

	###===============###
	###　　進捗報告 　　###
	###===============###
	def progress_report(self,seconds=60.0):
		self.progress_record['time'] = dt.now().strftime('%Y-%m-%d %H:%M:%S')
		self.progress_record['interval'] = seconds
		self.progress_record['progress'] = self.progress_record['n_done'] - self.progress_record['past_n_done']
		self.progress_record['past_n_done'] = copy.copy(self.progress_record['n_done'])
		print '[{1}] ** Report **  A-{0} : {2}({3}) < speeds = {4} pages/m > '.format(self.agent_name,dt.now(),self.progress_record['n_done'],self.progress_record['progress'],float(self.progress_record['progress'])/(seconds/60))
		with open(self.record_path+self.agent_name+'_'+'progress-record.json','a') as f:
			json.dump(self.progress_record, f)
			f.write('\n')
		return 

	###========================###
	###各リンクの確認変更する逐次関数###
	###========================###
	##Driverで扱っているオブジェクトをそのまま変更しちゃう怖い関数
	@timeout_decorator.timeout(60) #細分化に付き追加
	def each_linked_link_replacer(self,i,web_ele_obj,main_window):
		try:
			url = web_ele_obj.get_attribute('href')
			#禁止URLではない
			error = 0
			error += sum([ 1 for domain in self.forbidden_domain_list if domain in url])
			error += sum([ 1 for domain in self.forbidden_word_list if domain in url])
			if error > 0 :
				self.attack_result['invalid'] += 1
				return 
			#requestでの簡潔にアクセス
			r = requests.get(url,self.link_checking_time_out)
			if r.status_code == 200:
				if r.url != '':
					if sum([ 1 for blank_url in ['about:blank','javascript:void(0)'] if blank_url in r.url]) == 0:
						self.driver.execute_script(self.replace_js_code+'  return replace_link( {0} , "{1}" )'.format(i, r.url) )
						self.attack_result['done'] += 1
				return
			else:
				raise Exception

		except Exception as e:
			try:
				if self.link_checking:
					#webdriverでのアクセスに変更
					time.sleep(20)
					actions = ActionChains(self.driver)
					actions.move_to_element(web_ele_obj).perform()
					actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).click(web_ele_obj).perform()
					self.driver.switch_to.window(self.driver.window_handles[-1])
					time.sleep(20)
					new_url = self.driver.current_url
					self.driver.switch_to.window(main_window)
					self.driver.execute_script(self.replace_js_code+'  return replace_link( {0} , "{1}" )'.format(i, new_url) )
					self.attack_result['rescue_done'] += 1
				else:
					#ここでlink_check不要で返された例外は除外される。
					return 

			except  Exception as e:
				try:
					e_code = url
				except:
					e_code = "??"
				# print '[{1}] ** [{3}]Agent link_replace ERROR(continue to next link) **  A-{0} : {2}'.format(self.agent_name,dt.now(),e,e_code)
				self.driver.switch_to.window(main_window)#例外で拾われてdriverアクセスで発動されるので
		return 

	###==================###
	###実際にアクセスする関数###
	###==================###chromedriver = "/home/tanico/bin/chromedriver"
	@timeout_decorator.timeout(90) #細分化に付き追加
	def get_driver_obj(self,url):
		try:
			###=== WebDriverオブジェクトを作成する。===###
			chromedriver = "/home/"+self.agent_farm+"/bin/chromedriver"
			if self.agent_farm == 'macico':
				chromedriver = "/usr/local/bin/chromedriver"
			if self.agent_farm == 'eni4':
				chromedriver = "/home/tanico/bin/chromedriver"
			if self.agent_farm == 'e35':
				chromedriver = "/home/tanico/bin/chromedriver"
			# os.environ["webdriver.chrome.driver"] = chromedriver
			# self.driver = webdriver.Chrome(executable_path =  chromedriver ,chrome_options = self.options)
			self.driver = webdriver.Chrome(executable_path=chromedriver,chrome_options = self.options)
			self.driver.refresh();
			self.driver.set_page_load_timeout(self.out_time) #タイムアウト
			self.driver.get(url)

			# ##=== 取得ページのスクロール ===##
			sc.scroll(self.driver,True,1.5) #一旦スクロール(1.5秒)
		except Exception as e:
			print '[{1}] ** Agent Access worker ERROR **  A-{0} : {2}'.format(self.agent_name,dt.now(),e)
			raise Exception
		return

	###====================###
	###ENIちゃん用HTMLの置換群###
	###====================###
	def copy_target(self,from_path,to_path):
		try:
			shutil.copyfile(from_path, to_path)
		except Exception as e:
			print  e
			return False
		return True

	def source_replacer(self,html,url):
		soup = bs(html, "lxml")
		for tag  in soup.find_all(True):
			if tag.has_attr('src'):
				tag['src'] = urlparse.urljoin(url, tag['src'])
			if tag.has_attr('href'):
				tag['href'] = urlparse.urljoin(url, tag['href'])
		return soup

	def self_get_html_data(self,url):
		# url = 'https://www.ecopa.jp/notice/detail/869'
		# dump_filepath = 'ae36c4d47c87798dbe72155aa388f8a9_869.html'
		convert_url = None
		try:
			dump_filepath = self.dump_basepath+self.convert_url_dict[url]
			tmp_filepath = 'tmp_'+str(self.agent_name)+'.html'
			if self.copy_target(dump_filepath, tmp_filepath):
				with open(tmp_filepath,'r') as f:
					html = f.read()#.encode('utf-8')
					soup = self.source_replacer(html,url)
					with codecs.open(tmp_filepath, 'w', 'utf-8') as f:
						f.write(soup.prettify())
					# with open(tmp_filepath,mode = 'w') as f:
					# 	f.write(soup.prettify('utf-8'))
					print '[DONE]Replace'
					convert_url= 'file:///home/tanico/src/crawler/'+tmp_filepath
			else:
				print 'Copy is failed:'+dump_filepath +'->'+url

		except Exception as e:
			print '[{1}] ** Agent ERROR(Replacer) **  A-{0} : {2}'.format(self.agent_name,dt.now(),e)
			raise e

		return  convert_url


	###==================###
	###実際にアクセスする関数###
	###　のマスター        ###
	###==================###
	#@timeout_decorator.timeout(120) #細分化に付き廃止
	def access_page(self,url,domain):

		#アクセス前設定
		self.ready_browser(url)

		self.result_json = {}
		self.attack_result = {'invalid':0,'rescue_done':0,'done':0}
		self.checked_link_list = []

		try:

			###=== HTMLページ書き換え措置===###
			if self.require_convert_url:
				access_url = self.self_get_html_data(url)
				if access_url is None:
					raise Exception
			else:
				access_url = url

			###=== WebDriverオブジェクトを作成する。===###
			print  access_url
			self.get_driver_obj(access_url)

			# ##== 取得ページの画像 ==#
			# # self.driver.save_screenshot(self.image_path+ '_before.png') ## JS適用前保存

			##=== ソースの取得(SOUP化)と保存 ==## 
			self.html = self.driver.page_source.encode('utf-8')
			bs_data = bs(self.html,'lxml')
			with open(self.data_path+'_html',mode = 'w') as f:
				f.write(bs_data.prettify('utf-8'))

			##=== リンクの総当たり確認＋変更 ==##
			main_window = self.driver.current_window_handle  # 移動前のwindowを取っておく
			for i,web_ele_obj in enumerate(self.driver.execute_script(self.replace_js_code+" return get_linklist()")):
				self.each_linked_link_replacer(i,web_ele_obj,main_window)
			print self.attack_result

			##=== http or https のリンクのみ抽出 ===##
			# 禁止リスト入りしていない
			self.url_list = []
			tmp_url_list = [ link_obj.get_attribute('href') for link_obj in self.driver.find_elements_by_xpath("//a")]
			for url in tmp_url_list:
				if not url is None :
					if not url is '':
						if not check_words_in_list(url, self.forbidden_word_list):
							if not check_words_in_list(url, self.forbidden_domain_list):
								self.url_list.append(url)			


			##== JS実行　取得データ整形と保存 == ##
			js_result = self.driver.execute_script(self.checker_js_code+' return  startCheck()') ## JS適用
			result_dict = json.loads(js_result)
			result_dict['domain'] = domain
			with gzip.open(self.data_path+'_js-analyze.json.gz','w') as f:
				json.dump(result_dict, f)


			## 操作後操作 ##
			# self.driver.save_screenshot(self.image_path+'_after.png')
			# print '>>>>[END] After shot'

			## JSON操作 ##
			##なし
			self.driver.close()
			self.driver.quit()  # ブラウザを終了する。


		###=== 失敗した場合 ===###
		except KeyboardInterrupt as e:
			self.driver.close()
			self.driver.quit()  # ブラウザを終了する。
			print '[{1}] ** Force Safty Stop ** A-{0}'.format(self.agent_name,dt.now())
			return False

		except Exception as e:
			# print '>>>>[ERROR] @driver'
			print '[{1}] ** Agent ERROR **  A-{0} : {2}'.format(self.agent_name,dt.now(),e)
			try:
				self.driver.close()
				self.driver.quit()  # ブラウザを終了する。
			except:
				pass
			self.url_list = []

			return False 

		### 記録 ###
		record = {}
		record['time'] = dt.now().strftime('%Y-%m-%d %H:%M:%S')
		record['url'] = self.url['url']
		record['hash'] = self.url['hash']
		with open(self.record_path+self.agent_name+'_'+'record.json','a') as f:
			json.dump(record, f)
			f.write('\n')



		# print '>>[END] < '+self.url['url'][:100]+'... >'
		return True

	###===========###
	###WGET実行関数###
	###===========###
	@timeout_decorator.timeout(120)
	def wget_page(self,url):

		# ##== 取得ページのWGETあくせすと保存 ==##

		###設定####
		each_path = self.wget_base_path+self.url['hash']+'/'
		check_folder(each_path)

		cmd_array = ['wget','--tries=1','–-timeout=90','--quiet','--page-requisites','--convert-links','--no-host-directories','--user-agent='+self.now_agent,self.url['url']]

		### 実行 ###
		try:
			returncode = subprocess.check_call(cmd_array, cwd = each_path)
		except subprocess.CalledProcessError as e:
			print '[{1}] ** WGET_ERROR **  A-{0} : CODE : {2} - {3}'.format(self.agent_name,dt.now(),e.returncode,e.output)
		except Exception as e:
			print '[{1}] ** WGET_ERROR(!) **  A-{0} : CODE : {2} - {3}'.format(self.agent_name,dt.now(),e)

		return 



