# dkc3 text editor by koda v0.1
# CR32: 448EEC19 (HEADERLESS)

import argparse
import sys
import os
import re
import struct

def reverse_list(lst, n=None):
    """
    Invierte los primeros n-1 elementos de la lista y deja el último en su lugar.
    
    Args:
        lst (list): Lista de elementos.
        n (int, optional): Número de elementos a considerar para invertir. 
                           Si no se da, se toma toda la lista.
    
    Returns:
        list: Lista con los primeros n-1 elementos invertidos y el último en su lugar.
    """
    if not lst:
        return []

    if n is None or n > len(lst):
        n = len(lst)

    to_reverse = lst[:n-1]
    last_elem = lst[n-1]
    return to_reverse[::-1] + [last_elem]

class extraction:
    def __init__(self):
        pass
    
    def read_rom(rom_file, addr, size):
        """
        Reads a block of data from the ROM file.

        Parameters:
            addr (int): The starting address to read from.
            size (int): The number of bytes to read.

        Returns:
            bytes: The data read from the ROM.
        """
        with open(rom_file, "rb") as f:
            f.seek(addr)
            return f.read(size)

    def read_tbl(tbl_file):
        """
        Loads the TBL (table) file into a dictionary mapping byte sequences to characters.

        The table format should be one mapping per line in the form:
        HEX=Character(s)

        Comments (lines starting with ';' or '/') and invalid lines are ignored.

        Returns:
            dict[bytes, str]: A mapping of byte sequences to their character representation.
        """
        char_table = {}
        with open(tbl_file, "r", encoding="UTF-8") as f:
            for line in f:
                if not line or line.startswith(";") or line.startswith("/"):
                    continue
                if "=" in line:
                    hex_value, chars = line.split("=", 1)
                    try:
                        if len(hex_value) % 2 != 0:
                            print(f"Warning: '{hex_value}' is invalid! Skipped.")
                            continue
                        byte_key = bytes.fromhex(hex_value)
                        char_table[byte_key] = chars.strip("\n")
                    except ValueError:
                        print(f"Warning: '{hex_value}' is invalid! Skipped.")
        return char_table

    def read_ptr_table(data, base):
        """
        Reads a pointer table from ROM data.

        Each pointer entry is 4 bytes:
            [0-1] Length (little endian)
            [2-3] Position (little endian, add Base)

        Args:
            data (bytes): Raw ROM data containing the pointer table.
            base (int): Base to CPU addrs.

        Returns:
            tuple: (positions, lengths)
                positions (list[int]): Decoded pointer addresses.
                lengths (list[int]): Corresponding lengths.
        """
        positions = []
        lengths = []

        for i in range(0, len(data), 4):
            entry = data[i:i+4]
            if len(entry) < 4:
                break
            
            length = entry[0] | (entry[1] << 8)
            pos = (entry[2] | (entry[3] << 8)) + base

            lengths.append(length)
            positions.append(pos)

        return positions, lengths

    def huffman_decompress(rom_file, tbl_dict, tree_start, tree_size, ptr_start, script_length):
        def get_ushort(data, index):
            return data[index] | (data[index + 1] << 8)

        with open(rom_file, "rb") as f:
            rom_data = f.read()

        tree_base = tree_start + 2
        results = []

        for blk in range(len(ptr_start)):
            pos = ptr_start[blk]
            length = script_length[blk]

            curr_node = get_ushort(rom_data, tree_start)
            flags_addr = pos
            flags_mask = 0
            node_flags = 0
            symbols_count = 0

            output = []
            current_line = ""

            while symbols_count < length:
                if (flags_mask >> 1) == 0:
                    flags_mask = 0x8000
                    node_flags = get_ushort(rom_data, flags_addr)
                    flags_addr += 2
                else:
                    flags_mask >>= 1

                right_node = (node_flags & flags_mask) == 0
                node = get_ushort(rom_data, tree_base + curr_node + (2 if right_node else 0))

                if node == 0:
                    symbol = rom_data[tree_base + curr_node - 1]
                    key = bytes([symbol])
                    val = tbl_dict.get(key)  

                    if 1 <= symbol <= 4:
                        output.append(current_line)
                        current_line = ""
                        piece = val if val is not None else f"<{symbol:02X}>"
                        current_line += piece

                    else:
                        if val is not None:
                            current_line += val
                        else:
                            current_line += f"<{symbol:02X}>"

                    symbols_count += 1

                    curr_node = get_ushort(rom_data, tree_start)
                    flags_mask <<= 1
                else:
                    curr_node = node

            if current_line:
                output.append(current_line)

            if output and output[0] == "":
                output.pop(0)
            results.append(output)

        return results

    def write_out_file(file, script_text, pointers_list, lines_length):
        """
        Writes data to a file, formatting each line with a semicolon and newline.
        
        Parameters:
            file (str): The path to the output file.
            script_text (list): A list of strings representing the script content to write to the file.
            pointers_start_address (int): The starting address of the pointer table.
            pointer_table_size (int): The size of the pointer table.
            address_list (list): A list of addresses corresponding to each line in the script.
            lines_length (list): A list of the length of each line in the script.
        """
        with open(file, "w", encoding='UTF-8') as f:
            f.write(f";{{{pointers_list:08X}-{(pointers_list+lines_length-1):08X}-{lines_length:08X}}}\n")          
            i = 0
            for line in script_text:             
                f.write(f"@{i+1}\n")                
                f.write(f";{{{line}}}\n")               
                f.write(f"{line}\n")
                f.write("|\n")
                i += 1
                
