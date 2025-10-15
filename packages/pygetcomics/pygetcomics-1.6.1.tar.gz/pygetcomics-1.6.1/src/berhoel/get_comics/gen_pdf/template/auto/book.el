(TeX-add-style-hook
 "book"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("book" "a4paper" "landscape")))
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("geometry" "textwidth=189.9mm" "textheight=277.0mm" "headsep=1mm" "textwidth=277.0mm" "textheight=189.9mm")))
   (TeX-run-style-hooks
    "latex2e"
    "bk10"
    "graphicx"
    "geometry"
    "fontspec"
    "textpos"))
 :latex)

