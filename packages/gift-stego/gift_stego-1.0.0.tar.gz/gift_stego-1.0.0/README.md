# GIFT
## GIF Analysis Steganography Library/Tool

A pure Python library for hiding and recovering data in GIF files using LSB steganography with optional password-based encryption.

**Installation**

Install from PyPI:
```bash
pip install gift-stego
```

Or install from source:
```bash
git clone https://github.com/dtmsecurity/gift-stego.git
cd gift-stego
pip install -e .
```

**Dependencies**

There are no external dependencies - only Python 3.7+

**Library Usage**

```python
from gift import Gif

# Hide data in a GIF
with open('input.gif', 'rb') as f:
    gif = Gif(f, hide=True, blobs=[b'secret data'], password='mypassword')
    with open('output.gif', 'wb') as out:
        out.write(gif.buffer)

# Recover data from a GIF
with open('output.gif', 'rb') as f:
    gif = Gif(f, recover=True, password='mypassword')
    print(gif.blobs[0])  # b'secret data'

# Check GIF capacity before hiding
with open('input.gif', 'rb') as f:
    gif = Gif(f)
    capacity = gif.calculate_capacity()
    print(f"This GIF can hide {capacity} bytes")

# Validate data will fit
with open('input.gif', 'rb') as f:
    gif = Gif(f)
    data_to_hide = [b'file1 content', b'file2 content']
    can_fit, needed, available, info = gif.check_capacity(data_to_hide)
    if can_fit:
        print(f"Data will fit: {needed} bytes needed, {available} bytes available")
    else:
        print(f"Insufficient capacity!")
```


**CLI Usage**

After installation, use the `gift` command:

```
usage: gift [-h] [--source SOURCE] [--dest DEST] [--encrypt] [--decrypt] [--json]
            {hide,recover,analyze,spread,gather} filenames [filenames ...]

Options:
  --source SOURCE   Path to the source GIF file
  --dest DEST       Path to the destination GIF file
  --encrypt         Encrypt hidden data with a password
  --decrypt         Decrypt recovered data with a password
  --json            Output analyze results in JSON format
```

**Features**

- **LSB Steganography**: Hide data in the least significant bits of GIF pixel data
- **Encryption**: Password-based encryption using PBKDF2 key derivation (100,000 iterations)
- **Capacity Checking**: Automatic validation that files will fit before hiding
- **GIF Validation**: Validates GIF format and version before processing
- **JSON Output**: Machine-readable analysis output for automation
- **Error Handling**: Clear error messages for all failure cases

**Examples**

The GIFT CLI has the following modes:

- **hide** - hide multiple files across multiple frames of a GIF
- **recover** - recover multiple files from multiple frames of a GIF
- **spread** - hide a single file across all of the frames of a GIF
- **gather** - recover a single file that is hidden across all frames of a GIF
- **analyze** - analyze a GIF and dump all the frames to PNG files

**CLI Examples**

Let's start playing - We are going to hide a text file and a jpg in a GIF:

```bash
gift --source giphy.gif --dest output.gif hide hello.txt meme.jpg
Hiding files in giphy.gif and writing to output.gif
We will hide: hello.txt
We will hide: meme.jpg
Doing magic...
Done...now writing to output.gif
```


Let’s recover the files we hid:

```
gift --source output.gif recover recovered_hello.txt recovered_meme.jpg
Recovering files from output.gif
Recovering recovered_hello.txt
Recovering recovered_meme.jpg

% shasum hello.txt recovered_hello.txt
22596363b3de40b06f981fb85d82312e8c0ed511  hello.txt
22596363b3de40b06f981fb85d82312e8c0ed511  recovered_hello.txt
% shasum meme.jpg recovered_meme.jpg
a1838d4cb7cd2311dae420ec6bc8688e56dc5414  meme.jpg
a1838d4cb7cd2311dae420ec6bc8688e56dc5414  recovered_meme.jpg
```

Awesome! We successful got the original files back. Now if you want to spread the data from single file across all frames to reduce the visual impact you can used the ‘spread’ feature of the tool.

```
gift --source giphy.gif --dest output.gif spread meme.jpg
Hiding file across frames of giphy.gif and writing to output.gif
We will hide: meme.jpg
We have split meme.jpg into 118
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 47
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Chunk of size 46
Doing magic...
Done...now writing to output.gif
```

Let’s use the ‘gather’ feature to recover our file.

```
gift --source output.gif gather recovered_meme.jpg
Recovering files from output.gif
Recovering recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 47 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg
Writing recovered blob of size 46 to recovered_meme.jpg

% shasum meme.jpg
a1838d4cb7cd2311dae420ec6bc8688e56dc5414  meme.jpg
% shasum recovered_meme.jpg
a1838d4cb7cd2311dae420ec6bc8688e56dc5414  recovered_meme.jpg
```

