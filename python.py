from flask import Flask, jsonify, render_template, request
import cv2 as cv
from PIL import Image
import numpy as np
import csv
import rasterio
import time
import os
import shutil
import ee 
import geemap 
import gdown
from constants import LOC, IMAGE_COLLECTION, BANDS, START_DATE, END_DATE, CITY
import quickstart 
import test_dates # a = test_dates.get_dates(coord)

path = 'img'
file_id = ''

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
      
      bounds = ee.Geometry.Point(list(CITY.values())[0]).buffer(30*30).bounds().getInfo()['coordinates'][0]
      
      rect = create_rectangles(bounds=bounds)

      landsat_image = ee.ImageCollection(IMAGE_COLLECTION) \
                .filterBounds(ee.Geometry.Point(list(CITY.values())[0]).buffer(30*30)) \
                .filterDate(START_DATE, END_DATE) \
                .median() \
                .clip(rect[8]) # ee.Geometry.Point(list(CITY.values())[0].buffer(30*30)
      
      one_city = one_city.merge(landsat_image)
      for k in range(0, len(rect)-1):
         landsat_image = ee.ImageCollection(IMAGE_COLLECTION) \
                .filterBounds(rect[k]) \
                .filterDate(START_DATE, END_DATE) \
                .median() \
                .clip(rect[k])
         one_city = one_city.merge(landsat_image)

      landsat_data = one_city.getInfo()
      file_data = get_csv(landsat_data)

      cloud_cover = one_city.get('CLOUD_COVER').getInfo()
      cloud_cover_land = one_city.get('CLOUD_COVER_LAND').getInfo()
      collection_category = one_city.get('COLLECTION_CATEGORY').getInfo()
      image_quality_oli = one_city.get('IMAGE_QUALITY_OLI').getInfo()
      image_quality_tirs = one_city.get('IMAGE_QUALITY_TIRS').getInfo()

      #print(f'\n\n{cloud_cover}\n\n{cloud_cover_land}\n\n{collection_category}\n\n{image_quality_oli}\n\n{image_quality_tirs}\n\n')

      export_image_props(landsat_image.getInfo()['properties'])

      with open('csv_file.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(file_data.keys())
        writer.writerow(file_data.values())

      quickstart.upload_basic()
    

   if CITY:
    #export_to_drive(landsat_image, 'Natal')
    #name= 'Landsat_Image_Export' + '_Landsat_Img_.tif'
    #print(name)
    #download_img(quickstart.main(name))
    pass

   Map.addLayer(all_cities if not CITY else one_city, {'bands': BANDS, 'min': 1000, 'max': 30000}, 'Landsat RGB')
   Map.setCenter(-35.2086, -5.79448, 12)  # Longitude, Latitude, Zoom level

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
   
def create_rectangles(bounds):
   # min_lat, max_lat, min_long, max_long
   default_values =  [bounds[0][1], bounds[2][1], bounds[0][0], bounds[2][0]]

   # min_lat, max_lat, min_long, max_long
   w = default_values[3] - default_values[2]
   h = default_values[1] - default_values[0]

   new_0 = [default_values[3], default_values[3] + w, default_values[0], default_values[1]]
   new_1 = [default_values[2], default_values[2] - w, default_values[0], default_values[1]]
   new_2 = [default_values[2], default_values[3], default_values[1], default_values[1] + h]
   new_3 = [default_values[2], default_values[3], default_values[0], default_values[0] - h]

   new_4 = [new_2[0] - w, new_2[0], new_2[2], new_2[3]]
   new_5 = [new_4[1], new_4[1] + 2*w, new_4[2], new_4[3]]
   new_6 = [new_3[0] - w, new_3[0], new_3[2], new_3[3]]
   new_7 = [new_6[1], new_6[1] + 2*w, new_6[2], new_6[3]]

   # define values for all rectangles:
   rect0 = ee.Geometry.Polygon([[
         [new_0[0], new_0[2]],
         [new_0[1], new_0[2]],
         [new_0[1], new_0[3]],
         [new_0[0], new_0[3]],
         [new_0[0], new_0[2]]
      ]])
   rect1 = ee.Geometry.Polygon([[
      [new_1[1], new_1[2]],
      [new_1[0], new_1[2]],
      [new_1[0], new_1[3]],
      [new_1[1], new_1[3]],
      [new_1[1], new_1[2]]
   ]])
   rect2 = ee.Geometry.Polygon([[
         [new_2[0], new_2[2]],
         [new_2[1], new_2[2]],
         [new_2[1], new_2[3]],
         [new_2[0], new_2[3]],
         [new_2[0], new_2[2]]
      ]])
   rect3 = ee.Geometry.Polygon([[
         [new_3[0], new_3[3]],
         [new_3[1], new_3[3]],
         [new_3[1], new_3[2]],
         [new_3[0], new_3[2]],
         [new_3[0], new_3[3]]
      ]])
   rect4 = ee.Geometry.Polygon([[
         [new_4[0], new_4[2]],
         [new_4[1], new_4[2]],
         [new_4[1], new_4[3]],
         [new_4[0], new_4[3]],
         [new_4[0], new_4[2]]
      ]])
   rect5 = ee.Geometry.Polygon([[
         [new_5[0], new_5[2]],
         [new_5[1], new_5[2]],
         [new_5[1], new_5[3]],
         [new_5[0], new_5[3]],
         [new_5[0], new_5[2]]
      ]])
   rect6 = ee.Geometry.Polygon([[
         [new_6[0], new_6[3]],
         [new_6[1], new_6[3]],
         [new_6[1], new_6[2]],
         [new_6[0], new_6[2]],
         [new_6[0], new_6[3]]
      ]])
   rect7 = ee.Geometry.Polygon([[
         [new_7[0], new_7[2]],
         [new_7[1], new_7[2]],
         [new_7[1], new_7[3]],
         [new_7[0], new_7[3]],
         [new_7[0], new_7[2]]
      ]])
   rect8 = ee.Geometry.Polygon([
    [[default_values[2], default_values[0]],  # Bottom Left
     [default_values[3], default_values[0]],  # Bottom Right
     [default_values[3], default_values[1]],  # Top Right
     [default_values[2], default_values[1]],  # Top Left
     [default_values[2], default_values[0]]]  # Closing the polygon
   ])

   rectangles = rect0, rect1, rect2, rect3, rect4, rect5, rect6, rect7, rect8
   return rectangles

def get_csv(d, parent_key='', sep='_'):
   items = []
   for k, v in d.items():
    new_key = f'{parent_key}{sep}{k}' if parent_key else k
    if isinstance(v, dict):
        items.extend(get_csv(v, new_key, sep=sep).items())
    elif isinstance(v, list):
        if all(isinstance(i, dict) for i in v):
            for idx, item in enumerate(v):
                items.extend(get_csv(item, f'{new_key}{sep}{idx}', sep=sep).items())
        else:
            items.append((new_key, str(v)))  # Convert list to string if not all dicts
    else:
        items.append((new_key, v))
   return dict(items)

def export_image_props(props):
   properties = props
   csv_file = 'landsat_image_properties.csv'

# Write the properties to a CSV file
   with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Write the headers (property names)
    writer.writerow(['Property', 'Value'])
    
    # Write each property and its value
    for key, value in properties.items():
        writer.writerow([key, value])

   
if __name__ == '__main__':
    app.run(debug=True)

