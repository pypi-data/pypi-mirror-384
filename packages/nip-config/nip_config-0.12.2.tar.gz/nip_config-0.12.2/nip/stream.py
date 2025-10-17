from typing import Union, Type

import nip.tokens as tokens


class Stream:
    def __init__(self, sstream: str):
        self.lines = sstream.split("\n")
        self.lines = [line + " " for line in self.lines]
        self.line = 0
        self.pos = 0
        self.last_peak_pos = -1
        self._pass_forward()

    def peek(self, *args: Union[tokens.Token, Type[tokens.Token]]):
        """Reads several tokens from stream"""
        if not self:
            return None
        line = self.lines[self.line]
        pos = self.pos
        self.last_peak_pos = -1  # prevent step() after failed peek()
        read_tokens = []
        for arg in args:
            if isinstance(arg, tokens.Token):
                token_type = arg.__class__
            else:
                token_type = arg

            # skip empty line ending
            while pos < len(line) and line[pos].isspace():
                pos += 1
            if pos >= len(line):
                return None

            try:
                length, token = token_type.read(line[pos:])
                # mb: pass full stream to token. (This will allow multiline string parsing)
            except tokens.TokenError as e:
                raise StreamError(self.line, pos, e)

            if token is None:
                return None
            if isinstance(arg, tokens.Token) and token != arg:
                return None

            token.set_position(self.line, pos)
            read_tokens.append(token)
            pos += length

        self.last_peak_pos = pos
        return read_tokens

    def step(self):
        assert self.last_peak_pos > 0, "step() called before peaking any Token"
        line, pos = self.line, self.pos
        self.pos = self.last_peak_pos
        self._pass_forward()
        return line, pos  # the point we started reading, since this log is more convenient for user

    def _pass_forward(self):
        while self and (
            self.pos >= len(self.lines[self.line])
            or self.lines[self.line][self.pos :].isspace()
            or self.lines[self.line][self.pos :].strip()[0] == "#"
        ):
            self.line += 1
            self.pos = 0

        if not self:
            return

        while self.lines[self.line][self.pos].isspace():
            self.pos += 1

    def __bool__(self):
        return self.line < len(self.lines)


class StreamError(Exception):
    def __init__(self, line: int, position: int, msg: Exception):
        self.line = line
        self.pos = position
        self.msg = msg

    def __str__(self):
        return f"{self.line + 1}:{self.pos + 1}: {self.msg}"
