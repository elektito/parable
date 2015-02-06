from parable import Symbol
from cStringIO import StringIO

class ReadError(RuntimeError):
    pass

class EofReadError(ReadError):
    pass

class Reader(object):
    def __init__(self, file):
        self.file = file
        if isinstance(file, (str, unicode)):
            self.file = StringIO(file)
        self.row = 0
        self.col = 0

    def __read_char(self):
        b = self.file.read(1)
        if b == '':
            return ''

        self.col += 1
        if b == '\n':
            self.row += 1
        if b == '\r':
            self.row += 1
            b = self.read(1)
            if b == '':
                return '\n'
            if b == '\n':
                return '\n'
            self.file.seek(-1, 1)

        return b

    def __go_back(self):
        self.file.seek(-1, 1)

    def skip_whitespace(self):
        b = self.__read_char()
        while b:
            if b not in '; \t\r\n':
                self.__go_back()
                break

            if b == ';':
                while b and b != '\n':
                    b = self.__read_char()

            b = self.__read_char()

    def read_atom(self):
        self.skip_whitespace()

        atom = ''
        b = self.__read_char()
        if b == "'":
            return [Symbol('quote'), self.read()]

        while b and b not in '() \'\n\t\r;':
            atom += b
            b = self.__read_char()

        if b:
            self.__go_back()

        try:
            # is this an integer?
            integer = int(atom)

            # yes, it is.
            return integer
        except:
            pass # not an integer

        # is it a string literal?
        if len(atom) >= 2 and atom[0] == '"' and atom[-1] == '"':
            return atom[1:-1]

        return Symbol(atom)

    def read_list(self):
        b = self.__read_char()
        if not b or b != '(':
            raise ReadError('Expected "(".')

        items = []

        while True:
            self.skip_whitespace()
            b = self.__read_char()

            if not b:
                raise EofReadError('Unexpected end of file.')

            if b == ')':
                return items

            self.__go_back()
            if b == '(':
                items.append(self.read_list())
            else:
                items.append(self.read_atom())

    def read(self):
        self.skip_whitespace()
        b = self.__read_char()
        if not b:
            return None

        self.__go_back()
        if b == '(':
            return self.read_list()
        else:
            return self.read_atom()
