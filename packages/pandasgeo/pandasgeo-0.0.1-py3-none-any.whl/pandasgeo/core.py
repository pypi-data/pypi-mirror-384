#!/usr/bin/env python
# coding: utf-8
import geopandas as gpd
from shapely.ops import unary_union, triangulate,voronoi_diagram
from shapely.geometry import Polygon,Point,LineString,MultiPolygon, MultiPoint
from shapely import wkt
import pandas as pd
import numpy as np
import math,os,simplekml
import shapefile
import shutil
from geographiclib.geodesic import Geodesic
import kml2geojson as k2g
from itertools import chain
from scipy.spatial import cKDTree
import pyproj

def create_projected_kdtree(df, lon_col='lon', lat_col='lat'):
    """将经纬度转换为UTM投影并创建KDTree"""
    lons = df[lon_col].values
    lats = df[lat_col].values
    
    # 确定中心点（用于选择UTM区域）
    center_lon, center_lat = np.mean(lons), np.mean(lats)
    utm_zone = int((center_lon + 180) / 6) + 1
    hemisphere = 'north' if center_lat >= 0 else 'south'
    # EPSG code for WGS 84 / UTM zone
    epsg_code = 32600 + utm_zone if hemisphere == 'north' else 32700 + utm_zone
    
    # 创建转换器
    transformer = pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_code}", always_xy=True)
    
    # 转换为UTM坐标
    x, y = transformer.transform(lons, lats)
    points = np.column_stack((x, y))
    
    return points, f"EPSG:{epsg_code}"


def min_distance_twotable(df1, df2, 
                    lon1='lon1', lat1='lat1', lon2='lon2', lat2='lat2',
                    df2_id='id', n=1):
    """
    计算df1中每个点到df2中最近的n个点，并将结果添加到df1的副本中
    
    参数:
    df1 (DataFrame): 源数据，包含经纬度列
    df2 (DataFrame): 目标数据，包含经纬度列
    lon1 (str): df1的经度列名
    lat1 (str): df1的纬度列名
    lon2 (str): df2的经度列名
    lat2 (str): df2的纬度列名
    df2_id (str): df2中用于标识的ID列名
    n (int): 要查找的最近邻数量
    
    返回:
    DataFrame: 添加了最近邻信息的df1的副本
    """
    # 验证输入
    if n < 1:
        raise ValueError("n必须大于0")
    
    # 创建结果副本
    result = df1.copy()
    
    # 如果df2为空，直接返回填充NaN的结果
    if len(df2) == 0 or len(df1) == 0:
        for i in range(1, n+1):
            result[f'最近{i}id'] = np.nan
            result[f'最近{i}经度'] = np.nan
            result[f'最近{i}纬度'] = np.nan
            result[f'最近{i}距离'] = np.nan
        if n > 1:
            result['平均距离'] = np.nan
        return result
    
    # 提取坐标点并投影
    A_points, proj_crs = create_projected_kdtree(df1, lon1, lat1)
    
    # 为df2创建转换器
    transformer_b = pyproj.Transformer.from_crs("EPSG:4326", proj_crs, always_xy=True)
    lons_b = df2[lon2].values
    lats_b = df2[lat2].values
    x_b, y_b = transformer_b.transform(lons_b, lats_b)
    B_points = np.column_stack((x_b, y_b))

    # 创建KDTree进行高效搜索
    tree = cKDTree(B_points)
    
    # 查询最近的n个点（实际数量为min(n, len(df2))）
    k = min(n, len(df2))
    distances, indices = tree.query(A_points, k=k, workers=-1)
    
    # 处理k=1时的维度问题
    if k == 1:
        distances = distances.reshape(-1, 1)
        indices = indices.reshape(-1, 1)
    
    # 添加最近邻信息
    for i in range(k):
        # 获取df2中的对应点
        nearest_points = df2.iloc[indices[:, i]]
        
        # 添加列
        result[f'最近{i+1}id'] = nearest_points[df2_id].values
        result[f'最近{i+1}经度'] = nearest_points[lon2].values
        result[f'最近{i+1}纬度'] = nearest_points[lat2].values
        result[f'最近{i+1}距离'] = distances[:, i]
    
    # 添加缺失的列（当n>k时）
    for i in range(k, n):
        result[f'最近{i+1}id'] = np.nan
        result[f'最近{i+1}经度'] = np.nan
        result[f'最近{i+1}纬度'] = np.nan
        result[f'最近{i+1}距离'] = np.nan
    
    # 添加平均距离（当n>1时）
    if n > 1:
        # 提取所有距离列
        dist_cols = [f'最近{i+1}距离' for i in range(min(n, k))]
        if dist_cols:
            # 计算有效距离的平均值（忽略NaN）
            avg_distances = result[dist_cols].mean(axis=1)
            result['平均距离'] = avg_distances
        else:
            result['平均距离'] = np.nan
    
    return result

