from flask import Flask, jsonify, render_template, request
import ee 
import geemap 

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
   landsat_image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(ee.Geometry.Point([-8.0476, -34.8770])) \
        .filterDate('2021-01-01', '2021-12-31') \
        .median()
   Map.addLayer(landsat_image, {'bands': ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 3000}, 'Landsat RGB')
   Map.setCenter(-47.9292, -15.7801, 4)

   map_html = Map.to_html()  

   return render_template('index.html', map_html=map_html)


if __name__ == '__main__':
    app.run(debug=True)
