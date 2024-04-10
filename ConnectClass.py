import asyncio
from bleak import BleakClient, BleakScanner
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from tkinter import simpledialog, messagebox
import csv
import time
import os

device_name = "Arduino"
service_uuid = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
combined_characteristic_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
PATH= "/data"

class ArduinoDataCollector:
    def __init__(self, device_name, combined_characteristic_uuid, time_length=None, csv_file_name=None, selected_motion=None):
        self.device_name = device_name
        self.combined_characteristic_uuid = combined_characteristic_uuid
        self.csv_file_name = csv_file_name
        self.selected_motion = selected_motion
        self.time_length = time_length
        self.data_collection = []
        self.is_connected = False
        self.latest_data = None

    def prompt_csv_filename(self):  ##we can either pass it through in init or we can prompt if None
        if self.csv_file_name is None:
            messagebox.showerror("Error", "Invalid csv file name")
            #csv_file_name = input("Enter a file name:")
        else:
            self.csv_file_name = os.path.join(PATH, f"{self.csv_file_name}.csv")

    def prompt_movement_type(self):
        if self.selected_motion is None:
            messagebox.showerror("Error", "Invalid Movement")
            #movement_type = int(input("Enter the Movement Type (1=shot, 2=pass, 3=switch hands, 4=running, 5=dodge, 6=orient, 7=groundBall):"))
        movement_type = self.selected_motion
        return movement_type
    
    def write_header_to_csv(self):
        with open(self.csv_file_name, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            header = ["AX", "AY", "AZ", "GX", "GY", "GZ", "Movement_Type"]
            csv_writer.writerow(header)

    async def find_device(self):
        SearchCount = 0
        while True:
            devices = await BleakScanner.discover()
            #print(devices)
            target_device = next((device for device in devices if device.name == self.device_name), None)
            if target_device:
                return target_device
            else:
                SearchCount += 1
                if SearchCount >= 3:
                    self.is_connected = False
                    messagebox.showerror("Error", f"Make sure Stick:({device_name}) is turned on and in range")
                    break
                await asyncio.sleep(0.1)

    async def data_callback(self, sender: int, data: bytearray):
        #timestamp = time.time()
        data_str = data.decode("utf-8")
        data_list = [float(x) for x in data_str.split(",")]
        if len(data_list) == 6:
            ax, ay, az, gx, gy, gz = data_list
            #print(f'{ax},{ay},{az},{gx},{gy},{gz}')
            #self.latest_data = (ax, ay, az, gx, gy, gz)
            #print(data_list)
            self.write_to_csv(data_list)
        else:
            print("Warning: Unexpected data format")
            return

        await asyncio.sleep(0.1)

    def write_to_csv(self,data):
        self.data_collection.append([*data])
    
    async def main(self):
        time1 = self.time_length
        time1 = float(time1)

        self.prompt_csv_filename()

        self.prompt_movement_type()

        self.write_header_to_csv()

        device = await self.find_device()
        if not device:
            print(f"Device '{self.device_name}' not found")
            return

        async with BleakClient(device.address) as client:
            print(f"Connected to {self.device_name}")
            await client.start_notify(self.combined_characteristic_uuid, self.data_callback)
            await asyncio.sleep(time1)  # Collect data for 
            await client.stop_notify(self.combined_characteristic_uuid)
            print("Disconnected")
            self.is_connected = False
        if self.data_collection:
            with open(self.csv_file_name, "a", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                for row in self.data_collection:
                    row.append(self.selected_motion)
                    csv_writer.writerow(row)
            
            messagebox.showinfo("Information", "Data Collection Complete & Saved")

if __name__ == "__main__":
    collector = ArduinoDataCollector(device_name, combined_characteristic_uuid)