import ee

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize(project='project777-viirs-data')

##### STANDARD PARAMETERS #######
# Define ROI (contiguous United States)
roi = ee.Geometry.Rectangle([-125, 24, -65, 50])

# Define time range
start_date = '2000-02-18'
end_date = '2023-12-31'

# Get date from image
def get_date(image):
  return ee.Image(image).date().format('YYYY-MM-dd')

# Base function for applying North America-centric projection specification to a specifc img instance
def set_std_NA_projection(daymet_img):

    # Define the DAYMET projection using ee.Projection: NAD83 / Canada Lambert (EPSG:3347)
    NA_projection = ee.Projection('EPSG:3347') 

    return daymet_img.reproject(
        crs=NA_projection,
        scale=daymet_img.projection().nominalScale()    # Use Daymet's native resolution
    )

# Define a function to calculate weekly averages
def weekly_average_daymet(date, daily_collection, start_date='2000-02-18'):
    start = ee.Date(date)
    end = start.advance(1, 'week')
    filtered_collection = daily_collection.filterDate(start, end)
    mean_image = filtered_collection.mean()

    original_crs = daily_collection.first().projection().crs()
    original_scale = daily_collection.first().projection().nominalScale()
    mean_image = mean_image.setDefaultProjection(crs=original_crs, scale=original_scale)

    # Calculate week number since the start date
    week_number = start.difference(ee.Date(start_date), 'week').add(1)
    
    mean_image = mean_image.set('system:time_start', start.millis())
    mean_image = mean_image.set('week', week_number)

    return mean_image

### DAYMETv4 pre-processing
# Load and filter Daymet data; set default projection
daymet_daily = ee.ImageCollection('NASA/ORNL/DAYMET_V4') \
    .filterDate(start_date, end_date) \
    .filterBounds(roi)
daymet_daily = daymet_daily.map(set_std_NA_projection)

average_map = lambda date:  weekly_average_daymet(date, daily_collection=daymet_daily)

# Create a list of starting dates for each week
start_dates = ee.List.sequence(
    ee.Date(start_date).millis(),
    ee.Date(end_date).millis(),
    7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
)

# Map the weekly_average function over the list of start dates
weekly_averages = start_dates.map(average_map)

# Convert the list of weekly averages to an ImageCollection
daymet_weekly = ee.ImageCollection(weekly_averages)
daymet_weekly = daymet_weekly.map(set_std_NA_projection)

# Status Check
print('Number of DAYMETv4 weekly images:', daymet_weekly.size().getInfo())
print(daymet_weekly.first().propertyNames().getInfo())
print(daymet_weekly.first().bandNames().getInfo())
print(daymet_weekly.first().get('week').getInfo())
print(f"Spatial resolution of the weekly image: {daymet_weekly.first().projection().nominalScale().getInfo()} meters")
print(f"CRS: {daymet_weekly.first().projection().crs().getInfo()}")

# Print the list of dates
weekly_dates_list = daymet_weekly.toList(daymet_weekly.size()).map(get_date)
print('Weekly Dates:', weekly_dates_list.getInfo()[:3])
print()

def weekly_interpolation(img_collection, start_date, end_date):
  """Interpolates an ImageCollection to weekly averages."""

  # Create a list of weekly start dates
  weekly_dates = ee.List.sequence(
      ee.Date(start_date).millis(),  # Use .millis() directly
      ee.Date(end_date).millis(),    # Use .millis() directly
      7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
  )

  # Function to compute weekly average
  def weekly_average(date_millis):
    date = ee.Date(date_millis)
    start = date.advance(-8, 'day')  # 8 days before
    end = date.advance(8, 'day')     # 8 days after

    # use 17-day window to ensure at least one data point is captured, avoiding null bands 
    filtered = img_collection.filterDate(start, end)

    original_crs = img_collection.first().projection().crs()
    original_scale = img_collection.first().projection().nominalScale()

    weekly_avg = filtered.mean().set('system:time_start', date_millis)
    weekly_avg = weekly_avg.setDefaultProjection(crs=original_crs, scale=original_scale)

    return weekly_avg

  # Map the weekly average function over the date list
  weekly_evi = weekly_dates.map(weekly_average)

  return ee.ImageCollection(weekly_evi)

