# myPV

Home Assistant Component for myPV

<a href="https://github.com/dneprojects/mypv"></a>

<p align="center">
  <a href="https://github.com/custom-components/hacs"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg"></a>
  <img src="https://img.shields.io/github/v/release/dneprojects/mypv" alt="Current version">
</p>

## Installation

### HACS (recommended)

Add user defined repository 'https://github.com/dneprojects/mypv' for type integration.
Search for integration 'myPV', use the three dot menu on the right side to download.
Restart Home Assistant.
Add integration 'myPV' in the settings

### Manual download

Copy this folder to 'config/custom_components/mypv'.
Restart Home Assistant.
Add integration 'myPV' in the settings section.

## Configuration

The integration is configurated via UI.
Enter an IP range, in which myPV devices will be detected.

## Features

The myPV custom integration works locally in the home network utilizing the http api. So it doesn't need any login.
- The integration is written to support multiple devices. However, it is only tested just with one (ELWA 2).
- It offers binary sensors and sensors for all data points provided by the myPV devices.
- The heating power can be set manually by an input number between 0 and 3600 W. This will turn on the heater for a predefined time period. This period has to been setup via web or cloud setup, as it is not supported by the myPV api.
- A switch can be used to pass control to the local PID controller. The actual heating power is controlled by the device itself. This mode also depends on the configured time period.

## Credits

This integration is based on an implementation https://github.com/zaubererty/homeassistant-mvpv.
Although it worked fine, the main feature, controlling the device by home assistant automations was not possible.
So I totally rewrote the integration. 
However, thanks to the work of zaubererty at this place!
