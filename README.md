This tool allows simple extraction and insertion of text from the SNES USA version of Donkey Kong Country 3.
The pointer table is automatically updated, and all required table files are included.

## Usage

Synopsis:
```
dkc3_texteditor [extract|insert] -l [en | fr] -r "romfile" -f "outFile" -t "tableFile"

-h - Display help

-v - Output version information
```

Examples:

Extract:
```
dkc3_texteditor extract -l en -r "Donkey Kong Country 3.sfc" -f "dkc3_script" -t "dkc3_en.tbl"
```
Insert:
```
dkc3_texteditor insert -l en -r "Donkey Kong Country 3.sfc" -f "dkc3_script_en" -t "dkc3_en.tbl"
```

Once extracted, the tool will generate 20 text files. These can be easily edited using any text editor, such as Notepad++. After editing, the files can be reinserted into the game.

### Notes

The game uses Huffman compression, which means the number of distinct characters is limited by the size of the dictionary. This program does not modify the dictionary entries; instead, it compresses the text using the original dictionary.

As a recommendation, if you plan to translate the game into another language, it is advised to edit the French script, as it allows a larger character set (15 additional characters).

The project also includes an optional ASM routine written for the SNES Asar assembler. This routine sets French as the default language and disables English.

## Frecuency Answer Questions

### Can I use this tool in my personal project?

Of course, there's no need to ask. Feel free to use it in your project. I only ask that you mention me as contributor.

