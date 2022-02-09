import wifiCsiReceiver
import numpy as np
import matplotlib.pyplot as plt
from pymongo import MongoClient
from datetime import date
from dateutil import parser
import pandas as pd

client = pymongo.MongoClient('mongodb://localhost', 27017)
db = client.csiboxDB

db.command('create', 'amplitude', timeseries={ 'timeField': 'timestamp', 'metaField': 'data', 'granularity': 'hours' })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='query datas')
    parser.add_argument('--date',
                        type=integer,
                        default="today",
                        help='Select date for analyzing')    
    parser.add_argument('--start_time',
                        type=integer,
                        default="now",
                        help='Select start time interval')
    parser.add_argument('--end_time',
                        type=interger,
                        default="now",
                        help='Select end time interval')
    parser.add_argument('--time_granularity',
                        type=str,
                        default="hours",
                        help='Select time granularity')
    
    args = parser.parse_args()
    #date = date.now.strftime(
    #    %H:%M:%S