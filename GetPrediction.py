## Written by Carter L.
## Code connects to a BLE device and waits for data to be sent
## Will output data to terminal 

import asyncio
from bleak import BleakClient, BleakScanner

device_name = "Arduino"
service_uuid = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
combined_characteristic_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

class ArduinoLive:
    def __init__(self, device_name, combined_characteristic_uuid, intercept):
        self.device_name = device_name
        self.combined_characteristic_uuid = combined_characteristic_uuid
        self.is_connected = False
        self.latest_data = None
        self.intercept = intercept
        self.shot_count = 0  # Initialize shot count\
        

    async def find_device(self):
        try:
            devices = await BleakScanner.discover(timeout=3)
            target_device = next((device for device in devices if device.name == self.device_name), None)
            if target_device:
                self.is_connected = True
                return target_device
            else:
                self.is_connected = False
                #print('Device not found')
                return None
        except Exception as e:
            print(f"Error during device discovery: {e}")
            return None

    async def data_callback(self, sender: BleakClient, data: bytearray):
        try:
            data_str = data.decode("utf-8")
            data_list = [float(x) for x in data_str.split(":")]
            #print(data_list)
            gesture_probability = data_list[0]
            shot_speed = data_list[1]
            #print(gesture_probability)
            if (gesture_probability > 0.7):
                #print(gesture_probability)
                #shot_speed_mph = shot_speed * 2.23694
                #formatted_shot_speed = "{:.2f}".format(shot_speed_mph)
                self.shot_count += 1  # Increment shot count
                print(f"Shot_Count: {self.shot_count}")
                #print(f"Formatted shot speed: {formatted_shot_speed}")
                print(f"shot_speed: {shot_speed}")
            #print(f"0: {gesture_probability:.3f}")
        except Exception as e:
            print(f"Error in data callback: {e}")

    async def main(self):
        while True:
            device = await self.find_device()
            if not device:
                print(f"Device '{self.device_name}' not found")
                await asyncio.sleep(1)
                continue

            try:
                async with BleakClient(device.address) as client:
                    print(f"Connected to {self.device_name}")
                    self.is_connected = True

                    # Start notifications and keep the connection alive
                    await client.start_notify(self.combined_characteristic_uuid, self.data_callback)

                    # Keep the main loop running until the connection is broken
                    while client.is_connected:
                        await asyncio.sleep(0.1)
 
            except Exception as e:
                print(f"Error during BLE operation: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    intercept = -0.8320081659902461 
    collector = ArduinoLive(device_name, combined_characteristic_uuid, intercept=intercept)
    asyncio.run(collector.main())



