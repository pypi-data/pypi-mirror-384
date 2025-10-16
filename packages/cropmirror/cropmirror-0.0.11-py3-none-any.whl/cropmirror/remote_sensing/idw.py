import os
import numpy as np
import glob
from osgeo import gdal, osr
import pandas as pd
from scipy.interpolate import Rbf
import pathlib
from pyproj import Proj, transform


def read_img(filename):
    dataset = gdal.Open(filename)
    if dataset == None:
        raise Exception(f"cant find/open {filename}")
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_Band = dataset.RasterCount

    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)

    del dataset
    return im_proj, im_geotrans, im_data, im_width, im_height, im_Band


DType2GDAL = {
    "uint8": gdal.GDT_Byte,
    "uint16": gdal.GDT_UInt16,
    "int16": gdal.GDT_Int16,
    "uint32": gdal.GDT_UInt32,
    "int32": gdal.GDT_Int32,
    "float32": gdal.GDT_Float32,
    "float64": gdal.GDT_Float64,
    "cint16": gdal.GDT_CInt16,
    "cint32": gdal.GDT_CInt32,
    "cfloat32": gdal.GDT_CFloat32,
    "cfloat64": gdal.GDT_CFloat64,
}


def write_img(filename, im_proj, im_geotrans, im_data):
    if im_data.dtype.name in DType2GDAL:
        datatype = DType2GDAL[im_data.dtype.name]
    else:
        datatype = gdal.GDT_Float32
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
    if not pathlib.Path(filename).parent.exists():
        pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(filename, im_width, im_height, im_bands, datatype)

    dataset.SetGeoTransform(im_geotrans)
    dataset.SetProjection(im_proj)
    if im_bands == 1:
        dataset.GetRasterBand(1).WriteArray(im_data)
    else:
        for i in range(im_bands):
            dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
    del dataset


class GEOchange(object):

    def __init__(self, toEPSG):
        self.EPSG = toEPSG
        self.to_crs = osr.SpatialReference()
        self.to_crs.ImportFromEPSG(toEPSG)

    def run(self, infile, outfile):
        im_proj, im_geotrans, im_data, self.im_width, self.im_height, self.im_Band = (
            read_img(infile)
        )
        srs = osr.SpatialReference()
        srs.ImportFromWkt(im_proj)
        self.Transformation = osr.CoordinateTransformation(srs, self.to_crs)
        geotrans = self.setGeotrans(im_geotrans)
        write_img(outfile, self.to_crs.ExportToWkt(), geotrans, im_data)

    def setGeotrans(self, im_geotrans):
        lon, lat = self.imagexy2geo(im_geotrans, 0, 0)
        coords00 = self.Transformation.TransformPoint(lat, lon)
        lon, lat = self.imagexy2geo(im_geotrans, self.im_height, 0)
        coords01 = self.Transformation.TransformPoint(lat, lon)
        lon, lat = self.imagexy2geo(im_geotrans, 0, self.im_width)
        coords10 = self.Transformation.TransformPoint(lat, lon)

        trans = [0 for i in range(6)]
        trans[0] = coords00[0]
        trans[3] = coords00[1]
        trans[2] = (coords01[0] - trans[0]) / self.im_height
        trans[5] = (coords01[1] - trans[3]) / self.im_height
        trans[1] = (coords10[0] - trans[0]) / self.im_width
        trans[4] = (coords10[1] - trans[3]) / self.im_width
        return trans

    def imagexy2geo(self, im_geotrans, row, col):
        px = im_geotrans[0] + col * im_geotrans[1] + row * im_geotrans[2]
        py = im_geotrans[3] + col * im_geotrans[4] + row * im_geotrans[5]
        return px, py


def select_station(fp, x_lim, y_lim):
    s_p = []
    for m in fp:
        data = pd.read_csv(m, encoding="gbk")
        lat = data["LATITUDE"].values.tolist()
        lon = data["LONGITUDE"].values.tolist()
        if y_lim - 5 < lat[0] < y_lim + 5 and x_lim - 5 < lon[0] < x_lim + 5:
            s_p.append(m)
    return s_p