def min_site_one_table(data,id_name_column='id',
    lon='lon',lat='lat',
    num_min_results=3,Including_itself=False,juli_n=None):
    '''
    作用：表内找最近站点，一个或者多个
    参数说明：
    data: DataFrame - 包含位置数据的表格
    id_name_column: str - 每个数据点的ID或名称字段
    lon, lat: str - 经纬度字段名
    num_min_results: int - 查询最近的站点数量（>=1）
    Including_itself: bool - 是否包括自身
        True: 包括自己（距离为0）
        False: 不包括自己（默认）
    juli_n: float - 距离限制（米），超出此距离不计算
    
    返回：
    DataFrame - 包含最近站点信息和距离的表格
    '''
    
    # 参数验证
    if isinstance(num_min_results, (str, float)):
        raise ValueError('num_min_results必须是整数类型')
    if num_min_results < 1:
        raise ValueError('num_min_results必须大于0')
    
    # 复制数据并创建GeoDataFrame
    data_use = data.copy()
    
    if len(data_use) == 0:
        for i in range(1, num_min_results + 1):
            data_use[f'最近站点{i}'] = np.nan
            data_use[f'最近距离{i}'] = np.nan
            data_use[f'最近站点经度{i}'] = np.nan
            data_use[f'最近站点纬度{i}'] = np.nan
        if num_min_results > 1:
            data_use['平均距离'] = np.nan
        return data_use

    points, _ = create_projected_kdtree(data_use, lon, lat)
    tree = cKDTree(points)

    k = num_min_results + 1 if not Including_itself else num_min_results
    k = min(k, len(data_use))

    distances, indices = tree.query(points, k=k, workers=-1)

    if k == 1 and len(data_use) > 1:
        distances = distances.reshape(-1, 1)
        indices = indices.reshape(-1, 1)

    start_index = 1 if not Including_itself and len(data_use) > 1 else 0

    for i in range(num_min_results):
        col_idx = start_index + i
        if col_idx < k:
            # Get the indices for the i-th nearest neighbor
            neighbor_indices = indices[:, col_idx]
            
            # Get the data for the neighbors
            neighbor_data = data_use.iloc[neighbor_indices]
            
            data_use[f'最近站点{i+1}'] = neighbor_data[id_name_column].values
            data_use[f'最近距离{i+1}'] = distances[:, col_idx]
            data_use[f'最近站点经度{i+1}'] = neighbor_data[lon].values
            data_use[f'最近站点纬度{i+1}'] = neighbor_data[lat].values

            if juli_n is not None:
                data_use.loc[data_use[f'最近距离{i+1}'] > juli_n, [f'最近站点{i+1}', f'最近距离{i+1}', f'最近站点经度{i+1}', f'最近站点纬度{i+1}']] = np.nan
        else:
            data_use[f'最近站点{i+1}'] = np.nan
            data_use[f'最近距离{i+1}'] = np.nan
            data_use[f'最近站点经度{i+1}'] = np.nan
            data_use[f'最近站点纬度{i+1}'] = np.nan

    if num_min_results > 1:
        dist_cols = [f'最近距离{i+1}' for i in range(num_min_results)]
        data_use['平均距离'] = data_use[dist_cols].mean(axis=1)
        
    return data_use

def add_buffer(data,lon='lon',lat='lat',distance=50):
    '''
    作用：给每个点添加一个缓冲区面
    参数说明：
    data:DataFrame - 带有经纬度两列
    lon, lat: str - 经纬度字段名
    distance：缓冲区的距离（米）
    return GeoDataFrame
    '''
    gdf = add_points(data,lon,lat)
    gdf_buffer = gdf.to_crs(epsg=3857).buffer(distance).to_crs(epsg=4326)
    gdf['geometry'] = gdf_buffer
    return gdf

