#include <Arduino.h>
#include <ArduinoBLE.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h> 
// #include "/Users/carter/Downloads/logistic_regression_model.h"  // Include the header file with coefficients and intercept
#include "logistic_regression_model2.h"
#define CHARACTERISTIC_SIZE 100 // Adjusted size based on the data being sent // is this bytes?

BLEService sensorService("4fafc201-1fb5-459e-8fcc-c5c9c331914b");
BLECharacteristic combinedCharacteristic("beb5483e-36e1-4688-b7f5-ea07361b26a8", BLERead | BLENotify, CHARACTERISTIC_SIZE);

bool isConnected = false;
Adafruit_MPU6050 mpu;

const int windowSize = 154;
float ax[windowSize], ay[windowSize], az[windowSize];
int CurrIndex;

float shotSpeed; // Global variable to store shot speed

float AxMean, AxStdev, AxRMS, AxSkew, AxPeak;
float AyMean, AyStdev, AyRMS, AySkew, AyPeak;
float AzMean, AzStdev, AzRMS, AzSkew, AzPeak;

void setup(){

  pinMode(LED_BUILTIN, OUTPUT);  // For indicating errors using built-in LED

  if (!mpu.begin()) {
    while (1) {
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN)); // Blink the built-in LED
      delay(200);
    }
  }

  if (!BLE.begin()) {
    while (1) {
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN)); // Blink the built-in LED
      delay(1000);
    }
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_1000_DEG);

  BLE.setLocalName("Arduino");
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(combinedCharacteristic);
  BLE.addService(sensorService);
  BLE.advertise();
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {

    isConnected = true;

    while (central.connected()) {
      readSensorData();
      
      if (CurrIndex >= windowSize) {
        calculateStatistics();

        float prediction = makePrediction();

        if (prediction > 0.75){

          // Calculate shot speed
          float speed = calculateShotSpeed();

          // Format prediction as string
          char predictionStr[10];
          sprintf(predictionStr, "%f", prediction);

          // Format speed as string
          char speedStr[10];
          sprintf(speedStr, "%f", speed);

          // Concatenate prediction and speed into a single string
          char combinedStr[20]; // Adjust the size as needed
          sprintf(combinedStr, "%s:%s", predictionStr, speedStr);

          // Send the combined string over BLE
          combinedCharacteristic.writeValue(combinedStr);

        }
        CurrIndex = 0;
      }
      delay(10);  // Adjust delay
    }
    isConnected = false;
  }
}

void readSensorData() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  ax[CurrIndex] = ((a.acceleration.x + 156.96) / 313.92);
  ay[CurrIndex] = ((a.acceleration.y + 156.96) / 313.92);
  az[CurrIndex] = ((a.acceleration.z + 156.96) / 313.92);
  CurrIndex++;
}

void calculateStatistics() {
  // Mean
  AxMean = calculateMean(ax, windowSize);
  AyMean = calculateMean(ay, windowSize);
  AzMean = calculateMean(az, windowSize);

  // STD DEV
  AxStdev = calculateStandardDeviation(ax, windowSize, AxMean);
  AyStdev = calculateStandardDeviation(ay, windowSize, AyMean);
  AzStdev = calculateStandardDeviation(az, windowSize, AzMean);

  AxRMS = calculateRootMeanSquare(ax, windowSize);
  AyRMS = calculateRootMeanSquare(ay, windowSize);
  AzRMS = calculateRootMeanSquare(az, windowSize);

  AxSkew = calculateSkewness(ax, windowSize, AxMean, AxStdev);
  AySkew = calculateSkewness(ay, windowSize, AyMean, AyStdev);
  AzSkew = calculateSkewness(az, windowSize, AzMean, AzStdev);

  AxPeak = calculatePeakValue(ax, windowSize);
  AyPeak = calculatePeakValue(ay, windowSize);
  AzPeak = calculatePeakValue(az, windowSize);

}

float calculateMean(float data[], int size) {
  float sum = 0;
  for (int i = 0; i < size; i++) {
    sum += data[i];
  }
  return sum / size;
}

float calculateStandardDeviation(float data[], int size, float mean) {
  float variance = 0;
  for (int i = 0; i < size; i++) {
    variance += pow(data[i] - mean, 2);
  }
  return sqrt(variance / size);
}

float calculateRootMeanSquare(float data[], int size) {
  float sumOfSquares = 0;
  for (int i = 0; i < size; i++) {
    sumOfSquares += pow(data[i], 2);
  }
  return sqrt(sumOfSquares / size);
}

float calculateSkewness(float data[], int size, float mean, float stdev) {
  float sumCubedDeviation = 0;
  for (int i = 0; i < size; i++) {
    sumCubedDeviation += pow(data[i] - mean, 3);
  }
  float skewness = sumCubedDeviation / (size * pow(stdev, 3));
  return skewness;
}

float calculatePeakValue(float data[], int size) {
  float peak = data[0];
  for (int i = 1; i < size; i++) {
    if (data[i] > peak) {
      peak = data[i];
    }
  }
  return peak;
}

float calculateShotSpeed() {
  // Assuming each sample is 1 second apart
  float dt = 0.0064935065;

  // Calculate acceleration magnitude
  float accelerationMagnitude[windowSize];
  for (int i = 0; i < windowSize; i++) {
    accelerationMagnitude[i] = sqrt(pow(ax[i], 2) + pow(ay[i], 2) + pow(az[i], 2));
  }

  // Calculate shot speed
  float shotSpeed = 0;
  for (int i = 1; i < windowSize; i++) {
    shotSpeed += 0.5 * (accelerationMagnitude[i] + accelerationMagnitude[i - 1]) * dt;
  }

  return shotSpeed;
}

float makePrediction() {
  float input[] = { AxMean, AxStdev, AxRMS, AxSkew, AxPeak, AyMean, AyStdev, AyRMS, AySkew, AyPeak, AzMean, AzStdev, AzRMS, AzSkew, AzPeak };
  float logit = intercept;
  for (int i = 0; i < 15; i++) {
    logit += input[i] * coefficients[i];
  }
  float probability = 1 / (1 + exp(-logit));
  return probability;
}

