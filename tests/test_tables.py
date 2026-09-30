from palettebench.tables import latex_table


def test_latex_escapes_all_special_characters_once():
    rendered = latex_table(["Name"], [["a_b & 50% $x$ #1 {z} ~ ^ \\"]])
    assert r"a\_b \& 50\% \$x\$ \#1 \{z\}" in rendered
    assert r"\textasciitilde{}" in rendered
    assert r"\textasciicircum{}" in rendered
    assert r"\textbackslash{}" in rendered
