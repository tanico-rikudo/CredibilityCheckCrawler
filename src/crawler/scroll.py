# -*- coding: utf-8 -*-
import time

def scroll(self,fullsize=False,scroll_wait_time=1):
	# print 'scroll entered!'
	if fullsize:
		# print 'scroll entered!!--'
		# ページの左上までスクロール
		self.execute_script("window.scrollTo(0,0); return true;")#これつけないとエラー
		# print 'scroll entered!!'
		# ページサイズ取得
		total_height = self.execute_script("return document.body.scrollHeight")
		total_width = self.execute_script("return document.body.scrollWidth")
		# print 'scroll entered!!!'
		# 画面サイズ取得
		view_width = self.execute_script("return window.innerWidth")
		view_height = self.execute_script("return window.innerHeight")
		# print 'scroll entered!!'
		# スクロール操作用
		scroll_width = 0
		scroll_height = 0
		# print 'scroll entered!'
		row_count = 0
		# print 'scroll entered'
		# 縦スクロールの処理
		# print 'Height : '+ str(total_height)
		time.sleep(scroll_wait_time) #読み込みまち
		while scroll_height < total_height:
			# 横スクロール初期化
			col_count = 0
			scroll_width = 0
			self.execute_script("window.scrollTo(%d, %d); return true;" % (scroll_width, scroll_height)) 
			# 横スクロールの処理
			# print '>>>>[Wait] Scrolling'
			time.sleep(scroll_wait_time) #読み込みまち
			while scroll_width < total_width:

				if col_count > 0:
					# 画面サイズ分横スクロール
					self.execute_script("window.scrollBy("+str(view_width)+",0); return true;") 

				# 右端か下端に到達したら画像を切り取ってstitched_imageに貼り付ける
				if scroll_width + view_width >= total_width or scroll_height + view_height >= total_height:
					new_width = view_width
					new_height= view_height
					if scroll_width + view_width >= total_width:
						new_width = total_width - scroll_width
					if scroll_height + view_height >= total_height:
						new_height = total_height - scroll_height

					scroll_width += new_width

				else:
					scroll_width += view_width
					col_count += 1

			scroll_height += view_height

		return True
