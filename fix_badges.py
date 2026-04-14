#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix badge mismatches in 4 slides."""
import re, sys

FILEPATH = r"d:\04.vscode\화면정의서\건물톡\index.html"

with open(FILEPATH, 'r', encoding='utf-8') as f:
    content = f.read()

CIRCLE = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩']

def compute_tops(n, is_small=False):
    if n == 0: return []
    offset = 24
    if is_small:
        start, end = offset + 57, offset + 400
    else:
        start, end = offset + 72, offset + 460
    if n == 1:
        return [(start + end) // 2]
    step = (end - start) / (n - 1)
    return [int(start + i * step) for i in range(n)]

def remove_all_badges_in_slide(content, slide_id):
    """Remove all wf-num-label spans from a specific slide."""
    start = content.find(f'id="{slide_id}"')
    if start == -1:
        return content
    end_m = re.search(r'<div class="slide"', content[start+10:])
    end = start + 10 + end_m.start() if end_m else len(content)

    chunk = content[start:end]
    # Remove all wf-num-label lines
    chunk_lines = chunk.split('\n')
    new_lines = [l for l in chunk_lines if 'wf-num-label' not in l]
    new_chunk = '\n'.join(new_lines)
    return content[:start] + new_chunk + content[end:]

def add_badges_to_slide(content, slide_id, badge_nums):
    """Add badges to each wireframe in a slide."""
    start = content.find(f'id="{slide_id}"')
    if start == -1:
        return content
    end_m = re.search(r'<div class="slide"', content[start+10:])
    end = start + 10 + end_m.start() if end_m else len(content)
    chunk = content[start:end]

    # Process each wireframe in the chunk
    result = []
    lines = chunk.split('\n')
    i = 0
    wf_found = False
    wf_depth = 0
    wf_is_small = False

    while i < len(lines):
        line = lines[i]

        if not wf_found and '<div class="wireframe"' in line:
            wf_found = True
            wf_is_small = 'height:430px' in line or 'height:300px' in line
            opens = len(re.findall(r'<div\b', line))
            closes = len(re.findall(r'</div>', line))
            wf_depth = opens - closes
            result.append(line)
            i += 1
            continue

        if wf_found:
            opens = len(re.findall(r'<div\b', line))
            closes = len(re.findall(r'</div>', line))
            wf_depth += opens - closes

            if wf_depth <= 0:
                result.append(line)
                wf_found = False

                # Insert badges
                tops = compute_tops(len(badge_nums), wf_is_small)
                indent = re.match(r'(\s*)', line).group(1) + '  '
                for num, top in zip(badge_nums, tops):
                    result.append(f'{indent}<span class="wf-num-label" style="top:{top}px;">{num}</span>')

                i += 1
                continue

        result.append(line)
        i += 1

    new_chunk = '\n'.join(result)
    return content[:start] + new_chunk + content[end:]

# ── Fix 1: slide-UFMDS01510U-2 should have only ①② ──
content = remove_all_badges_in_slide(content, 'slide-UFMDS01510U-2')
content = add_badges_to_slide(content, 'slide-UFMDS01510U-2', ['①', '②'])

# ── Fix 2: slide-UFMDS01510U-3 should have only ④ ──
content = remove_all_badges_in_slide(content, 'slide-UFMDS01510U-3')
content = add_badges_to_slide(content, 'slide-UFMDS01510U-3', ['④'])

# ── Fix 3: slide-UFMDS01520U should have ①②③④ ──
content = remove_all_badges_in_slide(content, 'slide-UFMDS01520U')
content = add_badges_to_slide(content, 'slide-UFMDS01520U', ['①', '②', '③', '④'])

# ── Fix 4: slide-UFMDS01520U-2 should have ①②③④ ──
content = remove_all_badges_in_slide(content, 'slide-UFMDS01520U-2')
content = add_badges_to_slide(content, 'slide-UFMDS01520U-2', ['①', '②', '③', '④'])

with open(FILEPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print("Badge fixes applied.")
