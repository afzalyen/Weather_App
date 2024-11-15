import requests
import psycopg2
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import unicodedata

#Information of Database
DB_Info = {
    'dbname': 'weather_app',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost'
}

#Removing special character from City Name
def filer_city_name(city):
    return unicodedata.normalize('NFKD', city).encode('ASCII', 'ignore').decode('utf-8')


#Get the City's weather information through API
def get_weather_from_API(city):
    api_url = "http://api.openweathermap.org/data/2.5/weather"
    api_key = "11b1017cc012b0592cc171abbc7b2f3b"

    params = {'q': city, 
              'appid': api_key, 
              'units': 'metric'
              }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
       
        return {
            'city': filer_city_name(data['name']),
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'response' : str(data)
        }
    else:
        return None


#Insert the searched City's weather information in the DB
def insert_into_db(city, temperature, description,response):
    query = f'''
    INSERT INTO weather_data (city, temperature, description, created_at, response) 
    VALUES (%s, %s, %s, %s, %s)
    '''
    current_time = datetime.now()
    data = (city, temperature, description, current_time, response)
    
    try:
        conn = psycopg2.connect(**DB_Info)
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()

    except:
        messagebox.showerror("Error while inserting the data in DB")

    finally:
        cursor.close()
        conn.close()

#return data from DB depedning on limit  
def select_from_db(city):
    records = []
    try:
        #use ilike in filtering city to handle uppercase or lowercase letter
        query = f'''
        SELECT city, temperature, description, to_char(date_trunc('second', created_at), 'YYYY-MM-DD HH24:MI:SS') AS Time
        FROM weather_data 
        WHERE city ilike %s 
        ORDER BY created_at DESC
        '''

        conn = psycopg2.connect(**DB_Info)
        cursor = conn.cursor()
        cursor.execute(query, (city,))
        records = cursor.fetchall()


    except:
        messagebox.showerror("Error while searching the data in DB")

    finally:
        cursor.close()
        conn.close()
    return records




#show result of search
def show_result(records):
    for item in tree.get_children():
        tree.delete(item)

    for city, temperature, description, time in records:
        tree.insert("", tk.END, values=(city, temperature, description, time))


#Get the current weather of the city through API response, insert into database and show result
def get_current_weather():
    city = city_entry.get()
    if city:
        weather = get_weather_from_API(city)
        if weather:
            insert_into_db(weather['city'], weather['temperature'], weather['description'], weather['response'])
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records = [(weather['city'], weather['temperature'], weather['description'],current_time)]
            show_result(records)
        else:
            messagebox.showerror("Error", f"Could not retrieve data for {city}.")
    else:
        messagebox.showwarning("Input Error", "Please enter a city name.")


#Get the previous all searched records of that City
def get_previous_records():
    city = city_entry.get()
    if city:
        records = select_from_db(city) 

        if records:
            show_result(records)
        else:
            messagebox.showinfo("No Data", f"No previous records found for {city}.")
    else:
        messagebox.showwarning("Input Error", "Please enter a city name.")





#APP config
root = tk.Tk()
root.title("Weather App")
root.geometry("800x400")
root.configure(bg="#f0f4f7")

#Style for the table and widgets
style = ttk.Style()
style.configure("Treeview", font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
style.configure("TButton", font=("Arial", 10))

#TopFrame
top_frame = tk.Frame(root, bg="#f0f4f7")
top_frame.pack(pady=10)

#City entry
tk.Label(top_frame, text="City Name:", font=("Arial", 12), bg="#f0f4f7").grid(row=0, column=0, padx=5, pady=5)
city_entry = tk.Entry(top_frame, font=("Arial", 12))
city_entry.grid(row=0, column=1, padx=5, pady=5)

#search buttons
button_frame = tk.Frame(top_frame, bg="#f0f4f7")
button_frame.grid(row=0, column=2, padx=10, pady=5)

#current weather button
current_weather_button = ttk.Button(button_frame, text="Current Weather", command=get_current_weather, style="TButton")
current_weather_button.grid(row=0, column=0, padx=5)

#previous record button
previous_records_button = ttk.Button(button_frame, text="Previous Records", command=get_previous_records, style="TButton")
previous_records_button.grid(row=0, column=1, padx=5)

#Table config
columns = ("City", "Temperature (°C)", "Description", "Time")
tree = ttk.Treeview(root, columns=columns, show="headings", height=10)
tree.heading("City", text="City", anchor="w")
tree.heading("Temperature (°C)", text="Temperature (°C)", anchor="w")
tree.heading("Description", text="Description", anchor="w")
tree.heading("Time", text="Time", anchor="w")

#left allignment
tree.column("City", anchor="w")
tree.column("Temperature (°C)", anchor="w")
tree.column("Description", anchor="w")
tree.column("Time", anchor="w")

tree.pack(pady=10, fill="x")

#initially empty table
show_result([])

root.mainloop()
