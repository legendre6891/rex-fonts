from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

from collections import OrderedDict
import sys
import cgi

if len(sys.argv) != 3:
    print("usage:   generate_glyph_map.py <FONT> <OUTPUT SVG>")
    print("example: make_metrics.py font.otf font-table.svg\n")
    print("This script will create a single svg with all the symbols with"
          " their corresponding bounding boxes, and advance widths")
    sys.exit(1)

in_font  = sys.argv[1]
out_font = sys.argv[2]
font = TTFont(in_font)
glyphset = font.getGlyphSet()

# Find all unique glyphs by unicode
codes = {}
for cmap in font['cmap'].tables:
    codes.update(cmap.cmap)

# This provides Name -> Unicode mapping
code_lookup = {}
for code, name in codes.items():
    code_lookup[name] = code
            
glyphs = OrderedDict(sorted(glyphs.items(), key=lambda x: x[0]))

pre_header="""\
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="800" height="{}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style type="text/css">
      @font-face {{
        font-family: rex;
        src: url('{}');
      }}
    </style>
  </defs>
  <g font-family="rex" font-size="16px">
"""

header=""

g_template     = '<g transform="translate({},{})">'
rect_template  = '<rect x="{:.2f}em" y="{:.2f}em" width="{:.2f}em" height="{:.2f}em" fill="none" stroke="blue" stroke-width="0.2"/>\n'
adv_template   = '<rect x="{:.2f}em" y="{:.2f}em" width="{:.2f}em" height="{:.2f}em" fill="none" stroke="red" stroke-width="0.2"/>\n'
glyph_template = '<text>{}</text>\n'

# Get the height of x, used for scaling
# For now, use that 1ex = 8px, for some reason tests worked that way
#bbox_pen = BoundsPen(None)
#char_x   = glyphset.get('M')
#char_x.draw(bbox_pen)
#x_height = bbox_pen.bounds[3] - bbox_pen.bounds[1]
#scale = 16/x_height
unitsPerEm = 1000
scale = 1/unitsPerEm

# Get the bounding box
bbox_pen = BoundsPen(None, ignoreSinglePoints=True)
def get_bbox(glyph):
    global scale
    glyph.draw(bbox_pen)
    if bbox_pen.bounds == None:
        return None
    (xmin, ymin, xmax, ymax) = bbox_pen.bounds
    bbox_pen.bounds = None
    bbox_pen._start = None
    return (xmin * scale, ymin * scale, xmax * scale, ymax * scale)

# Draw glyphs
padding = 16
y  = 16
lh = 0
ld = 0
count = 1

def draw_glyphs(glyph_set):
    global header
    global line_glyphs
    global glyphset
    for idx, glyph in enumerate(glyph_set):
        code, (xmin, ymin, xmax, ymax) = line_glyphs[idx]
        width = max(font['hmtx'].metrics.get(glyphs[code], 0)[0] * 1/1000, 0)
        header += g_template.format(int(25*idx + 12.5 - (xmax-xmin)/2), int(y + lh))
        header += adv_template.format(0, -ymax, width, ymax-ymin)
        header += glyph_template.format(cgi.escape(chr(code)))
        header += rect_template.format(xmin, -ymax, xmax-xmin, ymax-ymin)
        header += '</g>'

# buffer for line glyphs
line_glyphs = []

for code, name in glyphs.items():
    if code < 32: continue
    
    # Completed a line
    if count%33 == 0:
        draw_glyphs(line_glyphs)

        line_glyphs = []
        y += lh - ld + padding
        lh = 0
        ld = 0
        count += 1
        
    bounds = get_bbox(glyphset.get(name))
    if bounds == None:
        print("No bounds for 0x{:X} aka {}".format(code, name))
        continue

    (xmin, ymin, xmax, ymax) = bounds
    lh = max(lh, ymax*16)
    ld = min(ld, ymin*16)
    count += 1
    
    line_glyphs.append( (code, bounds) )

if len(line_glyphs) > 0:
    draw_glyphs(line_glyphs)

header += "</g></svg>"
header = pre_header.format(y + lh + 16, in_font) + header

with open(out_font, 'w') as f:
    f.write(header)
