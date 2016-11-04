# TODO: Add dotless variants lookup?
from fontTools.ttLib import TTFont

import sys
import os

if len(sys.argv) != 2:
    print("usage: make-constants.py font.otf")
    print("\nThis file will read the MathConstants table of font.otf, generating " +
          "a Constants structure in rust.  The file will be saved as out/font/constants.rs")
    sys.exit(1)

font_file = sys.argv[1]
font = TTFont(font_file)
font_name = font['name'].getName(4,1,0).string

file_out = "out/" + os.path.splitext(os.path.basename(font_file))[0] + "/constants.rs"

header = '''\
// DO NOT MODIFY.  This file is automatically generated by ___ in the rex-font folder.
// 
// Font File: {}
// Font Nmae: {}
use font::Constants;

#[allow(dead_code)]
pub static CONSTANTS: Constants = Constants {{
'''.format(font_file, font_name)

constants = [
    ('AccentBaseHeight',	'accent_base_height'),
    ('AxisHeight',	'axis_height'),
    ('DelimitedSubFormulaMinHeight',	'delimited_sub_formula_min_height'),
    ('DisplayOperatorMinHeight',	'display_operator_min_height'),
    ('FlattenedAccentBaseHeight',	'flattened_accent_base_height'),
    ('FractionDenomDisplayStyleGapMin',	'fraction_denom_display_style_gap_min'),
    ('FractionDenominatorDisplayStyleShiftDown',	'fraction_denominator_display_style_shift_down'),
    ('FractionDenominatorGapMin',	'fraction_denominator_gap_min'),
    ('FractionDenominatorShiftDown',	'fraction_denominator_shift_down'),
    ('FractionNumDisplayStyleGapMin',	'fraction_num_display_style_gap_min'),
    ('FractionNumeratorDisplayStyleShiftUp',	'fraction_numerator_display_style_shift_up'),
    ('FractionNumeratorGapMin',	'fraction_numerator_gap_min'),
    ('FractionNumeratorShiftUp',	'fraction_numerator_shift_up'),
    ('FractionRuleThickness',	'fraction_rule_thickness'),
    ('LowerLimitBaselineDropMin',	'lower_limit_baseline_drop_min'),
    ('LowerLimitGapMin',	'lower_limit_gap_min'),
    ('MathLeading',	'math_leading'),
    ('OverbarExtraAscender',	'overbar_extra_ascender'),
    ('OverbarRuleThickness',	'overbar_rule_thickness'),
    ('OverbarVerticalGap',	'overbar_vertical_gap'),
    ('RadicalDegreeBottomRaisePercent',	'radical_degree_bottom_raise_percent'),
    ('RadicalDisplayStyleVerticalGap',	'radical_display_style_vertical_gap'),
    ('RadicalExtraAscender',	'radical_extra_ascender'),
    ('RadicalKernAfterDegree',	'radical_kern_after_degree'),
    ('RadicalKernBeforeDegree',	'radical_kern_before_degree'),
    ('RadicalRuleThickness',	'radical_rule_thickness'),
    ('RadicalVerticalGap',	'radical_vertical_gap'),
    ('ScriptPercentScaleDown',	'script_percent_scale_down'),
    ('ScriptScriptPercentScaleDown',	'script_script_percent_scale_down'),
    ('SkewedFractionHorizontalGap',	'skewed_fraction_horizontal_gap'),
    ('SkewedFractionVerticalGap',	'skewed_fraction_vertical_gap'),
    ('SpaceAfterScript',	'space_after_script'),
    ('StackBottomDisplayStyleShiftDown',	'stack_bottom_display_style_shift_down'),
    ('StackBottomShiftDown',	'stack_bottom_shift_down'),
    ('StackDisplayStyleGapMin',	'stack_display_style_gap_min'),
    ('StackGapMin',	'stack_gap_min'),
    ('StackTopDisplayStyleShiftUp',	'stack_top_display_style_shift_up'),
    ('StackTopShiftUp',	'stack_top_shift_up'),
    ('StretchStackBottomShiftDown',	'stretch_stack_bottom_shift_down'),
    ('StretchStackGapAboveMin',	'stretch_stack_gap_above_min'),
    ('StretchStackGapBelowMin',	'stretch_stack_gap_below_min'),
    ('StretchStackTopShiftUp',	'stretch_stack_top_shift_up'),
    ('SubSuperscriptGapMin',	'sub_superscript_gap_min'),
    ('SubscriptBaselineDropMin',	'subscript_baseline_drop_min'),
    ('SubscriptShiftDown',	'subscript_shift_down'),
    ('SubscriptTopMax',	'subscript_top_max'),
    ('SuperscriptBaselineDropMax',	'superscript_baseline_drop_max'),
    ('SuperscriptBottomMaxWithSubscript',	'superscript_bottom_max_with_subscript'),
    ('SuperscriptBottomMin',	'superscript_bottom_min'),
    ('SuperscriptShiftUp',	'superscript_shift_up'),
    ('SuperscriptShiftUpCramped',	'superscript_shift_up_cramped'),
    ('UnderbarExtraDescender',	'underbar_extra_descender'),
    ('UnderbarRuleThickness',	'underbar_rule_thickness'),
    ('UnderbarVerticalGap',	'underbar_vertical_gap'),
    ('UpperLimitBaselineRiseMin',	'upper_limit_baseline_rise_min'),
    ('UpperLimitGapMin',	'upper_limit_gap_min')
]

template = '    {}: {},\n'
for constant, name in constants:
    result = 0
    try:
        result = font['MATH'].table.MathConstants.__getattribute__(constant).Value
    except:
        result = font['MATH'].table.MathConstants.__getattribute__(constant)
    if result == 0:
        print("Unable to find constant: ", constant)
        continue
    header += template.format(name, result)
header += '};\n'

with open(file_out, 'w') as f:
    f.write(header)
