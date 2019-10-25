# -*- coding: utf-8 -*-
import Queue
from datetime import datetime as dt
import crawl_setting as cs #myself用の設定プラグイン
class access_pool(object):
	###=====================###
	###　LINKとURLの特殊Agent ###
	###=====================###

	##=== 初期化 ===##
	def __init__(self,q):

		super(access_pool, self).__init__()

		#プールの取得
		self.next_list = q

		#recent
		self.recent_list = []

		self.q_limit = 10 #Queueの上限数
		self.same_domain_recently = 5 #履歴に同一ドメインどれくらい含めるか
		self.wait_per_domain = 3 #1domainあたりどれくらい待機するか
		self.core = cs.core

	##=== アクセスするリンク数 ===##
	def check_link_pool(self):

		print '[{0}] ** Pool Report ** #pooled_link = {1}'.format(dt.now(),self.next_list.qsize())#macでは動かない

		return 

	##=== 次にアクセスするリンク ===##
	def get_next_link(self):
		reply_data = {}
		try:
			candidate_data =  self.next_list.get(block=False)
			reply_data['origin_url'] = candidate_data['origin_link']
			reply_data['url'] = candidate_data['link']
			reply_data['domain'] = candidate_data['domain']


			#直近リストと更新時間の設定
			count = sum(domain == reply_data['domain'] for domain in self.recent_list)
			reply_data['sleep'] = count*self.wait_per_domain

			if len(self.recent_list) > self.q_limit:
				self.recent_list.pop(0)

			if count < self.same_domain_recently:
				self.recent_list.append(reply_data['domain'])

		except Queue.Empty as e:
			# print e
			reply_data['sleep'] = 0
			reply_data['url'] = None
			reply_data['origin_url'] = None
		# print 'GET URL : {0}'.format(str(reply_data['origin_url'])) ###############
		return reply_data