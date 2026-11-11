import numpy as np
from osgeo import gdal

# 1. Tentukan path file raster P-Value dan output Q-Value
input_pvalue_path = r"H:\MAST LSWI 35 Tahun\p_value.tif"
output_qvalue_path = r"H:\MAST LSWI 35 Tahun\\Q-Value_FDR.tif"

# 2. Buka raster menggunakan GDAL (bawaan QGIS)
ds = gdal.Open(input_pvalue_path)
band = ds.GetRasterBand(1)
p_data = band.ReadAsArray().astype(np.float32)
nodata = band.GetNoDataValue()

if nodata is None:
    nodata = -9999.0

# 3. Masking nilai valid (abaikan NoData dan NaN)
valid_mask = (p_data != nodata) & (~np.isnan(p_data)) & (p_data >= 0)
p_flat = p_data[valid_mask]
m = len(p_flat)

print(f"Jumlah piksel valid terdeteksi: {m}")

# 4. Hitung Benjamini-Hochberg Adjusted q-value
sort_idx = np.argsort(p_flat)
p_sorted = p_flat[sort_idx]
ranks = np.arange(1, m + 1)

# Hitung raw q-value
q_raw = (p_sorted * m) / ranks

# Step-Up Procedure (Monotonic Cumulative Minimum dari belakang)
q_sorted = np.minimum.accumulate(q_raw[::-1])[::-1]
q_sorted = np.clip(q_sorted, 0, 1.0)

# Re-index kembali ke posisi piksel asli
q_flat = np.zeros_like(p_flat)
q_flat[sort_idx] = q_sorted

# Putar balik ke bentuk matriks 2D raster
q_raster = np.full_like(p_data, nodata, dtype=np.float32)
q_raster[valid_mask] = q_flat

# 5. Simpan ke file GeoTIFF baru
driver = gdal.GetDriverByName("GTiff")
out_ds = driver.Create(output_qvalue_path, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32)
out_ds.SetGeoTransform(ds.GetGeoTransform())
out_ds.SetProjection(ds.GetProjection())

out_band = out_ds.GetRasterBand(1)
out_band.WriteArray(q_raster)
out_band.SetNoDataValue(nodata)
out_band.FlushCache()

out_ds = None
ds = None

print(f"SUKSES! Raster Q-Value FDR telah berhasil dibuat di:\n{output_qvalue_path}")