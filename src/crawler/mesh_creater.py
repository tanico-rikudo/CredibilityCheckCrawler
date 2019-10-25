# -*- coding: utf-8 -*-
########################
# 特定要素の位置をmeshとして示す
# mesh は正規化される
#######################
import numpy as np
class page_mesh():
	def __init__ (self,data_info,page_info):
		import numpy as np
		self.info_item = ['X','Y','H','W']

		#メッシュの縦横(要指定)
		self.default = {}
		self.default['H'] = 200
		self.default['W'] = 100

		#メッシュの縦横間隔(要指定)
		self.mesh_int = {}
		self.mesh_int['H'] = 1
		self.mesh_int['W'] = 1

		#メッシュの　1判定への面積専有率(要指定)
		self.mesh_rate = 0.5
		self.mesh_bound = float(self.mesh_int['W'])*float(self.mesh_int['W'])*self.mesh_rate

		#mesh作成
		self.mesh = np.array([[ 0.0 for w in range(self.default['W'])] for h in range(self.default['H'])])

		self.page_info = page_info # あるページの縦横{ H : __ , W : __ }の形式.*辞書内にWH以外入っていてもOK*
		self.data_info = data_info # あるページの要素リスト[{ info_item の項目　}, {}, {}]*辞書内にXYWH以外入っていてもOK*

		self.compression_rate = {}
		self.compression_rate['H'] = float(self.default['H'])/float(self.page_info['H'])
		self.compression_rate['W'] = float(self.default['W'])/float(self.page_info['W'])
		self.compression_rate['Y'] = self.compression_rate['H']
		self.compression_rate['X'] = self.compression_rate['W']

		#正規化したデータにして再生
		self.data = [ { item : float(each_data[item]) *self.compression_rate[item] for item in self.info_item } for each_data in self.data_info ]

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

	##それぞれのデータをメッシュ化##
	## メッシュ下の基準は、あるメッシュ1*1（1*1は要指定項目）において、self.mesh_bound以上占有している場合は１それ以外は0
	## page_mesh が変える
	def make_mesh(self,is_binary = True):

		for data in self.data:
			mesh_dis = {}
			mesh_dis['X'] = { x_min : self.cal_cover_dis(data['X'],data['W'],x_min,self.mesh_int['W']) for x_min in range(self.default['W'])}
			mesh_dis['Y'] = { y_min : self.cal_cover_dis(data['Y'],data['H'],y_min,self.mesh_int['H']) for y_min in range(self.default['H'])}

			mesh = [[ 0 for w in range(self.default['W'])] for h in range(self.default['H'])]
			for y_min in range(self.default['H']):
				for x_min in range(self.default['W']):
					#個数加算方式の場合
					mesh[y_min][x_min] += 1 if mesh_dis['X'][x_min] * mesh_dis['Y'][y_min] > 0 else 0
					#閾値以上個数加算方式の場合
					# mesh[y_min][x_min] += 1 if mesh_dis['X'][x_min] * mesh_dis['Y'][y_min] >= self.mesh_bound else 0
					#専有面積加算方式の場合
					# mesh[y_min][x_min] += mesh_dis['X'][x_min] * mesh_dis['Y'][y_min]
			self.mesh += np.array(mesh)


		### 各種統計量算出  ###
		(height, width) = self.mesh.shape
		self.mesh_vec_list_x = []
		self.mesh_vec_list_y = []
		for h in  range(height):
			for w  in  range(width):
				for cnt in range(int(self.mesh[h][w])):
					self.mesh_vec_list_x.append(w)
					self.mesh_vec_list_y.append(h)

		self.cov_mesh_x		= float(np.cov(self.mesh_vec_list_x))#[0]#特殊処理
		self.cov_mesh_y		= float(np.cov(self.mesh_vec_list_y))#[0]#特殊処理
		self.mean_mesh_x	= np.mean(self.mesh_vec_list_x)
		self.mean_mesh_y	= np.mean(self.mesh_vec_list_y)
		self.cov_mesh	= np.cov([self.mesh_vec_list_x,self.mesh_vec_list_y],bias= True)#不偏分散では無い値を算出。通常分散


		if is_binary:
			self.mesh /= self.mesh #これは 0 or 1　処理
		else:
			pass


		return self.mesh

	## flatten 形式で　統合されたpage_meshが返る ##
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
