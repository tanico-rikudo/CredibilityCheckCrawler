# -*- coding: utf-8 -*-
########################
# 特定要素の位置をmeshとして示す
# mesh は正規化される
#######################
import numpy as np

class page_mesh():
	def __init__ (self,data_info,page_info,pos_key):

		self.info_item = ['X','Y','H','W']
		self.pos_key = pos_key

		#メッシュの縦横(要指定)
		self.default = {}
		self.default['H'] = 200
		self.default['W'] = 100

		#メッシュの縦横間隔(要指定)
		self.mesh_int = {}
		self.mesh_int['H'] = 1
		self.mesh_int['W'] = 1
		#メッシュの 1判定への面積専有率(要指定)
		self.mesh_rate = 0.5
		self.mesh_bound = float(self.mesh_int['W'])*float(self.mesh_int['W'])*self.mesh_rate
		#mesh作成
		self.mesh = np.array([[ 0.0 for w in range(self.default['W'])] for h in range(self.default['H'])])
		self.page_info = page_info # あるページの縦横{ H : __ , W : __ }の形式.*辞書内にWH以外入っていてもOK*
		self.data_info = data_info # あるページの要素リスト[{ info_item の項目 }, {}, {}]*辞書内にXYWH以外入っていてもOK*
		#一定以内のページしか取り扱わない場合において、強制的にデータを削除する。

		self.page_limit = {}
