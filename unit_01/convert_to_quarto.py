from dataclasses import dataclass
import os
from typing import TypedDict
import yaml
from TexSoup import TexSoup
from TexSoup.data import TexNode, TexCmd, TexExpr

# Define the input and output file paths
input_file = '/Users/rpuncel/Workspaces/slides/unit_01/unit_01.tex'
output_file = '/Users/rpuncel/Workspaces/slides/unit_01/unit_01_converted.qmd'

class QmdHeader(TypedDict):
    title: str
    subtitle: str
    author: str
    institute: str
    format: dict
    

def get_doc_metadata(doc):
    print(doc.title.string)
    return QmdHeader(
        title = str(doc.title.string),
        subtitle = str(doc.subtitle.string),
        author = str(doc.author.string),
        institute = str(doc.institute.string),
        format = {"revealjs": {"show-notes": True}}
    )

class Notes:
    def __init__(self, items: list):
        self.items = items

    def to_md(self):
        if len(self.items) == 0:
            return ''
        bullets = [f'- {item}' for item in self.items]

        return '\n'.join([
            '::: {.notes}',
            *bullets,
            ':::',
            ''
        ])

class Slide:

    def __init__(self, title: str, contents, notes: Notes):
        self.title = title
        self.contents = contents
        self.notes = notes
    
    def to_md(self):
        return ('\n'.join([
            f'## {self.title}',
            '\n'.join([str(x) for x in self.contents]),
            '',
            self.notes.to_md(),  
        ]))

class Section:
    
    def __init__(self, title: str):
        self.title = title
    
    def to_md(self):
        return f'# {self.title}'

class Slideshow:

    def __init__(self):
        self.title = ""
        self.subtitle = ""
        self.authors = list()
        self.sections_and_slides = list()
    
    def to_md(self):
        return '\n\n'.join([
            f'# {self.title}',
            *[s.to_md() for s in self.sections_and_slides]
        ]
        )

class UnorderedList:
    
    def __init__(self, items: list[str]):
        self.items = items

    def to_md(self):
        return '\n'.join([f'- {item}' for item in self.items])
    
    def __str__(self):
        return self.to_md()

class Block:
    def __init__(self, title, content: list):
        self.title = title
        self.content = content
    
    def to_md(self):
        content = [ str(c).lstrip() for c in self.content ]
        return '\n'.join([
            f'::: {{.callout-note title="{self.title}"}}',
           '\n'.join(content),
            ':::',
        ])
        
    def __str__(self):
        return self.to_md()
        

class Image:
    
    def __init__(self, path: str, caption = ''):
        self.caption = caption
        self.path = path
    
    def to_md(self):
        return f'![{self.caption}]({self.path})\n'

    def __str__(self):
        return self.to_md()

class OrderedList:

    def __init__(self, items: list[str]):
        self.items = items
    
    def to_md(self):
        return '\n'.join([f'{i+1}. {item}' for i, item in enumerate(self.items)])

    def __str__(self):
        return self.to_md()


def parse_list(root):
    result = list()
    for child in root.children:
        if child.name == 'itemize':
            result.append(UnorderedList(parse_list(child)))
        elif child.name == 'item':
            result.append(''.join([text for text in child.text]))
    return result

def parse_include_graphics(root):
    filename = root.args[1].string
    path = find_image_file(filename)
    if path is None:
        raise ValueError(f"could not find file path: {filename}")
    return Image(path)

def parse_simple(root):
    contents = list()
    for child in root.contents:
        if hasattr(child, "name"):
            if child.name == "textit":
                contents.append(f'_{str(child.args[0].string)}_')
            if child.name == "$":
                contents.append(child.string)
            else: contents.append(child.string)
        else: contents.append(child)
    return contents

def parse_block(root):
    block_title_expr = root.args[0]
    title = ' '.join(parse_simple(block_title_expr))
    skip = len(list(block_title_expr.contents))
    contents = list()
    for i, content in enumerate(root.contents):
        if i < skip:
            continue
        if isinstance(content, str):
            contents.append(content)
        else: contents.append(parse_texnode(content))


    return Block(title, contents)


@dataclass
class Column:
    
    width: float | None
    contents: str
    skip: int = 0

    def to_md(self):
        width_specifier = f'width="{self.width:g}%"' if self.width is not None else ""
        lines = []
        lines.append(f'::: {{.column {width_specifier}}}\n')
        for line in self.contents[self.skip:]:
            lines.append(str(line).rstrip().replace(r"\\", "\n"))
        lines.append('\n:::\n')
        return ''.join(lines)


    def __str__(self):
        return self.to_md()


