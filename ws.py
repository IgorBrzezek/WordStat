#!/usr/bin/env python3
"""
WordStats v0.0.6
Word length statistics analyzer.
Counts word occurrences by length ranges and displays results in tables and graphs.
"""

import argparse
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from collections import Counter


# === Program data =====================================================
__CODE_VERSION__ = "0.0.6"
__CODE_AUTHOR__ =  "Igor Brzezek"
__CODE_DATE__ = "16.01.2026"
__CODE_GITHUB__ = "https://github.com/IgorBrzezek"
# ======================================================================

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import colorama
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

progress_lock = threading.Lock()


@dataclass(frozen=True)
class LengthRange:
    min_len: int
    max_len: int

    def contains(self, length: int) -> bool:
        return self.min_len <= length <= self.max_len

    def __str__(self) -> str:
        return f"{self.min_len}-{self.max_len}"


class WordCounter:
    def __init__(self, length_ranges: List[LengthRange]):
        self.length_ranges = length_ranges
        self.counts = {length_range: 0 for length_range in length_ranges}
        self.other_count = 0
        self.total_words = 0

    def count_words(self, words: List[int]) -> None:
        for word_len in words:
            self.total_words += 1
            matched = False
            for length_range in self.length_ranges:
                if length_range.contains(word_len):
                    self.counts[length_range] += 1
                    matched = True
                    break
            if not matched:
                self.other_count += 1


def get_terminal_size() -> Tuple[int, int]:
    try:
        import shutil
        return shutil.get_terminal_size()
    except:
        return 80, 24


COLORS = [
    '\033[91m',  # Red (highest)
    '\033[93m',  # Yellow
    '\033[92m',  # Green
    '\033[96m',  # Cyan
    '\033[95m',  # Magenta
    '\033[97m',  # White
]
RESET = '\033[0m'


def get_color(index: int, total: int, use_color: bool) -> str:
    if not use_color or total <= 1:
        return ''
    if sys.platform == 'win32' and not HAS_COLORAMA:
        return ''
    color_index = min(index, len(COLORS) - 1)
    return COLORS[color_index]


def parse_length_ranges(range_str: str) -> List[LengthRange]:
    if range_str == 'auto':
        return []
    ranges = []
    parts = range_str.split(',')
    for part in parts:
        if '-' in part:
            min_len, max_len = part.split('-')
            ranges.append(LengthRange(int(min_len), int(max_len)))
        else:
            length = int(part)
            ranges.append(LengthRange(length, length))
    return ranges


def count_words_from_list(words: List[str]) -> Counter:
    lengths = [len(word) for word in words]
    return Counter(lengths)


def process_file(filepath: str, num_threads: int, show_progress: bool, delimiter: Optional[str] = None) -> Counter:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if delimiter:
        # If delimiter is a space, treat all whitespace (newlines, tabs, etc.) as delimiters
        if delimiter == " ":
            words = content.split()
        else:
            # Escape delimiter and split strictly, but also handle newlines as implicit delimiters
            # to avoid treating the whole file as one word if \n is present
            escaped_delim = re.escape(delimiter)
            # Split by the delimiter OR newline characters
            words = re.split(f'[{escaped_delim}\\n\\r]+', content)
        
        words = [word.strip() for word in words if word.strip()]
    else:
        # Default behavior: standard word boundary detection
        words = re.findall(r'\b\w+\b', content)

    total_words = len(words)

    if show_progress:
        print('Progress: 0.0%', end='\r', file=sys.stderr)

    if total_words == 0:
        return Counter()

    if num_threads == 1:
        counter = Counter()
        for idx, word in enumerate(words):
            counter.update([len(word)])
            if show_progress and idx % 1000 == 0:
                progress = (idx / total_words) * 100
                print(f'Progress: {progress:.1f}%', end='\r', flush=True, file=sys.stderr)
        if show_progress:
            print('Progress: 100.0%', flush=True, file=sys.stderr)
        return counter

    chunk_size = total_words // num_threads
    results = []
    processed_words = [0]

    def process_word_chunk(start_idx: int, end_idx: int) -> Counter:
        word_chunk = words[start_idx:end_idx]
        result = count_words_from_list(word_chunk)

        with progress_lock:
            processed_words[0] += len(word_chunk)
            if show_progress and processed_words[0] % 1000 == 0:
                progress = (processed_words[0] / total_words) * 100
                print(f'Progress: {progress:.1f}%', end='\r', flush=True, file=sys.stderr)

        return result

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < num_threads - 1 else total_words
            futures.append(executor.submit(process_word_chunk, start_idx, end_idx))

        for future in futures:
            results.append(future.result())

    if show_progress:
        print('Progress: 100.0%', flush=True, file=sys.stderr)

    total_counter = Counter()
    for counter in results:
        total_counter.update(counter)

    return total_counter


