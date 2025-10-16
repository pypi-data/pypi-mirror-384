import hashlib


# Custom exceptions
class GifError(Exception):
    """Base exception for GIF-related errors."""
    pass


class InvalidGifFormatError(GifError):
    """Raised when the file is not a valid GIF."""
    pass


class InsufficientCapacityError(GifError):
    """Raised when there's not enough space to hide the data."""
    pass


class GifParsingError(GifError):
    """Raised when GIF parsing fails."""
    pass


class Crypto:
    """Simple XOR-based encryption using password-derived keys."""

    @staticmethod
    def derive_key(password, salt=b'gift-stego-salt', key_length=32):
        """Derive encryption key from password using PBKDF2.

        Args:
            password: Password string
            salt: Salt bytes for key derivation
            key_length: Length of derived key in bytes

        Returns:
            Derived key as bytes
        """
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=key_length)

    @staticmethod
    def encrypt(data, password):
        """Encrypt data using XOR cipher with password-derived key.

        Args:
            data: Bytearray to encrypt
            password: Password string

        Returns:
            Encrypted bytearray with format: [salt(16 bytes)][encrypted_data]
        """
        # Generate random salt using system entropy
        salt = hashlib.sha256(str(id(data)).encode()).digest()[:16]
        key = Crypto.derive_key(password, salt)

        encrypted = bytearray()
        encrypted.extend(salt)  # Prepend salt

        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])

        return encrypted

    @staticmethod
    def decrypt(encrypted_data, password):
        """Decrypt data using XOR cipher with password-derived key.

        Args:
            encrypted_data: Bytearray with format [salt(16 bytes)][encrypted_data]
            password: Password string

        Returns:
            Decrypted bytearray
        """
        if len(encrypted_data) < 16:
            raise ValueError("Encrypted data too short")

        salt = bytes(encrypted_data[:16])
        ciphertext = encrypted_data[16:]

        key = Crypto.derive_key(password, salt)

        decrypted = bytearray()
        for i, byte in enumerate(ciphertext):
            decrypted.append(byte ^ key[i % len(key)])

        return decrypted


