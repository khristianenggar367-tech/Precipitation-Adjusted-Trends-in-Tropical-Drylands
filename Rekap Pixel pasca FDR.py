import numpy as np

# 1. Ambil active layer (Sens_Slope_LSWI_Significant_FDR005)
layer = iface.activeLayer()
if not layer or layer.type() != QgsMapLayer.RasterLayer:
    raise Exception("Pilih layer raster Sen's Slope LSWI yang aktif terlebih dahulu.")

provider = layer.dataProvider()
extent = layer.extent()
width = layer.width()
height = layer.height()

# Ambil block data raster band 1
block = provider.block(1, extent, width, height)
nodata = provider.sourceNoDataValue(1)

# 2. Konversi buffer data raster ke NumPy Array (float32)
slope_data = np.frombuffer(block.data(), dtype=np.float32)

# 3. Filter piksel valid (bukan NoData dan bukan NaN/Inf)
if nodata is not None:
    valid_mask = (slope_data != nodata) & np.isfinite(slope_data)
else:
    valid_mask = np.isfinite(slope_data)

valid_pixels = slope_data[valid_mask]
total_sig = len(valid_pixels)

if total_sig == 0:
    print("Tidak ditemukan piksel signifikan pada layer ini.")
else:
    # 4. Pemisahan Increasing (Wetting) vs Decreasing (Drying)
    inc_pixels = valid_pixels[valid_pixels > 0]
    dec_pixels = valid_pixels[valid_pixels < 0]

    n_inc = len(inc_pixels)
    n_dec = len(dec_pixels)

    # Menghitung resolusi spasial dari extent dan ukuran piksel raster secara dinamis
    pixel_size_x = layer.rasterUnitsPerPixelX()
    pixel_size_y = layer.rasterUnitsPerPixelY()
    pixel_area_m2 = pixel_size_x * pixel_size_y  # e.g., 30m x 30m = 900 m2

    # Konversi Luas
    area_inc_ha = (n_inc * pixel_area_m2) / 10_000
    area_dec_ha = (n_dec * pixel_area_m2) / 10_000
    area_inc_km2 = (n_inc * pixel_area_m2) / 1_000_000
    area_dec_km2 = (n_dec * pixel_area_m2) / 1_000_000

    # 5. Cetak Output Rekapitulasi
    print(f"==================================================")
    print(f" REKAPITULASI TREN LSWI SIGNIFIKAN (FDR Q <= 0.05)")
    print(f"==================================================")
    print(f"Nama Layer             : {layer.name()}")
    print(f"Resolusi Spasial       : {pixel_size_x:.2f} m x {pixel_size_y:.2f} m ({pixel_area_m2:.1f} m²)")
    print(f"TOTAL PIKSEL SIGNIFIKAN: {total_sig:,} piksel")
    print(f"--------------------------------------------------")
    print(f"1. SIGNIFICANT WETTING / KELEMBAPAN NAIK (LSWI Slope > 0):")
    print(f"   - Jumlah Piksel     : {n_inc:,} piksel ({n_inc/total_sig*100:.2f}%)")
    print(f"   - Luas Area         : {area_inc_ha:,.2f} Ha ({area_inc_km2:,.4f} km²)")
    print(f"--------------------------------------------------")
    print(f"2. SIGNIFICANT DRYING / PENGERINGAN (LSWI Slope < 0):")
    print(f"   - Jumlah Piksel     : {n_dec:,} piksel ({n_dec/total_sig*100:.2f}%)")
    print(f"   - Luas Area         : {area_dec_ha:,.2f} Ha ({area_dec_km2:,.4f} km²)")
    print(f"==================================================")