### Encryption Examples

Hide files with password encryption:

```bash
gift --source giphy.gif --dest encrypted.gif --encrypt hide secret.txt
Enter password:
Hiding files in giphy.gif and writing to encrypted.gif
We will hide: secret.txt
Analyzing GIF capacity...
Total capacity: 21870 bytes
Data to hide: 1024 bytes
Capacity check passed!
Encrypting data with password...
Doing magic...
Done...now writing to encrypted.gif
```

Recover encrypted files:

```bash
gift --source encrypted.gif --decrypt recover recovered_secret.txt
Enter password:
Recovering files from encrypted.gif
Decrypting data with password...
Recovering recovered_secret.txt
```

**Note:** Wrong password will result in decryption errors or garbled output.

### Analysis Examples

Standard text analysis with capacity information:

```bash
gift analyze giphy.gif
---
GIF INFO
---
header = GIF89a
frames = 118
total_capacity = 21870 bytes
---
[... detailed GIF analysis ...]
```

JSON output for automation and scripting:

```bash
gift --json analyze giphy.gif
{
  "gif_info": {
    "header": "GIF89a",
    "frames": 118
  },
  "capacity": {
    "total_bytes": 21870,
    "per_frame": [
      {"frame": 0, "capacity_bytes": 23433},
      {"frame": 1, "capacity_bytes": 23433},
      ...
    ]
  },
  "logical_screen_descriptor": {...},
  "global_color_table": {...},
  "application_extensions": [...],
  "image_descriptors": [...]
}
```

You can also use the analyze feature to investigate a GIF file and dump the frames:

