from TexSoup import TexSoup
from convert_to_quarto import *

def test_parse_include_graphics():
    tex = r"""\includegraphics[width=.8\textwidth]{figures/lego_1}"""
    soup = TexSoup(tex)
    parse_include_graphics(list(soup.children)[0])

def test_parse_slide_single_figure():
    tex = r'''
    \begin{frame}
  \frametitle{First Models}
  \note[item]{When we start out, our models are not going to resemble the world at all}
  \note[item]{They will be brittle - with no flexibility to make them look like the real world}
  \note[item]{Actually, just like this tower of legos, they may be very rectangle.}
  \note[item]{You may ask, where did this rectangular distribution come from?}
  \note[item]{The answer is we made it up!  and we just want to build
    something simple to understand how the bricks fit together}
  \centering 
  \includegraphics[width=.8\textwidth]{figures/legos_3} \\ 
  \footnotesize Image: Hans Schou (CC BY-SA 3.0)
\end{frame}
    '''
    soup = TexSoup(tex)
    assert 'blah' == parse_slide(soup).to_md()