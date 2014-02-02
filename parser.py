#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-

"""Library of parser combinators."""

import abc
import logging
import re

from base import base

LogLevel = base.LogLevel


class Error(Exception):
  """Errors raised in this module."""
  pass


class Input(object):
  """Wraps an input stream of characters to parse."""

  def __init__(self, text, pos=0, line=1, column=0):
    """Initializes a new text input object.

    Args:
      text: Full text this input reads from.
      pos: Character position to read from, in text.
      line: Known line number the specified position corresponds to.
      column: Known column number the specified position corresponds to.
    """
    self._text = text
    self._pos = pos
    self._line = line
    self._column = column

  @property
  def text(self):
    """Returns: the content of this input, as a string."""
    return self._text[self._pos:]

  @property
  def pos(self):
    """Returns: the absolute character position this input is at (0-based)."""
    return self._pos

  @property
  def line(self):
    """Returns: the line number this input is at (1-based)."""
    return self._line

  @property
  def column(self):
    """Returns: the column number this input is at (0-based)."""
    return self._column

  def NextChar(self):
    """Advances this input to the next character.

    Returns:
      The input moved to the next character.
    """
    if len(self._text) == 0:
      return self
    if self.text[0] == '\n':
      line = self._line + 1
      column = 0
    else:
      line = self._line
      column = self._column + 1
    return Input(text=self._text, pos=self._pos + 1, line=line, column=column)

  def Next(self, nchars):
    """Advances this input to the next nchars characters.

    Args:
      nchars: Number of characters to move forward to.
    Returns:
      The input moved nchars characters forward.
    """
    current = self
    for _ in range(nchars):
      current = current.NextChar()
    return current

  def __str__(self):
    return 'Input(line=%d, column=%d, pos=%d, len=%d)' \
        % (self.line, self.column, self.pos, len(self))

  def __repr__(self):
    return 'Input(line=%d, column=%d, pos=%d, len=%d, text=%r)' \
        % (self.line, self.column, self.pos, len(self),
           base.Truncate(self.text, 40))

  def __len__(self):
    """Returns: the number of characters in this input."""
    return len(self.text)


# ------------------------------------------------------------------------------


class ParsingResult(object):
  """Base class for the result of a parser."""

  def __init__(self, success, next, value=None, match=None, message=None):
    self._success = success
    self._next = next

    self._value = value
    self._match = match
    self._message = message

  @property
  def success(self):
    return self._success

  @property
  def match(self):
    """Returns: the string matched."""
    assert self._success
    return self._match

  @property
  def value(self):
    """Returns: the value that was parsed."""
    assert self._success
    return self._value

  @property
  def next(self):
    return self._next

  @property
  def message(self):
    return self._message


class Success(ParsingResult):
  def __init__(self, match, next, value=None):
    super(Success, self).__init__(
        success=True,
        next=next,
        match=match,
        value=value,
    )


class Failure(ParsingResult):
  def __init__(self, next, message=None):
    super(Failure, self).__init__(
        success=False,
        next=next,
        message=message,
    )

  def __str__(self):
    return 'Failure(message=%r, next=%r)' % (self.message, self.next)


# ------------------------------------------------------------------------------


class ParserBase(object, metaclass=abc.ABCMeta):
  """Base class for a parser."""

  def __init__(self):
    pass

  @abc.abstractmethod
  def Parse(self, input):
    """Parses the specified input, and returns a ParsingResult.

    Args:
      input: Input instance to parse.
    Returns:
      ParsingResult.
    """
    raise Error('Abstract')


class Str(ParserBase):
  """Matches an exact string. No leading space is skipped."""

  def __init__(self, str):
    self._str = str

  def Parse(self, input):
    if input.text.startswith(self._str):
      logging.log(LogLevel.DEBUG_VERBOSE, 'Matched Str(%r)', self._str)
      return Success(
          match=self._str,
          value=self._str,
          next=input.Next(len(self._str)),
      )
    else:
      return Failure(next=input)


class Regex(ParserBase):
  """Matches a regex. No leading soace is skipped."""

  def __init__(self, regex):
    """Creates a parser to match a regular expression.

    Args:
      regex: Regex to match.
    """
    self._regex = regex
    self._pattern = re.compile(regex)

  def Parse(self, input):
    match = self._pattern.match(input.text)
    if match is None:
      return Failure(next=input)
    else:
      matched_str = match.group(0)
      logging.log(
          LogLevel.DEBUG_VERBOSE,
          'Matched Regex(%r) = %r', self._pattern.pattern, matched_str)
      return Success(
          match=matched_str,
          value=matched_str,
          next=input.Next(len(matched_str)),
      )


