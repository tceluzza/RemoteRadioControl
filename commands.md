# CI-V Commands for the IC-7300

A pared-down selection of controls that I would like to be able to access with a single touch on the 7300. These 

## General format of CI-V commands

Controller to IC-7300
1. Preamble: `FE FE`
2. Transceiver address: `94` (default)
3. Controller address: `E0` (default)
4. Command number (Cn)
5. Sub-command number(s) (Sc)
6. Data (if applicable)
7. End-of-message: `FD`

IC-7300 to controller
* flip (2) and (3)
* OK or NG message:
    * Command is replaced with `FB` or `FA` respectively
    * Think "FB" as in "fine business"

## Knob-based controls
* VFO Control
    1. Read operating frequency: Cn `03` (see below for data)
    2. Set operating frequency: Cn `05` (see below for data)
    3. Read/Set selected/unselected VFO:
        * Cn `25`
        * Sc `00` for selected VFO, `01` for unselected VFO
        * Data: see below
* filter width
    * Cn `1A`
    * Sc `03`
    * Data: `00-31` where `00` = 50 Hz and `31` = 2700 Hz
* power output
    * Cn `14`
    * Sc `0A`
    * Data: `0000-0255` as big-endian packed BCD between 0 and 255

## Button-based controls
* mode
    * I might wait to implement this. This will probably be CW-only to start.
    1. Read operating mode: Cn `04` (see below for data)
    2. Set operating mode: Cn `06` (see below for data)
    3. Set/read operating mode for (un)selected VFO: Cn `26`
* band
    * I will probably just hard-code some frequencies in and use Cn `05` to jump to that rather than use the band-stacking register
* QSK
    * Cn `16`
    * Sc `47`
    * Data
        * `00` = OFF
        * `01` = Semi
        * `02` = Full
* tune
    * Cn `1C`
    * Sc `01`
    * Data `02` ("Send/read to tuning")
* tune rate
    * Handled in software


### Operating frequency data content
* 5 bytes of data
* Each nibble is 0-9 (little-endian packed binary-coded decimal/BCD):
    1. 10 Hz & 1 Hz
    2. 1 kHz & 100 Hz
    3. 100 kHz & 10 kHz
    4. 10 MHz & 1 MHz
    5. 1 GHz & 100 MHz (always `00` for the IC-7300)
* e.g. 14,074.512 kHz: `12 45 07 14 00`

### Mode data content
* 2 bytes of data
    1. Operating mode
        
        | byte | mode |
        | :---: | :---: |
        | 00 | LSB |
        | 01 | USB |
        | 02 | AM |
        | 03 | CW |
        | 04 | RTTY |
        | 05 | FM |
        | 07 | CW-R |
        | 08 | RTTY-R |
    2. Filter setting `01-03` (can be omitted; will select FIL1)

## Random notes that I might want to reference later....

    • Operating frequency
•
Command: 00, 03, 05, 1C 03

dxc change freq
cmd 05 - change
cmd 25 00 fd (check freq of selected vfo)
- reply 25 00 02 45 07 14 00 fd
cmd 1a 05 00 94 20 25 10 18
cmd 1d 05 00 95 15 00

dxl comm mode interr
cmd 04 --> 04 03 02 = CW

fil set nor = 06 03 03
        nar =    03 02
        wid =       01

    PBT1 = 14 07 [02 55]
       2 = 14 08

PWR = 14 0A [02 55]
TUN = 1C 01 02

band stac reg
1a 01 05 01 (20m first reg)
output : `90 35 04 14 00 03 01 00 00 08 85 00 08 85`
first 5 bytes - frequency `0,014,043.590 = 14,043.59`
next 2 bytes - mode? `03 01` = CW FIL1

freqs
1c 03
00,03,05