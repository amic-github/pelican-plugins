import docutils
import docutils.core
import docutils.io

from pelican import signals
from pelican.readers import *


def preprocess_escapes(source_path):
    output_string = ''
    source_file=open(source_path)

    ininlinemath = False
    indisplaymath = False
    
    inraw = False # A personal trick to ensure that raw directives, etc. will not be processed
    # If a line corresponds exactly to ".. UNPROCESSED" then the following is not preprocessed
    # until we find a line corresponding exactly to ".. PROCESSED"
              
    escaping = False

    for line in source_file:
        if not inraw and line == ".. UNPROCESSED\n":
            inraw = True
            continue
        if inraw and line == ".. PROCESSED\n":
            inraw = False
            continue
        if inraw:
            output_string += line
            continue
        
        for c in line:
            if c == "": break 
            if c == '\\':
                if escaping:
                    output_string += "\\\\" # the last one
                    if ininlinemath or indisplaymath:
                        output_string += "\\\\" # doubled
                    escaping = False
                else: escaping = True
                continue
            if escaping:
                if c == ']':
                    if indisplaymath:
                        indisplaymath = False
                        output_string += "\\\\]"
                    else: print("Math preprocessing error : \\] before \\[\n")
                elif c == '[':
                    if indisplaymath:
                        print("Math preprocessing error : \\[ after \\[\n")
                    else:
                        indisplaymath = True
                        output_string += "\\\\[" # doubled 
                elif c == ')':
                    if ininlinemath:
                        ininlinemath = False
                        output_string += "\\\\)" 
                    else: print("Math preprocessing error : \\) before \\(\n")
                elif c == '(':
                    if ininlinemath:
                        print("Math preprocessing error : \\( after \\(\n")
                    else:
                        ininlinemath = True
                        output_string += "\\\\(" # doubled 
                else:              
                    output_string += "\\"
                    if ininlinemath or indisplaymath:
                        output_string += "\\" # doubled 
                    output_string += c
                escaping = False
            else:
                if c == '$': ininlinemath = not ininlinemath
                output_string += c
        
    return output_string
    

class MathRstReader(BaseReader):
    """Reader for reStructuredText files escaping backslashes in math"""

    enabled = bool(docutils)
    file_extensions = ['rst']

    def __init__(self, *args, **kwargs):
        super(MathRstReader, self).__init__(*args, **kwargs)

    def _parse_metadata(self, document):
        return RstReader._parse_metadata(self, document)

    def _get_publisher(self, source_path):
        
        
        extra_params = {'initial_header_level': '2',
                        'syntax_highlight': 'short',
                        'input_encoding': 'utf-8',
                        'exit_status_level': 2}
        user_params = self.settings.get('DOCUTILS_SETTINGS')
        if user_params:
            extra_params.update(user_params)

        pub = docutils.core.Publisher(
            source_class=docutils.io.StringInput,
            destination_class=docutils.io.StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.writer.translator_class = PelicanHTMLTranslator
        pub.process_programmatic_settings(None, extra_params, None)
        pub.set_source(source=preprocess_escapes(source_path))
        pub.publish(enable_exit_status=True)
        return pub

    def read(self, source_path):
        """Parses restructured text"""
        pub = self._get_publisher(source_path)
        parts = pub.writer.parts
        content = parts.get('body')

        metadata = self._parse_metadata(pub.document)
        metadata.setdefault('title', parts.get('title'))

        return content, metadata

def add_reader(readers):
    readers.reader_classes['rst'] = MathRstReader

# This is how pelican works.
def register():
    signals.readers_init.connect(add_reader)
