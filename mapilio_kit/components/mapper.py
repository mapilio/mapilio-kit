import json
import os
import webbrowser

import folium


def create_map(json_path, output_html='map.html', tile_type='cartodbdark_matter'):
    # Load JSON data
    with open(json_path) as f:
        data = json.load(f)

    # Create a map centered at the first location
    latitude = data[0]['latitude']
    longitude = data[0]['longitude']
    mymap = folium.Map(location=[latitude, longitude], zoom_start=14, tiles=tile_type)

    import_path = '/'.join(json_path.split('/')[:-1])

    # Add markers to the map
    for entry in data[:-1]:
        lat = entry['latitude']
        lon = entry['longitude']
        anomaly = entry['anomaly']
        filename = entry['filename']

        # Extract additional features
        capture_time = entry.get('captureTime', 'N/A')
        altitude = entry.get('altitude', 'N/A')
        heading = entry.get('heading', 'N/A')
        source = entry.get('source', 'N/A')
        orientation = entry.get('orientation', 'N/A')
        roll = entry.get('roll', 'N/A')
        pitch = entry.get('pitch', 'N/A')
        yaw = entry.get('yaw', 'N/A')
        car_speed = entry.get('carSpeed', 'N/A')
        device_make = entry.get('deviceMake', 'N/A')
        device_model = entry.get('deviceModel', 'N/A')
        image_size = entry.get('imageSize', 'N/A')
        fov = entry.get('fov', 'N/A')
        megapixels = entry.get('megapixels', 'N/A')
        vfov = entry.get('vfov', 'N/A')
        path = entry.get('path', 'N/A')

        # Define marker color based on anomaly
        color = 'green' if anomaly == 0 else 'red'

        # Format popup content
        popup_content = f"""
        <img src='{os.path.join(import_path, path, filename)}' width='200'><br>
        <b>Anomaly:</b> {anomaly}<br>
        <b>Filename:</b> {filename}<br>
        <b>Capture Time:</b> {capture_time}<br>
        <b>Latitude:</b> {lat}<br>
        <b>Longitude:</b> {lon}<br>
        <b>Altitude:</b> {altitude}<br>
        <b>Heading:</b> {heading}<br>
        <b>Source:</b> {source}<br>
        <b>Orientation:</b> {orientation}<br>
        <b>Roll:</b> {roll}<br>
        <b>Pitch:</b> {pitch}<br>
        <b>Yaw:</b> {yaw}<br>
        <b>Car Speed:</b> {car_speed}<br>
        <b>Device Make:</b> {device_make}<br>
        <b>Device Model:</b> {device_model}<br>
        <b>Image Size:</b> {image_size}<br>
        <b>FOV:</b> {fov}<br>
        <b>Megapixels:</b> {megapixels}<br>
        <b>VFOV:</b> {vfov}<br>
        """

        # Add a marker
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=color)
        ).add_to(mymap)

        logo_url = 'https://end.mapilio.com/app/default/assets/images/mapilio_white.png?v=1719386247'
        logo_html = f"""
        <div style="position: fixed; 
                    top: 50px; right: 50px; width: 100px; height: 100px; 
                    background-color: transparent; z-index:9999;
                   ">
           <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="160" height="38" viewBox="0 0 160 38"><defs><filter id="Path_43354" x="127.659" y="3.316" width="8.564" height="8.563" filterUnits="userSpaceOnUse"><feOffset dx="1" dy="1"></feOffset><feGaussianBlur stdDeviation="0.4" result="blur"></feGaussianBlur><feFlood flood-opacity="0.078"></feFlood><feComposite operator="in" in2="blur"></feComposite><feComposite in="SourceGraphic"></feComposite></filter></defs><g id="sales_logo" transform="translate(4562.563 -17888.262)"><g id="mapilio_sale_logo" transform="translate(-4700.469 17880.762)"><g id="Group_47609" data-name="Group 47609" transform="translate(138.405 8.004)"><path id="Path_423" data-name="Path 423" d="M428.228,406.676c-3.275-2.909-8.983-7.647-10.276-11.892h.009a10.794,10.794,0,1,1,20.534,0h.009c-1.292,4.244-7,8.982-10.276,11.892Zm.02-9.412a4.194,4.194,0,0,0,1.94-.459,5.121,5.121,0,0,0,1.586-1.272,6.27,6.27,0,0,0,1.085-1.877,6.592,6.592,0,0,0,.4-2.316,6.348,6.348,0,0,0-.4-2.232,5.738,5.738,0,0,0-1.085-1.836,5.416,5.416,0,0,0-1.586-1.231,4.194,4.194,0,0,0-1.94-.459,4.321,4.321,0,0,0-1.961.459,5.331,5.331,0,0,0-1.607,1.231,5.74,5.74,0,0,0-1.085,1.836,6.345,6.345,0,0,0-.4,2.232,6.589,6.589,0,0,0,.4,2.316,6.273,6.273,0,0,0,1.085,1.877,5.046,5.046,0,0,0,1.607,1.272A4.321,4.321,0,0,0,428.248,397.264Z" transform="translate(-310.928 -372.593)" fill="#0056F1" fill-rule="evenodd"></path><path id="Path_4134" data-name="Path 4134" d="M20015.98-22331.754v-29.2h5.633v2.807a7.6,7.6,0,0,1,6.592-3.146,10.687,10.687,0,0,1,4.252.859,10.945,10.945,0,0,1,3.486,2.332,11.069,11.069,0,0,1,2.336,3.449,10.428,10.428,0,0,1,.859,4.211,10.879,10.879,0,0,1-.859,4.3,10.911,10.911,0,0,1-2.336,3.479,10.828,10.828,0,0,1-3.486,2.336,10.62,10.62,0,0,1-4.252.859,7.875,7.875,0,0,1-5.135-1.656v-.039l2.09-3.812.045.043a5.588,5.588,0,0,0,2.291.5,5.819,5.819,0,0,0,2.3-.459,5.885,5.885,0,0,0,1.895-1.285,5.864,5.864,0,0,0,1.273-1.914,5.964,5.964,0,0,0,.461-2.348,5.754,5.754,0,0,0-.461-2.289,5.8,5.8,0,0,0-1.273-1.871,6.154,6.154,0,0,0-1.895-1.264,5.853,5.853,0,0,0-2.3-.459,5.777,5.777,0,0,0-2.316.459,5.861,5.861,0,0,0-1.852,1.252,6.047,6.047,0,0,0-1.258,1.867,5.691,5.691,0,0,0-.457,2.27v18.727Zm-19.152-8.848a10.657,10.657,0,0,1-3.414-2.295,10.816,10.816,0,0,1-2.32-3.42,10.38,10.38,0,0,1-.852-4.174,10.453,10.453,0,0,1,.852-4.209,10.886,10.886,0,0,1,2.32-3.426,10.965,10.965,0,0,1,3.414-2.312,10.35,10.35,0,0,1,4.176-.859,8.491,8.491,0,0,1,3.795.811,7.9,7.9,0,0,1,2.8,2.336v-2.807h5.461v20.855h-5.461v-10.453a5.634,5.634,0,0,0-.459-2.262,5.771,5.771,0,0,0-1.27-1.836,5.787,5.787,0,0,0-1.885-1.238,5.814,5.814,0,0,0-2.23-.437,5.513,5.513,0,0,0-2.25.459,6.471,6.471,0,0,0-1.861,1.234,5.456,5.456,0,0,0-1.27,1.848,5.683,5.683,0,0,0-.459,2.277,5.468,5.468,0,0,0,.459,2.221,5.742,5.742,0,0,0,1.27,1.844,6.273,6.273,0,0,0,1.861,1.258,5.545,5.545,0,0,0,2.25.459,4.925,4.925,0,0,0,2.213-.459h.041v.084l2.086,3.715-.045.039a7.967,7.967,0,0,1-5.045,1.584A10.464,10.464,0,0,1,19996.828-22340.6Zm60.5.5v-20.855h5.557v20.855Zm-8.047,0,.039-29.2h5.508v29.2Zm-8.057,0v-20.855h5.555v20.855Zm-58.615,0,.043-12.467a3.2,3.2,0,0,0-.246-1.248,3.761,3.761,0,0,0-.689-1.053,3.342,3.342,0,0,0-1.045-.729,3.117,3.117,0,0,0-1.275-.271,3.141,3.141,0,0,0-2.336.98,3.231,3.231,0,0,0-.959,2.32v12.467h-5.551v-12.467a3.132,3.132,0,0,0-.252-1.248,3.3,3.3,0,0,0-.707-1.053,3.314,3.314,0,0,0-1.061-.709,3.526,3.526,0,0,0-1.359-.25,2.931,2.931,0,0,1-.375-.621c-.223-.416-.475-.865-.75-1.367q-.463-.867-1.127-1.984l.041-.086a6.255,6.255,0,0,1,3.961-1.41,6.437,6.437,0,0,1,3.8,1.041,7.125,7.125,0,0,1,2.254,2.564,3.466,3.466,0,0,1,.33-.5,8.2,8.2,0,0,1,2.65-2.318,6.583,6.583,0,0,1,3.113-.791,6.632,6.632,0,0,1,3.313.771,6.467,6.467,0,0,1,2.188,2.023,8.724,8.724,0,0,1,1.211,2.82,13.467,13.467,0,0,1,.375,3.146v12.434Zm-24.156,0v-20.855H19964v20.855Zm98.875-24.324v-4.879h5.557v4.879Zm-16.1,0v-4.879h5.555v4.879Z" transform="translate(-19958.447 22369.301)" fill="#fff"  stroke-width="1"></path></g></g></g></svg>
        </div>
        """
        logo_element = folium.Element(logo_html)
        mymap.get_root().html.add_child(logo_element)
    # Save the map to an HTML file
    mymap.save(output_html)

    # Open the map in a web browser
    webbrowser.open('file://' + os.path.realpath(output_html))

if __name__ == '__main__':
    # Call the function with the path to the JSON file
    create_map(
        '/home/visio-ai/PycharmProjects/mapilio-kit/videos/mapilio_sampled_video_frames/mapilio_image_description.json')
