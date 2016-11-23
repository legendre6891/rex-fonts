import os
import sys
from collections import OrderedDict
import toml

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

#from generateIds import MathFont

if len(sys.argv) != 2:
    print("usage: make-variants.py font.otf")
    print("\nThis file will read font.otf, extract the relavent infomration "
          "needed to create extendable glyphs in rust.  This will save the file "
          "as out/font/variants.rs.  This file assumes the font has a rex- prefix.")
    sys.exit(1)

font_file  = sys.argv[1]
file_out = "out/" + os.path.splitext(os.path.basename(font_file))[0][4:] + "/variants.rs"
font     = TTFont(font_file)
glyphset = font.getGlyphSet()

cmap = {}
for c in font['cmap'].tables:
    cmap.update(c.cmap)

# This provides and ordered -> Unicode mapping with every other attribute initialized
code = OrderedDict([ (name, code) for code, name in sorted(cmap.items()) ])

header = """\
// This file is automatically generated by `make-variants.py`
#![allow(dead_code)]

use std::collections::HashMap;
use super::variants::{ GlyphVariants, ConstructableGlyph, GlyphPart, ReplacementGlyph };


"""
    
vg_header="""\
lazy_static! {
    pub static ref VERT_VARIANTS: HashMap<u32, GlyphVariants> = {
        let mut m = HashMap::new();
"""

hg_header="""\
lazy_static! {
    pub static ref HORZ_VARIANTS: HashMap<u32, GlyphVariants> = {
        let mut m = HashMap::new();
"""

insert_t="""\
        m.insert(0x{:X}, GlyphVariants {{ // {}
"""

no_assembly_t="""\
            constructable: None,
"""

assembly_t="""\
            constructable: Some(ConstructableGlyph {{ 
                italics_correction: {}, 
                parts: vec![
"""

glyphpart_t="""\
                    GlyphPart {{ 
                        unicode:                0x{:X}, // {}
                        start_connector_length: {}, 
                        end_connector_length:   {}, 
                        full_advance:           {}, 
                        required:               {}, 
                    }},
"""

end_assembly_t="""\
                ],
            }),
"""

replacement_start_t="""\
            replacements: vec![
"""
            
replacement_t="""\
                ReplacementGlyph {{ unicode: 0x{:X}, advance: {} }}, // {}
"""

replacement_end_t="""\
            ],
        });
"""

variants_end_t="""
        m
    };
}
"""

# This function will do most of the work when we have a glyph construction 
def get_variants(construction, coverage):
    header = ""
    for idx, glyph in enumerate(construction):
        ucode = code[coverage[idx]]
        header += insert_t.format(ucode, coverage[idx])
        
        if glyph.GlyphAssembly is not None:
            ga = glyph.GlyphAssembly
            header += assembly_t.format(ga.ItalicsCorrection.Value)
            for part in ga.PartRecords:
                header += glyphpart_t.format(
                    code[part.glyph],   # Unicode
                    part.glyph,         # Name
                    part.FullAdvance,   # full_advance
                    part.StartConnectorLength,
                    part.EndConnectorLength, 
                    str(part.PartFlags == 0).lower())
            header += end_assembly_t
        else:
            header += no_assembly_t
                    
        header += replacement_start_t
        for gly in glyph.MathGlyphVariantRecord:
            header += replacement_t.format(
                code[gly.VariantGlyph],
                gly.AdvanceMeasurement,
                gly.VariantGlyph)
                        
        header += replacement_end_t
    header += variants_end_t
    return header

# Start with getting vertical glyphs:
header += vg_header
v_coverage  = font['MATH'].table.MathVariants.VertGlyphCoverage.glyphs
vert_glyphs = font['MATH'].table.MathVariants.VertGlyphConstruction
header += get_variants(vert_glyphs, v_coverage)

header += "\n\n"
header += hg_header
h_coverage  = font['MATH'].table.MathVariants.HorizGlyphCoverage.glyphs
horz_glyphs = font['MATH'].table.MathVariants.HorizGlyphConstruction
header += get_variants(horz_glyphs, h_coverage)

with open(file_out, 'w') as f:
    f.write(header)
