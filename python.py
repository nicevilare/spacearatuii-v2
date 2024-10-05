from flask import Flask, jsonify, render_template, request
import cv2 as cv
from PIL import Image
import numpy as np
import rasterio
import time
import os
import shutil
import ee 
import geemap 
import gdown
from constants import LOC, IMAGE_COLLECTION, BANDS, START_DATE, END_DATE, CITY

import quickstart 



# BANDS = ', '.join(f"'{band}'" for band in BANDS)

path = 'img'
file_id = ''

# print(BANDS)

app = Flask(__name__)

ee.Authenticate(auth_mode='localhost', scopes=[
    'https://www.googleapis.com/auth/earthengine',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email'
])

ee.Initialize(project='testearthengine-437300')

@app.route('/')
def index():

   Map = geemap.Map()

   all_cities = ee.ImageCollection([])
   one_city = ee.ImageCollection([])
   if not CITY:
       for _, coord in LOC.items():
        landsat_image = ee.ImageCollection(IMAGE_COLLECTION) \
                .filterBounds(ee.Geometry.Point(coord)) \
                .filterDate(START_DATE, END_DATE) \
                .median()
        all_cities = all_cities.merge(landsat_image)
   else:
      landsat_image = ee.ImageCollection(IMAGE_COLLECTION) \
                .filterBounds(ee.Geometry.Point(list(CITY.values())[0])) \
                .filterDate(START_DATE, END_DATE) \
                .median()
      one_city = one_city.merge(landsat_image)
   
   

   if CITY:
    export_to_drive(landsat_image, 'Natal')
    name= 'Landsat_Image_Export' + '_Landsat_Img_.tif'
    print(name)
    download_img(quickstart.main(name))


   Map.addLayer(all_cities if not CITY else one_city, {'bands': BANDS, 'min': 1000, 'max': 30000}, 'Landsat RGB')
   Map.setCenter(-47.9292, -15.7801, 4)  # Longitude, Latitude, Zoom level



   map_html = Map.to_html()  

   return render_template('index.html', map_html=map_html)


def create_dir(name, img):
    """
    create directory
    """
    if not os.path.exists(path):
      os.path.makedirs(path)
    file_path = path + '/' + name + '.txt'
#    with open(file_path, 'w') as file:
#       file.write(str(img))
    return file_path


def export_to_drive(img, folder):
   """
   export landsat image to drive 
   """
   task = ee.batch.Export.image.toDrive(image=img.select(BANDS), description='Landsat_Image_Export' + f'_{folder}_', scale=1000, region=ee.Geometry.Point(list(CITY.values())[0]), maxPixels=1e13,  folder=folder, fileFormat='GeoTIFF')
   task.start()
   while task.active():
    print('Exporting... Status:', task.status())
    time.sleep(10)
   print('Export completed. Check your specified folder on Google Drive for the image.')

   final_status = task.status()
   if final_status['state'] == 'COMPLETED':
        print('Export completed successfully. Check your specified folder on Google Drive for the image.')
   else:
        print('Export failed. Status:', final_status)


def download_img(id):
   """
   download landsat image from gdrive
   """
   url = 'https://drive.google.com/uc?id=' + id
   # https://drive.google.com/file/d/1ZUN3Cr_ERRKQI4O8BrEX1AyyasPj6frh/view?usp=drive_link
   gdown.download(url, 'landsat_image.tif', quiet=False)
   if os.path.exists('img/landsat_image.tif'):
      os.remove(os.path.join('img', 'landsat_image.tif'))
   shutil.move('landsat_image.tif', 'img')
   convert_to_png('img/landsat_image.tif')


def convert_to_png(name):
   """
   try to convert .tif to png :) 
   """
   with rasterio.open(name) as src:
      img_array = src.read()
# ta errado mas so como exemplo tem que refazer e eu to cansado
   first_band_array = img_array[0, :, :]
   first_band_array = cv.normalize(first_band_array, None, 0, 255, cv.NORM_MINMAX)
   first_band_array = first_band_array.astype(np.uint8)
   cv.imwrite('img/landsat_img_converted.png', first_band_array)
   


 

if __name__ == '__main__':
    app.run(debug=True)

"""
center_point = ee.Geometry.Point(list(CITY.values())[0])
      print(center_point)
      geometry = center_point.buffer(45).bounds()
      sample = landsat_image.sample({
      'region': geometry,  # Region size corresponding to 3x3 pixels
      'scale': 30,         # Landsat native scale in meters
      'numPixels': 9       # Sampling exactly 9 pixels
      })
      print(sample.getInfo()) 
      sample_fc = ee.FeatureCollection(sample)
      one_city = one_city.merge(sample_fc

"""

"""
   print(landsat_image.getInfo())

   pixel_area_image = ee.Image.pixelArea()

   valid_area_image = pixel_area_image.updateMask(landsat_image.mask())

   total_area = valid_area_image.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=region_of_interest,
    scale=30,  # Landsat 8 pixel scale (30 meters)
    maxPixels=1e9
)
   
   total_area_m2 = total_area.get('area').getInfo()

   total_area_km2 = total_area_m2 / 1e6
   print(f'Total area: {total_area_km2} km²')

### Calculating the number of pixels
# Reduce over region of interest to count the number of pixels
   pixel_count = landsat_image.reduceRegion( 
     reducer=ee.Reducer.count(),
    geometry=region_of_interest,
    scale=30,
    maxPixels=1e9
).get('B1').getInfo()  # Use band 1 ('B1') for pixel count

   print(f'Total number of pixels: {pixel_count}')


   print(f'\n\n\n{landsat_image.getInfo()}')
"""


"""

   tiff_image = Image.open("img/landsat_image.tif")
   jpeg_image = tiff_image.convert("RGB")
   jpeg_image.save("example.jpg")


   img = cv.imread('img/landsat_image_converted.png', cv.IMREAD_UNCHANGED)

# Check the max and min values of the image
   print(f'Min pixel value: {np.min(img)}')
   print(f'Max pixel value: {np.max(img)}')

# Normalize the image to [0, 255] for display
   img_normalized = cv.normalize(img, None, 0, 255, cv.NORM_MINMAX)

# Convert to uint8 (standard 8-bit image depth for display)
   img_normalized = img_normalized.astype(np.uint8)

# Save or display the normalized image
   cv.imwrite('normalized_landsat_image.png', img_normalized)
   cv.imshow('Normalized Image', img_normalized)
   cv.waitKey(0)
   cv.destroyAllWindows()
"""