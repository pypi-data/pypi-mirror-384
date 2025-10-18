import re
import os

from faster_whisper.transcribe import Word

INTERVAL_PATTERN = re.compile(
    r"( {8}intervals \[(\d*)\]\:\n {12}xmin = (\d*\.?\d*) \n {12}xmax = (\d*\.?\d*) \n {12}text = \"(.*)\" \n)",
    re.MULTILINE,
)

def get_intervals(fp: str):
    with open(fp, 'r', encoding='utf-8') as f:
        matches = re.findall(INTERVAL_PATTERN, f.read())

    assert int(matches[-1][1]) == len(matches), f'Trouble parsing textgrid. Index of final match: {matches[-1][1]}, but {len(matches)} matches.'

    return matches

def get_clip_timestamps(fp: str):
    
    matches = get_intervals(fp)

    speech_segments = []
    for match in matches:
        if match[4] != 'silent':
            speech_segments.append({
                'start': float(match[2]),
                'end': float(match[3])
            })
    
    return speech_segments

def write_textgrid_fill_utterances(fp: str, segments: list[str]):
    orig_text = open(fp, 'r', encoding='utf-8').read()
    intervals = get_intervals(fp)
    j = 0
    for interval in intervals:
        if interval[4] == '':
            if j >= len(segments):
                print(segments)
                raise ValueError(f"Not enough segments provided. Need at least {j+1}, but only have {len(segments)}")
            
            # Escape the pattern and do a simple string replacement
            old_interval = interval[0]
            new_interval = old_interval.replace('text = ""', f'text = "{segments[j]}"')
            
            orig_text = orig_text.replace(old_interval, new_interval, 1)  # Replace only first occurrence
            j += 1
    
    orig = os.path.splitext(fp)
    os.rename(fp, orig[0] + '_blank' + orig[1])
    with open(fp, 'w+', encoding='utf-8') as f:
        f.write(orig_text)

def write_textgrid_words(fp: str, words: list[Word]):

    with open(fp, 'w+', encoding='utf-8') as f:
        f.write("File type = \"ooTextFile\"\nObject class = \"TextGrid\"\n\n")

        audio_start = words[0].start.item()
        audio_end = words[-1].end.item()
        num_words = len(words)

        f.write(f"xmin = {audio_start} \n")
        f.write(f"xmax = {audio_end} \n")
        f.write("tiers? <exists> \n")
        f.write("size = 1 \n")
        f.write("item []: \n")
        f.write("    item [1]:\n")
        f.write("        class = \"WordTier\" \n")
        f.write("        name = \"words\" \n")
        f.write(f"        xmin = {audio_start} \n")
        f.write(f"        xmax = {audio_end} \n")
        f.write(f"        intervals: size = {num_words} )\n")

        for i in range(1, num_words + 1):
            word = words[i-1]
            f.write(f"        intervals [{i}]:\n")
            f.write(f"            xmin = {word.start.item()} \n")
            f.write(f"            xmax = {word.end.item()} \n")
            f.write(f"            text = \"{word.word.strip()}\" \n")