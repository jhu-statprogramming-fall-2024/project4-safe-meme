### 140.777.P4
### Our Changing Climate: A Geospatial Analysis of the Impact of Climate Change on Regional Cropland Health and Productivity
#### November 15, 2024

**Team Members:** Sara Hunsberger, Fernanda Montoya, Meklit Yimenu, Meucci Ilunga

**Project Goal:** To analyze the impact of climate change on cropland health and productivity using publicly available geospatial datasets.

**Project Description:**

This repository contains the code and data for our Project 4 submission in JHU-BSPH 140.777. Our project focuses on investigating how variations in climate (temperature, precipitation, etc) over the last 25 years have impacted global and regional cropland health and productivity over time. We aim to develop a basic descriptive model to identify future trends and risks associated with climate change and cropland.

**Core Programming Paradigms:**

* **Functional Programming:** For data cleaning, processing, and analysis.
* **Object oriented programming**: Python-based implementation for use in accessing datasets through Google Earth Engine API.   

**Data Acquisition**

The project will primarily use three data sources: cropland data, vegetation data, and climate data.

*   **Cropland Data:** This data will map out where cropland is in the United States. We will use the USDA NASS Cropland Data Layers or the global food support analysis data available from Earth Engine. Both datasets are considered public domain and can be retrieved with API calls from Earth Engine.
    
*   **Vegetation Data:** We will use MODIS data from Earth Engine, which also has no restrictions on use. This data includes the Normalized Difference Vegetation Index (NDVI), Enhanced Vegetation Index (EVI), and Terra MODIS Vegetation Continuous Fields as metrics to understand vegetation health in different areas.
    
*   **Climate Data:** We will use the PRISM Daily Spatial Climate Dataset from Earth Engine, which has no relevant restrictions on use. This dataset includes data on temperature and precipitation for different areas in the US.

Data acquisition will involve retrieving excerpts via API calls from Earth Engine combining them for analysis. Specifically, we will use the 'rgee' package in R or the equivalent for Python to interact with the Earth Engine API. This will allow us to access and download the necessary data for our analysis.

**Tentative Timeline:**
* **Week 1 (11/18):** Data extraction, processing, and exploratory analysis.
* **Week 2 (11/25):** Data analysis and visualization.
* **Week 3 (12/2):** Model development, evaluation, and analysis write-up.
* **Week 4 (12/9):** Finalize analysis and prepare presentation.
* **Week 5 (12/16):**  Finalize presentation and project report.

**Tentative Repository Structure:**
* **proposal:** Contains the project proposal source documents.
* **data:** Contains select raw and processed data files.
* **scripts:** Contains the R scripts for data cleaning, analysis, and visualization. This will include scripts to calculate the Normalized Difference Vegetation Index (NDVI) and other relevant metrics.
* **presentation:** Contains the final project presentation slides and any supporting materials.
* **report:** Contains the final project report in PDF format.

**Key Deadlines**
*   **Project Proposal:** November 15th, 2024
*   **Project Presentation:** December 11th, 2024
*   **Final Project Write-up and Group Evaluation:** December 19th, 2024

This repository will be updated regularly with our progress throughout the project.