def display_table(counter: WordCounter, use_color: bool, show_other: bool) -> str:
    output = []
    output.append('\n' + '=' * 60)
    output.append('Word Length Statistics')
    output.append('=' * 60)
    output.append(f"{'Length Range':<20} {'Count':<15} {'Percentage':<15}")
    output.append('-' * 60)

    items = [(str(lr), counter.counts[lr]) for lr in counter.length_ranges]
    if show_other:
        items.append(('Other', counter.other_count))

    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
    color_map = {item: idx for idx, item in enumerate(sorted_items)}

    for idx, (range_str, count) in enumerate(items):
        percentage = (count / counter.total_words * 100) if counter.total_words > 0 else 0
        color = ''
        if use_color and count > 0:
            color_idx = color_map.get((range_str, count), 0)
            color = get_color(color_idx, len(sorted_items) - 1, True)
        should_use_color = use_color and color and (sys.platform != 'win32' or HAS_COLORAMA)
        reset = RESET if should_use_color else ''
        if not should_use_color:
            color = ''
        output.append(f'{color}{range_str:<20} {count:<15} {percentage:>6.2f}%{reset}')

    output.append('-' * 60)
    output.append(f'{"Total":<20} {counter.total_words:<15} 100.00%')
    output.append('=' * 60 + '\n')

    return '\n'.join(output)


def display_horizontal_graph(counter: WordCounter, use_color: bool, show_other: bool) -> str:
    term_width, _ = get_terminal_size()
    max_bar_width = term_width - 45

    output = []
    output.append('\n' + '=' * term_width)
    output.append('Horizontal Bar Graph')
    output.append('=' * term_width)
    output.append(f"{'Length Range':<15} {'Count':<10} {'Bar':<{max_bar_width}}")
    output.append('-' * term_width)

    items = [(str(lr), counter.counts[lr]) for lr in counter.length_ranges]
    if show_other:
        items.append(('Other', counter.other_count))

    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
    color_map = {item: idx for idx, item in enumerate(sorted_items)}
    max_count = max(count for _, count in items) if items else 1

    for idx, (range_str, count) in enumerate(items):
        bar_length = int((count / max_count) * max_bar_width) if max_count > 0 else 0
        bar = '█' * bar_length
        color = ''
        if use_color and count > 0:
            color_idx = color_map.get((range_str, count), 0)
            color = get_color(color_idx, len(sorted_items) - 1, True)
        should_use_color = use_color and color and (sys.platform != 'win32' or HAS_COLORAMA)
        reset = RESET if should_use_color else ''
        if not should_use_color:
            color = ''
        output.append(f'{color}{range_str:<15} {count:<10} {bar:<{max_bar_width}}{reset}')

    output.append('=' * term_width + '\n')

    return '\n'.join(output)