class insertion:
    def __init__(self):
        pass
    def read_script(file):
        """
        Reads a file containing the game's text and returns it as a single list (continuous script).

        Parameters:
            file (str): The path to the file to read.

        Returns:
            text_data (str): A single string containing all text elements merged from the script.
        """
        with open(file, "r", encoding='UTF-8') as f:
            lines = [
                line.rstrip('\n') for line in f.readlines()
                if not (line.startswith(";") or line.startswith("@") or line.startswith("|") or line.startswith("&"))
            ]

        script = "".join(lines)
        return script
    
    def read_tbl(tbl_file):
        """
        Reads a .tbl file to create a character mapping table (supports DTE/MTE, multibyte values).
        
        Parameters:
            tbl_file (str): The path to the .tbl file.
        
        Returns:
            tuple: Contains:
                - char_table (dict): A dictionary where keys are bytes sequences and values are strings (characters or sequences).
                - chars_lengths (set): Set array with chain char lengths.
        """
        char_table = {}
        chars_lengths = set()

        with open(tbl_file, "r", encoding="UTF-8") as f:
            for line in f:
                if not line or line.startswith(";") or line.startswith("/"):
                    continue
                if "=" in line:
                    hex_value, chars = line.split("=", 1)
                    chars = chars.strip('\n')
                    try:
                        if len(hex_value) % 2 != 0:
                            print(f"Warning: '{hex_value}' is invalid! Skipped.")
                            continue
                        byte_key = bytes.fromhex(hex_value)
                        char_table[chars] = byte_key
                        chars_lengths.add(len(chars))
                    except ValueError:
                        print(f"Warning: '{hex_value}' is invalid! Skipped.")
                        continue        
        chars_lengths = sorted([l for l in chars_lengths if l > 0], reverse=True)
        
        return char_table, chars_lengths

    def encode_text(blocks, char_table, max_char_len):
        """
        Encodes a list of text blocks into bytearrays using a character table (supports multibyte mappings).
        Recognizes <XX> sequences as raw byte values.
        If an unmapped character is found, the process stops with an error.

        Parameters:
            blocks (list of str): List of text blocks to encode.
            char_table (dict): Dictionary {str -> bytes} from the inverted .tbl.
            max_char_len (int): Maximum length for multibyte sequences (from .tbl).

        Returns:
            list of bytearray: A list where each element is a bytearray representing an encoded block.
        """
        hex_pattern = re.compile(r'<([0-9A-Fa-f]{2})>')
        data_list = []

        for block_index, block in enumerate(blocks, start=1):
            block_data = bytearray()
            idx = 0

            while idx < len(block):
                hex_match = hex_pattern.match(block, idx)
                if hex_match:
                    byte_val = int(hex_match.group(1), 16)
                    block_data.append(byte_val)
                    idx += 4
                    continue

                match = None
                match_len = 0

                for l in max_char_len:
                    if idx + l <= len(block):
                        chunk = block[idx:idx + l]
                        if chunk in char_table:
                            match = char_table[chunk]
                            match_len = l
                            break

                if match:
                    block_data.extend(match)
                    idx += match_len
                else:
                    problem_char = block[idx:idx + 1]
                    print(f"\n[ERROR] Unmapped character found at script {block_index}, position {idx}: '{problem_char}'")
                    print("Please check your .tbl file or input text.")
                    sys.exit(1)

            data_list.append(block_data)

        return data_list

    def huffman_compress(encoded_blocks, rom_file, tree_start, tree_size, base):
        def get_ushort(data, index):
            return data[index] | (data[index + 1] << 8)

        with open(rom_file, "rb") as f:
            rom = f.read()

        tree_base = tree_start + 2
        root_node = get_ushort(rom, tree_start)

        SymbolLUT = {}

        TreeStack = []
        CurrNode = root_node
        Code = 0
        Depth = 0

        outer_break = False
        while True:
            TreeStack.append(CurrNode)

            LeftNode = (Code & 1) != 0
            if LeftNode:
                CurrNode = get_ushort(rom, tree_base + CurrNode)
            else:
                CurrNode = get_ushort(rom, tree_base + CurrNode + 2)

            if CurrNode == 0:
                node_ref = TreeStack.pop()
                symbol = rom[tree_base + node_ref - 1]
                SymbolLUT[symbol] = (Depth, (Code >> 1) & 0xFFFF)

                while True:
                    if len(TreeStack) == 0:
                        outer_break = True
                        break
                    CurrNode = TreeStack.pop()
                    Code >>= 1
                    Depth -= 1
                    if (Code & 1) == 0:
                        break

                if outer_break:
                    break

                Code |= 1
            else:
                Code <<= 1
                Depth += 1

        compressed_data = bytearray()
        symbol_count = []
        block_offsets = [base]

        for block_idx, block in enumerate(encoded_blocks, start=1):
            CurrWord = 0
            CurrBits = 0
            symbols_decoded = 0
            block_bytes = bytearray()

            for symbol in block:
                if symbol not in SymbolLUT:
                    print(f"[ERROR] Script: {block_idx}, encounter Symbol: {symbol:02X}, not found in huffman tree.")
                    sys.exit(1)

                Bits, CodeVal = SymbolLUT[symbol]
                if CurrBits + Bits <= 16:
                    CurrWord = (CurrWord << Bits) & 0xFFFF
                    CurrWord |= (CodeVal & ((1 << Bits) - 1))
                    CurrBits += Bits
                    
                else:
                    SplitBits = 16 - CurrBits
                    SplitCode = (CodeVal >> (Bits - SplitBits)) & ((1 << SplitBits) - 1)

                    CurrWord = (CurrWord << SplitBits) & 0xFFFF
                    CurrWord |= SplitCode

                    block_bytes.append(CurrWord & 0xFF)
                    block_bytes.append((CurrWord >> 8) & 0xFF)

                    CurrBits = Bits - SplitBits
                    # CurrWord = Code & ((1 << CurrBits) - 1);
                    CurrWord = CodeVal & ((1 << CurrBits) - 1)
                symbols_decoded += 1

            if CurrBits != 0:
                CurrWord = (CurrWord << (16 - CurrBits)) & 0xFFFF
                block_bytes.append(CurrWord & 0xFF)
                block_bytes.append((CurrWord >> 8) & 0xFF)

            compressed_data.extend(block_bytes)
            symbol_count.append(symbols_decoded)
            symbols_decoded = 0
            block_offsets.append(block_offsets[-1] + len(block_bytes))

            # DEBBUG(IGNORE)
