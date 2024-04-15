import ee
import google.auth
import geopandas as gpd
import pandas as pd
import json
import requests

credentials, _ = google.auth.default()
ee.Initialize(
    credentials,
    project="john-ee-282116",
    opt_url="https://earthengine-highvolume.googleapis.com",
)

input_file = "data/NEON_metadata.csv"
output_file = "data/NEON_metadata_ee.csv"
start_date, end_date = "2018-01-01", "2018-12-31"

points = pd.read_csv(input_file)
points = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(points.longitude, points.latitude, crs="EPSG:4326"),
    data=points,
)
points = (
    ee.FeatureCollection(json.loads(points.to_json()))
    .map(
        lambda f: f.set(
            "system:time_start", ee.Date.fromYMD(f.get("collectYear"), 1, 1)
        )
    )
    .filterDate(start_date, end_date)
)


s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
csPlus = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

# Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
QA_BAND = "cs_cdf"

# The threshold for masking; values between 0.50 and 0.65 generally work well.
# Higher values will remove thin clouds, haze & cirrus shadows.
CLEAR_THRESHOLD = 0.50

# NDMI = (NIR - SWIR1)/(NIR + SWIR1)

collection = (
    s2.filterDate(start_date, end_date)
    .linkCollection(csPlus, [QA_BAND])
    .map(lambda img: img.updateMask(img.select(QA_BAND).gte(CLEAR_THRESHOLD)))
    .map(lambda img: img.normalizedDifference(["B8", "B11"]).rename("NDMI"))
)
reducers = ee.Reducer.percentile([10, 90]).combine(
    reducer2=ee.Reducer.mean(), sharedInputs=True
)
image = collection.reduce(reducers)
new_feats = image.reduceRegions(
    collection=points, reducer=ee.Reducer.first(), scale=10, crs="EPSG:4326"
)


url = new_feats.getDownloadURL()
response = requests.get(url)
response.raise_for_status()
with open(output_file, "wb") as fd:
    fd.write(response.content)
