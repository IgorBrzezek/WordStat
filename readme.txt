WordStats (ws.py)

A powerful and flexible word length statistics analyzer. This Python script counts word occurrences by their length ranges and presents the results in clear tables, text-based graphs (horizontal and vertical bar charts), and an interactive GUI chart. It's designed for analyzing text files, dictionaries, or any document where word length distribution is important.

Additional Information:
  Author: Igor Brzezek
  GitHub: https://github.com/IgorBrzezek
  Version: 0.0.6
  Date: 16.01.2026

Features:
- Word Length Counting: Analyze words based on custom length ranges (e.g., 2-3, 4-5 characters).
- Automatic Range Detection: Automatically generate statistics for all unique word lengths found in the input.
- Custom Delimiters: Define specific characters to separate words, useful for structured files like dictionaries.
- Multithreaded Processing: Utilize multiple CPU cores for faster analysis of large files.
- Progress Indication: Monitor the processing progress with a percentage display.
- Multiple Output Formats:
  - Formatted table showing length ranges, counts, and percentages.
  - Text-based horizontal bar chart for terminal display.
  - Text-based vertical bar chart for terminal display.
  - Interactive graphical bar chart (requires Matplotlib).
- Color-coded Output: Enhance readability of terminal charts with color (requires Colorama on Windows).
- "Other" Category: Group words that do not fall into any specified length range.
- Output to File: Save all generated reports to a specified text file.

Installation:

To run this program, you need Python 3. The 'matplotlib' library is required for the GUI graph option, and 'colorama' is recommended for colored terminal output, especially on Windows.

1.  Ensure you have Python 3 installed.
2.  Install optional Python packages (if you need GUI graphs or enhanced terminal colors):
    pip install matplotlib colorama

Usage:

Run the script from your terminal.

Basic Examples:
  python ws.py -in text.txt -len 2-3,4-5,6-8
    (Analyzes 'text.txt' for word lengths in ranges 2-3, 4-5, and 6-8)

  python ws.py -in dictionary.dic -len auto --delim ' ' --pb
    (Analyzes 'dictionary.dic', automatically detects all word lengths,
     uses space as a delimiter, and shows progress)

  python ws.py -in document.txt -len 1-5,6-10,11-100 --graph h --color --out report.txt
    (Analyzes 'document.txt' with specified ranges, displays a colored horizontal
     graph, and saves output to 'report.txt'. Note: "11-" is not supported,
     use a large number like 11-100 instead if you want an upper bound.)

  python ws.py -in article.txt -len auto --gui --other
    (Analyzes 'article.txt', automatically detects all word lengths,
     displays a GUI graph, and includes an 'Other' category for unmatched words)

Command-line Options:

  -in FILE             Input text file to analyze (Required)
  -len RANGES          Length ranges in format a-b[,c-d[,e-f...]] or 'auto'
                       Example: -len 2-3,4-5,6-8
                       Example: -len auto (shows statistics for every word length found)
                       (Required)
  -out FILE            Write output to a specified file (same as screen output)
  --delim CHAR         Character used to separate words (default: word boundary detection).
                       Example: --delim ' ' treats all whitespace (spaces, tabs, newlines)
                       as separators. Useful for dictionary files.
                       Example: --delim ';' splits by semicolon and newlines.
                       Note: Newline characters are always treated as implicit delimiters.
  --graph MODE         Display text-based chart: h=horizontal, v=vertical bar chart
  --gui                Display graphical chart (requires --graph option and 'matplotlib' library)
  --color              Use colored bars in text-based charts (red for highest count, etc.)
  --other              Display statistics for words not matching any specified length range
  -t N                 Number of threads for parallel processing (default: 1)
  --pb                 Show progress percentage during file processing
  -h                   Show short help (one-line description, options on next line)
  --help               Show this detailed help message

Notes:
- The script uses regular expressions for word boundary detection by default. If '--delim' is used, splitting occurs based on the provided character and newlines.
- For `--gui` functionality, ensure `matplotlib` is installed. If not, the script will print an error message.
- For colored output, `colorama` is used on Windows. Ensure it's installed if colors don't appear correctly.
- When using `-len auto`, if a very long word is encountered, the GUI graph might not be optimally readable. Consider specifying ranges for better visualization.
- The `--gui` option currently implies a text-based graph (`--graph h` or `--graph v`) must also be specified. This is a minor design quirk.

Changelog:

Version 0.0.6 (2026-01-16)
- Initial release.
- Added support for multithreaded processing.
- Implemented progress bar for file processing.
- Introduced custom delimiter option.
- Enhanced output with text-based and GUI graphs.
- Improved word parsing logic for better accuracy.