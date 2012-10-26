# -*- coding: utf-8 -*-
"""
Tools for using an external program as an NLP pipe. See, for example,
freeling.py.
"""

from metanl.general import unicode_is_punctuation
import subprocess

class ProcessError(IOError):
    """
    A subclass of IOError raised when we can't start the external process.
    """
    pass

class ProcessWrapper(object):
    """
    A ProcessWrapper uses the `subprocess` module to keep a process open that
    we can pipe stuff through to get NLP results.
    
    Instead of every instance immediately opening a process, however, it waits
    until the first time it is needed, then starts the process.

    Many methods are intended to be implemented by subclasses of ProcessWrapper
    that actually know what program they're talking to.
    """
    def __del__(self):
        """
        Clean up by closing the pipe.
        """
        if hasattr(self, '_process'):
            self._process.stdin.close()

    @property
    def process(self):
        """
        Store the actual process in _process. If it doesn't exist yet, create
        it.
        """
        if hasattr(self, '_process'):
            return self._process
        else:
            self._process = self._get_process()
            return self._process
    
    def _get_command(self):
        """
        This method should return the command to run, as a list
        of arguments that can be used by subprocess.Popen.
        """
        raise NotImplementedError

    def _get_process(self):
        """
        Create the process by running the specified command.
        """
        command = self._get_command()
        try:
            return subprocess.Popen(command, bufsize=1, close_fds=True,
                                    stdout=subprocess.PIPE,
                                    stdin=subprocess.PIPE)
        except OSError:
            raise ProcessError("Couldn't start the external process: %r" %
                    command)

    def get_record_root(self, record):
        """
        Given a *record* (the data that the external process returns for a
        given single token), this specifies how to extract its root word
        (aka its lemma).
        """
        raise NotImplementedError

    def get_record_token(self, record):
        """
        Given a record, this specifies how to extract the exact word or token
        that was processed.
        """
        raise NotImplementedError

    def analyze(self, text):
        """
        Take text as input, run it through the external process, and return a
        list of *records* containing the results.
        """
        raise NotImplementedError

    def send_input(self, data):
        self.process.stdin.write(data)

    def receive_output_line(self):
        line = self.process.stdout.readline()
        if not line:
            raise ProcessError("reached end of output")
        return line

    def restart_process(self):
        if hasattr(self, '_process'):
            self._process.stdin.close()
        self._process = self._get_process()
        return self._process

    def tokenize_list(self, text):
        """
        Split a text into separate words.
        """
        return [self.get_record_token(record) for record in self.analyze(text)]

    def tokenize(self, text):
        """
        Yell at people who are still using simplenlp's bad idea of
        tokenization.
        """
        raise NotImplementedError("tokenize is deprecated. Use tokenize_list.")

    def is_stopword_record(self, record, common_words=False):
        """
        Given a record, return whether it represents a stopword (a word that
        should be discarded in NLP results).

        Note that we want very few words to be stopwords. Words that are
        meaningful but simply common can be recognized by their very high word
        frequency, and handled appropriately. Often, we only want determiners
        (such as 'a', 'an', and 'the' in English) to be stopwords.

        Takes in a vestigial parameter, `common_words`, and ignores it.
        """
        raise NotImplementedError

    def is_stopword(self, text):
        """
        Determine whether a single word is a stopword, or whether a short
        phrase is made entirely of stopwords, disregarding context.

        Use of this function should be avoided; it's better to give the text
        in context and let the process determine which words are the stopwords.
        """
        found_content_word = False
        for record in self.analyze(text):
            if not self.is_stopword_record(record):
                found_content_word = True
                break
        return not found_content_word

    def get_record_pos(self, record):
        """
        Given a record, get the word's part of speech.

        This default implementation simply distinguishes stopwords from
        non-stopwords.
        """
        if self.is_stopword_record(record):
            return 'STOP'
        else:
            return 'TERM'

    def normalize_list(self, text, cache=None):
        """
        Get a canonical list representation of text, with words
        separated and reduced to their base forms.

        TODO: use the cache.
        """
        words = []
        analysis = self.analyze(text)
        for record in analysis:
            if not self.is_stopword_record(record):
                words.append(self.get_record_root(record))
        if not words:
            # Don't discard stopwords if that's all you've got
            words = [self.get_record_token(record) for record in analysis]
        return words

    def normalize(self, text, cache=None):
        """
        Get a canonical string representation of this text, like
        :meth:`normalize_list` but joined with spaces.

        TODO: use the cache.
        """
        return ' '.join(self.normalize_list(text, cache))

    def tag_and_stem(self, text, cache=None):
        """
        Given some text, return a sequence of (stem, pos, text) triples as
        appropriate for the reader. `pos` can be as general or specific as
        necessary (for example, it might label all parts of speech, or it might
        only distinguish function words from others).
        """
        analysis = self.analyze(text)
        triples = []

        tag_is_next = False
        for record in analysis:
            root = self.get_record_root(record)
            token = self.get_record_token(record)

            if token:
                if tag_is_next:
                    triples.append((u'#'+token, 'TAG', u'#'+token))
                    tag_is_next = False
                elif token == u'#':
                    tag_is_next = True
                elif unicode_is_punctuation(token):
                    triples.append((token, '.', token))
                else:
                    pos = self.get_record_pos(record)
                    triples.append((root, pos, token))
        return triples

    def extract_phrases(self, text):
        """
        Given some text, extract phrases of up to 2 content words,
        and map their normalized form to the complete phrase.
        """
        analysis = self.analyze(text)
        for pos1 in xrange(len(analysis)):
            rec1 = analysis[pos1]
            if not self.is_stopword_record(rec1):
                yield self.get_record_root(rec1), rec1[0]
                for pos2 in xrange(pos1+1, len(analysis)):
                    rec2 = analysis[pos2]
                    if not self.is_stopword_record(rec2):
                        roots = [self.get_record_root(rec1),
                                 self.get_record_root(rec2)]
                        pieces = [analysis[i][0] for i in xrange(pos1, pos2+1)]
                        term = ' '.join(roots)
                        phrase = ''.join(pieces)
                        yield term, phrase
                        break