def add_buffer_groupbyid(data,lon='lon',lat='lat',distance=50,
                        columns_name='聚合id',id_lable_x='聚合_'):
    '''
    作用：按照给定的距离将一些点位融合在一起，添加一列聚合id用于标识
    参数说明：
    data:DataFrame - 带有经纬度两列
    lon, lat: str - 经纬度字段名
    distance：聚合的距离
    columns_name：添加的聚合的列名
    id_lable_x：添加的聚合列的内容命名前缀例如'聚合_'就会出现‘聚合_1’
    return DataFrame
    '''
    data_buffer = add_buffer(data,lon,lat,distance)
    # Use GeoDataFrame.dissolve
    data_dissolve = data_buffer.dissolve()
    # Explode multi-polygons to single polygons
    data_explode = data_dissolve.explode(index_parts=True).reset_index()
    data_explode[columns_name] = id_lable_x + data_explode['level_0'].astype(str)
    
    data_sjoin = gpd.sjoin(add_points(data,lon,lat),data_explode,how='left', op='within')
    
    # Ensure original columns are preserved
    data_columns = list(data.columns)
    if columns_name not in data_columns:
        data_columns.append(columns_name)
    
    # Drop extra columns from sjoin
    data_sjoin_use = data_sjoin[data_columns]
    return data_sjoin_use

def add_delaunay(
                df,
                id_use='栅格ID',
                lon='lon',
                lat='lat'):
    '''
    功能：将表格中的经纬度生成delaunay三角形，每个三角形关联id编号
    df::DataFrame
    id_use::表中的id列名
    lon::经度列名
    lat::纬度列名
    return gdf 可以直接导出为图层
    '''
    df['lonlat'] = df[lon].map(str) + df[lat].map(str)
    points = MultiPoint([[lon,lat] for lon,lat in zip(df[lon],df[lat])])
    triangles = triangulate(points,tolerance=0.00001)
    gdf = gpd.GeoDataFrame(pd.DataFrame([[index,t] for index,t in enumerate(triangles)],columns=['id','geometry']),crs="epsg:4326",geometry='geometry')
    
    # Correctly extract coordinates from the triangle polygon
    gdf[['site1','site2','site3']] = gdf['geometry'].apply(
        lambda c: pd.Series([f"{xy[0]}{xy[1]}" for xy in c.exterior.coords[:3]])
    )

    for i in range(1,4):
        gdf = gdf.merge(df[[id_use,'lonlat']].rename(columns={id_use:f'{id_use}_{i}','lonlat':f'site{i}'}),how='left',on=f'site{i}')
    return gdf

