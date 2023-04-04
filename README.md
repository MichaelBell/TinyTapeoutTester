# Tiny Tapeout Tester

Test your Tiny Tapeout design interactively by wiring it up to a Pico W running Micropython.

## Setup

The pins used to communicate with the Tiny Tapeout are specified in `tt.py`, by default they are:

| Inputs to TT | Outputs from TT |
| ------------ | --------------- |
| Clock: 12    | Clock: 9 |
| Data: 13     | Data: 8 |
| Latch En: 11 | |
| Scan Sel: 10 | |

The length of the scan chain is also specified in `tt.py`, you will need to set that correctly for your test environment or the Tiny Tapeout chip you are testing against.

Load the files on to a Pico W running Micropython and create a `secrets.py` specifying:
    wlan_ssid = "Your SSID"
    wlan_password = "Your password"

Upload all the files in the repo to your Pico W, and then launch `tt_main.py`.  When it connects it will log the IP address.  Open that in a web browser.
For example, if the IP address is 192.168.0.153 go to http://192.168.0.153/

## Usage

Select the number of the design you wish to interact with.  Input the byte you want to send to the design in binary and click Send.

The byte will be sent down the scan chain to the selected design and latched in.  Then the output fom your design is scanned, and shifted out.

The resulting byte of output is displayed in binary.

Many Tiny Tapeout designs are clocked using input 0.  To aid with sending data to these designs you can tick the Clock setting.  When ticked, each time you hit send two bytes will be sent to the selected design.

The first byte is sent with bit 0 set to 0, and the second with bit 0 set to 1.  This means the design sees stable inputs over a rising edge of the clock, allowing it to read the remaining inputs.  
The design output from after the second byte was latched in is displayed.

## Licensing and attributions

Except as otherwise noted, code is Copyright (c) 2023 Michael Bell and licensed under the Apache License v2.0.

The Tiny Tapeout logo belongs to the Tiny Tapeout project and is included with permission from Matt Venn.

The web framework phew is from Pimoroni.

The CSS was inspired by [this example](https://codepen.io/ainalem/pen/GRqPwoz), Copyright (c) 2023 by Mikael Ainalem and used under the MIT license.