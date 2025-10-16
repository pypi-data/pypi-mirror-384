from gift.core import Gif, InvalidGifFormatError, InsufficientCapacityError, GifError
import argparse
import os
import sys
import getpass
import json


def main():
    parser = argparse.ArgumentParser(description='Hide and Recover Files in GIFs')
    parser.add_argument('mode', choices=['hide', 'recover', 'analyze', 'spread', 'gather'],
                        help='Mode of operation: "hide" to hide files inside a GIF or "recover" to extract them.')
    parser.add_argument('--source', type=str, help='Path to the source GIF file.', required=False)
    parser.add_argument('--dest', type=str, help='Path to the destination GIF file.', required=False)
    parser.add_argument('--encrypt', action='store_true', help='Encrypt hidden data with a password')
    parser.add_argument('--decrypt', action='store_true', help='Decrypt recovered data with a password')
    parser.add_argument('--json', action='store_true', help='Output analyze results in JSON format')
    parser.add_argument('filenames', type=str, nargs='+',
                        help='Arbitrary list of filenames to hide or recover based on the mode.')
    args = parser.parse_args()

    # Get password if encryption/decryption requested
    password = None
    if args.encrypt or args.decrypt:
        password = getpass.getpass("Enter password: ")
        if not password:
            print("Error: Password cannot be empty", file=sys.stderr)
            sys.exit(1)

    if args.mode == 'hide':
        if not args.source:
            parser.error('The --source argument is required for "hide" mode.')
        if not args.dest:
            parser.error('The --dest argument is required for "hide" mode.')
        hide_files(args.source, args.dest, args.filenames, password if args.encrypt else None)
    elif args.mode == 'recover':
        if not args.source:
            parser.error('The --source argument is required for "recover" mode.')
        recover_files(args.source, args.filenames, password if args.decrypt else None)
    elif args.mode == 'analyze':
        analyze(args.filenames[0], json_output=args.json)
    elif args.mode == 'spread':
        if not args.source:
            parser.error('The --source argument is required for "spread" mode.')
        if not args.dest:
            parser.error('The --dest argument is required for "spread" mode.')
        spread_data(args.source, args.dest, args.filenames, password if args.encrypt else None)
    elif args.mode == 'gather':
        if not args.source:
            parser.error('The --source argument is required for "gather" mode.')
        gather_data(args.source, args.filenames, password if args.decrypt else None)


def hide_files(source_gif, destination_gif, filenames, password=None):
    """Hide multiple files in separate GIF frames."""
    # Validate source file exists
    if not os.path.isfile(source_gif):
        print(f"Error: Source GIF '{source_gif}' not found", file=sys.stderr)
        sys.exit(1)

    # Validate all files to hide exist
    for filename in filenames:
        if not os.path.isfile(filename):
            print(f"Error: File to hide '{filename}' not found", file=sys.stderr)
            sys.exit(1)

    print(f'Hiding files in {source_gif} and writing to {destination_gif}')
    payloads = []
    try:
        for filename in filenames:
            print(f"We will hide: {filename}")
            with open(filename, "rb") as fh:
                payload = fh.read()
                payloads.append(payload)

        # First pass: analyze capacity
        print("Analyzing GIF capacity...")
        with open(source_gif, "rb") as fh:
            gif_check = Gif(file_handle=fh)
            can_fit, total_needed, total_available, per_frame_info = gif_check.check_capacity(payloads)

        print(f"Total capacity: {total_available} bytes")
        print(f"Data to hide: {total_needed} bytes")

        if not can_fit:
            print(f"\nError: Insufficient capacity!", file=sys.stderr)
            print(f"Need {total_needed} bytes but only {total_available} bytes available", file=sys.stderr)
            print("\nPer-frame breakdown:", file=sys.stderr)
            for info in per_frame_info:
                if info['needed'] > 0:
                    status = "OK" if info['fits'] else "TOO BIG"
                    print(f"  Frame {info['frame']}: {info['needed']} bytes needed, {info['capacity']} bytes available [{status}]", file=sys.stderr)
            raise InsufficientCapacityError("Not enough space to hide all files")

        print("Capacity check passed!")

        # Second pass: actually hide the data
        if password:
            print("Encrypting data with password...")
        with open(source_gif, "rb") as fh, open(destination_gif, "wb") as oh:
            print("Doing magic...")
            g = Gif(file_handle=fh, hide=True, blobs=payloads, password=password)
            print(f"Done...now writing to {destination_gif}")
            oh.write(g.buffer)
    except GifError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: I/O error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to hide files: {e}", file=sys.stderr)
        sys.exit(1)