##            if block_idx == 1:
##                print(f"Block {block_idx} len={len(block_bytes)} bytes")
##                print(block_bytes.hex(" ").upper())

        block_offsets.pop()
        return compressed_data, len(compressed_data), symbol_count, block_offsets

    def create_4_bytes_pointers(script_size, script_offset):
        """
        Creates a bytearray of 4-byte pointers combining size and offset values in little endian.

        Parameters:
            script_size (list[int]): List of block sizes (2-byte values).
            script_offset (list[int]): List of block offsets (2-byte values).

        Returns:
            bytearray: Concatenated 4-byte pointers (size + offset), both in little endian.
        """
        script_size = reverse_list(script_size)
        script_offset = reverse_list(script_offset)

        pointers = bytearray()

        for size, offset in zip(script_size, script_offset):
            size_le = size.to_bytes(2, "little")
            offset_le = offset.to_bytes(2, "little")
            pointers.extend(size_le + offset_le)

        return pointers, len(pointers)
        
    def write_rom(rom_file, start_offset, original_size, data, fill_free_space, fill_free_space_byte):
        """
        Writes data to the ROM at the specified offset, filling any free space if requested.
        
        Parameters:
            rom_file (str): The path to the ROM file.
            start_offset (int): The offset in the ROM file where data should be written.
            original_size (int): The original size of the data to ensure there is enough space for the write operation.
            data (bytes or bytearray): The data to write to the ROM.
            fill_free_space (bool): Whether to fill the remaining space with a specific byte.
            fill_free_space_byte (byte): The byte used to fill the remaining space.
        
        Returns:
            int: The amount of free space left after writing the data.
        """
        free_space = int(original_size) - len(data)
        if fill_free_space:
            filled_data = data + bytes([fill_free_space_byte]) * free_space
        else:
            filled_data = data    
        with open(rom_file, "r+b") as f: 
            f.seek(start_offset)
            f.write(filled_data)
        return free_space
 
