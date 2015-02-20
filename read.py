from parable import Symbol, List, Bool, Integer, String
from cStringIO import StringIO

class ReadError(RuntimeError):
    pass

class EofReadError(ReadError):
    pass

class Reader(object):
    def __init__(self, file, filename):
        self.file = file
        self.filename = filename
        if isinstance(file, (str, unicode)):
            self.file = StringIO(file)

        self.row = 0
        self.col = 0

        self.__lines = self.file.readlines()

        self.skip_whitespace()

    def current(self):
        if self.row >= len(self.__lines) or \
           self.col >= len(self.__lines[self.row]):
            return ''

        return self.__lines[self.row][self.col]

    def next(self):
        if self.row >= len(self.__lines):
            return

        self.col += 1
        if self.col >= len(self.__lines[self.row]):
            self.col = 0
            self.row += 1
            self.skip_whitespace()

    def go_back(self):
        if self.row == 0 and self.col == 0:
            return

        self.col -= 1
        if self.col < 0:
            self.row -= 1
            if self.row < 0:
                self.row = 0
                self.col = 0
                return
            self.col = len(self.__lines[self.row]) - 1

    def skip_whitespace(self):
        b = self.current()
        while b:
            if b not in '; \t\r\n':
                break

            if b == ';':
                while b and b != '\n':
                    self.next()
                    b = self.current()
                self.go_back()

            self.next()
            b = self.current()

    def mark(self):
        self.__start_row = self.row
        self.__start_col = self.col

    def add_metadata(self, value):
        value.start_row = self.__start_row
        value.start_col = self.__start_col
        value.end_row = self.row
        value.end_col = self.col
        value.filename = self.filename

    def read_atom(self):
        self.skip_whitespace()

        atom = ''
        b = self.current()
        if b == "'":
            quote = Symbol('quote')
            self.mark()
            self.add_metadata(quote)

            self.mark()
            self.next()
            value = self.read()
            form = List([quote, value])
            self.add_metadata(form)
            return form

        if b == "`":
            backquote = Symbol('backquote')
            self.mark()
            self.add_metadata(backquote)

            self.mark()
            self.next()
            value = self.read()
            form = List([backquote, value])
            self.add_metadata(form)
            return form

        if b == ",":
            self.next()
            if self.current() == '@':
                name = 'unquote-splicing'
            else:
                self.go_back()
                name = 'unquote'
            unquote = Symbol(name)
            self.mark()
            self.add_metadata(unquote)

            self.mark()
            self.next()
            value = self.read()
            form = List([unquote, value])
            self.add_metadata(form)
            return form

        self.mark()

        # is it a string literal?
        if b == '"':
            self.mark()
            self.next()
            b = self.current()
            while b and b != '"':
                if b == '\\':
                    self.next()
                    b = self.current()
                    if not b:
                        continue

                    atom += b
                    self.next()
                    b = self.current()
                    b = self.current()
                    if not b:
                        continue
                else:
                    atom += b
                    self.next()
                    b = self.current()
            if not b:
                raise EofReadError('Unexpected end of file inside string literal.')
            string = String(atom)
            self.add_metadata(string)
            self.next()
            return string

        while b and b not in '() \'\n\t\r;':
            atom += b
            self.next()
            b = self.current()

        if b:
            self.go_back()

        try:
            # is this an integer?
            integer = int(atom)
            integer = Integer(integer)

            # yes, it is.
            self.add_metadata(integer)
            self.next()
            return integer
        except ValueError:
            pass # not an integer

        if atom == '#t':
            ret = Bool(True)
        elif atom == '#f':
            ret = Bool(False)
        else:
            ret = Symbol(atom)
        self.add_metadata(ret)
        self.next()
        return ret

    def read_list(self):
        b = self.current()
        if not b or b != '(':
            raise ReadError('Expected "(".')

        items = List()
        items.filename = self.filename
        items.start_row = self.row
        items.start_col = self.col

        self.next()
        while True:
            self.skip_whitespace()
            b = self.current()

            if not b:
                raise EofReadError('Unexpected end of file.')

            if b == ')':
                items.end_row = self.row
                items.end_col = self.col
                self.next()
                return items

            items.append(self.read())
            #self.next()

    def read(self):
        self.skip_whitespace()
        b = self.current()
        if not b:
            return None

        if b == '(':
            return self.read_list()
        else:
            return self.read_atom()
