import pkg_resources
from metanl.general import preprocess_text
from metanl.wordlist import get_frequency
from metanl.extprocess import ProcessWrapper, ProcessError
import re

UNSAFE_CHARS = ''.join(chr(n) for n in (range(0x00, 0x10) + range(0x11, 0x20) + range(0x7f, 0xa0)))
UNSAFE_RE = re.compile('[' + UNSAFE_CHARS + ']')

class FreelingWrapper(ProcessWrapper):
    r"""
    Handle English, Spanish, Italian, Portuguese, or Welsh text by calling an
    installed copy of FreeLing.

    The constructor takes one argument, which is the installed filename of the
    language-specific config file, such as 'en.cfg'.

        >>> english.tag_and_stem("This is a test.\n\nIt has two paragraphs, and that's okay.")
        [(u'this', u'DT', u'This'), (u'be', u'VBZ', u'is'), (u'a', u'DT', u'a'), (u'test', u'NN', u'test'), (u'.', '.', u'.'), (u'it', u'PRP', u'It'), (u'have', u'VBZ', u'has'), (u'two', u'DT', u'two'), (u'paragraph', u'NNS', u'paragraphs'), (u',', '.', u','), (u'and', u'CC', u'and'), (u'that', u'PRP', u'that'), (u'be', u'VBZ', u"'s"), (u'okay', u'JJ', u'okay'), (u'.', '.', u'.')]

    """
    def __init__(self, lang):
        self.lang = lang
        self.configfile = pkg_resources.resource_filename(__name__, 'data/freeling/%s.cfg' % lang)
        self.splitterfile = pkg_resources.resource_filename(__name__,
                'data/freeling/generic_splitter.dat')
        #self.input_log = open('input.log', 'w')
        #self.output_log = open('output.log', 'w')

    def _get_command(self):
        """
        Get the command for running the basic FreeLing pipeline in the
        specified language.

        The options we choose are:

            -f data/freeling/<language>.cfg
                load our custom configuration for the language
            --fsplit data/freeling/generic_splitter.dat
                don't do any special handling of ends of sentences
        """
        return ['analyze', '-f', self.configfile, '--fsplit',
                self.splitterfile]

    def get_record_root(self, record):
        """
        Given a FreeLing record, return the root word.
        """
        return record[1].lower()

    def get_record_token(self, record):
        """
        The token of a FreeLing record is the first item on the line.
        """
        return record[0]

    def get_record_pos(self, record):
        """
        In English, return the third segment of the record.

        In other languages, this segment contains one letter for the part of
        speech, plus densely-encoded features that we really have no way to
        use. Return just the part-of-speech letter.
        """
        if self.lang == 'en':
            return record[2]
        else:
            return record[2][0]

    def is_stopword_record(self, record, common_words=False):
        """
        Determiners are stopwords. Detect this by checking whether their POS
        starts with 'D'.
        """
        return (record[2][0] == 'D')

    def analyze(self, text):
        """
        Run text through the external process, and get a list of lists
        ("records") that contain the analysis of each word.
        """
        try:
            text = UNSAFE_RE.sub('', preprocess_text(text)).strip()
            if not text:
                return []
            chunks = text.split('\n')
            results = []
            for chunk_text in chunks:
                text = chunk_text.encode('utf-8')
                self.send_input(text + '\n')
                #self.input_log.write(text+'\n')
                out_line = ''
                while True:
                    out_line = self.receive_output_line()
                    #self.output_log.write(out_line)
                    out_line = out_line.decode('utf-8')

                    if out_line == u'\n':
                        break

                    record = out_line.strip(u'\n').split(u' ')
                    results.append(record)
            return results
        except ProcessError:
            self.restart_process()
            return self.analyze(text)

    def word_frequency(self, word, default_freq=0):
        """
        Looks up the word's frequency in the Leeds Internet corpus.
        """
        return get_frequency(word, self.lang, default_freq)

LANGUAGES = {}
english = LANGUAGES['en'] = FreelingWrapper('en')
spanish = LANGUAGES['es'] = FreelingWrapper('es')
italian = LANGUAGES['it'] = FreelingWrapper('it')
portuguese = LANGUAGES['pt'] = FreelingWrapper('pt')
russian = LANGUAGES['ru'] = FreelingWrapper('ru')
welsh = LANGUAGES['cy'] = FreelingWrapper('cy')
