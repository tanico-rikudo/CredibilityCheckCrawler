
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import  csv, os,glob,gzip,json,sys
from multiprocessing import Pool


# In[ ]:


###  setting ###
# data_folder_path = '../test_lot'
# data_folder_path = '../result_tanico_0423'

##### yamaco  #####
# core = 8
# data_folder_path = '/home/yamaco/crawl_result/yamaco_test_result' #yamaco
# result_folder_path  = '../analyze_result/source'
##### enigma4  #####
core = 35
data_folder_path ='/work/tanico_c/yamaco_test_result' #e4
result_folder_path  = '../../analyze_result/source'
result_folder_name = '2018_05_03_17_38_24'


# In[ ]:


def read_df(filepath):
	return pd.read_csv(filepath)

# def batch_processing(df):
#     for tag in ['image','iframe','link']
#         for item in ['count','area']:
#             df['ratio_image_'+item] = df['inner_image_'+item] / df['outer_image_'+item].astype(float)
#             df['comp_inner_ratio_image_'+item] = df['inner_image_'+item] / df['all_image_'+item].astype(float)
#             df['comp_outer_ratio_image_'+item] = df['outer_image_'+item] / df['all_image_'+item].astype(float)
#             for item in ['ratio_image_'+item, 'comp_inner_ratio_image_'+item,'comp_outer_ratio_image_'+item]:
#                 df[item] .replace([np.inf, -np.inf], np.nan,inplace=True)
#                 df  = df.dropna(subset=[item])
#     return df
        
def df_agg():
	filepath_list = glob.glob(result_folder_path+'/'+result_folder_name+'/*')
	print '#target_agg_file : ',len(filepath_list)
	p = Pool(core)
# 	df =  batch_processing(pd.concat(p.map(read_df, files)))
	df =  pd.concat(p.map(read_df, files))
	df.to_csv(result_folder+'/'+result_folder_name+'.csv')



# In[ ]:



if __name__ == '__main__':
 	df_agg() 

