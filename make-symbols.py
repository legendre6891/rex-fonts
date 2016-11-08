#!/bin/python
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from generateIds import MathFont

import os
import sys
from collections import OrderedDict

if len(sys.argv) != 2:
    print("usage: make-symbols.py font.otf")
    print("\nThis file will read font.otf to extract each glyph's ID. It " +
          "will then parse the 'unicode-math-table.tex' to find a mapping " +
          "from tex commands to symbols, while also gather it's atom type. " + 
          "It will then save the file in '/out/file/symbols.rs'.  This " +
          "script assumes the font is prefixed by rex-. " +
          "This script will also create '/out/files/offsets.rs'.")
    sys.exit(1)

###
# Collect all relavent glyph IDs.
#

font_file  = sys.argv[1]
file_out = "out/" + os.path.splitext(os.path.basename(font_file))[0][4:] + "/symbols.rs"
font     = TTFont(font_file)
glyphset = font.getGlyphSet()

mf = MathFont(font_file, 'unicode.toml')

###
# Parse unicode-math-table.tex
#

header = """\
// DO NOT MODIFY!
//
// This file is automatically generated by the ../tools/parse-unicode-math.py file using the
// unicode-math-table.tex file taken from `unicode-math` on CTAN. If you find a bug
// in this file, please modify ../tools/parse-unicode-math.py accordingly instead.
//
// FIXME: We should probably use the official unicode standards source.

#![allow(dead_code)]
use phf;
use parser::nodes::AtomType;
use font::Symbol;

pub static SYMBOLS: phf::Map<&'static str, Symbol> = phf_map! {
"""

# Convert ../unicode-math-table.tex atomtype to our AtomType.
convert_type = {
    "mathalpha": "Alpha",
    "mathpunct": "Punctuation",
    "mathopen": "Open",
    "mathclose": "Close",
    "mathord": "Ordinal",
    "mathbin": "Binary",
    "mathrel": "Relation",
    "mathop": "Operator",
    "mathfence": "Fence",
    "mathover": "Over",
    "mathunder": "Under",
    "mathaccent": "Accent",
    "mathaccentwide": "AccentWide",
    "mathbotaccent": "BotAccent",
    "mathbotaccentwide": "BotAccentWide",
}

# The following operators have `\limits` by default
operator_limits = {
    "coprod",
    "bigvee",
    "bigwedge",
    "biguplus",
    "bigcap",
    "bigcup",
    "prod",
    "sum",
    "bigotimes",
    "bigoplus",
    "bigodot",
    "bigsqcup",
}

# Fixme: This should be sorted, use a list instead.
additional_symbols = [
    ("Alpha",   ("0x391", "Alpha")),
    ("Beta",    ("0x392", "Alpha")),
    ("Gamma",   ("0x393", "Alpha")),
    ("Delta",   ("0x394", "Alpha")),
    ("Epsilon", ("0x395", "Alpha")),
    ("Zeta",    ("0x396", "Alpha")),
    ("Eta",     ("0x397", "Alpha")),
    ("Theta",   ("0x398", "Alpha")),
    ("Iota",    ("0x399", "Alpha")),
    ("Kappa",   ("0x39A", "Alpha")),
    ("Lambda",  ("0x39B", "Alpha")),
    ("Mu",      ("0x39C", "Alpha")),
    ("Nu",      ("0x39D", "Alpha")),
    ("Xi",      ("0x39E", "Alpha")),
    ("Omicron", ("0x39F", "Alpha")),
    ("Pi",      ("0x3A0", "Alpha")),
    ("Rho",     ("0x3A1", "Alpha")),

    ("Sigma",   ("0x3A3", "Alpha")),
    ("Tau",     ("0x3A4", "Alpha")),
    ("Upsilon", ("0x3A5", "Alpha")),
    ("Phi",     ("0x3A6", "Alpha")),
    ("Chi",     ("0x3A7", "Alpha")),
    ("Psi",     ("0x3A8", "Alpha")),
    ("Omega",   ("0x3A9", "Alpha")),

    ("alpha",   ("0x3B1", "Alpha")),
    ("beta",    ("0x3B2", "Alpha")),
    ("gamma",   ("0x3B3", "Alpha")),
    ("delta",   ("0x3B4", "Alpha")),
    ("epsilon", ("0x3B5", "Alpha")),
    ("zeta",    ("0x3B6", "Alpha")),
    ("eta",     ("0x3B7", "Alpha")),
    ("theta",   ("0x3B8", "Alpha")),
    ("iota",    ("0x3B9", "Alpha")),
    ("kappa",   ("0x3BA", "Alpha")),
    ("lambda",  ("0x3BB", "Alpha")),
    ("mu",      ("0x3BC", "Alpha")),
    ("nu",      ("0x3BD", "Alpha")),
    ("xi",      ("0x3BE", "Alpha")),
    ("omicron", ("0x3BF", "Alpha")),
    ("pi",      ("0x3C0", "Alpha")),
    ("rho",     ("0x3C1", "Alpha")),
    
    ("sigma",   ("0x3C3", "Alpha")),
    ("tau",     ("0x3C4", "Alpha")),
    ("upsilon", ("0x3C5", "Alpha")),
    ("phi",     ("0x3C6", "Alpha")),
    ("chi",     ("0x3C7", "Alpha")),
    ("psi",     ("0x3C8", "Alpha")),
    ("omega",   ("0x3C9", "Alpha")),
]

# TeX -> Unicode template
template = '    "{}" => Symbol {{ id: {}, atom_type: AtomType::{} }}, // Unicode: 0x{:X}, {}\n'

