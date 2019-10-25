# -*- coding: utf-8 -*-
############################
#######　 超重要項目　########
############################
# agent_farm = 'tanico'#基本はtanicoで
# agent_farm = 'yamaco'
# agent_farm = 'macico'
# agent_farm = 'eni4'
agent_farm = 'e35'


########  fakenewscourpus ########

# seed_dir = "../seed_url_list/"#固定

# seed_filename = 'unreliable_url.csv'  
# seed_filename = 'fake_url.csv'#tanico
# seed_filename = 'clickbait_url.csv'#無効

# seed_filename = 'credible_url.csv'#yes
# seed_filename = 'conspiracy_url.csv'#追加no


########  c3 dataset ########
# seed_dir = "../seed_url_list/c3_rank/"#固定
# seed_filename = "b_no_url.csv"
# seed_filename = "b_yes_url.csv"

# seed_filename = 'test_url.csv'#tanico(test)

########  ms(webcredibility) dataset ########
# seed_dir = "../seed_url_list/webcredibility/"#固定

# seed_filename = "ms_yes.csv"
# seed_filename = "ms_no.csv"

########  実世界データセット ########
seed_dir = "../seed_url_list/real_world/"#固定
# seed_filename = 'convert_url.csv'  
seed_filename = 'selected_convert_url.csv'  

#############################
#############################
#############################


####とりあえず、シカトURL####
forbidden_domain_list = ['apple','twitter','google','facebook','nicovideo','youtube','wikipedia','instagram','flickr','microsoft','amazon'] #
forbidden_word_list   = ["javascript:",'mailto:','sms:','line','tel:','login','logout','signin','signout']


######　保存先指定　#######
seed_filepath =  seed_dir+seed_filename

result_folder = '/home/'+agent_farm+'/crawl_result/'+agent_farm+'_no/'
if agent_farm == 'macico':
	result_folder = '/Users/'+agent_farm+'/crawl_result/'+agent_farm+'/' #For mac
if agent_farm == 'eni4':
	result_folder = '/work/tanico_c/crawl_result/'+agent_farm+'/'
if agent_farm == 'e35':
	result_folder = '/home/tanico/crawl_result/'+agent_farm+'/'


record_path = result_folder+'record/'
data_base_path = result_folder+'json/'
image_base_path = result_folder+'image/'
wget_base_path = result_folder+'wget/'
##########################
##########################
##########################


######　コアの指定　#######
core =  16#使用コア数tanico
# core =  8#使用コア数
# core =  4#使用コア数


seed_agent_name = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]#seedとしてクロール開始する連中 tanico
# seed_agent_name = [1,2,3,4,5,6,7]#seedとしてクロール開始する連中 yamaco
# seed_agent_name = [1,2,3]#seedとしてクロール開始する連中 yamaco

link_agent_name = [0]

######　吸収リンクの指定　#######
domain_max = 20#同一ドメイン最大取得数(最大取得数が大きいと、下の設定なしに、その数をクリアできないので注意)
wal_opt = 1 #  訪問先からゲットしたURLを次回URLリンクプールに突っ込む(0)/突っ込まない(1)
osd_opt = 0 #->訪問先からゲットしたURLを次回URLリンクプールに突っ込む(wal_opt=0)場合に、シードURLのドメインに限定する(0)/制限なし(1):(探索中のページと同一ドメインURLを取得したい場合)
wgl_opt = 0 #次回URL取得できなかった場合、待つ(0)/即終了(1)

######　ルーチンの指定　#######
progress_span = 60.0##進捗報告スパン(秒)
process_span = 0.2#ずーーとぐるぐるだけど、１週あたりの間隔

######　URLへのアクセス時の指定　#######
out_time = 30#タイムアウト時間(アクセスそのものの)
timeout_wait = 10 #URL取得できなかった場合、待つ、各試行の待ち時間
timeout_cnt  = 2 #URL取得できなかった場合、待つ、試行回数
link_checking = False
if link_checking:
	link_checking_time_out = 20
else:
	link_checking_time_out = 0.5 #リンクを個々にチェックする際のタイムアウト時間。(リンクの交換をなくすことは面倒なので、タイムアウトを極端にする。)

######　セキュリティ　#######
allow_xsite = True #(=====1=====)  Cross siteについて許容する場合(HTMLデータが既にある場合。)

######　指定URL種別　#######
##指定URL群各URLは”絶対的なhttp(s)から始まるやつ”であることは絶対に普遍##
##HTMLページのSRCなどのURLが相対URLである場合は、指定辞書ファイルを参照して交換を行った上で実施。## 
require_convert_url = True#(=====1=====)
# dump_basepath = '/work/shioura/dump/'
dump_basepath = '/home/tanico/dump/'

# (=====1=====) はかならず一致している！！！