def min_site_two_table(
                    data1,
                    data2,
                    lon1='lon',
                    lat1='lat',
                    lon2='lon',
                    lat2='lat',
                    id1='id1',
                    id2='id2',
                    num_min_results=3):
    '''
    作用：表与表之间找最近站点，一个或者多个
    参数说明：
    data1, data2: DataFrame - 包含位置数据的表格
    lon1, lat1: str - data1的经纬度字段名
    lon2, lat2: str - data2的经纬度字段名
    id1, id2: str - data1, data2的ID字段名
    num_min_results: int - 查询最近的站点数量（>=1）
    
    返回：
    DataFrame - 包含最近站点信息和距离的表格
    '''
    # 复制数据以避免修改原始数据
    data1_copy = data1.copy()
    data2_copy = data2.copy()

    if len(data1_copy) == 0 or len(data2_copy) == 0:
        for i in range(1, num_min_results + 1):
            data1_copy[f'最近站点{i}'] = np.nan
            data1_copy[f'最近距离{i}'] = np.nan
            data1_copy[f'最近站点经度{i}'] = np.nan
            data1_copy[f'最近站点纬度{i}'] = np.nan
        if num_min_results > 1:
            data1_copy['平均距离'] = np.nan
        return data1_copy

    # 创建GeoDataFrames
    gdf1 = add_points(data1_copy, lon1, lat1)
    gdf2 = add_points(data2_copy, lon2, lat2)

    # 使用 sindex.nearest
    k = min(num_min_results, len(gdf2))
    
    # sindex.nearest returns indices for gdf2
    indices_tuple = gdf1.sindex.nearest(gdf2, return_all=True, max_distance=None)
    
    # The result is a tuple of arrays (input_indices, tree_indices)
    # We need to group tree_indices by input_indices
    
    # Create a DataFrame to easily group results
    nearest_df = pd.DataFrame({
        'gdf1_idx': indices_tuple[0],
        'gdf2_idx': indices_tuple[1]
    })

    # Calculate distances for all pairs
    pt1 = gdf1.iloc[nearest_df['gdf1_idx']]
    pt2 = gdf2.iloc[nearest_df['gdf2_idx']]
    
    # Use precise distance calculation
    distances = distancea_df(pd.DataFrame({
        'lon1': pt1[lon1].values, 'lat1': pt1[lat1].values,
        'lon2': pt2[lon2].values, 'lat2': pt2[lat2].values
    }))
    nearest_df['distance'] = distances

    # Sort by distance and take top k for each gdf1 point
    nearest_df = nearest_df.sort_values(['gdf1_idx', 'distance'])
    top_k = nearest_df.groupby('gdf1_idx').head(k)

    # Pivot the table to get neighbors in columns
    pivoted = top_k.groupby('gdf1_idx').cumcount().add(1)
    top_k['neighbor_rank'] = pivoted
    
    result_df = top_k.pivot_table(
        index='gdf1_idx', 
        columns='neighbor_rank', 
        values=['gdf2_idx', 'distance']
    )
    
    # Flatten multi-level columns
    result_df.columns = [f'{val}{col}' for val, col in result_df.columns]
    
    # Merge back with original data1
    final_result = data1_copy.merge(result_df, left_index=True, right_index=True, how='left')

    # Rename columns and add lon/lat info
    for i in range(1, k + 1):
        gdf2_idx_col = f'gdf2_idx{i}'
        if gdf2_idx_col in final_result.columns:
            # Get integer indices, handling NaNs
            idx = final_result[gdf2_idx_col].dropna().astype(int)
            
            # Create new columns with default NaN
            final_result[f'最近站点{i}'] = np.nan
            final_result[f'最近站点经度{i}'] = np.nan
            final_result[f'最近站点纬度{i}'] = np.nan

            # Fill values using .loc
            final_result.loc[idx.index, f'最近站点{i}'] = gdf2.iloc[idx][id2].values
            final_result.loc[idx.index, f'最近站点经度{i}'] = gdf2.iloc[idx][lon2].values
            final_result.loc[idx.index, f'最近站点纬度{i}'] = gdf2.iloc[idx][lat2].values
            
            final_result.rename(columns={f'distance{i}': f'最近距离{i}'}, inplace=True)
            final_result.drop(columns=[gdf2_idx_col], inplace=True)

    # Fill missing columns if k < num_min_results
    for i in range(k + 1, num_min_results + 1):
        final_result[f'最近站点{i}'] = np.nan
        final_result[f'最近距离{i}'] = np.nan
        final_result[f'最近站点经度{i}'] = np.nan
        final_result[f'最近站点纬度{i}'] = np.nan

    if num_min_results > 1:
        dist_cols = [f'最近距离{i}' for i in range(1, num_min_results + 1) if f'最近距离{i}' in final_result.columns]
        final_result['平均距离'] = final_result[dist_cols].mean(axis=1)

    return final_result

def add_voronoi(data,lon='lon',lat='lat'):
    '''
    功能：将表格中的经纬度生成泰森多边形
    data::DataFrame
    lon::经度列名
    lat::纬度列名
    return gdf 可以直接导出为图层
    '''
    gdf = add_points(data,lon,lat)
    # 计算所有点的并集，作为泰森多边形的边界
    boundary = gdf.unary_union.convex_hull
    # 生成泰森多边形
    voronoi_polygons = voronoi_diagram(gdf.unary_union, envelope=boundary)
    
    # 创建一个GeoDataFrame来存储泰森多边形
    voronoi_gdf = gpd.GeoDataFrame(geometry=list(voronoi_polygons.geoms), crs="epsg:4326")
    
    # 将原始点与泰森多边形进行空间连接，以匹配属性
    # 注意：泰森多边形中的每个多边形都包含一个原始点
    joined_gdf = gpd.sjoin(voronoi_gdf, gdf, how="inner", op="contains")
    
    return joined_gdf

def distancea_str(lon1, lat1, lon2, lat2):
    """
    作用：计算两个经纬度点之间的距离
    lon1, lat1: float - 第一个点的经纬度
    lon2, lat2: float - 第二个点的经纬度
    return: float - 距离（米）
    """
    if any(v is None or np.isnan(v) for v in [lon1, lat1, lon2, lat2]):
        return None
    try:
        # 使用 WGS84 模型
        geod = Geodesic.WGS84
        result = geod.Inverse(lat1, lon1, lat2, lon2)
        return result['s12']
    except (ValueError, TypeError):
        return None

