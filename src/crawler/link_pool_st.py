
# -*- coding: utf-8 -*-

import random
import multiprocessing
import time


# from collections import deque #キュー構造
import Queue

import errno,sys
from socket import error as socket_error
from robotparser import RobotFileParser

from datetime import datetime as dt
import timeout_decorator

import crawl_setting as cs #myself用の設定プラグイン


class link_pool(object):
	###=====================###
	###　LINKとURLの特殊Agent ###
	###=====================###

	##=== 初期化 ===##
	def __init__(self,q,q_pre):

		super(link_pool, self).__init__()

		## 割り込み制御変数 ##
		self.mgr = multiprocessing.Manager()
		self.active = self.mgr.list()
		self.lock = multiprocessing.Lock()

		## 訪問済み ##
		self.visited_domain_dict = self.mgr.dict()

		self.recent_access_list = self.mgr.list()
		self.discard_list = self.mgr.list()

		self.wait_next_list = q_pre		##　処理待ちリンクのキュー
		self.next_list = q 		##　リンクのキュー

		self.error_dict = self.mgr.dict()

		## 各ドメインの上限 ##
		self.domain_max = cs.domain_max
		#　リンク制限
		self.osd_opt = cs.osd_opt


	def __str__(self):
		with self.lock:
			return str(self.active)


	###=====================###
	###リソースのアクセス数制限###
	###=====================###

	##=== ロックかける ===##
	def makeActive(self, name):
		self.now_ag_name = name
		with self.lock:
			self.active.append(name)

	##=== ロック解除 ===##
	def makeInactive(self, name):
		self.now_ag_name = ""
		with self.lock:
			self.active.remove(name)

	##=== 定期観察 ===##
	# def __str__(self):
	# 	with self.lock:
	# 		return str(self.active)


	##=== robots.txt取得 ===##
	## 判定OBJを返す ##
	@timeout_decorator.timeout(5)
	def access_robots_txt(self,domain):

		## ドメインに到達 ##
		if domain.split('/')[-1]=="":
			robots_url = domain+'robots.txt'
		else:
			robots_url = domain+'/robots.txt'

		rp = RobotFileParser() #アクセ獅子に行ってくれる。まぁhttpアクセスで
		rp.set_url('http://'+robots_url)
		rp.read()
		return rp


	##=== 訪問したことを通達 ===##
	def add_visited(self,data):

		##DOMAINを完璧に取得してくること！！！！　以下不要
		### urlの正規化を測りたいので、保存時におけるhttp or httpsを除去する
		### domainの正規化を測りたいので、保存時におけるhttp or httpsを除去する
		### 共に、wwwは除去の対象としない。これはwwwでまた別のサイトになり得るから

		###=====================###
		###Domain,URL,Robotを収容###
		###=====================###

		# data['url'] = data['url'].split('https',maxsplit=1)[-1]
		# data['url'] = data['url'].split('http',maxsplit=1)[-1]
		# data['domain'] = data['domain'].split('https',maxsplit=1)[-1]#取得できたので！
		# data['domain'] = data['domain'].split('http',maxsplit=1)[-1]

		#完了報告
		print self.visited_domain_dict
		# print data

		return

	##=== 特定のドメインにのみ追加リンクを許す ===##
	def set_arrow_domain_list(self,domain_list):
		if self.osd_opt == 0:
			self.arrow_domain_list = domain_list
		return


	##=== 収集したリンクリストを整理 ===##
	def add_wait_new_link_list(self,link_list,add_mode = True):

		if add_mode == False: #seedのみ実行用
			return
		self.add_link_by_hand()#常に途中即時装填処理を掛ける。
		if not link_list is None:
			random.shuffle(link_list)		#リンクはシャッフルして多様性強化
			for link in link_list:
				self.wait_next_list.put(link,block = True)
			print '[{1}] A-(Pool) < END (No sort out) > add new {0} links '.format(len(link_list),dt.now())
		return

	##=== エラーにおける予備URLの補填と台帳修正 ===##
	def rescue_link_list(self,data):
		##=== ドメイン定義されているか ===##
		try:
			recorded_target =  self.visited_domain_dict[data['domain']]
			recorded_target['link']   = recorded_target['pre_url'].pop()
			recorded_target['domain'] = data['domain']
			recorded_target['origin_link'] = 'http://'+recorded_target['link']
			recorded_target['scheduled_url'].add(recorded_target['link'])
			
			self.visited_domain_dict[recorded_target['domain']] = recorded_target
			self.next_list.put(recorded_target,block = True)
			print '[{0}] A-(Pool)  Rescured domain - {1} : {2}'.format(dt.now(),recorded_target['domain'],recorded_target['visit'])
			sys.stdout.flush()
		except Exception as e:
			recorded_target['error'] += 1
			recorded_target['visit'] -= 1 #１削減の処理は本来不要だけど、パターンが多すぎるのでとりあえず１減らしておく。
			print '[{0}] A-(Pool)  Rescured domain failed- {1} : {2} visited : {3}'.format(dt.now(),recorded_target['domain'],recorded_target['visit'],e)
			if recorded_target['error'] > self.domain_max :
				recorded_target['visit'] = self.domain_max
				print '[{0}] A-(Pool)  Rescured domain over failed {1}'.format(dt.now(),recorded_target['domain'])
			self.visited_domain_dict[recorded_target['domain']] = recorded_target

		return 			

	##=== 緊急装填処理 ===##
	def add_link_by_hand(self):
		try:
			if os.path.exists('../seed_url_list/emergency_url_list.csv'):
				link_list   = [line[0] for line in csv.reader(open('../seed_url_list/emergency_url_list.csv')) for agent in line ]
				for link in link_list:
					self.wait_next_list.put(link,block = True)
				print '[{1}] A-(Pool) < EME > add new {0} links '.format(len(link_list),dt.now())
		except:
			pass
		return 		

	##=== 待機リンクリストを整理 ===##
	##=== 1コアのみ ===##
	def add_new_link_list(self,alive_q):
		#linkはjs voidは抜いたURL
		##========================================##
		##===           訪問済みURLに追加        ===##
		##===         訪問済みDOMAINに加算       ===##
		##=== 訪問済みドメインに対応するrobotを更新 ===##
		##========================================##
		j = 0
		while True:
			try:
				if alive_q.full():
					print '[{0}] A-(Pool) < END > All agent is dead'.format(dt.now())
					break
			except Exception as e:
				print '[{0}] A-(Pool) < END > Alive check error: {1}'.format(dt.now(),e)
				break

			target = {}
			sys.stdout.flush()
			try:
				link = self.wait_next_list.get(block=True)#獲得までブロックされる。無制限
				target['origin_link'] = link.encode('utf-8')
				target['link'] = target['origin_link'].split('https://',1)[-1]
				target['link'] = target['link'].split('http://',1)[-1]
				target['domain'] = target['link'].split('/',1)[0]#取得リンクからしか生成できないため
			except Exception as e:
				print '[{0}] A-(Pool) < END > Get some Error(continue) : {1}'.format(dt.now(),e)
				continue

			if target['origin_link'] == 'http://localhost/':#終了コード(L168制限を解除のために)
				continue

			if self.osd_opt == 0:#ドメイン制限
				if not target['domain'] in  self.arrow_domain_list: #無いなら通過不可
					continue

			try :
				if target['origin_link'] == '':
					continue
				else:
					##=== ドメイン定義されているか ===##
					try:
						recorded_target =  self.visited_domain_dict[target['domain']]
						##=== ドメイン定義されていてアクセス上限数超えていないかどうか ===##
						if recorded_target['visit'] < self.domain_max:
							is_max_n_domain = False
						else:
							is_max_n_domain = True
						##=== 予定URLに該当しない(同一ドメイン内で) ===##
						if not target['link'] in recorded_target['scheduled_url']:
							##=== robots.txtによってアクセスが禁止されていない ===##
							if recorded_target['robots'].can_fetch("*",target['link']):
								##=== 過去にアクセスできないと判定 ===##
								##　存在したら駄目なので・・・・
								try:
									is_exist = self.error_dict[target['link']]
								except Exception as e:
									j+=1
									##=== アクセスURLリスト入り ===##
									##=== 最大数に達していない ===##
									if is_max_n_domain == False:
										recorded_target['visit']+=1
										recorded_target['scheduled_url'].add(target['link'])

										self.visited_domain_dict[target['domain']] = recorded_target
										self.next_list.put(target,block = True)
										sys.stdout.flush()
									else:
										##=== 最大数に達している ===##
										## scheduled_urlには入れない。
										recorded_target['pre_url'].add(target['link'])
										self.visited_domain_dict[target['domain']] = recorded_target
									continue

						##=== 廃棄URLリスト入り ===##
						# self.discard_list.append(target)

						continue

					except Exception as e:

						##=== 未定義の場合 ===##
						##=== OBJ生成する ===##
						domain_dict = {}
						j+=1

						##=== robots.txt取得可能か ===##
						try:
							domain_dict['robots'] = self.access_robots_txt(target['domain'])
						except:
							#timeoutの場合はエラーとみなす
							self.error_dict[target['link']] = 1
							# print '[{0}] A-(Pool) < NOT_ADD_link [new domain -> cut by timeout] > add new link : {1}'.format(dt.now(),target['link'])#うるさいので
							continue
						domain_dict['visit'] =  1
						domain_dict['error'] =  0
						domain_dict['pre_url'] = set()

						##=== robots.txtによってアクセスが禁止されていないか ===##
						if domain_dict['robots'].can_fetch("*",target['link']):
							#許可
							domain_dict['scheduled_url'] = set(target['link'])#初期化
						else:
							#禁止
							self.error_dict[target['link']] = 1
							# print '[{0}] A-(Pool) < NOT_ADD_link [new domain -> cut by robot] > add new link : {1}'.format(dt.now(),target['link'])#うるさいので
							continue

						##=== 許可されている場合は入れる ===##
						self.visited_domain_dict[target['domain']] = domain_dict
						self.next_list.put(target,block = True)
						print '[{0}] A-(Pool) < ADD_link [new domain] > add new link : {1}'.format(dt.now(),target['link'])
						sys.stdout.flush()
						continue



			except Exception as e:
				self.error_dict[target['link']] = 1#domainはだめ、linkでやろう
				print '[{0}] A-(Pool) LinkError[other] : {1} - {2}'.format(dt.now(),e,target)
				sys.stdout.flush()
				continue

		return

