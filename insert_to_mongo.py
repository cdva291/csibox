#inserting data in MongoDB
from pymongo import MongoClient
import dns
import wifi_csi_receiver

client = pymongo.MongoClient("mongodb://localhost", 27017)
try:
    print("Connected successfully!")
except:
    print("Could not  connect to MongoDB")

#database
db = client["csiboxDB"]
#Created or switched collection
collection = db["rssiA"]

# Insert Data  
list_rssiA = [

]
  
x = collection.insert_many(list_rssiA)
print(x)