@dataclass
class Columns:
    columns: list[Column]

    def to_md(self):
        content = "\n".join(c.to_md() for c in self.columns)
        return "\n".join([
            ":::: {.columns}\n",
            content,
            "::::"

        ])

    def __str__(self):
        return self.to_md()


def parse_columns(root):
    columns: list[Column] = []
    for child in root.children:
        assert child.name == "column"
        idx = child.args[0].string.find("\\textwidth")
        skip = 0
        if idx != -1:
            width_str = child.args[0].string[:idx]
            width = float(width_str)
            width_pct = width * 100
            skip = 2
        columns.append(Column(width_pct, child.contents, skip))
    return Columns(columns)


def parse_texnode(root):
    if root.name == 'itemize':
        return UnorderedList(parse_list(root))
    elif root.name == 'enumerate':
        return OrderedList(parse_list(root))
    elif root.name == "includegraphics":
        previous_image = parse_include_graphics(root)
        return previous_image
    elif root.name == "textit":
        return f'_{str(root.args[0].string)}_'
    elif root.name == "block":
        return parse_block(root)
    elif root.name == "columns":
        return parse_columns(root)
    elif root.name in ["$", "$$", "\\"]:
        return root
    elif root.name in ["centering", "footnotesize"]:
        return ""
    

    else:
        return root

def parse_slide(frame_root):  
    slide_title = ""
    if frame_root.frametitle is not None:
        slide_title = frame_root.frametitle.string
    contents = list()
    note_items = list()
    alls = frame_root.contents
    previous_image = None
    for child in alls:
        if isinstance(child, TexNode):
            if child.name == 'frametitle':
                slide_title = child.string
            elif child.name == "note":
                note_items.append(child.args[1].string)
            else:
                contents.append(parse_texnode(child))
        else:
            if r'\\' in str(child): continue
            elif str(child).startswith('%'): continue
            else: contents.append(str(child))
        
    return Slide(
                    title = slide_title,
                    contents = contents,
                    notes=Notes(note_items)
            )

def convert_doc(doc):
    root = doc.find("document")
    slideshow = Slideshow()
    for child in root.children:
        if child.name == "section":
            slideshow.sections_and_slides.append(Section(child.string))
        elif child.name == "frame":
            slide = parse_slide(child)
            if slide is None: continue
            slideshow.sections_and_slides.append(slide)
    return slideshow

# Function to check if an image file exists
def find_image_file(image_path):
    for ext in ['.jpg', '.png', '.pdf']:
        full_path = f"{image_path}{ext}"
        if os.path.exists(full_path):
            return full_path
    return None

def open_tex():
    # Read the LaTeX file
    with open(input_file, 'r') as file:
        tex_content = file.read()

    # Parse the LaTeX content using text2py
    parsed_content = TexSoup(tex_content)
    return parsed_content

def main():

    # Start writing the Quarto markdown content

    parsed_content = open_tex()
    doc = parsed_content
    metadata = get_doc_metadata(doc)
    qmd_content = "---\ntitle: 'Unit 01 Presentation'\nformat: revealjs\n---\n\n"
    qmd_content = convert_doc(parsed_content).to_md()

    # Write the Quarto markdown file
    with open(output_file, 'w') as file:
        file.write('---\n')
        yaml.dump(metadata, file)
        file.write('---\n\n')
        file.write(qmd_content)

def parse_orig(parse_content):

    # Process each parsed element
    for element in parsed_content:
        if element['type'] == 'frame':
            frame_content = element['content']

            # Extract notes
            notes = [note['content'] for note in element.get('notes', [])]

            # Extract images and check their existence
            for image in element.get('images', []):
                image_path = find_image_file(image['path'])
                if image_path:
                    frame_content = frame_content.replace(image['raw'], f"![]({image_path})")
                else:
                    frame_content = frame_content.replace(image['raw'], "")

            # Replace LaTeX-specific syntax with Markdown/Quarto syntax
            frame_content = frame_content.replace('\\', '')  # Remove remaining LaTeX backslashes

            # Add slide content
            qmd_content += "---\n\n"  # Slide separator
            qmd_content += frame_content + "\n\n"

            # Add notes if present
            if notes:
                qmd_content += "::: {.notes}\n"
                for note in notes:
                    qmd_content += f"- {note.strip()}\n"
                qmd_content += ":::\n\n"


if __name__ == '__main__':
    main()