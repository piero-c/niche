from mongoengine import DynamicDocument, connect

# Connect to your MongoDB database
connect('your_database_name')  # Replace with your actual database name

class Artist(DynamicDocument):
    meta = {
        'collection': 'artists',
        'indexes'   : [
            {
                'fields': ['genres.name']
            }
        ]
    }