def recover_files(source_gif, filenames, password=None):
    """Recover multiple files from separate GIF frames."""
    if not os.path.isfile(source_gif):
        print(f"Error: Source GIF '{source_gif}' not found", file=sys.stderr)
        sys.exit(1)

    print(f'Recovering files from {source_gif}')
    try:
        if password:
            print("Decrypting data with password...")
        with open(source_gif, "rb") as fh:
            g = Gif(file_handle=fh, recover=True, password=password)

        output_file_index = 0
        for filename in filenames:
            print(f'Recovering {filename}')
            if len(g.blobs) > output_file_index:
                with open(filename, "wb") as oh:
                    oh.write(g.blobs[output_file_index])
            else:
                print(f"Warning: Not enough hidden data found. Expected at least {output_file_index + 1} blobs, found {len(g.blobs)}")
            output_file_index += 1
    except GifError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: I/O error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to recover files: {e}", file=sys.stderr)
        sys.exit(1)


def analyze(gif_file, json_output=False):
    """Analyze a GIF file and dump frame information."""
    if not os.path.isfile(gif_file):
        print(f"Error: GIF file '{gif_file}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(gif_file, "rb") as fh:
            g = Gif(file_handle=fh)

        if json_output:
            # Build JSON structure
            data = {
                "gif_info": {
                    "header": g.header.decode(),
                    "frames": g.frames
                },
                "logical_screen_descriptor": {},
                "global_color_table": {},
                "application_extensions": [],
                "image_descriptors": [],
                "capacity": {
                    "total_bytes": g.calculate_capacity(),
                    "per_frame": []
                }
            }

            # Logical Screen Descriptor
            for attr, value in vars(g.LogicalScreenDescriptor).items():
                if not callable(value) and not attr.startswith("__"):
                    data["logical_screen_descriptor"][attr] = value

            # Global Color Table
            for attr, value in vars(g.GlobalColorTable).items():
                if not callable(value) and not attr.startswith("__"):
                    if attr == "gct_colors":
                        data["global_color_table"][attr] = value[:10] if value else []  # Limit for brevity
                    else:
                        data["global_color_table"][attr] = value

            # Application Extensions
            for app_ext in g.application_extensions:
                ext_data = {}
                for attr, value in vars(app_ext).items():
                    if not callable(value) and not attr.startswith("__"):
                        if attr == "sub_blocks":
                            ext_data[attr] = [{"size": sb.sub_block_size, "data_length": len(sb.sub_block_data)} for sb in value[:5]]
                        else:
                            ext_data[attr] = value
                data["application_extensions"].append(ext_data)

            # Image Descriptors
            for i, img_desc in enumerate(g.frame_image_descriptors):
                desc_data = {}
                for attr, value in vars(img_desc).items():
                    if not callable(value) and not attr.startswith("__"):
                        if attr == "local_color_table":
                            desc_data[attr + "_length"] = len(value) if value else 0
                        else:
                            desc_data[attr] = value
                data["image_descriptors"].append(desc_data)

                # Per-frame capacity
                frame_pixels = img_desc.width * img_desc.height
                frame_capacity = frame_pixels // 8 - len(g.MAGIC_CODE)
                data["capacity"]["per_frame"].append({
                    "frame": i,
                    "capacity_bytes": frame_capacity
                })

            print(json.dumps(data, indent=2))
        else:
            # Original text output
            print("---")
            print("GIF INFO")
            print("---")
            print(f"header = {g.header.decode()}")
            print(f"frames = {g.frames}")
            print(f"total_capacity = {g.calculate_capacity()} bytes")
            print("---")
            print("LOGICAL SCREEN DESCRIPTOR")
            print("---")
            for attr, value in vars(g.LogicalScreenDescriptor).items():
                if not callable(value) and not attr.startswith("__"):
                    print(f"{attr} = {value}")
            print("---")
            print("GLOBAL COLOR TABLE")
            print("---")
            for attr, value in vars(g.GlobalColorTable).items():
                if not callable(value) and not attr.startswith("__"):
                    print(f"{attr} = {value}")
            print("---")
            print("APPLICATION EXTENSIONS")
            print("---")
            for application_extension in g.application_extensions:
                for attr, value in vars(application_extension).items():
                    if not callable(value) and not attr.startswith("__"):
                        if attr == "sub_blocks":
                            for sub_block in value:
                                print(f"sub_block_size: {sub_block.sub_block_size}")
                                print(f"sub_block_data: {sub_block.sub_block_data}")
                        else:
                            print(f"{attr} = {value}")
                print("---")
            print("---")
            print("IMAGE DESCRIPTORS")
            print("---")
            for image_descriptor in g.frame_image_descriptors:
                for attr, value in vars(image_descriptor).items():
                    if not callable(value) and not attr.startswith("__"):
                        print(f"{attr} = {value}")
                print("---")
            print("---")
            print("DUMP FRAMES")
            print("---")
            g.render_images()
    except IOError as e:
        print(f"Error: I/O error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to analyze GIF: {e}", file=sys.stderr)
        sys.exit(1)


def split_bytearray(data, num_chunks):
    chunk_size, remainder = divmod(len(data), num_chunks)
    sizes = [chunk_size + (1 if i < remainder else 0) for i in range(num_chunks)]
    chunks = []
    start = 0
    for size in sizes:
        chunks.append(data[start:start + size])
        start += size

    return chunks


def spread_data(source_gif, destination_gif, filenames, password=None):
    """Spread a single file across all frames of a GIF."""
    if not os.path.isfile(source_gif):
        print(f"Error: Source GIF '{source_gif}' not found", file=sys.stderr)
        sys.exit(1)

    filename = filenames[0]
    if not os.path.isfile(filename):
        print(f"Error: File to hide '{filename}' not found", file=sys.stderr)
        sys.exit(1)

    print(f'Hiding file across frames of {source_gif} and writing to {destination_gif}')
    try:
        payloads = []
        print(f"We will hide: {filename}")
        with open(filename, "rb") as fh:
            payload = fh.read()

        with open(source_gif, "rb") as fh:
            gif_info = Gif(file_handle=fh)
            number_frames = gif_info.frames

        if number_frames == 0:
            print("Error: No frames found in GIF", file=sys.stderr)
            sys.exit(1)

        payloads = split_bytearray(payload, number_frames)
        print(f"We have split {filename} into {len(payloads)} chunks")
        for chunk in payloads:
            print(f"Chunk of size {len(chunk)}")

        # Check capacity
        print("Analyzing GIF capacity...")
        can_fit, total_needed, total_available, per_frame_info = gif_info.check_capacity(payloads)
        print(f"Total capacity: {total_available} bytes")
        print(f"Data to hide: {total_needed} bytes")

        if not can_fit:
            print(f"\nError: Insufficient capacity!", file=sys.stderr)
            print(f"File is too large to spread across all frames", file=sys.stderr)
            raise InsufficientCapacityError("Not enough space to spread file")

        print("Capacity check passed!")

        if password:
            print("Encrypting data with password...")
        with open(source_gif, "rb") as fh, open(destination_gif, "wb") as oh:
            print("Doing magic...")
            g = Gif(file_handle=fh, hide=True, blobs=payloads, password=password)
            print(f"Done...now writing to {destination_gif}")
            oh.write(g.buffer)
    except GifError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: I/O error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to spread data: {e}", file=sys.stderr)
        sys.exit(1)


def gather_data(source_gif, filenames, password=None):
    """Gather a file that was spread across all frames of a GIF."""
    if not os.path.isfile(source_gif):
        print(f"Error: Source GIF '{source_gif}' not found", file=sys.stderr)
        sys.exit(1)

    print(f'Recovering files from {source_gif}')
    try:
        if password:
            print("Decrypting data with password...")
        with open(source_gif, "rb") as fh:
            g = Gif(file_handle=fh, recover=True, password=password)

        output_filename = filenames[0]
        print(f'Recovering {output_filename}')

        if len(g.blobs) == 0:
            print("Warning: No hidden data found in GIF")

        with open(output_filename, "wb") as oh:
            for blob in g.blobs:
                print(f"Writing recovered blob of size {len(blob)} to {output_filename}")
                oh.write(blob)
    except GifError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: I/O error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to gather data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()