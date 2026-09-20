import re

with open('spa/src/components/OldMiniPlayer.tmp.vue', 'r') as f:
    old_content = f.read()

with open('spa/src/components/MiniPlayer.vue', 'r') as f:
    current_content = f.read()

# Extract old timeline + container
old_match = re.search(r'(<!-- Timeline scrubber \(above controls\) -->.*?</div>\s*)(<!-- Cast Modal -->)', old_content, re.DOTALL)
if not old_match:
    old_match = re.search(r'(<!-- Timeline scrubber \(above controls\) -->.*?</div>\n    </div>\n\n    <!-- Cast Modal -->)', old_content, re.DOTALL)
    if not old_match:
        print("Failed to find old timeline + container block")
        exit(1)

old_block = old_match.group(1).strip()
# Notice: old_block includes the closing wrapper for 'now-playing-glass', let's be careful.
# Actually, let's just find the exact boundaries.

# Find old timeline
old_tl_m = re.search(r'(<!-- Timeline scrubber \(above controls\) -->.*?</div>)(\s+<div class="now-playing-container">)', old_content, re.DOTALL)
old_timeline = old_tl_m.group(1)

# Find old container
old_cnt_m = re.search(r'(<div class="now-playing-container">.*?)(\n    </div>\n\n    <!-- Cast Modal -->)', old_content, re.DOTALL)
old_container = old_cnt_m.group(1)

# Current template
curr_tl_m = re.search(r'(<!-- Timeline scrubber \(above controls, desktop only\) -->.*?</div>)(\s+<div class="now-playing-container mobile-slot-2">)', current_content, re.DOTALL)
if not curr_tl_m:
    print("Failed to find current timeline block")
    exit(1)
curr_timeline = curr_tl_m.group(1)

curr_cnt_m = re.search(r'(<div class="now-playing-container mobile-slot-2">.*?)(\n    </div>\n\n    <!-- Cast Modal -->)', current_content, re.DOTALL)
curr_container = curr_cnt_m.group(1)

new_template_body = f"""
      <div class="desktop-layout-wrapper" style="width: 100%;">
{old_timeline}
{old_container}
      </div>

      <div class="mobile-layout-wrapper" style="width: 100%;">
{curr_container}
      </div>
"""

# Replace in current content
new_content = current_content.replace(curr_tl_m.group(1) + curr_tl_m.group(2) + curr_container, new_template_body)

# Append styles
new_content = new_content.replace('</style>', '''
.desktop-layout-wrapper { display: block; }
.mobile-layout-wrapper { display: none; }
@media (max-width: 768px) {
  .desktop-layout-wrapper { display: none !important; }
  .mobile-layout-wrapper { display: block !important; }
}
</style>''', 1)

with open('spa/src/components/MiniPlayer.vue', 'w') as f:
    f.write(new_content)

print("Patch applied successfully.")
