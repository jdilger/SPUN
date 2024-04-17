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
output_file = "data/NEON_metadata_ee_2.csv"
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


def indices(img: ee.Image) -> ee.Image:
    img = img.multiply(0.0001)
    ndmi = img.normalizedDifference(["B8", "B11"]).rename("NDMI")
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    nbr = img.normalizedDifference(["B8", "B12"]).rename("NBR")
    nd_gr = img.normalizedDifference(["B3", "B4"]).rename("ND_GREEN_RED")
    red_swir_r = img.select("B8").divide(img.select("B11")).rename("RED_SWIR_RATIO")
    savi = img.expression(
        "((NIR - RED) / (NIR + RED + 0.5)) * (1 + 0.5)",
        {"NIR": img.select("B8"), "RED": img.select("B4")},
    ).rename("SAVI")
    return ee.Image.cat([ndmi, ndvi, nbr, red_swir_r, nd_gr, savi])


collection = (
    s2.filterDate(start_date, end_date)
    .linkCollection(csPlus, [QA_BAND])
    .map(lambda img: img.updateMask(img.select(QA_BAND).gte(CLEAR_THRESHOLD)))
    .map(lambda img: indices(img))
)
reducers = (
    ee.Reducer.percentile([10, 90])
    .combine(
        reducer2=ee.Reducer.mean(),
        sharedInputs=True,
    )
    .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
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