def cal_sum_tem_rain(s_p, datel):
    dd = datel[0:4] + "-" + datel[4:6] + "-" + datel[6:]
    lon, lat, sum_tem, sum_rain, qiwen = [], [], [], [], []
    for n in s_p:
        data = pd.read_csv(n, encoding="gbk")
        lat1 = data["LATITUDE"].values.tolist()
        lat.append(lat1[0])
        lon1 = data["LONGITUDE"].values.tolist()
        lon.append(lon1[0])
        tem = data["TEMP"].values.tolist()
        rain = data["PRCP"].values.tolist()
        datee = data["DATE"].values.tolist()
        tem = np.array(tem)
        rain = np.array(rain)
        tem[tem > 70] = 0
        rain[rain > 500] = 0
        sum_tem.append(np.sum(tem - 17.22))
        sum_rain.append(np.sum(rain * 25.4))
        try:
            indexx = datee.index(dd)
            qiwen.append(tem[indexx])
        except:
            qiwen.append(np.mean(tem))
    return lon, lat, sum_tem, sum_rain, qiwen


def idw(lon, lat, sum_tem, sum_rain, qiwen, lonn, latt):
    xi, yi = np.meshgrid(lonn, latt)
    rbf1 = Rbf(lon, lat, sum_tem, function="inverse")
    tems = rbf1(xi, yi)
    rbf2 = Rbf(lon, lat, sum_rain, function="inverse")
    rains = rbf2(xi, yi)
    rbf3 = Rbf(lon, lat, qiwen, function="inverse")
    qiwens = rbf3(xi, yi)
    return tems, rains, qiwens


def write_tiff(lonn, latt, savename, dtaa):
    driver = gdal.GetDriverByName("GTiff")
    dataset1 = driver.Create(savename, len(lonn), len(latt), 1, gdal.GDT_Float32)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(4326)
    dataset1.SetProjection(spatial_ref.ExportToWkt())
    dataset1.SetGeoTransform(
        (lonn[0], lonn[1] - lonn[0], 0, latt[-1], 0, latt[-2] - latt[-1])
    )
    dataset1.GetRasterBand(1).WriteArray(dtaa)


# def do_idw(satation_path,savepath,tif):

def do_idw(lon, lat, sum_tem, sum_rain, qiwen, savepath, tif,suffix):
    im_proj, im_geotrans, im_data, im_width, im_height, im_Band = read_img(tif)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromWkt(im_proj)
    epsg_code = spatial_ref.GetAttrValue("AUTHORITY", 1)
    utm_proj = Proj(init="epsg:{}".format(epsg_code))
    wgs84_proj = Proj(init="epsg:4326")
    x_lim, y_lim = transform(utm_proj, wgs84_proj, im_geotrans[0], im_geotrans[3])
    x_lim1, y_lim1 = transform(
        utm_proj,
        wgs84_proj,
        im_geotrans[0] + im_geotrans[1],
        im_geotrans[3] + im_geotrans[0 - 1],
    )
    lonn = np.arange(x_lim - 0.01, x_lim + im_width * (x_lim1 - x_lim) + 0.01, 0.001)
    latt = np.arange(y_lim + 0.01, y_lim + im_height * (y_lim1 - y_lim) - 0.01, -0.001)

    # fp = glob.glob(satation_path+'/*.csv')
    # s_p = select_station(fp,x_lim,y_lim)
    # datee = os.path.basename(tif).split('_')[0]
    # lon,lat,sum_tem,sum_rain,qiwen = cal_sum_tem_rain(s_p,datee)

    tems1, rains1, qiwens1 = idw(lon, lat, sum_tem, sum_rain, qiwen, lonn, latt)

    air_temperature_file = os.path.join(savepath,f"air_temperature-{suffix}.tif")
    accumulated_rainfall_file = os.path.join(savepath,f"accumulated_rainfall-{suffix}.tif")
    accumulated_temperature_file = os.path.join(savepath,f"accumulated_temperature-{suffix}.tif")
    
    idw_air_temperature_file = os.path.join(savepath,f"Idw_air_temperature-{suffix}.tif")
    idw_accumulated_rainfall_file = os.path.join(savepath,f"Idw_accumulated_rainfall-{suffix}.tif")
    idw_accumulated_temperature_file = os.path.join(savepath,f"Idw_accumulated_temperature-{suffix}.tif")
    
    write_tiff(lonn, latt, accumulated_temperature_file, tems1)
    write_tiff(lonn, latt, accumulated_rainfall_file, rains1)
    write_tiff(lonn, latt, air_temperature_file, qiwens1)
    change = GEOchange(int(epsg_code))
    change.run(accumulated_temperature_file, idw_accumulated_temperature_file)
    change.run(accumulated_rainfall_file, idw_accumulated_rainfall_file)
    change.run(air_temperature_file, idw_air_temperature_file)
    # os.remove(savepath + "/积温.tif")
    # os.remove(savepath + "/积雨.tif")
    # os.remove(savepath + "/气温.tif")


