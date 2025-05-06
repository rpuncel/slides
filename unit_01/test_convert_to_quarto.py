from TexSoup import TexSoup
from convert_to_quarto import *

def test_parse_include_graphics():
    tex = r"""\includegraphics[width=.8\textwidth]{figures/lego_1}"""
    soup = TexSoup(tex)
    parse_include_graphics(list(soup.children)[0])


def test_parse_slide_notes_only():
    tex = r"""
    \begin{frame}
  \frametitle{First Models}
  \note[item]{They will be brittle - with no flexibility to make them look like the real world}
  \note[item]{Actually, just like this tower of legos, they may be very rectangle.}
    something simple to understand how the bricks fit together}
\end{frame}
    """
    soup = TexSoup(tex)
    expect = """## First Models


::: {.notes}
- They will be brittle - with no flexibility to make them look like the real world
- Actually, just like this tower of legos, they may be very rectangle.
:::
"""
    assert parse_slide(list(soup.children)[0]).to_md() == expect

def test_parse_slide_single_figure():
    tex = r"""
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
    """
    soup = TexSoup(tex)
    expect = """## First Models
![](figures/legos_3.jpg)


::: {.notes}
- When we start out, our models are not going to resemble the world at all
- {They will be brittle - with no flexibility to make them look like the real world}
- {Actually, just like this tower of legos, they may be very rectangle.}
- {You may ask, where did this rectangular distribution come from?}
- {The answer is we made it up!  and we just want to build
    something simple to understand how the bricks fit together}
:::


"""
    assert parse_slide(list(soup.children)[0]).to_md() == expect


def test_parse_block():
    text = r"""\begin{block}{Definition 1.1.12: \textit{partition}}
    A set of sets $A_{1}, A_{2}, \dots, A_{n}$ is a \textit{partition} of set $S$, if $A_{1}, A_{2}, \dots, A_{n}$ are nonempty and
    pairwise disjoint, and if $S = A_{1} \cup A_{2} 
    \cup \cdots \cup A_{n}$.
  \end{block}
    """
    expect = """::: {.callout-note title="Definition 1.1.12:  _partition_ "}

A set of sets $A_{1}, A_{2}, \dots, A_{n}$ is a _partition_ of set $S$, if $A_{1}, A_{2}, \dots, A_{n}$ are nonempty and
pairwise disjoint, and if $S = A_{1} \cup A_{2} 
\cup \cdots \cup A_{n}$.
  
:::"""
    soup = TexSoup(text)
    parsed = parse_block(list(soup.children)[0])
    assert parsed.to_md() == expect
