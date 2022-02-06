import os, png, math, argparse
import numpy as np
from apng import APNG
from apnggif import apnggif

print("worx-ani\nA dumper for .ani/.sld graphics files\nMade by kkzero\nStarting extraction...")

parser = argparse.ArgumentParser()
parser.add_argument('file', metavar='F', type=str, help='.ani/.sld file')
args = parser.parse_args()

input_ani = open(args.file, "rb")
input_ani.seek(0)

#Gets the RGB666 palettes from the file
def get_pals(pal_list, pals_offset):
    input_ani.seek(pals_offset)
    for i in range(0, 256):
        pal_r = int.from_bytes(input_ani.read(1), byteorder='little')
        pal_g = int.from_bytes(input_ani.read(1), byteorder='little')
        pal_b = int.from_bytes(input_ani.read(1), byteorder='little')
        pal_r8 = int(math.floor(pal_r * 255.0 / 63.0 + 0.5))
        pal_g8 = int(math.floor(pal_g * 255.0 / 63.0 + 0.5))
        pal_b8 = int(math.floor(pal_b * 255.0 / 63.0 + 0.5))
        pal_list.append((pal_r8, pal_g8, pal_b8))
    return

#Gets the pointers to each frame
def get_frameptrs(ptr_list, ptrs_offset):
    input_ani.seek(ptrs_offset)
    for i in range(0, ani_framecount):
        ptr_list.append(int.from_bytes(input_ani.read(4), byteorder='little'))
    return

#Decompresses the RLE frame data
def decomp_frame(frame_offset):
    output_frame = []
    output_bytes = []
    input_ani.seek(frame_offset)
    while True:
        current_byte = int.from_bytes(input_ani.read(1), byteorder='little')
        #End of frame indicator
        if current_byte == 0x0:
            break
        #Repeat byte an 8-bit amount of times
        elif current_byte > 0x0 and current_byte <= 0x3F:
            read8_byte = input_ani.read(1)
            for i in range(0, current_byte):
                output_frame.append(read8_byte)
        #Repeat byte a 14-bit amount of times
        elif current_byte >= 0x40 and current_byte <= 0x7F:
            read16_byte1 = input_ani.read(1)
            read16_byte2 = input_ani.read(1)
            byte1_or = (current_byte & 0x3F) << 8
            for i in range(0, byte1_or | int.from_bytes(read16_byte1, byteorder='little')):
                output_frame.append(read16_byte2)
        #Output next data: xx - 0x80
        elif current_byte >= 0x81 and current_byte <= 0xBF:
            for i in range(0, current_byte - 0x80):
                output_frame.append(input_ani.read(1))
        #Output next data: yy + ((xx & 0xF) * 0x100) 
        elif current_byte >= 0xC0 and current_byte <= 0xFF:
            adv_val = int.from_bytes(input_ani.read(1), byteorder='little')
            for i in range(0, adv_val + ((current_byte & 0x3F) * 0x100)):
                output_frame.append(input_ani.read(1))
        #If an unknown byte is somehow found, decomp will halt
        else:
            print("UNKNOWN BYTE DETECTED: " + hex(current_byte) + " at " + hex(input_ani.tell() - 1))
            break
    #If the decomp somehow isn't the res size, this shouldn't happen
    if len(output_frame) < ani_resx * ani_resy:
        for i in range(len(output_frame), ani_resx * ani_resy):
            output_frame.append(b'00')
    
    return output_frame

#MAIN PROGRAM
#Get header data
ani_header = input_ani.read(4)
if ani_header != b'*ANI':
    raise Exception("Input file is not .ani/.sld")
ani_magic = int.from_bytes(input_ani.read(4), byteorder='little')
ani_unk0 = int.from_bytes(input_ani.read(4), byteorder='little')
ani_framecount = int.from_bytes(input_ani.read(4), byteorder='little')
ani_unkpointer = int.from_bytes(input_ani.read(4), byteorder='little')
ani_palarray = int.from_bytes(input_ani.read(4), byteorder='little')
ani_frameptrarray = int.from_bytes(input_ani.read(4), byteorder='little')
ani_unkarray = int.from_bytes(input_ani.read(4), byteorder='little')
ani_unk1 = int.from_bytes(input_ani.read(4), byteorder='little')
ani_filetype = int.from_bytes(input_ani.read(4), byteorder='little')
ani_resx = int.from_bytes(input_ani.read(4), byteorder='little')
ani_resy = int.from_bytes(input_ani.read(4), byteorder='little')

ani_pals = []
get_pals(ani_pals, ani_palarray)
ani_frameptrs = []
get_frameptrs(ani_frameptrs, ani_frameptrarray)
bak_frame = []

try:
    os.mkdir("./" + os.path.splitext(args.file)[0])
except:
    print("Directory " + os.path.splitext(args.file)[0] + " already exists, continuing...")

#Just a text file to provide some specifics on the original animation file
ani_meta = open(os.path.splitext(args.file)[0] + "/" + os.path.split(args.file)[1][0:-4] + ".txt", "w")
ani_meta.write(str("Name: " + os.path.split(args.file)[1]) + "\n")
#ani_meta.write(str("Framerate Base: " + str(ani_fps)) + "\n")
ani_meta.write(str("Frames: " + str(ani_framecount)) + "\n")
ani_meta.write(str("Resolution: " + str(ani_resx) + "x" + str(ani_resy)) + "\n")

#Initialize the backup frame
for i in range(0, ani_resx * ani_resy):
    bak_frame.append(b'')
count = 0

#Create PNGs out of the frames
for i in ani_frameptrs:
    f = open("./" + os.path.splitext(args.file)[0] + "/" + os.path.split(args.file)[1][0:-4] + "_" + str(count).zfill(3) + ".png", "wb")
    current_frame = decomp_frame(i)

    #Subsequent frames are overlaid onto the previous one, so take the transparency into account
    for k in range(0, ani_resx * ani_resy):
        if int.from_bytes(current_frame[k], byteorder='little') == 0:
            current_frame[k] = bak_frame[k]
    del bak_frame
    bak_frame = []
    for k in range(0, ani_resx * ani_resy):
        bak_frame.append(current_frame[k])
    
    w = png.Writer(width=ani_resx, height=ani_resy, palette=ani_pals)
    w.write(f, np.reshape(current_frame, (ani_resy, ani_resx)))
    #except ValueError:
        
    f.close()
    count += 1

#Create APNG, then GIF
pngframes = []
for i in range(0, count):
    pngframes.append("./" + os.path.splitext(args.file)[0] + "/" + os.path.split(args.file)[1][0:-4] + "_" + str(i).zfill(3) + ".png")
APNG.from_files(pngframes, delay=125).save("./" + os.path.splitext(args.file)[0] + "/" + os.path.split(args.file)[1][0:-4] + ".png")
apnggif("./" + os.path.splitext(args.file)[0] + "/" + os.path.split(args.file)[1][0:-4] + ".png")

#The end
print("Animation extracted.")
input_ani.close()