def display_vertical_graph(counter: WordCounter, use_color: bool, show_other: bool) -> str:
    _, term_height = get_terminal_size()
    max_chart_height = int((term_height - 10) * 0.6)

    items = [(str(lr), counter.counts[lr]) for lr in counter.length_ranges]
    if show_other:
        items.append(('Other', counter.other_count))

    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
    color_map = {item: idx for idx, item in enumerate(sorted_items)}
    max_count = max(count for _, count in items) if items else 1
    chart_height = min(max_chart_height, max_count)

    output = []
    output.append('\n' + '=' * 50)
    output.append('Vertical Bar Graph')
    output.append('=' * 50)

    bar_heights = []
    for _, count in items:
        height = int((count / max_count) * chart_height) if max_count > 0 else 0
        bar_heights.append(max(1, height))

    for level in range(max(bar_heights), 0, -1):
        row = []
        for idx, bar_height in enumerate(bar_heights):
            color = ''
            if use_color and bar_height >= level:
                count = items[idx][1]
                if count > 0:
                    color_idx = color_map.get(items[idx], 0)
                    color = get_color(color_idx, len(sorted_items) - 1, True)
            should_use_color = use_color and color and (sys.platform != 'win32' or HAS_COLORAMA)
            reset = RESET if should_use_color else ''
            if not should_use_color:
                color = ''
            if bar_height >= level:
                row.append(f'{color}██{reset}')
            else:
                row.append('  ')
        output.append('  ' + ' '.join(row))

    output.append('  ' + '-'.join(['--' for _ in items]))
    labels = [range_str[:2].ljust(2) for range_str, _ in items]
    output.append('  ' + ' '.join(labels))
    output.append('=' * 50 + '\n')

    return '\n'.join(output)


def display_gui_graph(counter: WordCounter, show_other: bool) -> None:
    if not HAS_MATPLOTLIB:
        print("Error: matplotlib is not installed. Install it with: pip install matplotlib")
        return

    labels = [str(lr.min_len) if lr.min_len == lr.max_len else str(lr) for lr in counter.length_ranges]
    counts = [counter.counts[lr] for lr in counter.length_ranges]

    if show_other:
        labels.append('Other')
        counts.append(counter.other_count)

    colors = ['#ff0000', '#ffff00', '#00ff00', '#00ffff', '#ff00ff', '#ffffff']

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#e0e0e0')
    ax.set_facecolor('#e0e0e0')
    bars = ax.bar(labels, counts, color=colors[:len(labels)])

    ax.set_xlabel('Length Range')
    ax.set_ylabel('Word Count')
    ax.set_title('Word Length Distribution')

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'{int(height)}',
                ha='center', va='bottom')

    plt.tight_layout()
    plt.show()


def print_short_help() -> None:
    print(f"Word Length Statistics Analyzer - Author: {__CODE_AUTHOR__} - Version: {__CODE_VERSION__} - Date: {__CODE_DATE__}", file=sys.stderr)
    print(file=sys.stderr)
    print("Word Length Statistics Analyzer - Count word lengths in text files", file=sys.stderr)
    print("Options: -in FILE -len RANGES|auto [-out FILE] [--delim CHAR] [--graph h|v] [--color] [--other] [-t N] [--pb] [--gui] [-h|--help]", file=sys.stderr)


