
# -*- coding: utf-8 -*-
#################
### connection制限解除
#################
import agent as ag
import link_pool_st as lp
import access_pool as ap

import multiprocessing
from time import sleep
from datetime import datetime as dt
import datetime as dt_parent
import sys,os,shutil,csv
import random ### seed?urlをシャッフル（実装済み）＊＊＊＊説明無し＊＊＊＊

import crawl_setting as cs #myself用の設定プラグイン
import json



##############################
### Agent.pyにも設定項目あり###
### wget項目停止中
##############################



class crawl_master():

	def __init__(self):

		self.agent_farm = cs.agent_farm
		# 結果フォルダ
		self.result_folder = cs.result_folder


		fo = open(self.result_folder+'log.out', 'w')
		sys.stdout = fo

		self.seed_filepath = cs.seed_filepath
		print  self.seed_filepath



		#保存ファイル先を設定(コアの部分)
		self.result_folder =  cs.result_folder
		self.record_path = cs.record_path
		self.data_base_path = cs.data_base_path
		self.image_base_path = cs.image_base_path
		self.wget_base_path = cs.wget_base_path

		self.check_folder(self.data_base_path)
		self.check_folder(self.image_base_path)
		self.check_folder(self.record_path)
		self.check_folder(self.wget_base_path)

		print '[END] delete & make'

		self.core =  cs.core#使用コア数
		self.domain_max = cs.domain_max#同一ドメイン最大取得数
		self.progress_span = cs.progress_span##進捗報告スパン(秒)
		self.process_span = cs.process_span#ずーーとぐるぐるだけど、１週あたりの間隔
		self.out_time = cs.out_time#タイムアウト時間(アクセスそのものの)

		self.seed_agent_name = cs.seed_agent_name#seedとしてクロール開始する連中
		self.link_agent_name = cs.link_agent_name

		self.wal_opt = cs.wal_opt #訪問先からゲットしたURLをリンクプールに突っ込む(0)/突っ込まない(1)
		self.wgl_opt = cs.wgl_opt #URL取得できなかった場合、待つ(0)/即終了(1)

		self.timeout_wait = cs.timeout_wait #URL取得できなかった場合、待つ、各試行の待ち時間
		self.timeout_cnt  = cs.timeout_cnt #URL取得できなかった場合、待つ、試行回数

		return

	def check_folder(self,path):
		if  os.path.exists(path):
			shutil.rmtree(path)			
			os.makedirs(path)
			print 'delete & make',path
		else:
			os.makedirs(path)
			print 'make',path
		return 

	#seedがあればseedを返す、それ以外はなにもしない。
	## 補助関数 ##
	def extract_domain_url(self,origin_url):#上の補助関数
		url = origin_url.split('//',1)[-1]
		domain = url.split('/',1)[0]#取得リンクからしか生成できないため
		return url,domain

	def seed_data(self,data,url=""):
		sys.stdout.flush()
		data['origin_url'] = url
		data['url'],data['domain'] = self.extract_domain_url(data['origin_url'])
		return data



	def make_seed_list(self):
		try:
			self.seed_url_list = [ line[0] for line in csv.reader(open(self.seed_filepath)) ]
			self.seed_domain_list = [ self.extract_domain_url(url)[1] for url in self.seed_url_list ]
			print '[{0}] < ENTER seed url link  > A-(parent) : #link = {1}'.format(dt.now(),len(self.seed_url_list))
			print '[{0}] < INITIAL DOMAIN > A-(parent) : #domain = {1}'.format(dt.now(),len(self.seed_domain_list))

		except Exception as e:
			print '[{0}] < [FAILED] ENTER seed url link  > A-(parent) : {1}'.format(dt.now(),e)

		sys.stdout.flush()
		return 


	###各Agentの挙動を統括###
	def agent_master(self,link_process,link_pool, access_pool,alive_q,convert_url_dict):
		###==================###
		###各Agentの大本の挙動統括#
		###==================###

		name = multiprocessing.current_process().name
		print '[{1}] A-{0} : Start'.format(name,dt.now())
		##== 初期化処理 ==##
		#初回はシードURLにアクセスし、リンクを拾い上げる

		agent_obj = ag.Agent(name,convert_url_dict)#共有物を中へ

		data = {}
		data['sleep'] = self.process_span
		sys.stdout.flush()


		if str(name) == "0":
			print '[{1}] < ENTER link optimizer > A-{0}'.format(name,dt.now())
			sys.stdout.flush()
			## 永遠にリンクの整理をやる ##
			with link_process: #獲得までたいきさせられる
				link_pool.set_arrow_domain_list(self.seed_domain_list)#seed
				link_pool.add_wait_new_link_list(self.seed_url_list)#seed
				link_pool.add_new_link_list(alive_q)
			return #終了

		else:
			data = self.seed_data(data,"")
			status = 'wait_get_link'
			print '[{1}] < ENTER Sleep optimize(START) > A-{0}'.format(name,dt.now())
			sys.stdout.flush()
			sleep(10)#１５秒待機

		
		###以下の関数をurl通過なし版と追加あり版で実行する
		### 追加無し版は全てのpoolが終了した地点で切り替える必要
		self.agent_crawl_routine(name,agent_obj,link_pool,access_pool,link_process,alive_q,status,data)
	    ################################################

		return

	def agent_crawl_routine(self,name,agent_obj,link_pool,access_pool,link_process,alive_q,status,data):
		### URLが帰ってくるまで永遠に周る ###
		###==============###
		###各Agentの挙動詳細#
		###==============###

		past_report = dt.now()
		while True:
			sys.stdout.flush()
			
			###== 進捗報告 ==### MODE : *___ 
			span = (dt.now() - past_report)
			if  span > dt_parent.timedelta(seconds=self.progress_span):
				agent_obj.progress_report(span.total_seconds())
				past_report = dt.now()
				sys.stdout.flush()
				access_pool.check_link_pool()

			###== 次回URL取得 ==### MODE : _*__
			if status == 'wait_get_link':
				#print '[{1}] A-{0} : < ENTER > Get link '.format(name,dt.now())
				access_pool.check_link_pool()
				sys.stdout.flush()
				data = access_pool.get_next_link()
				### ない場合は終了(mode判定) ###
				if data['url'] is None:
					if self.wgl_opt == 1 :
						print '[{1}] A-{0} : END'.format(name,dt.now())
						sys.stdout.flush()
						status = 'end'
					else:
						data = access_pool.get_next_link()
						if data['url'] is None: #再試行
							timeout_cnt = 0
							while True:
								timeout_cnt+=1
								sleep(self.timeout_wait)
								data = access_pool.get_next_link()

								if not data['url'] is None:
									#取得できた
									break
								else:
									#######コメントアウトしておわらせない########
									#site毎にしたいので、、、ていし処理
									if timeout_cnt == self.timeout_cnt:
										#できないならば、で、１０会
										print '[{1}] A-{0} : END'.format(name,dt.now())
										sys.stdout.flush()
										status = 'end'
										break
						else:
							#無事通過。復活
							status = 'wait_access'
							print '[{1}] A-{0} : (Revive)< END > Get link'.format(name,dt.now())
							continue
				else:
					print '[{2}] A-{0} : NEXT -> {1}'.format(name,data['origin_url'],dt.now())
					if data['sleep'] > 0:
						print '[{2}] A-{0} : Sleep -> {1}'.format(name,data['sleep'],dt.now())

					status = 'wait_access'

					print '[{1}] A-{0} : < END > Get link'.format(name,dt.now())
				sys.stdout.flush()

			sleep(data['sleep'])
			data['sleep'] = self.process_span

			if status == 'wait_access':
				### コネクション数制限 ###
				print '[{2}] A-{0} : ACCESSing -> {1}'.format(name,data['origin_url'],dt.now())
				sys.stdout.flush()
				agent_status = False
				try:
					agent_status = agent_obj.access_page(data['origin_url'],data['domain']) #アクセスと解析(wget is abolished)
				except:
					print '[{2}] A-{0} : < Error > ACCESSing -> {1}'.format(name,data['origin_url'],dt.now())
					agent_status = False

				status = 'wait_agg_link'
				print '[{2}] A-{0} : < END > ACCESSing -> {1}'.format(name,data['origin_url'],dt.now())

				access_pool.check_link_pool()
				sys.stdout.flush()

			###== リンク追加 ==###
			if status == 'wait_agg_link':
				### 結果反映 ###
				print '[{2}] A-{0} : < ENTER > Aggregating -> {1}'.format(name,data['origin_url'],dt.now())
				sys.stdout.flush()
				with link_process: #獲得までたいきさせられる
					link_pool.makeActive(name) #権利獲得管理用
					### ------------------------ ###
					try:
						if agent_status == True:
							if self.wal_opt == 1:
								print '[{2}] A-{0} : < SKIP > Aggregating -> {1}'.format(name,data['origin_url'],dt.now())

							else:
								url_list = agent_obj.url_list
								if not url_list is None:
									link_pool.add_wait_new_link_list(url_list) #とりあえずぶっこむ
							sys.stdout.flush()
						else:
							#捨てアドからlinkpoolに復活させる処理、最大数１減らす
							link_pool.rescue_link_list(data) 
					except:
						pass
					### ------------------------ ###
					link_pool.makeInactive(name)	#権利廃棄管理用
					status = 'wait_get_link'
					print '[{2}] A-{0} : < END > Aggregating -> {1}'.format(name,data['origin_url'],dt.now())
					sys.stdout.flush()

			if status == 'end':
				alive_q.put(name)
				link_pool.add_wait_new_link_list(['http://localhost/']) #とりあえずぶっこむ
				break

		sys.stdout.flush()
		return 


	def crawl_master(self):
		self.make_seed_list()#移転
		##== URLプールの作成 =##
		##収集側と配給側で共有する
		q_pre = multiprocessing.Queue() #一次請けリンクpoolの作成。容量は無限大
		q = multiprocessing.Queue() #リンクpoolの作成。容量は無限大
		link_pool = lp.link_pool(q,q_pre) #リンク収集
		access_pool =  ap.access_pool(q) #リンク配給

		##== HTMLをDL済みでそこにアクセスする場合には解決が必要。で、共有辞書 ==##
		mgr = multiprocessing.Manager()
		convert_url_dict = mgr.dict()

		# if cs.require_convert_url:
		# 	with open('../asset/convert_dict.json') as f:
		# 		convert_url_dict.update(json.load(f))
		# 	print '[DONE] Read convert dict : Len = ',len(convert_url_dict)
		# else:
		# 	pass
		if cs.require_convert_url:
			with open('../asset/selected_convert_dict.json') as f:
				convert_url_dict.update(json.load(f))
			print '[DONE] Read convert dict : Len = ',len(convert_url_dict)
		else:
			pass

		# invalid_pool =  ivp.invalid_pool(q) #意味のないリンク

		##== ネットワークコネクション数制限 ==##
		link_process = multiprocessing.Semaphore(self.core)#全コアがアクセス可能

		##== 生死のコミュニケーション==##
		alive_q = multiprocessing.Queue(self.core-1)

		##== リンクプール処理系の同時取扱数制限 ==##
		# connection_process = multiprocessing.Semaphore(400) ##いくつでもいい。 

		##== Agentにプール情報を割り当て ==##
		agents = [ multiprocessing.Process(target=self.agent_master, name=str(i), args=(link_process, link_pool, access_pool, alive_q,convert_url_dict)) for i in range(self.core) ]

		try:
			##== Agentの実行 ==##
			for agent in agents:
				agent.start()

			##== 終了は合わせる ==##
			for agent in agents:
				agent.join()

			print "[{0}] Crawling is finished ".format(dt.now())

		except KeyboardInterrupt as e:
			os.system('pkill -KILL -f chromedriver')
			print '[Force Safty Stop] Parent Process'

		except Exception as e:
			os.system('pkill -KILL -f chromedriver')
			print '[Force Safty Stop] Parent Process(except)'
		return 	

	    
if __name__ == '__main__':
	cm = crawl_master()
	cm.crawl_master()
