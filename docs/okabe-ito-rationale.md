# Okabe–Ito baseline: original rationale and audit scope

PaletteBench uses the eight-colour Okabe–Ito palette as its initial baseline. This page distinguishes the original design rationale from the measurements performed by this software.

## Original design goals

Okabe and Ito described their proposal as a palette intended to be:

- unambiguous to people with and without colour-vision deficiencies;
- vivid enough that familiar colour names remain easy to identify;
- reproducible with similar appearance on screen and in print.

The individual hue choices were deliberate:

- vermillion was used instead of a conventional red because it remains more recognisable to protan observers;
- hues between yellow and green were avoided because they can be confused with yellow and orange;
- bluish green was chosen to reduce confusion with red and brown;
- reddish purple was chosen because violet lies close to blue for many colour-deficient observers;
- warm colours between vermillion and yellow were separated partly through apparent intensity;
- sky blue and blue were separated through brightness and saturation.

Their usage guidance is as important as the hexadecimal values. They recommend alternating warm and cool colours, introducing clear brightness or saturation differences when two colours from the same broad temperature family are used together, and avoiding combinations in which both colours have low saturation or low brightness. They also warn that yellow and sky blue can be difficult in thin lines or small marks, where orange and darker blue may be preferable.

The broader Color Universal Design guidance advocates redundant coding: colour should be accompanied by position, shape, line style, labels, or another cue. It also cautions against referring to an item only by its colour name.

The later CUD recommended-colour work makes two further principles explicit. First, a universal palette is a compromise across different observers rather than the palette that is individually optimal for any one group. Second, not every possible pair in a larger palette is equally distinguishable; when fewer colours are needed, the more reliable subsets should be preferred. Accurate colour management also matters because relatively small reproduction changes may create additional confusable pairs.

Primary sources:

- Masataka Okabe and Kei Ito, [Color Universal Design: How to make figures and presentations that are friendly to Colorblind people](https://jfly.uni-koeln.de/color/).
- Yasuyo G. Ichihara et al., [Color Universal Design—The Selection of Four Easily Distinguishable Colors for All Color Vision Types](https://jfly.uni-koeln.de/color/ichihara_etal_2008.pdf).
- CUDO/Kei Ito, [Color Universal Design recommended colour set, second edition](https://jfly.uni-koeln.de/color/colorset_old_2/) (Japanese).

## What PaletteBench measures

The workbench provides objective, reproducible evidence about:

- CIEDE2000 separation under normal and simulated CVD conditions;
- the weakest pair, lower tail, mean, median, and distribution of pairwise distances;
- changes in those quantities relative to a baseline;
- pair-specific increases and decreases when colour IDs match;
- lightness, relative luminance, grayscale separation, and contrast against black and white;
- within-group and between-group separation for structured palettes.

In comparison reports, a positive change means increased separation according to the named metric; a negative change means decreased separation. Counts below descriptive thresholds are also compared. No weighted or opaque accessibility score is calculated.

## What the comparison cannot establish

The audit does not directly measure:

- whether a colour has an intuitive or consistently recognisable name;
- print-gamut suitability or matching across calibrated print and display systems;
- the visual-semantic benefit of alternating warm and cool categories;
- the suitability of colours for a particular mark size, background, or spatial arrangement;
- redundant coding in the final figure;
- performance by human observers.

Consequently, a derivative can improve several PaletteBench metrics without being categorically “better than Okabe–Ito.” The appropriate conclusion is narrower: it has greater or smaller modelled separation under stated conditions. Design rationale, reproduction medium, category semantics, and human evaluation remain separate evidence.

