import os
import pandas as pd
import mysql.connector as connector
import sql_connect
import numpy as np
#lis

def get_state_code(state_name,conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT code FROM states WHERE name = %s;", (state_name,))
        result = cursor.fetchone()
        _=cursor.fetchall()# <-- Add this line
        return result[0] if result else None


def get_district_code(district_name,state_code,conn):
    with  conn.cursor() as cursor:
        cursor.execute("SELECT code FROM district WHERE name = %s and state_code = %s;", (district_name,state_code))
        result = cursor.fetchone()
        _=cursor.fetchall()
        return result[0] if result else None
    
def get_city_code(city_name,district_code, conn):
    with conn.cursor() as cursor:
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM city WHERE name = %s and district_code=%s;", (city_name,district_code))
        result = cursor.fetchone()
        _=cursor.fetchall()
        return result[0] if result else None

def insert_states(states,conn):
    cursor =  conn.cursor()
    for index, state in enumerate(states,start=1):
        try:
            cursor.execute("INSERT INTO states (code,name) VALUES (%s,%s);", (index,state))
            #print(f"Inserted '{state}', affected rows: {cursor.rowcount}")
        except Exception as e:
            print(f"Skipped '{state}' due to error: {e}")    
    conn.commit()
        

def insert_districts(districts,conn):
    state= list(districts.keys())[0]
    state_code = get_state_code(state,conn)
    with  conn.cursor() as cursor:
        for index, district in enumerate(districts[state],start=1):
            try:
                
                cursor.execute("INSERT INTO district (name,state_code) VALUES (%s,%s);", (district,state_code))
                #print(f"Inserted '{district}', affected rows: {cursor.rowcount}")
            except Exception as e:
                print(f"Skipped '{district}' due to error: {e}")    
        conn.commit()
    return state_code
        

def insert_cities(places,state_code,conn):
    with conn.cursor() as cursor:
        for key in places.keys():
            district_code  = get_district_code(key,state_code,conn)
            
            cities = places[key]
            for city,locality in cities.items():
                try:
                    cursor.execute("INSERT IGNORE INTO city (name,district_code) VALUES (%s,%s);", (city,district_code))
                    conn.commit()
                    city_code = get_city_code(city,district_code,conn)
                    for location in locality:
                        try:
                            cursor.execute("INSERT IGNORE INTO locality (name,city_code) VALUES (%s,%s);", (location,city_code))
                            conn.commit()
                        except Exception as e:
                            print(f"Skipped '{location}' due to error: {e}")

                except Exception as e:
                    print(f"Skipped '{city}' due to error: {e}")    
            
            
        
def insert_localities(places,state_code,conn):
    with conn.cursor() as cursor:
        for key in localities.keys():# things to do
            district_code = get_district_code(state_code,conn)
            city_code = get_city_code(key,conn) 
            for index, locality in enumerate(localities[key],start=1):    
                try:
                    cursor.execute("INSERT IGNORE INTO locality (name,city_code) VALUES (%s,%s);", (locality,city_code))
                    #print(f"Inserted '{locality}', affected rows: {cursor.rowcount}")
                    
                except Exception as e:
                    print(f"Skipped '{locality}' due to error: {e}")    
            conn.commit()

def get_region_info(file):
    df= pd.read_csv("c:/Indian's States/converted/"+file)
    valid_data = df.loc[4:]
    #print(valid_data.head())
    district_names= valid_data.iloc[:,2].unique()
    district = {file.split('.')[0]: district_names.tolist()} 
    cities = valid_data.groupby(valid_data.columns[2])[valid_data.columns[4]].unique()
    locality = valid_data.groupby(valid_data.columns[4])[valid_data.columns[7]].unique()
    places= {}
    for dis in district_names:
        if dis is not np.nan:
            places[dis]= {}
            city = cities[dis].tolist()
            for c in city:
                places[dis][c]=[]
                loc = locality[c].tolist()
                for l in loc:  
                    places[dis][c].append(l)
                
    return district,places


if __name__ == "__main__":
    states =[]
    files = [f for f in os.listdir("c:/Indian's States/converted") if f.endswith('.csv')]
    for file in files:
            state = file.split('.')[0]
            states.append(state)
    with sql_connect.connect_sql() as conn:
        insert_states(states,conn)
        
    with sql_connect.connect_sql() as conn:    
        for file in files:
            district,places = get_region_info(file)
            #print(locality)
            state_code= insert_districts(district,conn)
            insert_cities(places,state_code,conn)
            #insert_localities(places,state_code,conn)


