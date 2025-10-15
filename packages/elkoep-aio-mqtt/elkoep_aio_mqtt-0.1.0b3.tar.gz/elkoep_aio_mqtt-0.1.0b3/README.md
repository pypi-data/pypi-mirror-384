# elkoep-aio-mqtt

A library that provides a wrapper around Home Assistant's MQTT component for communication with [iNELS](https://www.inels.com/) devices by ElkoEP company.

This library is designed to run exclusively within Home Assistant and leverages Home Assistant's built-in MQTT functionality.

[Pypi](https://pypi.org/project/elkoep-aio-mqtt/)

# Install

This library is designed to be installed as a dependency for the iNELS integration for Home Assistant. It is not intended to run as a standalone.

# Development status

Supported RF devices

- Switches (01, 02)
- Shutters (03, 21)
- Light dimmers (04, 05)
- RGB light (06)
- Switches with external temperature sensors (07)
- Wireless thermovalves (09)
- Temperature sensors (10)
- Thermostats (12)
- Flood detectors (15)
- Generic detector (16)
- Motion detector (17)
- Controllers/buttons (18, 19)
- Temperature and humidity sensors (29)

Supported bus devices

- SA3-01B (100)
- DA3-22M (101)
- GRT3-50 (102)
- GSB3-90Sx (103)
- SA3-02B (104)
- SA3-02M (105)
- SA3-04M (106)
- SA3-06M (107)
- SA3-012M (108)
- SA3-022M (109)
- FA3-612M (111)
- RC3-610DALI (114)
- IM3_20B (115)
- IM3_40B (116)
- IM3_80B (117)
- DMD3-1 (120)
- IM3-140M (121)
- WSB3-20 (122)
- WSB3-40 (123)
- WSB3-20H (124)
- WSB3-40H (125)
- GCR3-11 (128)
- GCH3-31 (129)
- GSP3-100 (136)
- GDB3-10 (137)
- GSB3-40SX (138)
- GSB3-60SX (139)
- GSB3-20SX (140)
- GBP3-60 (141)
- GSB3-40-V2 (143)
- GSB3-60-V2 (144)
- GSB3-90-V2 (146)
- DAC3-04B (147)
- DAC3-04M (148)
- DCDA-33M (150)
- DA3-66M (151)
- DA3-03M/RGBW (153)
- ADC3-60M (156)
- TI3-10B (157)
- TI3-40B (158)
- TI3-60M (159)
- IDRT3-1 (160)
- JA3-018M (163)
- Virtual heating regulator (167)
- Virtual cooling regulator (168)
- SA3_014M (169)
- JA3_014M (170)
- MCD3-01 (171)
- PMS3-01 (172)
- GSB3-40Sx-V2 (174)
- GSB3-60Sx-V2 (175)
- GSB3-90Sx-V2 (176)
- MSB3-40 (177)
- MSB3-60 (178)
- MSB3-90 (179)
- GRT3-70 (180)
- GRT3-270 (180)
- BITS (bits)
- INTEGERS (integers)