### MODIS EVI
# Load and filter MODIS-EVI data
modis_EVI = ee.ImageCollection('MODIS/061/MOD13A2') \
    .filterDate(start_date, end_date) \
    .filterBounds(roi) \
    .select(['EVI', 'NDVI'])

# Interpolate data to produce weekly images
weekly_EVI = weekly_interpolation(modis_EVI, start_date, end_date)

# Reproject to 1000m x 1000m while keeping the original projection
weekly_EVI = weekly_EVI.map(lambda image: image.reproject(
    crs=image.projection(),  # Maintain the original projection
    scale=1000               # 1km resolution
))

### Status Check
print('Number of Weekly MODIS-EVI images:', weekly_EVI.size().getInfo())
print(weekly_EVI.first().bandNames().getInfo())
print(f"Spatial resolution of weekly_EVI image: {weekly_EVI.first().projection().nominalScale().getInfo()} meters")
print(f"CRS: {weekly_EVI.first().projection().crs().getInfo()}")
print()

### MODIS ET (500m)
# Load and filter MODIS-ET data
modis_ET = ee.ImageCollection('MODIS/061/MOD16A2GF') \
    .filterDate(start_date, end_date) \
    .filterBounds(roi) \
    .select(['ET', 'LE', 'PET', 'PLE'])

# Downsample MODIS ET to 1km
modis_ET = modis_ET.map(lambda image: image.reduceResolution(
    reducer=ee.Reducer.mean(),
    maxPixels=1024  # This is important to avoid exceeding memory limits
).reproject(
    crs=image.projection(),  # Maintain the original projection
    scale=1000               # 1km resolution
))

# Interpolate data to produce weekly images
weekly_ET = weekly_interpolation(modis_ET, start_date, end_date)

### MODIS FPAR (500m)
# Load and filter MODIS-FPAR data
modis_FPAR = ee.ImageCollection('MODIS/061/MOD15A2H') \
    .filterDate(start_date, end_date) \
    .filterBounds(roi) \
    .select(['Fpar_500m', 'Lai_500m'],  # Old band names
            ['FPAR', 'LAI'],            # New band names
    )

# Downsample MODIS FPAR to 1km
modis_FPAR = modis_FPAR.map(lambda image: image.reduceResolution(
    reducer=ee.Reducer.mean(),
    maxPixels=1024
).reproject(
    crs=image.projection(),
    scale=1000
))

# Interpolate data to produce weekly images
weekly_FPAR = weekly_interpolation(modis_FPAR, start_date, end_date)

##### status check
print('Number of Weekly MODIS-ET images:', weekly_EVI.size().getInfo())
print(weekly_ET.first().bandNames().getInfo())
print(f"Spatial resolution of the image: {weekly_ET.first().projection().nominalScale().getInfo()} meters")
print(f"CRS: {weekly_ET.first().projection().crs().getInfo()}")
print()

print('Number of Weekly MODIS-FPAR images:', weekly_EVI.size().getInfo())
print(weekly_FPAR.first().bandNames().getInfo())
print(f"Spatial resolution of the image: {weekly_FPAR.first().projection().nominalScale().getInfo()} meters")
print(f"CRS: {weekly_FPAR.first().projection().crs().getInfo()}")
print()

### GFSAD
# Define a function to reclassify the land cover values to:
# (0) no crops
# (1) irrigated crops
# (2) rainfed crops
def reclassify_gfsad_landcover(image):
  # Create a dictionary mapping old values to new values
  remap_values = {
      0: 0,  # Non-croplands remain 0
      1: 1,  # Irrigation major becomes irrigated (1)
      2: 1,  # Irrigation minor becomes irrigated (1)
      3: 2,  # Rainfed becomes rainfed (2)
      4: 2,  # Rainfed with minor fragments becomes rainfed (2) 
      5: 2,  # Rainfed with very minor fragments becomes rainfed (2)
  }

  # Use the remap() function to reclassify the image
  reclassified = image.remap(
      list(remap_values.keys()), list(remap_values.values())
  )

  reclassified = reclassified.rename(['crop'])

  return reclassified