# ------------------------------------------------------------------------------


# Matches spaces, new lines, tabs:
RE_SPACES = re.compile(r"""\s+""")

# Matches spaces a C-style comments (end-of-line and multi-line):
RE_CSTYLE_COMMENTS = re.compile(r"""(\s|//.*|(?m)/\*(\*(?!/)|[^*])*\*/)+""")


class Token(ParserBase):
  """Matches a token, skipping leading spaces if any."""

  def __init__(self, parser, spaces=RE_SPACES):
    """Creates a new parser for a token.

    Args:
      parser: Parser for the token to match.
      spaces: Regex matcher for the leading spaces to skip.
          Defaults to normal space characters (includes tabs, new lines, etc).
    """
    self._parser = parser
    self._spaces = spaces
    self._space_parser = Regex(self._spaces)

  def Parse(self, input):
    # Consume leading spaces, if any:
    result = self._space_parser.Parse(input)

    # Apply token parser:
    return self._parser.Parse(result.next)


def TokenStr(str, spaces=RE_SPACES):
  """Matches a token, skipping leading spaces if any."""
  return Token(Str(str), spaces=spaces)


def TokenRegex(regex, spaces=RE_SPACES):
  """Matches a token specified as a regex, skipped leading spaces if any."""
  return Token(Regex(regex), spaces=spaces)


# ------------------------------------------------------------------------------


class Opt(ParserBase):
  """Matches an optional construction."""

  def __init__(self, parser):
    self._parser = parser

  def Parse(self, input):
    result = self._parser.Parse(input)
    if result.success:
      return result
    else:
      return Success(next=input, match='')


class Rep(ParserBase):
  """Matches a repeated construction."""

  def __init__(self, parser, nmin=0, nmax=None):
    """Initializes a parser for a repeated construction.

    Args:
      parser: Parser for the construction to repeat.
      nmin: Minimum number of repeats.
      nmax: Maximum number of repeats, or None.
    """
    self._parser = parser
    assert (nmin >= 0)
    self._nmin = nmin
    assert ((nmax is None) or (nmax >= nmin))
    self._nmax = nmax

  def Parse(self, input):
    values = []
    nrepeats = 0
    current_input = input

    while (self._nmax is None) or (nrepeats < self._nmax):
      result = self._parser.Parse(current_input)
      if result.success:
        values.append(result.value)
        current_input = result.next
        nrepeats += 1
      else:
        break

    if nrepeats < self._nmin:
      return Failure(next=input)
    else:
      full_match = input.text[:(current_input.pos - input.pos)]
      return Success(next=current_input, match=full_match, value=values)


def Rep1(parser, nmax=None):
  """Repeats a construction at least once."""
  return Rep(parser=parser, nmin=1, nmax=nmax)


class Seq(ParserBase):
  """Matches a sequence of constructions."""

  def __init__(self, *parsers):
    assert (len(parsers) > 0)
    self._parsers = parsers

  def Parse(self, input):
    current_input = input
    values = []
    for parser in self._parsers:
      assert hasattr(parser, 'Parse'), repr(parser)
      result = parser.Parse(current_input)
      if result.success:
        values.append(result.value)
        current_input = result.next
      else:
        return Failure(next=input, message=result.message)
    full_match = input.text[:current_input.pos - input.pos]
    return Success(match=full_match, next=current_input, value=values)


class Branch(ParserBase):
  """Parses one construction from an ordered list of possibilities."""

  def __init__(self, *parsers):
    assert (len(parsers) > 0)
    self._parsers = parsers

  def Parse(self, input):
    for parser in self._parsers:
      result = parser.Parse(input)
      if result.success:
        return result
    return Failure(next=input, message=result.message)


# ------------------------------------------------------------------------------


class _Map(ParserBase):
  def __init__(self, parser, mapfn):
    self._parser = parser
    self._mapfn = mapfn

  def Parse(self, input):
    result = self._parser.Parse(input)
    if result.success:
      result = Success(
          match=result.match,
          next=result.next,
          value=self._mapfn(result.value),
      )
    return result


