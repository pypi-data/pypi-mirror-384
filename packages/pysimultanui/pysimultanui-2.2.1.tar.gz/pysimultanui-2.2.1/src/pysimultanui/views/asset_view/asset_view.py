import os
from nicegui import ui
from ..type_view import TypeView

from PySimultan2.files import FileInfo


extension_lookup_dict = {'.html': 'HTML',
               '.apl': 'APL',
               '.asn': 'ASN.1',
               '.conf': 'Asterisk',
               '.b': 'Brainfuck',
               '.c': 'C',
               '.cs': 'C#',
               '.cpp': 'C++',
               '.hpp': 'C++',
               '.clj': 'Clojure',
               '.cljs': 'ClojureScript',
               '.gss': 'Closure Stylesheets (GSS)',
               'CMakeLists.txt': 'CMake',
               '.cbl': 'Cobol',
               '.coffee': 'CoffeeScript',
               '.lisp': 'Common Lisp',
               '.cql': 'CQL',
               '.cr': 'Crystal',
               '.css': 'CSS',
               '.cypher': 'Cypher',
               '.pyx': 'Cython',
               '.d': 'D',
               '.dart': 'Dart',
               '.diff': 'diff',
               'Dockerfile': 'Dockerfile',
               '.dtd': 'DTD',
               '.dylan': 'Dylan',
               '.ebnf': 'EBNF',
               '.ecl': 'ECL',
               '.edn': 'edn',
               '.e': 'Eiffel',
               '.elm': 'Elm',
               '.erl': 'Erlang',
               '.epl': 'Esper',
               '.fs': 'Forth',
               '.factor': 'Factor',
               '.fcl': 'FCL',
               '.f': 'Fortran',
               '.s': 'Gas',
               '.feature': 'Gherkin',
               '.go': 'Go',
               '.groovy': 'Groovy',
               '.hs': 'Haskell',
               '.hx': 'Haxe',
               '.http': 'HTTP',
               '.hxml': 'HXML',
               '.idl': 'Web IDL',
               '.java': 'Java',
               '.js': 'JavaScript',
               '.jinja': 'Jinja2',
               '.jinja2': 'Jinja2',
               '.json': 'JSON',
               '.jsonld': 'JSON-LD',
               '.jsx': 'JSX',
               '.jl': 'Julia',
               '.kt': 'Kotlin',
               '.tex': 'LaTeX',
               '.less': 'LESS',
               '.liquid': 'Liquid',
               '.ls': 'LiveScript',
               '.lua': 'Lua',
               '.sql': 'SQL',
               '.md': 'Markdown',
               '.m': 'Octave',
               '.mbox': 'Mbox',
               '.mrc': 'mIRC',
               '.mo': 'Modelica',
               '.msc': 'MscGen',
               '.msgenny': 'MsGenny',
               '.mps': 'MUMPS',
               '.nginx': 'Nginx',
               '.nsi': 'NSIS',
               '.nt': 'NTriples',
               '.mm': 'Objective-C++',
               '.ml': 'OCaml',
               '.oz': 'Oz',
               '.pas': 'Pascal',
               '.pl': 'Perl',
               '.pgp': 'PGP',
               '.php': 'PHP', '.pig': 'Pig', '.plsql': 'PLSQL', '.ps1': 'PowerShell', '.properties': 'Properties files',
               '.proto': 'ProtoBuf', '.pug': 'Pug', '.pp': 'Puppet', '.py': 'Python', '.q': 'Q', '.r': 'R',
               '.changes': 'RPM Changes', '.spec': 'RPM Spec', '.rb': 'Ruby', '.rs': 'Rust', '.sas': 'SAS', '.sass': 'Sass',
               '.scala': 'Scala', '.scm': 'Scheme', '.scss': 'SCSS', '.sh': 'Shell', '.sieve': 'Sieve',
               '.st': 'Smalltalk', '.sml': 'SML', '.solr': 'Solr', '.sparql': 'SPARQL', '.ods': 'Spreadsheet',
               '.sqlite': 'SQLite', '.nut': 'Squirrel', '.stex': 'sTeX', '.styl': 'Stylus', '.swift': 'Swift',
               '.sv': 'SystemVerilog', '.tcl': 'Tcl', '.textile': 'Textile', '.tiddly': 'TiddlyWiki',
               '.tiki': 'Tiki wiki', '.toml': 'TOML', '.tr': 'Troff', '.tsx': 'TSX', '.ttcn': 'TTCN',
               '.cfg': 'TTCN_CFG', '.ttl': 'Turtle', '.ts': 'TypeScript', '.vb': 'VB.NET',
               '.vbs': 'VBScript', '.vm': 'Velocity', '.v': 'Verilog', '.vhdl': 'VHDL', '.vue': 'Vue',
               '.wasm': 'WebAssembly', '.xml': 'XML', '.xq': 'XQuery', '.xu': 'Xù', '.ys': 'Yacas',
               '.yml': 'YAML',
               '.yaml': 'YAML',
               '.z80': 'Z80'}


class AssetDetailView(object):

    def __init__(self, *args, **kwargs):
        self.component: FileInfo = kwargs.get('component')
        self.parent = kwargs.get('parent')

        self.editor = None

    @ui.refreshable
    def ui_content(self, *args, **kwargs):
        with ui.row().classes('w-full'):
            ui.input(label='Name', value=self.component.name).bind_value(self.component, 'name').classes('w-full')

        with ui.row():
            ui.label('Key:')
            ui.label(self.component.resource_entry.Key)

        with ui.row():
            ui.label('Size:')
            ui.label(f'{self.component.file_size / 1024:.3f} KB' if self.component.file_size/1024 < 1024
                     else f'{self.component.file_size / 1024 / 1024:.3f} MB')

        with ui.row():
            ui.label('Last Modified:')
            ui.label(str(self.component.last_modified))

        file_extension = os.path.splitext(self.component.name)[1]

        # if file_extension in ['.txt']:
        #     with ui.row():
        #         editor = ui.editor(placeholder='Type something here').bind_value(self.component, 'content',
        #                                                                          backward=lambda x: x)

        try:
            with (ui.card().classes('w-full h-full')):
                content = self.component.content

                file_extension = os.path.splitext(self.component.name)[1]

                self.editor = ui.codemirror(value=content,
                                            language=extension_lookup_dict.get(file_extension, None)
                                            ).classes('w-full h-full')

            with ui.row().classes('w-full'):
                ui.select(self.editor.supported_languages, label='Language', clearable=True) \
                    .classes('w-32').bind_value(self.editor, 'language')
                ui.select(self.editor.supported_themes, label='Theme') \
                    .classes('w-32').bind_value(self.editor, 'theme')

                ui.button('Save', on_click=self.save, icon='save').classes('q-mt-md')

        except Exception as e:
            ui.notify(f'Could not load content: {e}')

    def save(self, event):
        self.component.content = self.editor.value
        ui.notify('Saved!')


class AssetView(TypeView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def asset(self):
        return self.component

    @ui.refreshable
    def ui_content(self):
        with ui.card().classes('w-full h-full').props('color="blue-800" keep-color') as self.card:
            with ui.item().classes('w-full h-full'):
                with ui.item_section():
                    self.checkbox = ui.checkbox()
                with ui.item_section():
                    ui.label(self.asset.name)
                with ui.item_section():
                    ui.label(str(self.asset.file_size / 1024))
                with ui.item_section():
                    ui.label(str(self.asset.last_modified))
                with ui.item_section():
                    dl_button = ui.button(icon='download', on_click=self.download).classes('q-ml-auto')

    def download(self, event):
        ui.download(f'assets/{self.asset.name}')