# Load GFSAD data and reclassify input data
gfsad = reclassify_gfsad_landcover(ee.Image('USGS/GFSAD1000_V1'))

# status check
print(gfsad.bandNames().getInfo())
print(f"Spatial resolution of the GFSAD image: {gfsad.projection().nominalScale().getInfo()} meters")
print(f"CRS of GFSAD: {gfsad.projection().crs().getInfo()}")
print()

### CONSOLIDATE DATASETS
datasets = [daymet_weekly, weekly_EVI, weekly_ET, weekly_FPAR]
limit = 1245
limited_datasets = [col.limit(limit) for col in datasets]

# Combine the limited collections
merged_dataset = ee.ImageCollection(limited_datasets[0])
for img_set in limited_datasets[1:]:
  merged_dataset = merged_dataset.combine(img_set)

# Add gfsad band data to all images in the merged datasets
band_order = ['crop', 'dayl', 'prcp', 'srad', 'swe', 'tmax', 'tmin', 'vp', 'EVI', 'NDVI', 'ET', 'LE', 'PET', 'PLE', 'FPAR', 'LAI']
add_gfsad_bands = lambda img: img.addBands(gfsad)
reorder_bands = lambda img: img.select(band_order)
merged_dataset = merged_dataset.map(add_gfsad_bands)

# Skip week 71, reorder all bands; week 71 is missing FPAR data....
merged_dataset = merged_dataset.filter(ee.Filter.neq('system:index', '70')).map(reorder_bands)

print(merged_dataset.size().getInfo())
print(merged_dataset.first().bandNames().getInfo())
print()

# Ensure all images across all bands have consistent, common projection
# Since focusing on CONUS, use EPSG:3347 as default
target_projection_crs = ee.Projection('EPSG:3347') 
target_scale = 1000  # meters

def reproject_image(image):
    return image.reproject(crs=target_projection_crs, scale=target_scale)

merged_dataset = merged_dataset.map(reproject_image)

print(f"Spatial resolution of merged data image: {merged_dataset.first().projection().nominalScale().getInfo()} meters")
print(f"CRS: {merged_dataset.first().projection().crs().getInfo()}")
print()

##############################
##############################
##############################
# Export data to google drive
# testing with first 10 images
import time
ee.Authenticate()
ee.Initialize()

# Load the US states FeatureCollection
states = ee.FeatureCollection("TIGER/2018/States")

# Filter for Illinois
roi = states.filter(ee.Filter.eq('NAME', 'Illinois'))

# Apply preprocessing to the ImageCollection
def process_and_export(image):
    
    # Preprocess the image (clip to ROI, resample, and convert bands)
    clipped_image = image.clip(roi).toFloat().resample('bilinear')
    
    # Get the date from the image 
    date = ee.Date(image.get('system:time_start'))
    date_string = date.format('YYYY-MM-dd').getInfo()

    # Calculate the week number
    start_date = ee.Date('2000-02-18') 
    week_number = date.difference(start_date, 'week').add(1).getInfo()

    # Pad the week number with zeros to ensure it has four digits
    week_string = str(week_number).zfill(4)

    # Create an export task for each image
    task = ee.batch.Export.image.toDrive(
        image=clipped_image,
        description=f'california_{date_string}',
        folder='EarthEngineExports',
        fileNamePrefix=f'illinois_1kmx1km_{week_string}_{date_string}',
        crs='EPSG:3347',
        scale=1000,
        region=roi.geometry().bounds(),
        maxPixels=1e13,
        fileFormat='GeoTIFF'
    )
    
    task.start()
    print(f"Started export task for {date_string}. Task ID: {task.id}")

    return(task)

# Iterate over all images in the ImageCollection
tasks = []
full_list = merged_dataset.toList(merged_dataset.size())
#for i in range(merged_dataset.size().getInfo()):
#for i in range(100):
for i in range(merged_dataset.size().getInfo()):
    image = ee.Image(full_list.get(i))

    task = process_and_export(image)
    tasks.append((i, task))

    print(task.status())
    index = str(i + 1).zfill(4)
    print(index)
    print()

