
# plane-side

A voting system so people can crowdsource their opinion on which side of a place offers best view for travelling to a certain airport. 

This app uses Flask-Python in the backend, SQLite for Modeling, and Html/CSS/AJAX/Jquery for the Views. 

The app offers an external API. You can request your key with 500 requests per month. 

How to use our API:  
Make a URL Request to 
http://localhost:5000/api/?key={Your API-KEY}&iata={IATA-Code for the Airport you Want} 
The output will be a JSON with {"IATA Code": "Best Side"}

Only IATA codes are available for requests at this moment. 

Please install all the requirements in the file requirements.txt to properly run the app. 