# Parse 'unicode-math-table.tex'.  Store relavent information in
# `symbols` as 4-tuples:
#     (TeX command, Id, AtomType, Unicode, Description)
symbols = []
with open('unicode-math-table.tex', 'r') as f:
    for line in f:
        code = int("0x" + line[20:25],16)
        cmd  = line[28:53].strip()

        cursor = 56
        while line[cursor] != '}': cursor += 1
        atom = line[56:cursor]

        cursor += 2  # Skip next `}{` sequence
        desc = line[cursor:-3]

        if mf.gid.get(code, None) == None:
            print("Unable to find 0x{:X} -- {}.".format(code, desc))
            continue

        symbols.append([cmd, mf.gid[code], convert_type[atom], code, desc])

# Write '.../syc/symbols.rs'
with open(file_out, 'w', newline='\n') as f:
    f.write(header)
    f.write("    // unicode-math.dtx command table\n")
    for tpl in symbols:
        # For operators, we annotate if they have limits or not on default
        if tpl[2] == "Operator":
            tpl[2] += "({})".format(str(tpl[0] in operator_limits).lower())
        f.write(template.format(*tpl))
    
    f.write("    // Additional commands from TeX\n")
    for name, (code, ty) in additional_symbols:
        code = int(code, 16)
        if mf.gid.get(code, None) == None:
            print("Missing greek glyph: {}, {}".format(code, name))
            continue
        f.write(template.format(name, mf.gid[code], ty, code, ""))
    f.write('};')



# The following is scratch work, kept in case it's need later

# The following table gives offsets to the code point for various styles.
# This will be need to convert input code points to the proper math font
# code points.

# *         -> 0x2217  //  Centered asterisk

# A...Za...z           // Substract 6 from 'a' to make A...Za...z adjacent
#                      // Substract 0x41 to find offset from A
# mbf       -> 0x1D400 // Math Bold
# mit       -> 0x1D434 // Math Italic
# mbfit     -> 0x1D468 // Math Bold Italic
# mscr      -> 0x1D49C // Math Script
# mbfscr    -> 0x1D4D0 // Math Bold Script
# mfrak     -> 0x1D504 // Math Fraktur
# Bbb       -> 0x1D538 // Math double-struck
# mbffrak   -> 0x1D56C // Math Bold Fraktur
# msans     -> 0x1D5A0 // Math Sans-serif
# mbfsans   -> 0x1D5D4 // Math Bold Sans-serif
# mitsans   -> 0x1D608 // Math Italic Sans-serif
# mbfitsans -> 0x1D63C // Math Bold Italic Sans-serif
# mtt       -> 0x1D670 // Math Monospace

# Greek:       0391-03C9      // Lots of gaps here
# mbf       -> 0x1D6A8  // Greek Bold
# mit       -> 0x1D6E2  // Greek italic
# mbfit     -> 0x1D71C  // Greek Bold Italic
# mbfsans   -> 0x1D756  // Greek Bold Sans-serif
# mbfitsans -> 0x1D790  // Greek Bold Italic Sans-serif

# 0..9                  // Subtract by 0x30 to get relative offset
# mbf       -> 0x1D7CE  // Math Bold Digit
# Bbb       -> 0x1D7D8  // Math doube-struck Digit
# msans     -> 0x1D7E2  // Math Sans-serif Digit
# mbfsans   -> 0x1D7EC  // Math Bold Sans-serif Digit
# mtt       -> 0x1D7F6  // Math Monospace Digit

header="""\
// Do not modify.  Automatically generated.
use parser::nodes::AtomType;
use font::{Style, Symbol};

pub trait IsAtom {
    fn atom_type(&self, Style) -> Option<Symbol>;
}

impl IsAtom for char {
    fn atom_type(&self, mode: Style) -> Option<Symbol> {
        match *self {
"""

range_template ="""\
            c @ '{}'...'{}' => Some(Symbol {{
                id: (c as i32 + {}) as u16,
                atom_type: AtomType::{},
            }}),\n"""

single_template="""\
            c @ '{}' => Some(Symbol {{
                id: {} as u16,
                atom_type: AtomType::{},
            }}),\n"""

# A list of ranges that are have consecutive unicode points, which
# are included in the font and thus have consecutive glyph ids
ranges = [
    ('a', 'z', 'Alpha'),
    ('A', 'Z', 'Alpha'),
    ('0', '9', 'Alpha'),
    ('Α', 'Ρ', 'Alpha'), # \Alpha to \Rho
    ('Σ', 'Ω', 'Alpha'), # \Sigma to \Omega
    ('α', 'ρ', 'Alpha'), # \alpha to \rho
    ('σ', 'ω', 'Alpha'), # \sigma to \omega
]

singles = [
    ('*', 'Binary'),
    ('+', 'Binary'),
    ('(', 'Open'),
    ('[', 'Open'),
    (']', 'Close'),
    (')', 'Close'),
    ('?', 'Close'),
    ('!', 'Close'),
    ('=', 'Relation'),
    ('<', 'Relation'),
    ('>', 'Relation'),
    (':', 'Relation'),
    (',', 'Punctuation'),
    (';', 'Punctuation'),
    ('|', 'Ordinal'),
    ('/', 'Ordinal'),
    ('@', 'Ordinal'),
    ('.', 'Ordinal'),
    ('"', 'Ordinal'),
]

for start, end, atom in ranges:
    header += range_template.format(
        start, end, mf.gid[ord(start)] - ord(start), atom)
    
for c, atom in singles:
    header += single_template.format(c, mf.gid[ord(c)], atom)

header += """\
            _ => None,
        }
    }
}"""
    
file_out = "out/" + os.path.splitext(os.path.basename(font_file))[0][4:] + "/offsets.rs"

with open(file_out, 'w', encoding='utf8') as f:
    f.write(header)

