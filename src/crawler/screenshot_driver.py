# -*- coding: utf-8 -*-
from PIL import Image
import time

def save_screenshot(self, filename, fullsize=False):

    filepath = '/'.join(filename.split('/')[:-1])

    if fullsize:
        # ページの左上までスクロール
        self.execute_script("window.scrollTo(0, 0);")

        # ページサイズ取得
        total_height = self.execute_script("return document.body.scrollHeight")
        total_width = self.execute_script("return document.body.scrollWidth")

        # 画面サイズ取得
        view_width = self.execute_script("return window.innerWidth")
        view_height = self.execute_script("return window.innerHeight")

        # 画像処理用
        stitched_image = Image.new("RGB", (total_width, total_height))

        # スクロール操作用
        scroll_width = 0
        scroll_height = 0

        row_count = 0

        print total_height,total_width,view_height,view_width
        # 縦スクロールの処理
        while scroll_height < total_height:
            # 横スクロール初期化
            col_count = 0
            scroll_width = 0
            self.execute_script("window.scrollTo(%d, %d)" % (scroll_width, scroll_height)) 
            # 横スクロールの処理
            while scroll_width < total_width:
                if col_count > 0:
                    # 画面サイズ分横スクロール
                    self.execute_script("window.scrollBy("+str(view_width)+",0)") 

                tmpname = filepath + '/tmp_%d_%d.png' % (row_count, col_count)
                self.get_screenshot_as_file(tmpname)
                #time.sleep(3)

                # 右端か下端に到達したら画像を切り取ってstitched_imageに貼り付ける
                if scroll_width + view_width >= total_width or scroll_height + view_height >= total_height:
                    new_width = view_width
                    new_height= view_height
                    if scroll_width + view_width >= total_width:
                        new_width = total_width - scroll_width
                    if scroll_height + view_height >= total_height:
                        new_height = total_height - scroll_height
                    tmp_image = Image.open(tmpname)
                    tmp_image.crop((view_width - new_width, view_height - new_height, view_width, view_height)).save(tmpname)
                    stitched_image.paste(Image.open(tmpname), (scroll_width, scroll_height))
                    scroll_width += new_width

                # 普通に貼り付ける
                else:
                    stitched_image.paste(Image.open(tmpname), (scroll_width, scroll_height))
                    scroll_width += view_width
                    col_count += 1

            scroll_height += view_height
            #time.sleep(3)


        # 指定のfilenameにstitched_image格納
        stitched_image.save(filename)
        return True

    # fullsize=Falseの場合は通常のスクリーンショットを取得
    else:
        self.get_screenshot_as_file(filename)