def Map(parser, mapfn):
  """Rewrites a successful result's value.

  Args:
    parser: Parser whose successful result should be mapped.
    mapfn: Function that rewrites the value.
  Returns:
    The original parser wrapped to map the result value.
  """
  return _Map(parser, mapfn)


ParserBase.Map = Map


class Ref(ParserBase):
  """Parser reference. Allows forward declaration of parsers."""

  def __init__(self):
    self._ref = None

  def Bind(self, parser):
    assert (self._ref is None), 'Reference already set.'
    self._ref = parser

  def Parse(self, input):
    assert (self._ref is not None), ('Unbound parser reference: %r.' % (self,))
    return self._ref.Parse(input)


# ------------------------------------------------------------------------------


"""Parses a C-style identifier."""
Identifier = Regex(r'[A-Za-z_][A-Za-z0-9_]*')


def GetRangeForBase(base):
  """Returns a regex range of characters for a digit in a given base.

  Args:
    Base for the digits to recognize.
  Returns:
    The regex range for the specified digit base.
  """
  assert (base > 1)
  if base <= 10:
    return '[0-%s]' % (base - 1)
  else:
    lower = chr(base + ord('a'))
    upper = chr(base + ord('A'))
    return '[0-9a-%sA-%s]' % (lower, upper)


class Integer(ParserBase):
  """Parses an integer of a given base."""

  def __init__(self, base=10, prefix=''):
    assert ((base >= 2) and (base <= 36))
    self._base = base
    self._digit_parser = Regex(r'-?%s%s+' % (prefix, GetRangeForBase(base)))

  def Parse(self, input):
    result = self._digit_parser.Parse(input)
    if result.success:
      result = Success(
          match=result.match,
          value=int(result.match, self._base),
          next=result.next,
      )
    return result


HexInteger = Integer(base=16, prefix='0[xX]')
OctalInteger = Integer(base=8, prefix='0[oO]')
BinaryInteger = Integer(base=2, prefix=r'0[bB]')
DecimalInteger = Integer(base=10, prefix='')

# Parses C/Java/Python-style integers:
AllInteger = Branch(
    HexInteger,
    OctalInteger,
    BinaryInteger,
    DecimalInteger,
)


def Unescape(string):
  unescaped = ''
  while len(string) > 0:
    char = string[0]
    string = string[1:]
    if char != '\\':
      unescaped += char
    else:
      char = string[0]
      string = string[1:]
      if char == 'u':
        unescaped += chr(int(string[:4], 16))
      elif char == 'n':
        unescaped += '\n'
      elif char == 'r':
        unescaped += '\r'
      elif char == 't':
        unescaped += '\t'
      else:
        unescaped += char
  return unescaped


class SingleQuoteStringLiteral(ParserBase):
  """Matches a single-quote string literal."""

  def __init__(self):
    self._regex_parser = \
        Regex(r"""'(?:[^'\\]|(?:\\u[0-9a-fA-F]{4})|(?:\\[^u]))*'""")

  def Parse(self, input):
    result = self._regex_parser.Parse(input)
    if result.success:
      literal = result.match[1:-1]
      literal = Unescape(literal)
      result = Success(
          match=result.match,
          value=literal,
          next=result.next,
      )
    return result


class DoubleQuoteStringLiteral(ParserBase):
  """Matches a double-quote string literal."""

  def __init__(self):
    self._regex_parser = \
        Regex(r'''"(?:[^"\\]|(?:\\u[0-9a-fA-F]{4})|(?:\\[^u]))*"''')

  def Parse(self, input):
    result = self._regex_parser.Parse(input)
    if result.success:
      literal = result.match[1:-1]
      literal = Unescape(literal)
      result = Success(
          match=result.match,
          value=literal,
          next=result.next,
      )
    return result


class TripleQuoteStringLiteral(ParserBase):
  """Matches a triple-quote string literal."""

  def __init__(self):
    self._regex_parser = \
        Regex(r'"""(?:[^\\]|(?:\\u[0-9a-fA-F]{4})|(?:\\[^u]))*?"""')

  def Parse(self, input):
    result = self._regex_parser.Parse(input)
    if result.success:
      literal = result.match[3:-3]
      literal = Unescape(literal)
      result = Success(
          match=result.match,
          value=literal,
          next=result.next,
      )
    return result


# Matches any string literal:
AllString = Branch(
    TripleQuoteStringLiteral,
    DoubleQuoteStringLiteral,
    SingleQuoteStringLiteral,
)
