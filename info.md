# myPV

Home Assistant Component for myPV

<a href="https://github.com/dneprojects/mypv></a>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

### Installation

Copy this folder to '<config_dir>/custom_components/mypv/'.

### HACS

Search for integration 'myPV'

### Configuration

The integration is configurated via UI.
Enter an IP range, in which myPV devices will be detected.

### Features

The myPV custom integration works locally in the home network utilizing the http api. So it doesn't need any login.
- The integration is written to support multiple devices. However, it is only tested just with one (ELWA 2).
- It offers binary sensors and sensors for all data points provided by the myPV devices.
- The heating power can be set manually by an input number between 0 and 3600 W. This will turn on the heater for a predefined time period. This period has to been setup via web or cloud setup, as it is not supported by the myPV api.
- A second number input can be used to pass control to the local PID controller. It also takes values from 0 to 3600 W, but the actual power is controlled by the device itself.


