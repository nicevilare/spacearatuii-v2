from flask import Flask, jsonify, render_template, request
import cv2 as cv
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

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# BANDS = ', '.join(f"'{band}'" for band in BANDS)

path = 'img'
file_id = ''

print(BANDS)

app = Flask(__name__)

ee.Authenticate(auth_mode='localhost', scopes=[
    'https://www.googleapis.com/auth/earthengine',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email'
])

ee.Initialize(project='aratu-436806')

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

   #export_to_drive(landsat_image, 'Natal')
   
   name= 'Landsat_Image_Export' + '_Landsat_Img_.tif'
   #print(name)
   #download_img(quickstart.main(name))


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

def convert_to_png(name):
   """
   try to convert .tif to png :) 
   """
   with rasterio.open(name) as src:
      img_array = src.read()
   first_band_array = img_array[0, :, :]
   first_band_array = cv.normalize(first_band_array, None, 0, 255, cv.NORM_MINMAX)
   first_band_array = first_band_array.astype(np.uint8)
   cv.imwrite('img/landsat_img_converted.png', first_band_array)
 

if __name__ == '__main__':
    app.run(debug=True)