def print_long_help() -> None:
    print(f"Word Length Statistics Analyzer - Author: {__CODE_AUTHOR__} - Version: {__CODE_VERSION__} - Date: {__CODE_DATE__}", file=sys.stderr)
    print(file=sys.stderr)
    print("""
Word Length Statistics Analyzer
 
A program that counts word occurrences by length ranges and displays results
in tables and/or text-based or graphical charts.

USAGE:
    word_stats.py -in FILE -len RANGES [OPTIONS]
 
REQUIRED OPTIONS:
    -in FILE        Input text file to analyze
    -len RANGES     Length ranges in format a-b[,c-d[,e-f...]] or 'auto'
                    Example: -len 2-3,4-5,6-8 counts words with length 2-3, 4-5, or 6-8
                    Example: -len auto shows statistics for every word length found
 
OUTPUT OPTIONS:
    -out FILE       Write output to file (same as screen output)
    --graph MODE    Display text-based chart: h=horizontal, v=vertical bar chart
    --gui           Display graphical chart (requires --graph and matplotlib)
 
DELIMITER OPTIONS:
    --delim CHAR    Character used to separate words (default: word boundary detection)
                    Example: --delim ' ' treats all whitespace (spaces, tabs, newlines) 
                    as separators. Useful for dictionary files (.dic).
                    Example: --delim ';' splits by semicolon and newlines.
                    Note: The program always treats newline characters as implicit 
                    delimiters to prevent counting large file blocks as single words.
 
DISPLAY OPTIONS:
    --color         Use colored bars in charts (red for highest count, then yellow, green, cyan, magenta, white)
    --other         Display statistics for words not matching any specified length range
 
PERFORMANCE OPTIONS:
    -t N            Number of threads for parallel processing (default: 1)
    --pb            Show progress percentage during file processing
 
HELP OPTIONS:
    -h              Show short help (one line description, options on next line)
    --help          Show this detailed help message
 
EXAMPLES:
    word_stats.py -in text.txt -len 2-3,4-5,6-8
    word_stats.py -in dictionary.dic -len auto --delim ' ' --pb
""", file=sys.stderr)


def main():
    args = sys.argv[1:]

    if '-h' in args:
        print_short_help()
        sys.exit(0)

    if '--help' in args:
        print_long_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-in', dest='input_file', required=True,
                        help='Input text file to analyze')
    parser.add_argument('-out', dest='output_file', default=None,
                        help='Output file for results')
    parser.add_argument('-len', dest='length_ranges', required=True,
                        help='Length ranges in format a-b[,c-d[,e-f...]] or "auto" for all word lengths')
    parser.add_argument('--delim', dest='delimiter', default=None,
                        help='Character used to separate words (default: word boundary detection)')
    parser.add_argument('--graph', dest='graph_mode', choices=['h', 'v'], default=None,
                        help='Display text-based chart: h=horizontal, v=vertical')
    parser.add_argument('--gui', dest='gui', action='store_true',
                        help='Display graphical chart (requires --graph)')
    parser.add_argument('--color', dest='use_color', action='store_true',
                        help='Use colored bars in charts')
    parser.add_argument('--other', dest='show_other', action='store_true',
                        help='Display statistics for words not matching any specified length range')
    parser.add_argument('-t', dest='num_threads', type=int, default=1,
                        help='Number of threads for parallel processing (default: 1)')
    parser.add_argument('--pb', dest='show_progress', action='store_true',
                        help='Show progress percentage during file processing')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.gui and not args.graph_mode:
        print("Error: --gui requires --graph option.", file=sys.stderr)
        sys.exit(1)

    length_ranges = parse_length_ranges(args.length_ranges)
    length_counter = Counter(process_file(args.input_file, args.num_threads, args.show_progress, args.delimiter))

    if not length_ranges:
        max_len = max(length_counter.keys()) if length_counter else 0
        if max_len > 1000:
            length_ranges = [LengthRange(length, length) for length in sorted(length_counter.keys())]
        else:
            length_ranges = [LengthRange(i, i) for i in range(1, max_len + 1)]

    counter = WordCounter(length_ranges)
    for length, count in length_counter.items():
        matched = False
        for length_range in length_ranges:
            if length_range.contains(length):
                counter.counts[length_range] += count
                matched = True
                break
        if not matched:
            counter.other_count += count
        counter.total_words += count

    output_lines = []

    output_lines.append(display_table(counter, args.use_color, args.show_other))

    if args.graph_mode == 'h':
        output_lines.append(display_horizontal_graph(counter, args.use_color, args.show_other))
    elif args.graph_mode == 'v':
        output_lines.append(display_vertical_graph(counter, args.use_color, args.show_other))

    output = '\n'.join(output_lines)

    print(output)

    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(output)

    if args.gui:
        display_gui_graph(counter, args.show_other)


if __name__ == '__main__':
    main()