# 		self.page_limit['H'] = 1080 * 1 #既定の画面縦サイズまでしか考慮しない。重み#2(1画面目まで通常考慮)
# 		self.page_limit['W'] = 1920 * 1 #既定の画面横サイズまでしか考慮しない。重み#2(1画面目まで通常考慮)

		# self.page_limit['H'] = 1080 * 2 #既定の画面縦サイズの2倍までしか考慮しない。重み#3(2画面目まで通常考慮)
		# self.page_limit['W'] = 1920 * 1 #既定の画面横サイズまでしか考慮しない。重み#3(2画面目まで通常考慮)

		# self.page_limit['H'] = 1080 * 3 #既定の画面縦サイズの3倍までしか考慮しない。重み#4(3画面目まで通常考慮)
		# self.page_limit['W'] = 1920 * 1 #既定の画面横サイズまでしか考慮しない。重み#4(3画面目まで通常考慮)

		self.page_limit['H'] = self.page_info['H'] #全考慮	
		self.page_limit['W'] = self.page_info['W'] #全考慮
		
		if self.page_limit['H']>page_info['H']:
			self.page_limit['H']=page_info['H']
		if self.page_limit['W']>page_info['W']:
			self.page_limit['W']=page_info['W']

		self.page_limit_h_half = self.page_limit['H']/2.0
		self.compression_rate = {}
		self.compression_rate['H'] = float(self.default['H'])/float(self.page_limit['H'])
		self.compression_rate['W'] = float(self.default['W'])/float(self.page_limit['W'])
		self.compression_rate['Y'] = self.compression_rate['H']
		self.compression_rate['X'] = self.compression_rate['W']
		# print  'ddd'
		#正規化したデータにして再生
		self.data = [ self.convert_each_data(each_data) for each_data in self.data_info ]
		self.data = [ data for data in self.data if data is not None ]
		# print  'ddd'

		#要素面積情報格納
		self.area_data = np.array([])
		# print  'ddd'
		#重み設定
		self.cal_weight()
		# print  'ddd'
		return

	def convert_each_data(self,each_data):
		data = { item : float(each_data[item]) for item in self.info_item }
		data['adjusted'] = { item : float(each_data['adjusted'][item]) for item in self.info_item }#一応XYHWの全値が存在
		if data['X'] > self.page_limit['W'] or data['Y'] > self.page_limit['H'] :
			return  None#どちらかの軸において全部が超えてたら除外全部０(通常とadjust共通)

		#超過分調整(通常)
		if (data['X'] + data['W']) > self.page_limit['W'] :
			data['W'] = self.page_limit['W'] - data['X']
			data['adjusted']['X'] = data['X'] + data['W']/2.0
			data['adjusted']['W'] = data['W'] 
		if (data['Y'] + data['H']) > self.page_limit['H'] :
			data['H'] = self.page_limit['H'] - data['Y']
			data['adjusted']['Y'] = data['Y'] + data['H']/2.0
			data['adjusted']['H'] = data['H'] 
			
		#調整後→圧縮
		compressed_data = { item : float(data[item]) *self.compression_rate[item] for item in self.info_item }
		compressed_data['adjusted'] = { item :float(data['adjusted'][item]) *self.compression_rate[item] for item in self.info_item }

		return  compressed_data

	def weight_function(self,h,w):
		#絶対座標ベースで(h,w)における重みを計算
		#重みは必ず1以下で、倍率形式にすること。0より大きく,1以下ってこと
		# h:たて
		# w:よこ
		# weight = 1#重みなし
		# period = 1080.0 * 3.0
		# period = 1080.0 * 2.0
		period = 1080.0 * 1.0
		# try:
		# 	hh = h/period
		# 	weight = (0.5)**(hh)#重み#1(２画面目最終で1/2に到達)
		# except:
		# 	weight = 1#どうせ打ち消される
			
		try:
			if h > (self.page_limit['H']/2.0):
				hh = (self.page_limit['H']-h)/period
			else:
				hh = h/period
			weight = (0.5)**(hh)
		except:
			weight = 1#どうせ打ち消される
		
		return weight

	## 設定値から重みを計算 ##    
	def cal_weight(self):
		weight_page = [[ self.weight_function(h,w) for w in range(self.page_info['W'])] for h in range(self.page_info['H'])]#とりあえずページ上全て計算
		self.weight_mesh = [[ weight_page[int(h/self.compression_rate['H'])][int(w/self.compression_rate['W'])] for w in range(self.default['W'])] for h in range(self.default['H'])]#meshが圧縮→大本の代表値を検索しに行くスタンス


	## 線分がどの程度かぶっているか ##
	def cal_cover_dis(self,data_x,data_w,x_min,mesh): 
		if data_x <= x_min:
			if (x_min + mesh ) <  (data_x + data_w):
				result = 1
			elif x_min < data_x  + data_w:
				result = data_x  + data_w - x_min
			else:
				result = 0
		elif data_x  < x_min+ mesh:
			if (data_x + data_w) < (x_min + mesh ):
				result = data_w
			else :
				result = (x_min + mesh) - data_x
		else:
			result = 0
		return result

	## それぞれのデータをメッシュ化##
	## メッシュ下の基準は、あるメッシュ1*1（1*1は要指定項目）において、self.mesh_bound以上占有している場合は１それ以外は0
	## page_mesh が変える
	def make_mesh(self,is_binary = True):
		self.mesh_vec_list_x = []
		self.mesh_vec_list_y = []
		for data in self.data:
			mesh_dis = {}
			mesh_dis['X'] = { x_min : self.cal_cover_dis(data['X'],data['W'],x_min,self.mesh_int['W']) for x_min in range(self.default['W'])}
			mesh_dis['Y'] = { y_min : self.cal_cover_dis(data['Y'],data['H'],y_min,self.mesh_int['H']) for y_min in range(self.default['H'])}

			mesh = np.array([[ 0.0 for w in range(self.default['W'])] for h in range(self.default['H'])])

			for y_min in range(self.default['H']):
				for x_min in range(self.default['W']):

					#専有面積加算方式の場合
					mesh[y_min][x_min] += self.weight_mesh[y_min][x_min]*(mesh_dis['X'][x_min] * mesh_dis['Y'][y_min])

			self.mesh += np.array(mesh)
			np.append(self.area_data,sum(mesh.flatten()))#正論		
			## 各種統計量算出  ###
			if self.pos_key == 'leftup':
				self.mesh_vec_list_x.append(data['X'])
				self.mesh_vec_list_y.append(data['Y'])
			elif self.pos_key == 'center':
				# try:
				self.mesh_vec_list_x.append(data['adjusted']['X'])
				self.mesh_vec_list_y.append(data['adjusted']['Y'])
				# except Exception as e:
				# 	print data


		self.cov_mesh_x		= float(np.ma.cov(self.mesh_vec_list_x))#[0]#特殊処理
		self.cov_mesh_y		= float(np.ma.cov(self.mesh_vec_list_y))#[0]#特殊処理
		self.mean_mesh_x	= np.nanmean(self.mesh_vec_list_x)
		self.mean_mesh_y	= np.nanmean(self.mesh_vec_list_y)
		self.cov_mesh	= np.ma.cov([self.mesh_vec_list_x,self.mesh_vec_list_y],bias= True)#不偏分散では無い値を算出。通常分散
		self.cov_mesh_area  = float(np.ma.cov(self.area_data))#[0]#特殊処理
		self.mean_mesh_area = np.nanmean(self.area_data)#[0]#特殊処理
		self.sum_mesh_area  = np.nansum(self.area_data)#[0]#特殊処理


		if is_binary:
			self.mesh /= self.mesh #これは 0 or 1 処理
		else:
			pass


		return self.mesh

	## flatten 形式で 統合されたpage_meshが返る ##
	def export(self):
		mesh_name_matrix = [[ 'mesh_'+str(w)+'-'+str(h) for w in range(self.default['W'])] for h in range(self.default['H'])]
		mesh_name_vector = []
		mesh_data_vector = []
		for mesh_name in mesh_name_matrix:
			mesh_name_vector.extend(mesh_name)
		for mesh_data in self.mesh:
			mesh_data_vector.extend(mesh_data)
		flatten_dict = { name: data for name,data in zip(mesh_name_vector, mesh_data_vector)}
		return flatten_dict 
