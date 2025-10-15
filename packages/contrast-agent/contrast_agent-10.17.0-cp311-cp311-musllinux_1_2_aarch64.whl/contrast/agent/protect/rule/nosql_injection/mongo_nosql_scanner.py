# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
import re


class MongoNoSqlScanner:
    """
    Most of this code used to be a base class for protect SQLi infilter analysis for
    various databases. Now it's only used for MongoDB; agent-lib handles the rest.

    TODO: PYT-2546 We should remove this module and its parent (`rule.nosql_injection`)
    """

    # States
    STATE_INSIDE_TOKEN = "STATE_INSIDE_TOKEN"
    STATE_INSIDE_NUMBER = "STATE_INSIDE_NUMBER"
    STATE_EXPECTING_TOKEN = "STATE_EXPECTING_TOKEN"
    STATE_INSIDE_DOUBLEQUOTE = "STATE_INSIDE_DOUBLEQUOTE"
    STATE_INSIDE_SINGLEQUOTE = "STATE_INSIDE_SINGLEQUOTE"
    STATE_INSIDE_STRING_ESCAPE_BLOCK = "STATE_INSIDE_STRING_ESCAPE_BLOCK"
    STATE_INSIDE_LINE_COMMENT = "STATE_INSIDE_LINE_COMMENT"  # inside comment that will continue to the end of the line
    STATE_INSIDE_BLOCK_COMMENT = "STATE_INSIDE_BLOCK_COMMENT"  # inside a comment that will end with a closing tag
    STATE_SKIP_NEXT_CHARACTER = "STATE_SKIP_NEXT_CHARACTER"

    # Regex
    DIGIT_REGEX = re.compile(r"\d")
    WHITESPACE_REGEX = re.compile(r"[\s]")
    NON_WHITESPACE_REGEX = re.compile(r"[^\s]")

    OPERATOR_REGEX = re.compile(r"[+=*^/%><!-]")

    # Special characters
    ASTRIX_CHAR = "*"
    DASH_CHAR = "-"
    SLASH_CHAR = "/"
    LEFT_ANGLE = "<"

    NO_BOUNDARY = -1

    def __init__(self):
        self._token_boundaries = None

    def crosses_boundary(self, query, index, input_string):
        """
        Checks if the input string crosses the boundary in the query
        """
        last_boundary = 0

        for boundary in self.token_boundaries(query):
            if boundary > index:
                if boundary < index + len(input_string):
                    return last_boundary, boundary

                break

            last_boundary = boundary

        return self.NO_BOUNDARY, self.NO_BOUNDARY

    def token_boundaries(self, query):
        """
        Memoization of token boundaries
        """
        if self._token_boundaries is None:
            self._token_boundaries = self.scan_token_boundaries(query)

        return self._token_boundaries

    def scan_token_boundaries(self, query):
        """
        Scans the query to identify boundaries
        """
        boundaries = []

        if not query:
            return boundaries

        state = MongoNoSqlScanner.STATE_EXPECTING_TOKEN
        index = 0

        while index < len(query):
            char = query[index]

            previous_state = state

            state = self.process_state(boundaries, state, char, index, query)

            if state == MongoNoSqlScanner.STATE_SKIP_NEXT_CHARACTER:
                index += 1
                state = previous_state
            elif state == MongoNoSqlScanner.STATE_INSIDE_STRING_ESCAPE_BLOCK:
                index = self.find_escape_sequence_boundary(query, index + 1)
                state = previous_state
            elif state == MongoNoSqlScanner.STATE_INSIDE_BLOCK_COMMENT:
                index = self.find_block_comment_boundary(query, index + 2)
                index += 1
                state = previous_state

                boundaries.append(index)
            elif state == MongoNoSqlScanner.STATE_INSIDE_LINE_COMMENT:
                index = self.find_new_line_boundary(query, index + 1)
                state = previous_state

                boundaries.append(index)

            index += 1

        return boundaries

    def process_state(self, boundaries, current_state, char, index, query):
        """
        Processes the current state within the query
        """
        result = None

        if current_state == MongoNoSqlScanner.STATE_EXPECTING_TOKEN:
            result = self.process_expecting_token(boundaries, char, index, query)
        elif current_state == MongoNoSqlScanner.STATE_INSIDE_NUMBER:
            result = self.process_number(boundaries, char, index)
        elif current_state == MongoNoSqlScanner.STATE_INSIDE_TOKEN:
            result = self.process_inside_token(boundaries, char, index, query)
        elif current_state == MongoNoSqlScanner.STATE_INSIDE_DOUBLEQUOTE:
            result = self.process_double_quote(boundaries, char, index, query)
        elif current_state == MongoNoSqlScanner.STATE_INSIDE_SINGLEQUOTE:
            result = self.process_single_quote(boundaries, char, index, query)

        return result

    def process_expecting_token(self, boundaries, char, index, query):
        """
        Processes the character based on the expected token
        """
        result = MongoNoSqlScanner.STATE_EXPECTING_TOKEN

        if char == "'":  # single quote
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_SINGLEQUOTE
        elif char == '"':  # double quote
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_DOUBLEQUOTE
        elif re.match(MongoNoSqlScanner.DIGIT_REGEX, char):  # digit
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_NUMBER
        elif self.start_line_comment(char, index, query):  # line comment
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_LINE_COMMENT
        elif self.start_block_comment(char, index, query):  # block comment
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_BLOCK_COMMENT
        elif re.match(MongoNoSqlScanner.NON_WHITESPACE_REGEX, char):  # non whitespace
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_TOKEN

        return result

    def process_inside_token(self, boundaries, char, index, query):
        """
        Process the character and returns the new state
        """
        result = MongoNoSqlScanner.STATE_INSIDE_TOKEN

        if char == "'":  # single quote
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_SINGLEQUOTE
        elif char == '"':  # double quote
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_DOUBLEQUOTE
        elif self.start_line_comment(char, index, query):  # line comment
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_LINE_COMMENT
        elif self.start_block_comment(char, index, query):  # block comment
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_INSIDE_BLOCK_COMMENT
        elif self.is_operator(char) or re.match(
            MongoNoSqlScanner.WHITESPACE_REGEX, char
        ):  # operator
            boundaries.append(index)
            result = MongoNoSqlScanner.STATE_EXPECTING_TOKEN

        return result

    def process_number(self, boundaries, char, index):
        """
        Check if the character is a number
        """
        if re.match(MongoNoSqlScanner.DIGIT_REGEX, char) or char == ".":
            return MongoNoSqlScanner.STATE_INSIDE_NUMBER

        boundaries.append(index)
        return MongoNoSqlScanner.STATE_EXPECTING_TOKEN

    def process_double_quote(self, boundaries, char, index, query):
        """
        Processes the double quote within a query
        """
        if self.escape_char(char):
            return MongoNoSqlScanner.STATE_SKIP_NEXT_CHARACTER

        if self.escape_sequence_start(char):
            return MongoNoSqlScanner.STATE_INSIDE_STRING_ESCAPE_BLOCK

        if char == '"':
            if self.double_quote_escape_in_double_quote() and self.is_double_quote(
                query, index + 1
            ):
                return MongoNoSqlScanner.STATE_SKIP_NEXT_CHARACTER

            boundaries.append(index)
            return MongoNoSqlScanner.STATE_EXPECTING_TOKEN

        return MongoNoSqlScanner.STATE_INSIDE_DOUBLEQUOTE

    def process_single_quote(self, boundaries, char, index, query):
        """
        Processes a single quote within a query
        """
        if self.escape_char(char):
            return MongoNoSqlScanner.STATE_SKIP_NEXT_CHARACTER

        if self.escape_sequence_start(char):
            return MongoNoSqlScanner.STATE_INSIDE_STRING_ESCAPE_BLOCK

        if char == "'":
            if self.single_quote_escape_in_single_quote() and self.is_single_quote(
                query, index + 1
            ):
                return MongoNoSqlScanner.STATE_SKIP_NEXT_CHARACTER

            boundaries.append(index)
            return MongoNoSqlScanner.STATE_EXPECTING_TOKEN

        return MongoNoSqlScanner.STATE_INSIDE_SINGLEQUOTE

    def is_double_quote(self, query, index):
        """
        Checks if the character at the index is a double quote
        """
        if index < 0 or index >= len(query):
            return False

        return query[index] == '"'

    def is_single_quote(self, query, index):
        """
        Checks if the character at the index is a single quote
        """
        if index < 0 or index >= len(query):
            return False

        return query[index] == "'"

    def find_escape_sequence_boundary(self, query, index):
        """
        Finds a boundary of an escape sequence
        """
        pos = index

        while pos < len(query):
            char = query[pos]

            if self.escape_sequence_end(char):
                break
            pos += 1

        return pos

    def find_block_comment_boundary(self, query, index):
        """
        Finds a boundary for a block comment
        """
        pos = index

        while pos < len(query):
            char = query[pos]

            if self.end_block_comment(char, pos, query):
                break
            pos += 1

        return pos

    def find_new_line_boundary(self, query, index):
        """
        Finds a new line boundary
        """
        pos = index

        while pos < len(query):
            char = query[pos]

            if char in ["\n", "\r"]:
                break
            pos += 1

        return pos

    def is_operator(self, char):
        """
        Checks if a character is an operator via regex
        """
        return re.match(MongoNoSqlScanner.OPERATOR_REGEX, char) is not None

    def start_line_comment(self, char, index, query):
        """
        Validates char is the start of a line comment
        """
        if char == self.SLASH_CHAR and query[index + 1] == self.SLASH_CHAR:
            return True

        return (
            char == MongoNoSqlScanner.LEFT_ANGLE
            and query[index + 1] == self.DASH_CHAR
            and query[index + 2] == self.DASH_CHAR
        )

    def start_block_comment(self, char, index, query):
        """
        Is the current character / sequence of characters the start of a block comment?
        """
        return False

    def end_block_comment(self, char, index, query):
        """
        Is the current character / sequence of characters the end of a block comment?
        """
        if char != MongoNoSqlScanner.ASTRIX_CHAR or not self.query_longer_than_index(
            query, index, 2
        ):
            return False

        return query[index + 1] == MongoNoSqlScanner.SLASH_CHAR

    def double_quote_escape_in_double_quote(self):
        """
        Indicates if '""' inside of double quotes is the equivalent of '\"'
        For Mongo, this is True
        """
        return True

    def single_quote_escape_in_single_quote(self):
        """
        Indicates if "''" inside of single quotes is the equivalent of "\'"
        We assume yes by default
        """
        return True

    def redefines_escape_char(self):
        """
        Does this language let the user redefine the escape character
        We assume no by default
        """
        return False

    def escape_char(self, char):
        """
        Is the character provided an escape character?
        By default, we'll assume
        """
        return char == "\\"

    def support_string_escape_sequence(self):
        """
        Does this language support string escape sequences?
        We assume no by default
        """
        return False

    def escape_sequence_start(self, char):
        """
        Is this the start of a string escape sequence?
        Since escape sequences aren't supported, the answer is always false
        """
        return False

    def escape_sequence_end(self, char):
        """
        Is this the end of a string escape sequence?
        Since escape sequences aren't supported, the answer is always false
        """
        return False

    def query_longer_than_index(self, query, index, diff):
        return len(query) - diff >= index
