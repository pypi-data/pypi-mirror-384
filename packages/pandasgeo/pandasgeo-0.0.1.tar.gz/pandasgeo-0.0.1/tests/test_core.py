import pandasgeo as pdg
import pytest

def test_distancea_str():
    """
    测试 distancea_str 函数计算两个点之间的距离。
    """
    # 定义两个点，位于赤道上，经度相差1度
    lon1, lat1 = 0, 0
    lon2, lat2 = 1, 0

    # 在赤道上，1度的经度差大约是 111.32 公里
    expected_distance_meters = 111319.49

    # 调用函数计算距离
    calculated_distance = pdg.distancea_str(lon1, lat1, lon2, lat2)

    # 使用 pytest.approx 来比较浮点数，允许有一定的误差
    assert calculated_distance == pytest.approx(expected_distance_meters, rel=1e-4)

def test_add_points():
    """
    测试 add_points 函数是否能正确将DataFrame转换为GeoDataFrame。
    """
    import pandas as pd
    from shapely.geometry import Point

    # 创建一个简单的DataFrame
    data = {'id': ['A', 'B'], 'lon': [10, 20], 'lat': [30, 40]}
    df = pd.DataFrame(data)

    # 调用函数
    gdf = pdg.add_points(df, lon='lon', lat='lat')

    # 验证返回的是否是GeoDataFrame
    assert 'geometry' in gdf.columns
    # 验证第一个点的坐标是否正确
    assert gdf.geometry.iloc[0] == Point(10, 30)
    # 验证行数是否保持不变
    assert len(gdf) == len(df)