class Gif:
    """GIF parser and steganography engine for hiding/recovering data in GIF files."""

    # Constants
    MAGIC_CODE = bytearray(b'\xde\xad\xbe\xef')
    MAX_SUB_BLOCK_SIZE = 255
    MAX_LZW_CODE_SIZE = 12
    EXTENSION_INTRODUCER = b'\x21'
    IMAGE_SEPARATOR = b'\x2C'
    APPLICATION_EXTENSION_LABEL = b'\xFF'

    def __init__(self, file_handle, hide=False, recover=False, blobs=None, password=None):
        """Initialize GIF parser.

        Args:
            file_handle: File handle to read GIF data from
            hide: If True, hide blobs in the GIF frames
            recover: If True, recover blobs from the GIF frames
            blobs: List of byte arrays to hide in frames
            password: Optional password for encryption/decryption
        """
        if blobs is None:
            blobs = []

        # Initialize all instance attributes
        self.buffer = bytearray(b'')
        self.file_handle = file_handle
        self.hide = hide
        self.recover = recover
        self.password = password
        self.application_extensions = []
        self.frame_image_descriptors = []
        self.frame_image_uncompressed_data = []
        self.frame_image_data = []
        self.header = ""
        self.frames = 0
        self.append_read_to_buffer = True

        # Encrypt blobs if password is provided and we're hiding
        if self.hide and self.password:
            self.blobs = [Crypto.encrypt(blob, self.password) for blob in blobs]
        else:
            self.blobs = blobs

        self.parse_gif_header()
        self.parse_logical_screen_descriptor()
        self.parse_global_color_table()
        self.block_iterator()

        # Decrypt blobs if password is provided and we're recovering
        if self.recover and self.password and len(self.blobs) > 0:
            try:
                self.blobs = [Crypto.decrypt(blob, self.password) for blob in self.blobs]
            except Exception as e:
                raise GifError(f"Decryption failed: {e}. Wrong password?")

    class LogicalScreenDescriptor:
        screen_width = None
        screen_height = None
        packed_fields = None
        gct_flag = None
        color_res = None
        sort_flag = None
        gct_size = None
        bg_color_index = None
        pixel_aspect_ratio = None

    class GlobalColorTable:
        gct_size = None
        gct_colors = None

    class ApplicationExtension:
        block_size = None
        app_identifier = None
        app_auth_code = None
        sub_blocks = []

    class SubBlock:
        sub_block_size = None
        sub_block_data = None

        def __init__(self):
            self.sub_block_size = 0
            self.sub_block_data = bytearray(b'')

    class ImageDescriptor:
        left_position = None
        top_position = None
        width = None
        height = None
        local_color_table_flag = None
        interlace_flag = None
        sort_flag = None
        reserved = None
        local_color_table_size = None
        local_color_table = None

    class ImageData:
        min_code_size = None
        sub_blocks = []

        def __init__(self):
            self.min_code_size = 8
            self.sub_blocks = []

    def file_handle_read(self, size):
        data = self.file_handle.read(size)
        if self.append_read_to_buffer:
            self.buffer += data
        return data

    def parse_gif_header(self):
        """Parse and validate GIF header."""
        self.header = self.file_handle_read(6)
        if len(self.header) < 6:
            raise InvalidGifFormatError("File is too small to be a valid GIF")

        # Validate GIF magic bytes
        if self.header[:3] != b'GIF':
            raise InvalidGifFormatError(f"Invalid GIF signature: expected 'GIF', got '{self.header[:3].decode('ascii', errors='replace')}'")

        # Validate version
        version = self.header[3:6]
        if version not in (b'87a', b'89a'):
            raise InvalidGifFormatError(f"Unsupported GIF version: {version.decode('ascii', errors='replace')}")

    def parse_logical_screen_descriptor(self):
        self.LogicalScreenDescriptor.screen_width = int.from_bytes(self.file_handle_read(2), 'little')
        self.LogicalScreenDescriptor.screen_height = int.from_bytes(self.file_handle_read(2), 'little')
        self.LogicalScreenDescriptor.packed_fields = int.from_bytes(self.file_handle_read(1), 'little')
        self.LogicalScreenDescriptor.gct_flag = (self.LogicalScreenDescriptor.packed_fields & 0b10000000) >> 7
        self.LogicalScreenDescriptor.color_res = (self.LogicalScreenDescriptor.packed_fields & 0b01110000) >> 4
        self.LogicalScreenDescriptor.sort_flag = (self.LogicalScreenDescriptor.packed_fields & 0b00001000) >> 3
        self.LogicalScreenDescriptor.gct_size = self.LogicalScreenDescriptor.packed_fields & 0b00000111
        self.LogicalScreenDescriptor.bg_color_index = int.from_bytes(self.file_handle_read(1), 'little')
        self.LogicalScreenDescriptor.pixel_aspect_ratio = int.from_bytes(self.file_handle_read(1), 'little')

    def parse_global_color_table(self):
        if self.LogicalScreenDescriptor.gct_flag:
            gct_size_bits = self.LogicalScreenDescriptor.packed_fields & 0b00000111
            self.GlobalColorTable.gct_size = 2 ** (gct_size_bits + 1)
            gct_data = self.file_handle_read(3 * self.GlobalColorTable.gct_size)
            self.GlobalColorTable.gct_colors = \
                [(gct_data[i], gct_data[i + 1], gct_data[i + 2]) for i in range(0, len(gct_data), 3)]

    def lzw_decode(self, min_code_size, compressed):
        clear_code = 1 << min_code_size
        eoi_code = clear_code + 1
        next_code = eoi_code + 1
        current_code_size = min_code_size + 1

        dictionary = {i: [i] for i in range(clear_code)}
        dictionary[clear_code] = []
        dictionary[eoi_code] = None

        bit_pos = 0
        data_length = len(compressed) * 8
        output = []

        current_code = None

        while bit_pos + current_code_size <= data_length:
            value = 0
            limit = bit_pos + current_code_size
            for i in range(bit_pos, limit):
                byte_pos = i // 8
                bit_offset = i % 8
                if compressed[byte_pos] & (1 << bit_offset):
                    value |= 1 << (i - bit_pos)

            code = value
            bit_pos += current_code_size

            if code == clear_code:
                current_code_size = min_code_size + 1
                next_code = eoi_code + 1
                dictionary = {i: [i] for i in range(clear_code)}
                dictionary[clear_code] = []
                dictionary[eoi_code] = None
                current_code = None
            elif code == eoi_code:
                break
            else:
                entry = dictionary.get(code)
                if entry is None:
                    if code == next_code:
                        entry = dictionary[current_code] + [dictionary[current_code][0]]
                    else:
                        raise ValueError(f"Invalid code: {code}")

                output.extend(entry)

                if current_code is not None:
                    dictionary[next_code] = dictionary[current_code] + [entry[0]]
                    next_code += 1

                    if next_code >= (1 << current_code_size) and current_code_size < 12:
                        current_code_size += 1

                current_code = code

        return output

    def lzw_encode(self, min_code_size, data):
        # Initialization
        clear_code = 1 << min_code_size
        eoi_code = clear_code + 1
        next_code = eoi_code + 1
        current_code_size = min_code_size + 1

        dictionary = {chr(i): i for i in range(clear_code)}

        output = bytearray()
        buffer = 0
        buffer_length = 0
        current = ""

        def write_code_to_buffer(code, buffer, buffer_length, output):
            buffer |= code << buffer_length
            buffer_length += current_code_size
            while buffer_length >= 8:
                output.append(buffer & 0xFF)
                buffer >>= 8
                buffer_length -= 8
            return buffer, buffer_length

        # Write clear_code to buffer
        buffer, buffer_length = write_code_to_buffer(clear_code, buffer, buffer_length, output)

        for i in data:
            current += chr(i)
            if current not in dictionary:
                buffer, buffer_length = write_code_to_buffer(dictionary[current[:-1]], buffer, buffer_length, output)

                if next_code < (1 << current_code_size):
                    dictionary[current] = next_code
                    next_code += 1
                else:
                    if current_code_size < 12:
                        dictionary[current] = next_code
                        next_code += 1
                        current_code_size += 1

                current = current[-1]

        if current in dictionary:
            buffer, buffer_length = write_code_to_buffer(dictionary[current], buffer, buffer_length, output)
        buffer, buffer_length = write_code_to_buffer(eoi_code, buffer, buffer_length, output)

        if buffer_length > 0:
            output.append(buffer & 0xFF)

        return output

    def block_iterator(self):
        """Iterate through GIF blocks and parse them."""
        while True:
            block_type = self.file_handle_read(1)
            if not block_type:
                break
            if block_type == self.EXTENSION_INTRODUCER:
                extension_function_code = self.file_handle_read(1)
                if extension_function_code == self.APPLICATION_EXTENSION_LABEL:
                    self.parse_application_extension()
                else:
                    extension_length = int.from_bytes(self.file_handle_read(1), 'little')
                    self.file_handle_read(extension_length)
                    self.parse_sub_blocks()
            elif block_type == self.IMAGE_SEPARATOR:
                self.parse_image_descriptor()
                self.parse_image_data()
            else:
                pass

    def parse_application_extension(self):
        application_extension = self.ApplicationExtension()
        application_extension.block_size = int.from_bytes(self.file_handle_read(1), 'little')
        if application_extension.block_size == 11:  # Typically 11 for Application Extension
            application_extension.app_identifier = self.file_handle_read(8).decode('ascii')
            application_extension.app_auth_code = self.file_handle_read(3).hex()
            sub_blocks, data = self.parse_sub_blocks()
            application_extension.sub_blocks += sub_blocks
        self.application_extensions.append(application_extension)

    def parse_sub_blocks(self):
        sub_blocks = []
        data = bytearray()
        while True:
            sub_block_size = int.from_bytes(self.file_handle_read(1), 'little')
            if sub_block_size == 0:
                break
            else:
                sub_block = self.SubBlock()
                sub_block.sub_block_size = sub_block_size
                sub_block.sub_block_data = self.file_handle_read(sub_block_size)
                data += sub_block.sub_block_data
                sub_blocks.append(sub_block)
        return sub_blocks, data

    def generate_sub_blocks(self, temp_buffer):
        """Generate GIF sub-blocks from a buffer.

        Args:
            temp_buffer: Data buffer to split into sub-blocks

        Returns:
            List of SubBlock objects
        """
        sub_blocks = []
        while temp_buffer:
            # Take up to MAX_SUB_BLOCK_SIZE bytes from the buffer
            chunk = temp_buffer[:self.MAX_SUB_BLOCK_SIZE]
            temp_buffer = temp_buffer[self.MAX_SUB_BLOCK_SIZE:]

            sub_block = self.SubBlock()
            sub_block.sub_block_data = chunk
            sub_block.sub_block_size = len(chunk)
            sub_blocks.append(sub_block)

        # Add terminating zero-length sub-block
        sub_block = self.SubBlock()
        sub_block.sub_block_data = b''
        sub_block.sub_block_size = 0
        sub_blocks.append(sub_block)

        return sub_blocks

    def lsb_encode(self, frame_data, byte_array):
        for byte_index, byte_val in enumerate(byte_array):
            for bit_index in range(8):
                pixel_index = byte_index * 8 + bit_index
                frame_data[pixel_index] &= 0xFE  # Clear the least significant bit
                frame_data[pixel_index] |= (byte_val >> bit_index) & 1  # Set the least significant bit
        return frame_data

    def lsb_decode(self, frame_data):
        """Decode data hidden using LSB steganography.

        Args:
            frame_data: Uncompressed frame pixel data

        Returns:
            Decoded bytearray if magic code is found, empty bytearray otherwise
        """
        num_bytes = len(frame_data) // 8
        decoded_bytes = bytearray()
        for byte_index in range(num_bytes):
            decoded_byte = 0
            for bit_index in range(8):
                pixel_index = byte_index * 8 + bit_index
                decoded_byte |= (frame_data[pixel_index] & 1) << bit_index  # Extract the least significant bit
            decoded_bytes.append(decoded_byte)
        if self.MAGIC_CODE in decoded_bytes:
            return decoded_bytes.split(self.MAGIC_CODE)[0]
        else:
            return bytearray()

    def parse_image_data(self):
        """Parse image data block including LZW decompression and steganography operations."""
        min_code_size = int.from_bytes(self.file_handle_read(1), 'little')
        if min_code_size > self.MAX_LZW_CODE_SIZE:
            return
        if self.hide:
            self.append_read_to_buffer = False
        sub_blocks, data = self.parse_sub_blocks()
        image_data = self.ImageData()
        image_data.min_code_size = min_code_size
        image_data.sub_blocks = sub_blocks
        self.frame_image_data.append(image_data)
        uncompressed_frame = self.lzw_decode(min_code_size, data)
        if self.hide:
            if self.frames < len(self.blobs) and len(self.blobs[self.frames] + self.MAGIC_CODE) > (len(uncompressed_frame) / 8):
                print("Warning: Blob to be hidden was too big, skipping")
                hidden_frame = uncompressed_frame
            elif self.frames < len(self.blobs):
                if len(self.blobs[self.frames]) > 0:
                    blob_to_hide = self.blobs[self.frames] + self.MAGIC_CODE
                    hidden_frame = self.lsb_encode(uncompressed_frame, blob_to_hide)
                else:
                    hidden_frame = uncompressed_frame
            else:
                hidden_frame = uncompressed_frame
            hidden_frame_compressed = self.lzw_encode(min_code_size, hidden_frame)
            new_sub_blocks = self.generate_sub_blocks(hidden_frame_compressed)
            for block in new_sub_blocks:
                self.buffer += block.sub_block_size.to_bytes(1, 'little')
                self.buffer += block.sub_block_data
            self.append_read_to_buffer = True

        if self.recover:
            try:
                blob_recovered = self.lsb_decode(uncompressed_frame)
                if len(blob_recovered) > 0:
                    self.blobs.append(blob_recovered)
            except (IndexError, ValueError) as e:
                # Failed to decode - frame may not contain hidden data
                pass

        self.frame_image_uncompressed_data.append(uncompressed_frame)
        self.frames += 1

    def calculate_capacity(self):
        """Calculate the total capacity available for hiding data in bytes.

        Returns:
            Total capacity in bytes across all frames
        """
        total_capacity = 0
        for descriptor in self.frame_image_descriptors:
            # Each pixel can store 1 bit, so divide by 8 for bytes
            frame_pixels = descriptor.width * descriptor.height
            frame_capacity = frame_pixels // 8
            # Account for magic code overhead
            frame_capacity -= len(self.MAGIC_CODE)
            if frame_capacity > 0:
                total_capacity += frame_capacity
        return total_capacity

    def check_capacity(self, blobs):
        """Check if there's enough capacity to hide the provided blobs.

        Args:
            blobs: List of byte arrays to hide

        Returns:
            tuple: (can_fit: bool, total_needed: int, total_available: int, per_frame_info: list)
        """
        per_frame_info = []
        for i, descriptor in enumerate(self.frame_image_descriptors):
            frame_pixels = descriptor.width * descriptor.height
            frame_capacity = frame_pixels // 8 - len(self.MAGIC_CODE)
            blob_size = len(blobs[i]) if i < len(blobs) else 0

            per_frame_info.append({
                'frame': i,
                'capacity': frame_capacity,
                'needed': blob_size,
                'fits': blob_size <= frame_capacity
            })

        total_needed = sum(len(blob) for blob in blobs)
        total_available = self.calculate_capacity()

        return total_needed <= total_available, total_needed, total_available, per_frame_info

    def render_images(self):
        frame_number = 0
        for image_descriptor in self.frame_image_descriptors:
            uncompressed = self.frame_image_uncompressed_data[frame_number]

            frame_data = [[image_descriptor.local_color_table[pixel] for pixel in
                           uncompressed[row * image_descriptor.width:(row + 1) * image_descriptor.width]] for
                          row in range(image_descriptor.height)]
            print(f"writing frame_{frame_number}.png")
            self.write_png(f'frame_{frame_number}.png', len(frame_data[0]), len(frame_data), frame_data)
            frame_number += 1

    def write_png(self, filename, width, height, data):
        import zlib
        import struct
        # Create a new file in binary write mode.
        with open(filename, 'wb') as f:
            # PNG header
            f.write(b"\x89PNG\r\n\x1a\n")

            # IHDR chunk
            ihdr = [width, height, 8, 2, 0, 0, 0]
            f.write(struct.pack("!I", 13))
            f.write(b"IHDR")
            f.write(struct.pack("!2I5B", *ihdr))
            f.write(struct.pack("!I", zlib.crc32(b"IHDR" + struct.pack("!2I5B", *ihdr)) & 0xFFFFFFFF))

            # IDAT chunk
            raw_data = b"".join(
                b"\x00" + bytes(pixel for pixel_row in row_data for pixel in pixel_row)
                for row_data in data
            )
            compressed = zlib.compress(raw_data, level=9)
            f.write(struct.pack("!I", len(compressed)))
            f.write(b"IDAT")
            f.write(compressed)
            f.write(struct.pack("!I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF))

            # IEND chunk
            f.write(struct.pack("!I", 0))
            f.write(b"IEND")
            f.write(struct.pack("!I", zlib.crc32(b"IEND") & 0xFFFFFFFF))

    def parse_image_descriptor(self):
        # Read and process Image Descriptor (9 bytes)
        left_position = int.from_bytes(self.file_handle_read(2), 'little')
        top_position = int.from_bytes(self.file_handle_read(2), 'little')
        width = int.from_bytes(self.file_handle_read(2), 'little')
        height = int.from_bytes(self.file_handle_read(2), 'little')
        packed_field = int.from_bytes(self.file_handle_read(1), 'little')

        local_color_table_flag = (packed_field & 0x80) >> 7
        interlace_flag = (packed_field & 0x40) >> 6
        sort_flag = (packed_field & 0x20) >> 5
        reserved = (packed_field & 0x18) >> 3
        local_color_table_size = packed_field & 0x07

        if local_color_table_flag:
            lct_size = packed_field & 0x07
            lct_length = 3 * (2 ** (lct_size + 1))
            lct_data = self.file_handle_read(lct_length)
            local_color_table = [(lct_data[i], lct_data[i + 1], lct_data[i + 2]) for i in range(0, len(lct_data), 3)]
        else:
            local_color_table = self.GlobalColorTable.gct_colors

        image_descriptor = self.ImageDescriptor()
        image_descriptor.left_position = left_position
        image_descriptor.top_position = top_position
        image_descriptor.width = width
        image_descriptor.height = height
        image_descriptor.local_color_table_flag = local_color_table_flag
        image_descriptor.interlace_flag = interlace_flag
        image_descriptor.sort_flag = sort_flag
        image_descriptor.reserved = reserved
        image_descriptor.local_color_table_size = local_color_table_size
        image_descriptor.local_color_table = local_color_table

        self.frame_image_descriptors.append(image_descriptor)

