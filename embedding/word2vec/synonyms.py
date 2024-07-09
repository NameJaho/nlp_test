import gensim
import pandas as pd
from tools import utils
import os
from gensim.models import KeyedVectors

root_path = utils.get_root_path()
wechat_path = os.path.join(root_path, 'models/vector', 'word2vec_wx')
print(wechat_path)

#model = KeyedVectors.load_word2vec_format(wechat_path)
model = gensim.models.Word2Vec.load(wechat_path)

# find most similar words
testwords = ['服务', '出海', '价', '价格', '资源', '动销', '供应链', '生态', '运营', '流量', '平台', '消费者']
for i in range(len(testwords)):
    res = model.wv.most_similar(testwords[i], topn=5)
    print(testwords[i])
    print(res)

