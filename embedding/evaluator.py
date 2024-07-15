# 对比两版数据结果的准确率


def compare_rank_best(pred_col, real_col, df, topn, filter_col=None):
    if filter_col:
        df = df[df[filter_col] == 1]
    pos_arr = []
    neg_arr = []
    total_arr = []
    for query, sub in df.groupby('sentence1'):
        sub = sub.sort_values(by=pred_col, ascending=False)
        top_score = sub.head(topn)[real_col].sum()
        tail_score = topn - sub.tail(topn)[real_col].sum()
        # tail_score =0
        pos_arr.append(top_score)
        neg_arr.append(tail_score)
        total_arr.append(top_score + tail_score)
        # print(pred_col,query, top_score,tail_score)
    return np.array(pos_arr).mean(), np.array(neg_arr).mean(), np.array(total_arr).mean()


def get_eva_info(df, model_names, topns, real_col='label'):
    eva_df = []

    for model_name in model_names:
        arr = [model_name]
        for topn in topns:
            pscore, nscore, tscore = compare_rank_best(pred_col=model_name, real_col=real_col, df=df, topn=topn)
            arr = arr + [pscore, nscore, tscore]
        eva_df.append(arr)
    eva_names = []
    for topn in topns:
        eva_names = eva_names + [str(topn) + '_pos', str(topn) + '_neg', str(topn) + '_total']
    eva_df = pd.DataFrame(eva_df, columns=['model_name'] + eva_names)
    return eva_df


def get_all_model_names(model_names):
    all_model_names = []
    for model_name in model_names:
        all_model_names.append(model_name)
        # all_model_names.append(model_name+'_boost')
        # all_model_names.append(model_name+'_fre_weighted')
    return all_model_names


df = df.rename({"llm_label": 'label'}, axis=1)
# len(df[df['type']=='validation_4000'])

model_names = [i.split('/')[-1] for i in ps]
topns = [10, 20, 50, 100]
# all_model_names = get_all_model_names(model_names)
all_model_names = ['bge_small_lr4e5_contract_0617_full_summary_200epoch', 'dmeta_small_lr3e5_contrast_0618_200epoch',
                   #    'bge_lr4e5_0627_new_label_v1','bge_lr4e5_0627_new_label_v1.5','bge_lr4e5_0627_old_label_v1',
                   'bge_lr4e5_0627_new_label_v1', 'bge_lr4e5_0628', 'bge_lr4e5_0704']
# topns = [100]
# all_model_names = ['bge_small_lr4e5_contract_0617_full_summary_200epoch','bge_lr4e5_contrastive_0626']
eva_df = get_eva_info(df, model_names=all_model_names, topns=topns)
eva_df