#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Rules 1, 2, 5:
  Rule 5: Replace IT jargon with plain Korean
  Rule 2: Add .wf-num-label badges to all mockup-blocks
  Rule 1: Split slide-UFMDS01510U-2 (5 states) into 2 slides
"""
import re, sys

FILEPATH = r"d:\04.vscode\화면정의서\건물톡\index.html"

with open(FILEPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ──────────────────────────────────────────────
# RULE 5: IT jargon replacements
# ──────────────────────────────────────────────
replacements = [
    # Combined ROLE patterns first (to avoid partial replacement)
    ('ROLE_USER / ROLE_FIELD',          '일반 구성원'),
    ('ROLE_USER · ROLE_FIELD',          '일반 구성원'),
    ('ROLE_USER·FIELD',                 '일반 구성원'),
    ('ROLE_USER/FIELD',                 '일반 구성원'),
    ('ROLE_MANAGER·ADMIN',              '건물 관리자·앱 관리자'),
    ('ROLE_MANAGER · ROLE_ADMIN',       '건물 관리자 · 앱 관리자'),
    ('ROLE_MANAGER · ADMIN',            '건물 관리자·앱 관리자'),
    ('ROLE_MANAGER·ROLE_ADMIN',         '건물 관리자·앱 관리자'),
    # Individual ROLE
    ('ROLE_USER',                       '일반 구성원'),
    ('ROLE_FIELD',                      '일반 구성원'),
    ('ROLE_MANAGER',                    '건물 관리자'),
    ('ROLE_ADMIN',                      '앱 관리자'),
    # API terms
    ('API: GET /posts/{postId} 응답값으로', '서버에서 받은 기존 게시글 내용으로'),
    ('API 호출 성공',                    '저장 성공'),
    ('API 실패',                         '저장 실패'),
    ('게시글 목록 API 응답이 빈 배열([ ]) 이면', '게시글 목록이 비어 있으면'),
    ('GET API',                          '데이터 불러오기'),
    ('PATCH API',                        '데이터 수정'),
    ('API',                              '서버 연동'),
    # Other
    ('Back Stack',                      '화면 이동 기록'),
    ('shimmer',                         '반짝임 로딩 효과'),
    ('CMS 관리 권장',                    '관리 시스템으로 관리 권장'),
    ('CMS',                             '관리 시스템'),
    (' BO에서',                          ' 운영자 화면에서'),
    ('FAB(+)',                           '글쓰기 버튼(+)'),
    ('(FAB)',                            '(글쓰기 버튼)'),
    ('FAB 숨김',                         '글쓰기 버튼 숨김'),
    # Only plain FAB remaining (not in class names / HTML comments)
    # We replace FAB only when surrounded by typical text context
]

for old, new in replacements:
    content = content.replace(old, new)

# Targeted: remaining bare "FAB" in spec text (not CSS comments)
# Replace "FAB" when not inside an HTML comment or class attribute
# Simple approach: replace in spec-table and annotation areas
# Since remaining FAB occurrences are in visible spec text, global replace is OK
content = re.sub(r'\bFAB\b', '글쓰기 버튼', content)

# opacity in spec-table text only (not in style attributes)
# Pattern: " opacity 0.55" or "opacity 0.5" in text content (not style="...opacity...")
content = re.sub(
    r'(?<![";])opacity ([\d.]+)(?![\s]*[;"\)])',
    lambda m: f'흐림 처리({m.group(1)})',
    content
)

# ──────────────────────────────────────────────
# RULE 2: CSS changes
# ──────────────────────────────────────────────

# 1. Add position:relative to .mockup-block
content = content.replace(
    '  .mockup-block { display: flex; flex-direction: column; align-items: center; gap: 6px; }',
    '  .mockup-block { display: flex; flex-direction: column; align-items: center; gap: 6px; position: relative; }'
)

# 2. Add .wf-num-label CSS after .mockup-label.tobe rule
wf_badge_css = """  .wf-num-label {
    position: absolute;
    background: var(--brand);
    color: #fff;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 9px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 30;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    border: 1.5px solid #fff;
    right: -9px;
    pointer-events: none;
    line-height: 1;
  }"""

content = content.replace(
    '  .mockup-label.tobe { background: var(--brand); color: #fff; }',
    '  .mockup-label.tobe { background: var(--brand); color: #fff; }\n' + wf_badge_css
)

# ──────────────────────────────────────────────
# RULE 2: Parse spec rows per slide
# ──────────────────────────────────────────────

CIRCLE_NUMS = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩']

lines = content.split('\n')
slide_spec_rows = {}  # {slide_id: ['①','②',...]}
current_slide_id = None
in_spec_table = False

for line in lines:
    # Detect slide ID
    m = re.search(r'<div class="slide"[^>]* id="(slide-[^"]+)"', line)
    if m:
        current_slide_id = m.group(1)
        slide_spec_rows.setdefault(current_slide_id, [])

    # Detect spec table boundaries
    if '<table class="spec-table">' in line:
        in_spec_table = True
    if '</table>' in line:
        in_spec_table = False

    # Collect spec row numbers
    if in_spec_table and current_slide_id:
        for cn in CIRCLE_NUMS:
            if f'<td>{cn}</td>' in line:
                rows = slide_spec_rows[current_slide_id]
                if cn not in rows:
                    rows.append(cn)
                break

# ──────────────────────────────────────────────
# RULE 2: Add badges to mockup-blocks
# ──────────────────────────────────────────────

def compute_tops(n, is_small):
    """Compute badge top positions within the mockup-block coordinate space.
    Label ~18px + gap ~6px → wireframe starts at ~24px.
    For normal (490px): body from top+66 to top+484.
    For small (430px): body from top+57 to top+427.
    """
    if n == 0:
        return []
    offset = 24  # label + gap
    if is_small:
        wf_h = 430
        body_start = 57   # status-bar ~14px + header ~25px + offset
        body_end   = 400
    else:
        wf_h = 490
        body_start = 72   # status-bar ~18px + header ~30px + offset
        body_end   = 460

    start = offset + body_start
    end   = offset + body_end

    if n == 1:
        return [(start + end) // 2]
    step = (end - start) / (n - 1)
    return [int(start + i * step) for i in range(n)]

def process_badges(lines_in, slide_spec_rows):
    result = []
    i = 0
    current_slide = None
    in_mb = False        # inside mockup-block
    wf_found = False     # wireframe div detected
    wf_depth = 0
    wf_is_small = False

    while i < len(lines_in):
        line = lines_in[i]

        # Detect slide ID
        m = re.search(r'<div class="slide"[^>]* id="(slide-[^"]+)"', line)
        if m:
            current_slide = m.group(1)

        # Detect mockup-block start
        if 'class="mockup-block"' in line:
            in_mb = True
            wf_found = False
            wf_depth = 0

        # Detect wireframe start inside mockup-block
        if in_mb and not wf_found and '<div class="wireframe"' in line:
            wf_found = True
            wf_is_small = ('height:430px' in line or 'height:300px' in line
                           or 'height:350px' in line)
            # Count divs on this opening line itself
            opens  = len(re.findall(r'<div\b', line))
            closes = len(re.findall(r'</div>', line))
            wf_depth = opens - closes   # should be 1
            result.append(line)
            i += 1
            continue

        if wf_found:
            opens  = len(re.findall(r'<div\b', line))
            closes = len(re.findall(r'</div>', line))
            wf_depth += opens - closes

            if wf_depth <= 0:
                # Wireframe just closed – append close line first
                result.append(line)
                wf_found = False

                # Insert badges
                rows = slide_spec_rows.get(current_slide, [])
                if rows:
                    tops = compute_tops(len(rows), wf_is_small)
                    indent = re.match(r'(\s*)', line).group(1)
                    # Shift right by 2 spaces relative to the wireframe close tag
                    bi = indent + '  '
                    for row_num, top in zip(rows, tops):
                        result.append(
                            f'{bi}<span class="wf-num-label" style="top:{top}px;">{row_num}</span>\n'
                        )
                i += 1
                continue

        result.append(line)
        i += 1

    return result

lines = process_badges(lines, slide_spec_rows)
content = '\n'.join(lines)

# ──────────────────────────────────────────────
# RULE 1: Split slide-UFMDS01510U-2 (5 states → 2 slides)
# ──────────────────────────────────────────────
# Current: S04, S05, S06, S07, S08 on one slide
# After:   slide-UFMDS01510U-2  → S04, S05  (spec rows ①②)
#          slide-UFMDS01510U-3  → S06, S07, S08 (spec row ④)

# Build replacement for slide-UFMDS01510U-2
OLD_SLIDE2 = '''<div class="slide" id="slide-UFMDS01510U-2">
  <div class="slide-header">
    <div class="breadcrumb">
      <b>건물톡</b>
      <span class="sep">›</span>
      <span>게시글 상세</span>
      <span class="sep">›</span>
      <span style="color:rgba(255,255,255,0.5);">분실물 상태 · 댓글 조건부</span>
    </div>
    <div class="slide-id">UFMDS01510U — 2/2</div>
  </div>'''

NEW_SLIDE2_HEADER = '''<div class="slide" id="slide-UFMDS01510U-2">
  <div class="slide-header">
    <div class="breadcrumb">
      <b>건물톡</b>
      <span class="sep">›</span>
      <span>게시글 상세</span>
      <span class="sep">›</span>
      <span style="color:rgba(255,255,255,0.5);">분실물 상태 (S04 · S05)</span>
    </div>
    <div class="slide-id">UFMDS01510U — 2/3</div>
  </div>'''

content = content.replace(OLD_SLIDE2, NEW_SLIDE2_HEADER, 1)

# Fix meta block (슬라이드 2/2 → 2/3, 이 슬라이드 값)
content = content.replace(
    '          <span class="meta-value">2 / 2</span>',
    '          <span class="meta-value">2 / 3</span>',
    1
)
content = content.replace(
    '          <span class="meta-value" style="font-size:11px; line-height:1.6;">S04 분실물 찾는중<br>S05 분실물 해결됨<br>S06 댓글 있음<br>S07 댓글 없음<br>S08 댓글 미허용</span>',
    '          <span class="meta-value" style="font-size:11px; line-height:1.6;">S04 분실물 찾는중<br>S05 분실물 해결됨</span>',
    1
)

# ── Find the boundaries of S06 ~ end of spec-table inside slide-UFMDS01510U-2 ──
# Strategy: find "<!-- S06: 댓글 있음 -->" and extract from there to end of the slide

# Find position of S06 comment inside slide-UFMDS01510U-2
slide2_start = content.index('<div class="slide" id="slide-UFMDS01510U-2">')

# S06 block starts with this comment
S06_MARKER = '          <!-- S06: 댓글 있음 -->'
s06_pos = content.index(S06_MARKER, slide2_start)

# The spec-zone that covers S04–S08 starts right after the mockup-zone ends
# Find "        </div><!-- /mockup-zone -->" after S06
MOCKUP_ZONE_END = '        </div><!-- /mockup-zone -->'
mz_end_pos = content.index(MOCKUP_ZONE_END, s06_pos)

# Find where slide-UFMDS01510U-2 ENDS (closing </div> for the slide)
# The slide ends with </div> after the spec zone. We find the next slide start.
NEXT_SLIDE_MARKER = '\n\n\n<!-- ══'
next_slide_pos = content.index(NEXT_SLIDE_MARKER, mz_end_pos)

# The spec section (from after mockup-zone to slide end)
spec_and_tail = content[mz_end_pos:next_slide_pos]

# Extract the 3 spec rows that go on each new slide
# Row ① and ② → stay on slide-2
# Row ④ → move to slide-3

# The spec table content
spec_table_start = spec_and_tail.index('<table class="spec-table">')
spec_table_end   = spec_and_tail.index('</table>') + len('</table>')
spec_table_full  = spec_and_tail[spec_table_start:spec_table_end]

# Extract thead
thead_m = re.search(r'(<thead>.*?</thead>)', spec_table_full, re.DOTALL)
thead = thead_m.group(1) if thead_m else ''

# Extract tbody rows
row_pattern = re.compile(r'<tr>.*?</tr>', re.DOTALL)
rows_all = row_pattern.findall(spec_table_full)

rows_s04s05 = [r for r in rows_all if '①' in r or '②' in r]  # rows for S04/S05
rows_s06s08 = [r for r in rows_all if '④' in r]               # row for S06-S08

def make_spec_table(thead_html, rows_list):
    rows_str = '\n              '.join(rows_list)
    return f'''<table class="spec-table">
            {thead_html}
            <tbody>
              {rows_str}
            </tbody>
          </table>'''

spec_table_s04s05 = make_spec_table(thead, rows_s04s05)
spec_table_s06s08 = make_spec_table(thead, rows_s06s08)

# The callout div (state transition flow) - move to slide-3 only
callout_start = spec_and_tail.find('<!-- State transition callout -->')
callout_html = ''
if callout_start != -1:
    callout_end = spec_and_tail.find('</div><!-- /spec-zone -->', callout_start)
    if callout_end != -1:
        callout_html = spec_and_tail[callout_start:callout_end]

# The rest of spec_and_tail after spec-table (footer etc.)
footer_start = spec_and_tail.index('</table>') + len('</table>')
footer_end   = len(spec_and_tail)
footer_html  = spec_and_tail[footer_start:footer_end]  # includes spec-zone close, slide footer

# Build the NEW content for the section between s06_pos and next_slide_pos
# Slide-2 gets: S04, S05 mockup-blocks + spec for ①②
# The S06-S08 mockup-blocks are REMOVED from slide-2

# Build new spec zone for slide-2 (without the callout)
new_spec_zone_s2 = f'''        </div><!-- /mockup-zone -->

        <!-- Spec zone -->
        <div class="spec-zone">
          <div class="spec-screen-title">게시글 상세 (S04–S05) — 분실물 상태</div>

          {spec_table_s04s05}
        </div><!-- /spec-zone -->

      </div><!-- /screen-content -->
    </div><!-- /slide-main -->
  </div><!-- /slide-body -->

  <div class="slide-footer">
    <span class="footer-crumb">건물톡 화면정의서 <span class="sep">›</span> <b>게시글 상세</b></span>
    <span class="footer-right">UFMDS01510U · SD2026-003 · V0.1</span>
  </div>
</div>'''

# Now build slide-3 (S06, S07, S08)
# Extract nav HTML from slide-2 (reuse the same nav)
nav_start = content.index('    <!-- Left Nav -->', slide2_start)
nav_end   = content.index('    <!-- Main -->', nav_start)
nav_html  = content[nav_start:nav_end].rstrip()

# S06, S07, S08 mockup blocks
s06s07s08_end = content.index(MOCKUP_ZONE_END, s06_pos) + len(MOCKUP_ZONE_END)
s06s07s08_html = content[s06_pos:s06s07s08_end]  # includes the 3 mockup blocks + zone close

slide3_html = f'''

<!-- ══════════════════════════════════════
     SLIDE: UFMDS01510U 게시글 상세 — S06·S07·S08
══════════════════════════════════════ -->
<div class="slide" id="slide-UFMDS01510U-3">
  <div class="slide-header">
    <div class="breadcrumb">
      <b>건물톡</b>
      <span class="sep">›</span>
      <span>게시글 상세</span>
      <span class="sep">›</span>
      <span style="color:rgba(255,255,255,0.5);">댓글 조건부 렌더링 (S06 · S07 · S08)</span>
    </div>
    <div class="slide-id">UFMDS01510U — 3/3</div>
  </div>

  <div class="slide-body">
{nav_html}

    <!-- Main -->
    <div class="slide-main">
      <!-- Screen meta -->
      <div class="screen-meta">
        <div class="meta-row">
          <span class="meta-label">화면 ID</span>
          <span class="meta-value code">UFMDS01510U</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">슬라이드</span>
          <span class="meta-value">3 / 3</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">이 슬라이드</span>
          <span class="meta-value" style="font-size:11px; line-height:1.6;">S06 댓글 있음<br>S07 댓글 없음<br>S08 댓글 미허용</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">상태 변경</span>
          <span class="meta-value" style="font-size:11px;">건물 관리자 설정</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">우선순위</span>
          <span class="meta-tag tag-p1">P1</span>
        </div>
      </div>

      <!-- Content -->
      <div class="screen-content">
        <!-- 3 Wireframes -->
        <div class="mockup-zone" style="gap:7px; align-items:flex-start; padding:8px 6px;">
{s06s07s08_html.rstrip()}

        <!-- Spec zone -->
        <div class="spec-zone">
          <div class="spec-screen-title">게시글 상세 (S06–S08) — 댓글 조건부 렌더링</div>

          {spec_table_s06s08}

          {callout_html}
        </div><!-- /spec-zone -->

      </div><!-- /screen-content -->
    </div><!-- /slide-main -->
  </div><!-- /slide-body -->

  <div class="slide-footer">
    <span class="footer-crumb">건물톡 화면정의서 <span class="sep">›</span> <b>게시글 상세</b></span>
    <span class="footer-right">UFMDS01510U · SD2026-003 · V0.1</span>
  </div>
</div>'''

# Replace the original content from s06_pos to next_slide_pos
# with: new_spec_zone_s2 + slide3_html
content = content[:s06_pos] + new_spec_zone_s2 + slide3_html + content[next_slide_pos:]

# ──────────────────────────────────────────────
# Write output
# ──────────────────────────────────────────────
with open(FILEPATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done. File written.")
