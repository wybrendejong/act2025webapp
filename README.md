# act2025webapp
This web application is an end product for the 2025 ACT project issued by Sogelink for WUR students.

The codebase is structured as follows:
- **main.py** - **Entry point** of the Web Application. Instantiates the application class and starts the application.
- src/**webapp.py** - Contains the application class, responsible for the ui and linking all functionality together.
- src/**data_loading.py** - Contains functions that load and pre-process the data.
- src/**classification.py** - Contains functions for training the classifier and making predictions.
- src/**mapping.py** - Contains functions for creating maps.

The directories data_exploration and data_enrichment contain python scripts and jupyter notebooks used for data exploration and analysis.

The user interface consists of two main parts: the map on the left and a sidepanel on the right. The sidepanel consists of three sections: the data inspection section, the model performance section and the upload file section. The data inspection section allows users to input a postal code. It then displays the probability of rats being present as well the historical rat sightings in the corresponding PC4 area. The model performance section shows the user the precision and recall scores of the model for the areas with rat sightings. A 'help' button in this section opens a dialog box that explains these metrics and how they should be interpreted.  

Finally, the upload file section contains a widget that allows users to upload an export of  the rat monitor as an excel file. On uploading a file, the data will be processed and the classification model will be trained. This process can take several minutes. Afterwards the webpage will reload and show the newly created prediction map. The first time the web application runs on a device, it will not have access to any rat monitor data. In this case, rat monitor data has to be uploaded before the map and the side panel show any data. This is also true when, upon a restart of the application, the loading of saved data fails for whatever reason.
