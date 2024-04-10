# Menu for the DATA Collection & Sensor Testing 
import tkinter as tk
from tkinter import ttk #PhotoImage
from tkinter import messagebox #simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler

# from bleak import BleakClient, BleakScanner
import pandas as pd
import os
import sys
import asyncio
from Data_Collection_UI.ConnectClass import ArduinoDataCollector
# import threading
# import time
# import numpy as np

device_name = "Arduino"
service_uuid = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
combined_characteristic_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
## Paths to Store Data and Cleaned data
PATH1 = "/Users/carter/Desktop/api_projects/first_api/cleaned_data"
PATH2 = "/Users/carter/Desktop/api_projects/first_api/data"

class SSM:
    def __init__(self, root):
        self.root = root
        self.root.geometry("980x600")
        
        self.root.title("Smart Stick Menu")
        self.root.resizable(False,False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        ###FILES
        self.files = [f for f in os.listdir(PATH1) if os.path.isfile(os.path.join(PATH1, f))]

        self.files_raw = [f for f in os.listdir(PATH2) if os.path.isfile(os.path.join(PATH2, f))]

        self.label_graph = tk.Label(root, text="Select a file to graph:")
        self.label_graph.grid(row=0, column=0)

        self.graph_button = tk.Button(root, text="Graph", command=self.process_and_plot_data, width=15, height=1)
        self.graph_button.grid(row=1, column=1, padx=8, pady=0)

        #self.files_raw = tk.StringVar() # This variable will hold the name of the chosen file
        self.dropdown_raw = ttk.Combobox(root, values=self.files_raw)
        self.dropdown_raw.grid(row=0, column=1)

        self.connect_button = tk.Button(root, text="Connect & Capture",command=self.connect_to_device, width=10, height=1)
        self.connect_button.grid(row=1, column=2, padx=5, pady=0)

        ## ADD all data into one csv file 
        self.concat_button = tk.Button(root, text="Concatenate All Data", command=self.concatenate_data, width=15, height=1)
        self.concat_button.grid(row=0, column=2, padx=10, pady=10)

        ##AXIS FOR CHARTS
        self.show_axis_vars = {
            'AX': tk.BooleanVar(value=True),
            'AY': tk.BooleanVar(value=True),
            'AZ': tk.BooleanVar(value=True),
            'GX': tk.BooleanVar(value=True),
            'GY': tk.BooleanVar(value=True),
            'GZ': tk.BooleanVar(value=True),
            'Stats': tk.BooleanVar(value=False)
        }
        self.show_all_axis = tk.BooleanVar(value=True)

        ##MOTION SELECTION MENU -- IN 1st LOG regression model (0,1) 0 = MISC 1 = SHOT 
        self.show_motions = {
            0: "Shot",
            1 : "Run w B",
            2 : 'Run n B',
            3 : 'Still',
            4 : 'GB',
            5 : 'Passing'
        }

        self.label_motion_grab = tk.Label(root, text="Motion Select:\n0:Shot\n1:Run w B\n2:Run n B\n3:Still\n4:GB\n5:Passing")
        self.label_motion_grab.grid(row=1, column=6)

        self.motion_grab = tk.StringVar()  # This variable will hold the name of the chosen file
        self.dropdown_motion = ttk.Combobox(root,width=5,textvariable=self.motion_grab, values=list(self.show_motions.keys()))
        self.dropdown_motion.grid(row=0, column=6, pady=0)

        ##USER INPUT FILE NAME -- To Name File When Testing
        self.label_file_name = tk.Label(root, text="File Name:")
        self.label_file_name.grid(row=1, column=4)

        self.hold_user_input_file_name = tk.StringVar()
        self.user_input_file_name = tk.Entry(root,textvariable=self.hold_user_input_file_name, width=10)
        self.user_input_file_name.grid(row=0, column=4, padx=5, pady=0)

        # USER TIME ENTRY 
        self.label_time_entry = tk.Label(root, text="Time Entry")
        self.label_time_entry.grid(row=1, column=5)

        self.hold_time = tk.IntVar()
        self.time_input_window = tk.Entry(root,textvariable=self.hold_time, width=3)
        self.time_input_window.grid(row=0, column=5)

        ###-----LIVE--CONNECT--BUTTON---###
        self.connect_live_button = tk.Button(root, text="Start Live Session",command=self.connect_live_to_dev, width=15, height=1)
        self.connect_live_button.grid(row=0, column=7)
        self.root.mainloop()

    def update_toclean_dropdown_menu(self):
        PATH2 = "/Users/carter/Desktop/api_projects/first_api/data"
        self.files_raw = [f for f in os.listdir(PATH2) if os.path.isfile(os.path.join(PATH2, f))]
        self.dropdown_raw["values"] = self.files_raw

    def save_to_cleaned_data(self, df, output_file):
        
        output_folder = "cleaned_data"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_path = os.path.join(output_folder, output_file)

        df.to_csv(output_path, index=False)

    def process_and_plot_data(self):
        # Get the file name
        name_to_clean = self.dropdown_raw.get()

        # Check if a file name is entered
        if not name_to_clean:
            messagebox.showwarning("Warning", "Please enter a file name.")
            return

        # Read the CSV file
        csv_clean = f"/Users/carter/Desktop/api_projects/first_api/data/{name_to_clean}"
        df = pd.read_csv(csv_clean)

        # Clean the data -- add this is to see scaled data. 
        #df = self.clean_data(df)
         
        # Plot the data
        self.plot_data(df, name_to_clean)

    def clean_data(self, df):
        # Columns for scaling
        accel_cols = ['AX', 'AY', 'AZ']
        gyro_cols = ['GX', 'GY', 'GZ']

        # Scale accelerometer and gyroscope data using StandardScaler
        scaler = StandardScaler()
        df[accel_cols] = scaler.fit_transform(df[accel_cols])
        df[gyro_cols] = scaler.fit_transform(df[gyro_cols])

        self.save_to_cleaned_data(df, output_file=self.dropdown_raw.get())

        return df

    def plot_data(self, df, name_to_clean):
        # Process the data for plotting

        # df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        # df['Timestamp'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()

        #time_x  = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()
        interval = 1
        df = df.iloc[::interval]

        # Create figure and axes objects
        fig, ax = plt.subplots(figsize=(7, 4)) #fits a 6,4 good at col = 0

        lines = []

        for column in df.columns:
            if column != 'Timestamp' and column in self.show_axis_vars and self.show_axis_vars[column].get():
                #line, = ax.plot(df['Timestamp'], df[column], label=column)
                line, = ax.plot(df.index, df[column], label=column)
                lines.append(line)

        # Include statistics on the plot if 'Stats' checkbox is checked
        if self.show_axis_vars['Stats'].get():
            max_values = "TEST__TEST__TEST"
            ax.text(4, 1, max_values, transform=ax.transAxes, verticalalignment='top')

        ax.set_xlabel('Freq')
        ax.set_ylabel('Values')
        ax.set_title(f'Data: {name_to_clean}')
        ax.legend(handles=lines, loc='upper right')

        ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=10))

        # Embed the plot in the tkinter window
        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=3, column=0, columnspan=6, padx=0, pady=8)
        canvas.draw()

        # Create checkboxes for axis visibility
        axis_frame = tk.Frame(self.root)
        axis_frame.grid(row=4, column=1, columnspan=3, padx=0, pady=10)

        tk.Checkbutton(axis_frame, text="All Axis", variable=self.show_all_axis, command=self.update_axis_checkboxes).grid(row=0, column=0, sticky='w')
        col = 1
        for idx, axis in enumerate(self.show_axis_vars.keys(), start=1):
            tk.Checkbutton(axis_frame, text=axis, variable=self.show_axis_vars[axis], command=self.update_plot).grid(row=0, column=col, sticky='w')
            col += 1
        
        plt.close(fig)

    def update_plot(self):
        self.process_and_plot_data()

    def update_axis_checkboxes(self):
        all_checked = self.show_all_axis.get()
        for axis in self.show_axis_vars:
            self.show_axis_vars[axis].set(all_checked)
        self.update_plot()


    def concatenate_data(self):
        #cleaned_folder = "cleaned_data"
        output_file = "multinominal_data_All.csv"
        PATHT = '/Users/carter/Desktop/api_projects/first_api/data/'
        cleaned_path = os.path.join(PATHT)

        # Get all CSV files in the cleaned_data folder
        csv_files = [f for f in os.listdir(cleaned_path) if f.endswith('.csv')]

        if not csv_files:
            messagebox.showwarning("Warning", "No CSV files found in the 'data' folder.")
            return

        # Concatenate all CSV files
        dfs = []
        for file in csv_files:
            df = pd.read_csv(os.path.join(cleaned_path, file))
            # Adjust timestamp based on the first data point's timestamp
            #df['Timestamp'] = (df['Timestamp'] - df['Timestamp'].iloc[0]) + dfs[-1]['Timestamp'].iloc[-1] if dfs else 0
            dfs.append(df)

        concatenated_df = pd.concat(dfs, ignore_index=True)

        # Save the concatenated data to a new CSV file
        output_path = os.path.join(cleaned_path, output_file)
        concatenated_df.to_csv(output_path, index=False)

        messagebox.showinfo("Information", "Data Concatenation Complete.")

    ###Connect function using class from ConnectClass.py

    def connect_to_device(self):
        get_motion = self.motion_grab.get()
        get_file_name = self.hold_user_input_file_name.get()
        get_time_capture = self.hold_time.get()
        if get_motion and get_file_name and get_time_capture:
            collector = ArduinoDataCollector(device_name,combined_characteristic_uuid, time_length=get_time_capture, csv_file_name=get_file_name, selected_motion=get_motion)
            #self.device_connected = True
            asyncio.run(collector.main())
            self.update_toclean_dropdown_menu()
            #self.live_plot()
        else:
            messagebox.showerror("Error", "Invalid Input")

    
    def connect_live_to_dev(self):
        print('TEST--Button clicked')

    def on_closing(self):
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
