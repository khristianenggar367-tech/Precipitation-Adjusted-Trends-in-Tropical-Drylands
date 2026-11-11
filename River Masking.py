import glob
import os
import re
import numpy as np
from osgeo import gdal

# ==========================================
# 1. KONFIGURASI PATH & PATTERN
# ==========================================
folder_ndvi = r"H:\RESTREND\NDVI HARMONISASI"
folder_residu = r"H:\RESIDU"
folder_output = r"H:\RESIDU_MASKED"
ndvi_threshold = 0.10

os.makedirs(folder_output, exist_ok=True)

files_ndvi_raw = glob.glob(os.path.join(folder_ndvi, "*.tif"))
files_residu_raw = glob.glob(os.path.join(folder_residu, "*.tif"))

map_ndvi = {}
for f in files_ndvi_raw:
    match = re.search(r"NDVI\s+(\d{4})\s+Baru", os.path.basename(f), re.IGNORECASE)
    if match:
        map_ndvi[match.group(1)] = f

map_residu = {}
for f in files_residu_raw:
    fname = os.path.basename(f)
    year = fname.replace(".tif", "").strip()
    if year.isdigit() and len(year) == 4:
        map_residu[year] = f

years_common = sorted(list(set(map_ndvi.keys()) & set(map_residu.keys())))
print(f"Mencocokkan {len(years_common)} tahun data (1990–2024)...\n")

# ==========================================
# 2. EKSTRAKSI MASKER VEGETASI STATIK (NDVI >= 0.10)
# ==========================================
print("Mengekstrak Masker Vegetasi Statik dari NDVI HARMONISASI...")

# Tentukan dimensi terkecil untuk standardisasi grid
min_rows, min_cols = None, None
for yr in years_common:
    ds = gdal.Open(map_ndvi[yr])
    r, c = ds.RasterYSize, ds.RasterXSize
    min_rows = r if min_rows is None else min(min_rows, r)
    min_cols = c if min_cols is None else min(min_cols, c)

first_ds = gdal.Open(map_ndvi[years_common[0]])
geo_transform = first_ds.GetGeoTransform()
projection = first_ds.GetProjection()

valid_mask = np.ones((min_rows, min_cols), dtype=bool)

for yr in years_common:
    ds = gdal.Open(map_ndvi[yr])
    data_ndvi = ds.GetRasterBand(1).ReadAsArray()[:min_rows, :min_cols]

    year_mask = (data_ndvi != -9999) & (~np.isnan(data_ndvi)) & (data_ndvi >= ndvi_threshold)
    valid_mask = valid_mask & year_mask

total_valid_pixels = np.sum(valid_mask)
total_masked_pixels = (min_rows * min_cols) - total_valid_pixels

print(f"\n==========================================")
print(f" [VERIFIKASI MASKER NDVI]")
print(f" Total Piksel Vegetasi Valid (N) = {total_valid_pixels:,} Pixels")
print(f" Total Piksel Sungai/Air Termasking = {total_masked_pixels:,} Pixels")
print(f"==========================================\n")

# ==========================================
# 3. TERAPKAN MASKING KE RASTER RESIDU
# ==========================================
print("Memproses masking ke folder H:\\RESIDU_MASKED...\n")

for yr in years_common:
    f_residu = map_residu[yr]
    file_name = f"{yr}.tif"
    out_path = os.path.join(folder_output, file_name)

    src_ds = gdal.Open(f_residu)
    data_residu = src_ds.GetRasterBand(1).ReadAsArray()[:min_rows, :min_cols] # Auto-slice ke dimensi mask
    nodata_val = -9999

    masked_data = np.where(valid_mask, data_residu, nodata_val)
    count_valid = np.sum(masked_data != nodata_val)

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(out_path, min_cols, min_rows, 1, gdal.GDT_Float32)
    out_ds.SetGeoTransform(geo_transform)
    out_ds.SetProjection(projection)

    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(masked_data)
    out_band.SetNoDataValue(nodata_val)
    out_band.FlushCache()

    out_ds = None
    src_ds = None

    print(f"Berhasil: {file_name} -> Valid Pixels = {count_valid:,}")

print("\n[SUKSES 100%] Masking selesai tanpa error dimensi!")