```
gift analyze output.gif

---
GIF INFO
---
header = GIF89a
frames = 118
---
LOGICAL SCREEN DESCRIPTOR
---
screen_width = 500
screen_height = 375
packed_fields = 246
gct_flag = 1
color_res = 7
sort_flag = 0
gct_size = 6
bg_color_index = 57
pixel_aspect_ratio = 0
---
GLOBAL COLOR TABLE
---
gct_size = 128
gct_colors = [(21, 163, 221), (6, 3, 16), (15, 141, 200), (2, 101, 151), (56, 173, 230), (37, 202, 252), (5, 36, 87), (36, 217, 255), (39, 74, 122), (21, 202, 250), (42, 118, 170), (2, 63, 124), (41, 100, 148), (1, 87, 151), (2, 104, 168), (1, 84, 135), (52, 202, 253), (2, 126, 185), (11, 124, 207), (2, 117, 171), (56, 217, 254), (2, 70, 146), (31, 232, 255), (32, 56, 103), (23, 122, 185), (24, 84, 134), (22, 103, 162), (22, 87, 151), (20, 118, 169), (21, 185, 241), (21, 68, 145), (37, 183, 242), (2, 184, 240), (49, 143, 197), (55, 190, 244), (83, 38, 69), (28, 87, 165), (10, 178, 226), (38, 185, 221), (37, 212, 243), (52, 210, 241), (71, 200, 252), (20, 214, 245), (12, 237, 255), (21, 218, 255), (5, 104, 186), (21, 103, 188), (0, 214, 244), (6, 86, 171), (3, 202, 247), (5, 219, 254), (66, 100, 140), (72, 192, 187), (12, 248, 230), (49, 224, 210), (122, 164, 195), (78, 21, 30), (116, 20, 28), (80, 4, 8), (108, 34, 44), (146, 20, 30), (145, 34, 42), (153, 9, 15), (178, 20, 23), (196, 17, 26), (115, 61, 100), (107, 88, 134), (30, 205, 151), (42, 161, 75), (109, 84, 32), (207, 46, 47), (146, 142, 67), (212, 71, 74), (255, 255, 255), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
---
APPLICATION EXTENSIONS
---
block_size = 11
app_identifier = NETSCAPE
app_auth_code = 322e30
sub_block_size: 3
sub_block_data: b'\x01\x00\x00'
sub_block_size: 60
sub_block_data: b'?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?> <x:xmpm'
sub_block_size: 101
sub_block_data: b'ta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 6.0-c002 79.164460, 2020/05/12-16:04:17        ">'
sub_block_size: 32
sub_block_data: b'<rdf:RDF xmlns:rdf="http://www.w'
sub_block_size: 51
sub_block_data: b'.org/1999/02/22-rdf-syntax-ns#"> <rdf:Description r'
sub_block_size: 100
sub_block_data: b'f:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/" xm'
sub_block_size: 108
sub_block_data: b'ns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#" xmp:CreatorTool="Adobe Photoshop 21.2 (Macintosh)"'
sub_block_size: 32
sub_block_data: b'xmpMM:InstanceID="xmp.iid:2A4A11'
sub_block_size: 55
sub_block_data: b'951C011EB8B3DEEE1F100462C" xmpMM:DocumentID="xmp.did:2A'
sub_block_size: 52
sub_block_data: b'A117A51C011EB8B3DEEE1F100462C"> <xmpMM:DerivedFrom s'
sub_block_size: 116
sub_block_data: b'Ref:instanceID="xmp.iid:2A4A117751C011EB8B3DEEE1F100462C" stRef:documentID="xmp.did:2A4A117851C011EB8B3DEEE1F100462C'
sub_block_size: 34
sub_block_data: b'/> </rdf:Description> </rdf:RDF> <'
sub_block_size: 47
sub_block_data: b'x:xmpmeta> <?xpacket end="r"?>\x01\xff\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf6\xf5\xf4\xf3\xf2\xf1\xf0'
sub_block_size: 239
sub_block_data: b'\xee\xed\xec\xeb\xea\xe9\xe8\xe7\xe6\xe5\xe4\xe3\xe2\xe1\xe0\xdf\xde\xdd\xdc\xdb\xda\xd9\xd8\xd7\xd6\xd5\xd4\xd3\xd2\xd1\xd0\xcf\xce\xcd\xcc\xcb\xca\xc9\xc8\xc7\xc6\xc5\xc4\xc3\xc2\xc1\xc0\xbf\xbe\xbd\xbc\xbb\xba\xb9\xb8\xb7\xb6\xb5\xb4\xb3\xb2\xb1\xb0\xaf\xae\xad\xac\xab\xaa\xa9\xa8\xa7\xa6\xa5\xa4\xa3\xa2\xa1\xa0\x9f\x9e\x9d\x9c\x9b\x9a\x99\x98\x97\x96\x95\x94\x93\x92\x91\x90\x8f\x8e\x8d\x8c\x8b\x8a\x89\x88\x87\x86\x85\x84\x83\x82\x81\x80\x7f~}|{zyxwvutsrqponmlkjihgfedcba`_^]\\[ZYXWVUTSRQPONMLKJIHGFEDCBA@?>=<;:9876543210/.-,+*)(\'&%$#"! \x1f\x1e\x1d\x1c\x1b\x1a\x19\x18\x17\x16\x15\x14\x13\x12\x11\x10\x0f\x0e\r\x0c\x0b\n\t\x08\x07\x06\x05\x04\x03\x02\x01\x00'
---snip---
IMAGE DESCRIPTORS
---
left_position = 0
top_position = 0
width = 500
height = 375
local_color_table_flag = 0
interlace_flag = 0
sort_flag = 0
reserved = 0
local_color_table_size = 0
local_color_table = [(21, 163, 221), (6, 3, 16), (15, 141, 200), (2, 101, 151), (56, 173, 230), (37, 202, 252), (5, 36, 87), (36, 217, 255), (39, 74, 122), (21, 202, 250), (42, 118, 170), (2, 63, 124), (41, 100, 148), (1, 87, 151), (2, 104, 168), (1, 84, 135), (52, 202, 253), (2, 126, 185), (11, 124, 207), (2, 117, 171), (56, 217, 254), (2, 70, 146), (31, 232, 255), (32, 56, 103), (23, 122, 185), (24, 84, 134), (22, 103, 162), (22, 87, 151), (20, 118, 169), (21, 185, 241), (21, 68, 145), (37, 183, 242), (2, 184, 240), (49, 143, 197), (55, 190, 244), (83, 38, 69), (28, 87, 165), (10, 178, 226), (38, 185, 221), (37, 212, 243), (52, 210, 241), (71, 200, 252), (20, 214, 245), (12, 237, 255), (21, 218, 255), (5, 104, 186), (21, 103, 188), (0, 214, 244), (6, 86, 171), (3, 202, 247), (5, 219, 254), (66, 100, 140), (72, 192, 187), (12, 248, 230), (49, 224, 210), (122, 164, 195), (78, 21, 30), (116, 20, 28), (80, 4, 8), (108, 34, 44), (146, 20, 30), (145, 34, 42), (153, 9, 15), (178, 20, 23), (196, 17, 26), (115, 61, 100), (107, 88, 134), (30, 205, 151), (42, 161, 75), (109, 84, 32), (207, 46, 47), (146, 142, 67), (212, 71, 74), (255, 255, 255), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
---snip---
DUMP FRAMES
---
writing frame_0.png
writing frame_1.png
writing frame_2.png
writing frame_3.png
writing frame_4.png
writing frame_5.png
writing frame_6.png
writing frame_7.png
writing frame_8.png
writing frame_9.png
writing frame_10.png
---snip---
```

**References**

- https://dtm.uk/gif-steganography/

**Author**

- [@dtmsecurity](https://twitter.com/dtmsecurity)

- [@dtm@infosec.exchange](https://infosec.exchange/@dtm)