if __name__ == "__main__":
    # 气象站点数据路径
    station_path = "/Users/zhoupeng/Desktop/代码20240911/过程数据/气象站点数据/2024"  # 气象站点数据路径
    # 气象站点插值保存的路径
    # savepath = "/Users/zhoupeng/Desktop/代码20240911/过程数据"
    savepath = "."
    # 影像路径
    # tif = "/Users/zhoupeng/Desktop/代码20240911/过程数据/20240909_021318_75_24ee_3B_AnalyticMS_SR_8b_clip.tif"
    tif = "20240909_021318_75_24ee_3B_AnalyticMS_SR_8b_clip.tif"
    # 执行主函数
    center_longitude = 132.690268
    center_latitude = 47.287796
    # 气象站lat,lon  
    lat =[49.33, 48.53, 48.34, 48.06, 47.42, 47.2, 47.34, 47.4, 48.22, 47.19, 47.14, 46.44, 46.47, 46.18, 47.0, 46.13, 46.44, 46.38, 46.23, 46.48, 45.57, 45.58, 45.5, 45.26, 45.46, 45.45, 45.18, 45.16, 45.46, 45.33, 45.16, 44.36, 44.56, 44.3, 44.23, 44.2, 44.05, 43.22, 43.07, 43.42, 43.18, 42.32, 42.46, 42.54, 42.52, 42.57]
    lon = [128.28, 130.24, 129.26, 129.14, 128.5, 130.12, 130.5, 132.32, 134.17, 131.5, 131.59, 129.53, 130.18, 129.35, 130.43, 130.33, 131.07, 131.09, 132.1, 134.0, 128.02, 128.44, 128.48, 128.16, 131.01, 130.36, 130.55, 130.14, 132.58, 131.52, 131.06, 129.24, 130.33, 129.4, 131.1, 129.28, 131.08, 128.12, 128.55, 130.16, 129.47, 129.0, 129.24, 130.17, 129.3, 129.5]
    qiwen = [15.749056603773585, 14.937735849056605, 13.352830188679246, 14.343396226415095, 15.907547169811322, 16.220754716981133, 16.69245283018868, 16.950943396226414, 15.80566037735849, 16.50943396226415, 16.95, 17.17924528301887, 17.649056603773584, 17.701886792452832, 17.022641509433964, 16.724528301886792, 18.4188679245283, 17.962264150943398, 17.39056603773585, 16.492307692307694, 17.362264150943396, 17.40754716981132, 17.516981132075472, 16.87735849056604, 17.41509433962264, 17.952830188679247, 17.486792452830187, 16.971698113207548, 16.99056603773585, 17.364150943396226, 17.607547169811323, 16.415384615384617, 17.052830188679245, 17.218867924528304, 16.069811320754717, 17.362264150943396, 17.964150943396227, 16.464150943396227, 16.884615384615383, 16.08867924528302, 17.318867924528302, 17.430188679245283, 18.31320754716981, 18.479245283018866, 18.203773584905658, 18.08867924528302]
    sum_rain = [0.0, 1.7, 1.9, 4.2, 4.699999999999999, 5.0, 3.6999999999999997, 5.5, 14.600000000000001, 3.3, 3.5, 4.9, 6.5, 7.7, 5.1000000000000005, 16.3, 5.1, 6.4, 4.4, 18.2, 14.700000000000001, 14.7, 17.9, 19.1, 16.9, 1.1, 13.7, 16.7, 30.8, 13.8, 16.7, 21.9, 14.5, 20.2, 20.8, 23.8, 13.1, 27.6, 11.2, 13.299999999999999, 21.1, 1.0, 2.8, 4.7, 3.5000000000000004, 5.5]
    sum_tem = [834.7, 791.7, 707.7, 760.2, 843.1, 859.7, 884.7, 898.4, 837.7, 875.0, 881.4, 910.5, 935.4, 938.2, 902.2, 886.4, 976.1999999999999, 952.0, 921.7, 857.6, 920.1999999999999, 922.6, 928.4, 894.5, 923.0, 951.5, 926.8, 899.5, 900.5, 920.3, 933.2, 853.6, 903.8, 912.6, 851.7, 920.2, 952.1, 872.6, 878.0, 852.7, 917.9, 923.8, 970.6, 979.4, 964.8, 958.7]
    
    do_idw(lon, lat, sum_tem, sum_rain, qiwen, savepath, tif)
