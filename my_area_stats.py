import numpy as np
import pandas as pd
import geopandas as gpd
import statistics
import math


def weighted_average(group, value_col, weight_col):
    
    values = pd.to_numeric(group[value_col])
    weights = pd.to_numeric(group[weight_col])
    
    if len(values) and len(weights) and weights.sum() > 0:
        return (values * weights).sum() / weights.sum()
    elif len(values):
        return values.mean()
    else:
        return None
    

def weighted_sum(group, value_col, weight_col):
    
    values = pd.to_numeric(group[value_col])
    weights = pd.to_numeric(group[weight_col])
    
    if len(values) and len(weights) and weights.sum() > 0:
        return (values * weights).sum()
    elif len(values):
        return values.mean()
    else:
        return None
    
    
def val_per_area(areas, area_id, to_aggr, modes, value_col=None, weight_col=None):
    
    cols = list(areas.columns)
    result = areas.copy()
    
    joined = gpd.sjoin(result, to_aggr, how='left', predicate='intersects')
    
    for mode in modes:

        if mode == 'wavg':      
            result_col = value_col + '_' + mode
            aggr = joined[[area_id, value_col, weight_col]].groupby(area_id).apply(lambda group:weighted_average(group, value_col, weight_col))
            df_aggr = aggr.to_frame(name=result_col)
            
        elif mode == 'wsum':
            result_col = value_col + '_' + mode
            aggr = joined[[area_id, value_col, weight_col]].groupby(area_id).apply(lambda group:weighted_sum(group, value_col, weight_col))
            df_aggr = aggr.to_frame(name=result_col)

        elif mode == 'mean':  
            result_col = value_col + '_' + mode
            df_aggr = joined[[area_id, value_col]].groupby(area_id).mean(value_col)
            df_aggr = df_aggr.rename(columns={value_col: result_col})

        elif mode == 'median':
            result_col = value_col + '_' + mode
            df_aggr = joined[[area_id, value_col]].groupby(area_id).median(value_col)
            df_aggr = df_aggr.rename(columns={value_col: result_col})

        elif mode == 'min':
            result_col = value_col + '_' + mode
            df_aggr = joined[[area_id, value_col]].groupby(area_id).min(value_col)
            df_aggr = df_aggr.rename(columns={value_col: result_col})

        elif mode == 'max':
            result_col = value_col + '_' + mode
            df_aggr = joined[[area_id, value_col]].groupby(area_id).max(value_col)
            df_aggr = df_aggr.rename(columns={value_col: result_col})

        elif mode == 'sum':
            result_col = value_col + '_' + mode
            df_aggr = joined[[area_id, value_col]].groupby(area_id).sum(value_col)
            df_aggr = df_aggr.rename(columns={value_col: result_col})
            
        elif mode == 'count':          
            result_col = '_' + mode
            df_aggr = pd.DataFrame(joined.groupby(area_id).agg(['count'])['index_right']['count'])
            df_aggr = df_aggr.rename(columns={'count': result_col})
            
        elif mode == 'bool':
            result_col = '_' + mode
            df_aggr = pd.DataFrame(joined.groupby(area_id).agg(['count'])['index_right']['count'])
            df_aggr = df_aggr.astype('bool')
            df_aggr = df_aggr.rename(columns={'count': result_col})
            
        if not result_col in cols:
            cols.append(result_col)
            
        if result_col in result.columns:
            result = result.drop(columns=[result_col])
        
        result = result.merge(df_aggr[result_col], how='left', on=area_id).drop_duplicates(subset=[area_id])
    
    result = result[cols].copy()

    return result  


