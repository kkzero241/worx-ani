# worx-ani

A decompressor/converter for .ANI/.SLD animation files, as used in the Brunswick Frameworx bowling scoring system.

![](/example/img1.gif) ![](/example/img2.gif)

![](/example/img3.gif) ![](/example/img4.gif) 

# Dependencies
This tool relies on `numpy`, `APNG`, and `apnggif` for external dependencies. They can be acquired via `pip -m install`.

# Usage
Run the script in Python with `worx-ani.py [-h] F`, where `F` is the path to the .ANI/.SLD file you wish to convert. If all goes well, a folder with the filename will appear in the directory of the original file, containing the following:
* A text file with some information regarding the original file.
* PNGs of each frame of the animation.
* Both an APNG and a GIF of the animation.

# Status
## What works
* The exciter animations.
* The Frameworx logo and copyright graphics.
## What doesn't
* The "SPM"-prefixed .SLD files.
* The <= 5KB .ANI files.
## What else
* The output framerate (125/1000 sec between frames) seems to line up, but is nonetheless a guess.

# Format specs 
## Layout
* Header
* Palette List
* Unknown List
* Frame Pointer List
* Frame Data
## Header
| Offset | Size | Desc |
|---------|-----|------|
|0x00| 4 | "*ANI" header string
|0x04| 4 | Magic value? Seems to always be 0x200
|0x08| 4 | Unknown
|0x0C| 4 | Number of frames in the animation
|0x10| 4 | Pointer to unknown data
|0x14| 4 | Pointer to palette data
|0x18| 4 | Pointer to array of frame pointers
|0x1C| 4 | Pointer to unknown array, could just be padding?
|0x20| 4 | Unknown, seems to be 0 or -1 for the files that work
|0x24| 4 | Seems to be 1 for .ANI files and 2 for .SLD files
|0x28| 4 | Horizontal resolution
|0x2C| 4 | Vertical resolution
|0x30| 4 | Unknown
|0x34|0x40| Unknown area
## Palette List
A 0x300 byte long array of palette data, stored as 18-bit RGB666 values.
## Unknown List
Self-explanatory, I'm not sure what this data is, seems to be 4 times the frame count plus 1 in size though.
## Frame Pointer List
An array of size 4 times the frame count plus 1. Contains pointers to the data for each animation frame, plus the last one pointing to the end of the file. Also followed by unknown data before the first frame.
## Frame Data
Each animation frame is compressed in a most likely proprietary RLE scheme.
| Opcode | Format | Description |
|-|-|-|
| 0x00 | 00 | Marks end of frame data
| 0x01-0x3F | xx yy | Outputs yy an xx amount of times
| 0x40-0x7F | xxyy zz | Outputs zz an ((yy & 0x3F) << 8 \| xx) amount of times
| 0x80-0xBF | xx | Outputs the next (xx - 0x80) bytes
| 0xC0-0xFF | xx yy | Outputs the next (yy + (xx & 0x3F) * 0x100)  bytes

Every frame after the first one treats palette index 0x00 as transparency, so subsequent frames get "overlaid" onto the previous one's data.

# Where do I find these files?
As far as I know the only known dump of Frameworx data was [shared to archive.org in 2021](https://archive.org/details/brunswick-frameworx-10pin-animations-sounds).
Additionally, there exist animations that aren't even in this collection, such as "The Great Sparedini".