def distancea_df(data, lon1='lon1', lat1='lat1', lon2='lon2', lat2='lat2'):
    """
    作用：计算DataFrame中两对经纬度点之间的距离
    data: DataFrame - 包含经纬度列
    lon1, lat1: str - 第一对经纬度列名
    lon2, lat2: str - 第二对经纬度列名
    return: Series - 包含距离的Series
    """
    distances = data.apply(
        lambda row: distancea_str(row[lon1], row[lat1], row[lon2], row[lat2]),
        axis=1
    )
    return distances

def add_points(data,lon='lon',lat='lat'):
    '''
    作用：将一个带有经纬度的DataFrame转换成GeoDataFrame
    参数说明：
    data:DataFrame - 带有经纬度两列
    lon, lat: str - 经纬度字段名
    return GeoDataFrame
    '''
    data['geometry'] = [Point(xy) for xy in zip(data[lon], data[lat])]
    data_pot = gpd.GeoDataFrame(data, crs="epsg:4326", geometry='geometry')
    return data_pot

def gdf_to_kml(gdf, out_kml_path, name='name', description='description'):
    '''
    作用：将GeoDataFrame转换成kml文件
    参数说明：
    gdf: GeoDataFrame - 需要转换的GeoDataFrame
    out_kml_path: str - 输出的kml文件路径
    name: str - kml中每个要素的名称字段
    description: str - kml中每个要素的描述字段
    '''
    kml = simplekml.Kml()
    for index, row in gdf.iterrows():
        if isinstance(row.geometry, Point):
            pnt = kml.newpoint()
            pnt.name = str(row[name]) if name in row else ''
            pnt.description = str(row[description]) if description in row else ''
            pnt.coords = [(row.geometry.x, row.geometry.y)]
        elif isinstance(row.geometry, LineString):
            ls = kml.newlinestring()
            ls.name = str(row[name]) if name in row else ''
            ls.description = str(row[description]) if description in row else ''
            ls.coords = list(row.geometry.coords)
        elif isinstance(row.geometry, Polygon):
            pol = kml.newpolygon()
            pol.name = str(row[name]) if name in row else ''
            pol.description = str(row[description]) if description in row else ''
            pol.outerboundaryis = list(row.geometry.exterior.coords)
            if row.geometry.interiors:
                pol.innerboundaryis = [list(interior.coords) for interior in row.geometry.interiors]
    kml.save(out_kml_path)

def shp_to_kml(shp_path, out_kml_path, name='name', description='description'):
    '''
    作用：将shp文件转换成kml文件
    参数说明：
    shp_path: str - shp文件路径
    out_kml_path: str - 输出的kml文件路径
    name: str - kml中每个要素的名称字段
    description: str - kml中每个要素的描述字段
    '''
    gdf = gpd.read_file(shp_path, encoding='utf-8')
    gdf_to_kml(gdf, out_kml_path, name, description)

def kml_to_shp(kml_path, out_shp_path):
    '''
    作用：将kml文件转换成shp文件
    参数说明：
    kml_path: str - kml文件路径
    out_shp_path: str - 输出的shp文件路径
    '''
    # 创建一个临时目录来存放转换后的geojson
    temp_dir = "temp_kml_to_shp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        # kml2geojson 会在指定目录下生成 geojson 文件
        k2g.convert(kml_path, temp_dir)
        
        # 查找生成的geojson文件
        geojson_files = [f for f in os.listdir(temp_dir) if f.endswith('.geojson')]
        if not geojson_files:
            raise FileNotFoundError("kml to geojson conversion failed, no geojson file found.")
            
        # 读取第一个geojson文件
        gdf = gpd.read_file(os.path.join(temp_dir, geojson_files[0]))
        
        # 写入shp文件
        gdf.to_file(out_shp_path, encoding='utf-8')
        
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def wkt_to_shp(df, wkt_col, out_shp_path):
    '''
    作用：将含有wkt格式的DataFrame转换成shp文件
    参数说明：
    df: DataFrame - 含有wkt格式的DataFrame
    wkt_col: str - wkt所在的列名
    out_shp_path: str - 输出的shp文件路径
    '''
    df['geometry'] = df[wkt_col].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="epsg:4326")
    gdf.to_file(out_shp_path, encoding='utf-8')