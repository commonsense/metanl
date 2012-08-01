from metanl.general import preprocess_text
from metanl.wordlist import get_frequency
from metanl.extprocess import ProcessWrapper
import re

UNSAFE_CHARS = ''.join(chr(n) for n in (range(0x00, 0x10) + range(0x11, 0x20) + range(0x7f, 0xa0)))
UNSAFE_RE = re.compile('[' + UNSAFE_CHARS + ']')

class FreelingWrapper(ProcessWrapper):
    """
    Handle English, Spanish, Italian, Portuguese, or Welsh text by calling an
    installed copy of FreeLing.

    The constructor takes one argument, which is the installed filename of the
    language-specific config file, such as 'en.cfg'.
    """
    def __init__(self, lang):
        self.lang = lang
        self.configfile = lang+'.cfg'
        #self.input_log = open('input.log', 'w')
        #self.output_log = open('output.log', 'w')

    def _get_command(self):
        return ['analyze', '-f', self.configfile,
                '--nonumb', '--noloc', '--nodate', '--noquant', '--flush']

    def get_record_root(self, record):
        """
        Given a FreeLing record, return the root word.
        """
        return record[1].lower()

    def get_record_token(self, record):
        return record[0].lower()

    def get_record_pos(self, record):
        if self.lang == 'en':
            return record[2]
        else:
            return record[2][0]

    def is_stopword_record(self, record, common_words=False):
        return (record[2][0] == 'D')
    
    def analyze(self, text):
        """
        Run text through the external process, and get a list of lists
        ("records") that contain the analysis of each word.
        """
        text = UNSAFE_RE.sub('', preprocess_text(text)).strip()
        if not text:
            return []
        chunks = text.split('\n')
        results = []
        for chunk_text in chunks:
            text = chunk_text.encode('utf-8')
            self.process.stdin.write(text+'\n')
            #self.input_log.write(text+'\n')
            out_line = ''
            while True:
                out_line = self.process.stdout.readline()
                #self.output_log.write(out_line)
                out_line = out_line.decode('utf-8')

                if out_line == u'\n':
                    break

                record = out_line.strip(u'\n').split(u' ')
                results.append(record)
        return results

    def word_frequency(self, word, default_freq=0):
        """
        Looks up the word's frequency in the Leeds Internet corpus.
        """
        return get_frequency(word, self.lang, default_freq)

languages = {}
english = languages['en'] = FreelingWrapper('en')
spanish = languages['es'] = FreelingWrapper('es')
italian = languages['it'] = FreelingWrapper('it')
portuguese = languages['pt'] = FreelingWrapper('pt')
welsh = languages['cy'] = FreelingWrapper('cy')

