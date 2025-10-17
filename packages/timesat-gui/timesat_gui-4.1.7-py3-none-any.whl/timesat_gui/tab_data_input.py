from dash import dcc, html
from dash.dependencies import Input, Output, State
import folium
import os
import base64
import numpy as np
import rasterio
from rasterio.warp import transform_bounds, transform
import tempfile
import matplotlib.pyplot as plt

# Layout for the Data Input tab
layout_data_input = html.Div([
    html.H3("Upload File List of GeoTIFFs:"),
    dcc.Upload(
        id='upload-file-list',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='file-path', style={'margin': '10px'}),
    dcc.Dropdown(id='image-dropdown', style={'width': '50%', 'margin': '10px'}),

    html.Div(id='output-map', style={'height': '500px'})
])

# Function to reproject GeoTIFF bounds from the original CRS to EPSG:4326 (WGS 84)
def reproject_bounds_to_epsg4326(src):
    bounds = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
    return bounds

# Function to reproject lat/lon to GeoTIFF CRS
def latlon_to_tiff_coordinates(lat, lon, src):
    tiff_crs = src.crs
    x, y = transform('EPSG:4326', tiff_crs, [lon], [lat])
    return x[0], y[0]

# Function to extract pixel values from a list of GeoTIFFs
def extract_pixel_values(geotiff_paths, lat, lon):
    pixel_values = []
    for path in geotiff_paths:
        with rasterio.open(path) as src:
            tiff_x, tiff_y = latlon_to_tiff_coordinates(lat, lon, src)
            row, col = src.index(tiff_x, tiff_y)
            value = src.read(1)[row, col]
            pixel_values.append(value)
    return pixel_values

# Callback for uploading and parsing the file list
def register_data_input_callbacks(app):
    @app.callback(
        [Output('image-dropdown', 'options'),
         Output('file-path', 'children')],
        [Input('upload-file-list', 'contents')],
        [State('upload-file-list', 'filename')]
    )

    def parse_file_list(contents, filename):
        if contents:
            # Create the 'uploads' directory if it doesn't exist
            if not os.path.exists("uploads"):
                os.makedirs("uploads")

            # Decode the base64-encoded contents
            _, content_string = contents.split(',')
            
            # Define the path where the file should be saved
            filelist_path = os.path.join("uploads", filename)
            
            # Save the uploaded file to the 'uploads' directory
            with open(filelist_path, "wb") as f:
                f.write(base64.b64decode(content_string))

            # Check if the file was saved successfully
            if os.path.exists(filelist_path):
                print(f"File saved successfully to {filelist_path}")
            else:
                print(f"Failed to save file to {filelist_path}")

            # Now attempt to open and read the saved file
            try:
                with open(filelist_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()

                num_images = int(lines[0].strip())
                image_paths = [line.strip() for line in lines[1:num_images + 1]]

                options = [{'label': os.path.basename(path), 'value': path} for path in image_paths]

                # Return dropdown options and display file path
                return options, html.Div(f"Uploaded file list: {os.path.abspath(filelist_path)}")

            except FileNotFoundError:
                print(f"File not found: {filelist_path}")
                return [], html.Div(f"Error: Could not find file {filelist_path}")

        return [], ""


    # Callback for updating the map
    @app.callback(
        [Output('output-map', 'children')],
        [Input('image-dropdown', 'value')]
    )
    def update_map(selected_image):
        if selected_image:
            with rasterio.open(selected_image) as src:
                bounds_epsg4326 = reproject_bounds_to_epsg4326(src)
                band1 = src.read(1)

                # Check for the NoData value
                nodata_value = src.nodata

                if nodata_value is not None:
                    # Set NoData values to np.nan
                    band1 = np.where(band1 == nodata_value, np.nan, band1)
                
                # Normalize the band to 0-255 and use 'jet' colormap
                band1_norm = np.interp(band1, (np.nanmin(band1), np.nanmax(band1)), (0, 255)).astype(np.uint8)
                temp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                plt.imsave(temp_img.name, band1_norm, cmap="jet")

            # Calculate map center as the midpoint of bounds
            map_center = [(bounds_epsg4326[1] + bounds_epsg4326[3]) / 2, (bounds_epsg4326[0] + bounds_epsg4326[2]) / 2]
            map_zoom = 10  # Set a moderate zoom level based on the extent of the image

            m = folium.Map(location=map_center, zoom_start=map_zoom)
            m.add_child(folium.LatLngPopup())

            folium.TileLayer(
                tiles='http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr="Google", name="Google Satellite", max_zoom=20, subdomains=["mt0", "mt1", "mt2", "mt3"]
            ).add_to(m)

            # Lock opacity to 0.7
            folium.raster_layers.ImageOverlay(
                image=temp_img.name,
                bounds=[[bounds_epsg4326[1], bounds_epsg4326[0]], [bounds_epsg4326[3], bounds_epsg4326[2]]],
                opacity=0.6,
                interactive=True,
                cross_origin=False,
                zindex=1,
            ).add_to(m)

            m.fit_bounds([[bounds_epsg4326[1], bounds_epsg4326[0]], [bounds_epsg4326[3], bounds_epsg4326[2]]])

            m.save('map.html')
            map_iframe = html.Iframe(srcDoc=open('map.html', 'r').read(), width="100%", height="500px")
            return [map_iframe]
        return [html.Div("Please select an image from the dropdown menu")]

    # Callback for extracting pixel values on map click
    @app.callback(
        Output('pixel-values-store', 'data'),
        Input('clicked-location', 'data'),
        State('image-dropdown', 'value')
    )
    def extract_pixel_values_on_click(clicked_location, selected_image):
        if clicked_location and selected_image:
            lat, lon = clicked_location['lat'], clicked_location['lng']
            with rasterio.open(selected_image) as src:
                tiff_x, tiff_y = latlon_to_tiff_coordinates(lat, lon, src)
                try:
                    row, col = src.index(tiff_x, tiff_y)
                    value = src.read(1)[row, col]
                    return {'lat': lat, 'lon': lon, 'value': value}
                except (IndexError, ValueError):
                    # Return None if the pixel coordinates are out of bounds
                    return {'lat': lat, 'lon': lon, 'value': None}
        return {'lat': None, 'lon': None, 'value': None}