def main():
    parser = argparse.ArgumentParser(
        description="Donkey Kong Country 3 text editor by koda v0.1"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # --- extract ---
    extract_parser = subparsers.add_parser("extract", help="Extract text from ROM")
    extract_parser.add_argument("-l", "--lang", default="en", choices=["en", "fr"],
                                help="Language (default: en)")
    extract_parser.add_argument("-r", "--romFile", required=True,
                                help="ROM file path")
    extract_parser.add_argument("-f", "--outFile", required=True,
                                help="Output text file")
    extract_parser.add_argument("-t", "--tblFile", required=True,
                                help="Table (.tbl) file")

    # --- insert ---
    insert_parser = subparsers.add_parser("insert", help="Insert text into ROM")
    insert_parser.add_argument("-l", "--lang", default="en", choices=["en", "fr"],
                               help="Language (default: en)")
    insert_parser.add_argument("-r", "--romFile", required=True,
                               help="ROM file path")
    insert_parser.add_argument("-f", "--inFile", required=True,
                               help="Input text file")
    insert_parser.add_argument("-t", "--tblFile", required=True,
                               help="Table (.tbl) file")

    # Version
    #parser.add_argument("-v", "--version", action="version",
                        #version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "extract":
        rom_file = args.romFile
        tbl_file = args.tblFile
        out_file = args.outFile
        lang = args.lang
        if lang == 'en':
            PTR_START_OFFSET = 0x379DF5
            PTR_END_OFFSET = 0x379E44
            PTR_SIZE = PTR_END_OFFSET - PTR_START_OFFSET + 1
            TREE_START_OFFSET = 0x379EE5
            TREE_END_OFFSET = 0x37A1E4
            TREE_SIZE = TREE_END_OFFSET - TREE_START_OFFSET + 1
            BASE = 0x3A0000
            TEXT_START_OFFSET = 0x3A0000
            TEXT_END_OFFSET = 0x3A5392
            TEXT_SIZE = TEXT_END_OFFSET - TEXT_START_OFFSET + 1
        elif lang == 'fr':
            PTR_START_OFFSET = 0x379E45
            PTR_END_OFFSET = 0x379E94
            PTR_SIZE = PTR_END_OFFSET - PTR_START_OFFSET + 1
            TREE_START_OFFSET = 0x37A1E5
            TREE_END_OFFSET = 0x37A570
            TREE_SIZE = TREE_END_OFFSET - TREE_START_OFFSET + 1
            BASE = 0x3A5393
            TEXT_START_OFFSET = 0x3A5393
            TEXT_END_OFFSET = 0x3AA1B2
            TEXT_SIZE = TEXT_END_OFFSET - TEXT_START_OFFSET + 1
        else:
            print("Invalid Language Exiting...")
            sys.exit(1)

        # Load class
        extract = extraction()

        # Load Tbl
        tbl_dict = extraction.read_tbl(tbl_file)

        # Get Pointers
        ptr_table = extraction.read_rom(rom_file, PTR_START_OFFSET, PTR_SIZE)  

        # Split ptr and lenghts
        ptr_array, length_array = extraction.read_ptr_table(ptr_table, BASE)
        ptr_array = reverse_list(ptr_array)
        length_array = reverse_list(length_array)
        
        # Decomprees
        decompress_blocks = extraction.huffman_decompress(rom_file, tbl_dict, TREE_START_OFFSET, TREE_SIZE, ptr_array, length_array)

        # Write script
        base_out_file = out_file

        for i, block_text in enumerate(decompress_blocks, start=1):
            out_file_i = f"{base_out_file}_{lang}_{i}.txt"
            extraction.write_out_file(out_file_i, block_text, ptr_array[i-1], length_array[i-1])
            print(f"Text extracted to {out_file_i}")
        print(f"TEXT BLOCK SIZE: {TEXT_SIZE} / {hex(TEXT_SIZE)} bytes.")
        print(f"PTR_TABLE BLOCK SIZE: {PTR_SIZE} / {hex(PTR_SIZE)} bytes.")     
        print("Extraction complete.\n")
       
    elif args.command == "insert":
        rom_file = args.romFile
        tbl_file = args.tblFile
        script_file = args.inFile
        lang = args.lang
        if lang == 'en':
            PTR_START_OFFSET = 0x379DF5
            PTR_END_OFFSET = 0x379E44
            PTR_SIZE = PTR_END_OFFSET - PTR_START_OFFSET + 1
            #75 different characters
            TREE_START_OFFSET = 0x379EE5
            TREE_END_OFFSET = 0x37A1E4
            TREE_SIZE = TREE_END_OFFSET - TREE_START_OFFSET + 1
            BASE = 0x0
            TEXT_START_OFFSET = 0x3A0000
            TEXT_END_OFFSET = 0x3A5392
            TEXT_SIZE = TEXT_END_OFFSET - TEXT_START_OFFSET + 1
            
        elif lang == 'fr':          
            PTR_START_OFFSET = 0x379E45
            PTR_END_OFFSET = 0x379E94
            PTR_SIZE = PTR_END_OFFSET - PTR_START_OFFSET + 1
            #90 different characters
            TREE_START_OFFSET = 0x37A1E5
            TREE_END_OFFSET = 0x37A570
            TREE_SIZE = TREE_END_OFFSET - TREE_START_OFFSET + 1
            BASE = 0x0
            TEXT_START_OFFSET = 0x3A5393
            TEXT_END_OFFSET = 0x3AA1B2
            TEXT_SIZE = TEXT_END_OFFSET - TEXT_START_OFFSET + 1
            TEXT_SIZE = 0x6000
        else:
            print("Invalid Language Exiting...")
            sys.exit(1)
            
        # Load class
        insert = insertion()

        # Load Tbl
        tbl_dict, byte_lenghts = insertion.read_tbl(tbl_file)

        # Read Script
        base_in_file = script_file        
        all_scripts = []
        for i in range(1, 21):
            script_path = f"{base_in_file}_{i}.txt"
            script_data = insertion.read_script(script_path)
            all_scripts.append(script_data)

        # Encode Scripts
        encoded_scripts = insertion.encode_text(all_scripts, tbl_dict, byte_lenghts)
        
        # Compress
        compress_script, compress_script_raw_size, scripts_lengths, script_offsets = insertion.huffman_compress(encoded_scripts, rom_file, TREE_START_OFFSET, TREE_SIZE, BASE)
        
        # Create 4 byte pointer
        new_ptr_table_raw_bytes, new_ptr_table_raw_bytes_size = insertion.create_4_bytes_pointers(scripts_lengths, script_offsets)

        # Check raw bytes size
        if compress_script_raw_size > TEXT_SIZE:
            print(f"\nERROR: script size has exceeded its maximum size. Remove {compress_script_raw_size - TEXT_SIZE} bytes of excess in the block.")
            sys.exit(1)
        if new_ptr_table_raw_bytes_size > PTR_SIZE:
            print(f"\nERROR: table pointer size has exceeded its maximum size. Remove {new_ptr_table_raw_bytes_size - PTR_SIZE} excess bytes.")
            sys.exit(1)

        # Write data to ROM and print summary
        script_freespace =  insertion.write_rom(rom_file, TEXT_START_OFFSET, TEXT_SIZE, compress_script, False, 0xFF)
        print(f"Script text written to address {hex(TEXT_START_OFFSET)}, {script_freespace} bytes free.")
        ptrs_freespace = insertion.write_rom(rom_file, PTR_START_OFFSET, PTR_SIZE, new_ptr_table_raw_bytes, False, 0xFF)
        print(f"Pointer table written to address {hex(PTR_START_OFFSET)}, {ptrs_freespace//4} lines/pointers left.")
        
    else:
        sys.stdout.write("Usage: extract <romFile> <outFile> <tblFile>\n")
        sys.stdout.write("       insert <outFile> <romFile> <tblFile>\n")
        sys.stdout.write("       -v show version.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
