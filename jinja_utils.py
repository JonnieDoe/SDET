#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""Jinja2 Utils module."""


from jinja2 import nodes, Undefined
from jinja2.exceptions import TemplateRuntimeError
from jinja2.ext import Extension


class SilentUndefined(Undefined):
    """Don`t break page-loads because vars aren`t there!"""

    def _fail_with_undefined_error(self, *args, **kwargs):
        """Raise an error if a var is undefined."""
        raise ValueError('JINJA2: something was undefined!')


class RaiseExtension(Extension):
    """Custom RaiseExtension for Jinja2 templates.
    https://github.com/duelafn/python-jinja2-apci/blob/master/jinja2_apci/error.py
    """

    # This is our keyword(s) set:
    tags = (['raise'])

    # See also: jinja2.parser.parse_include()
    def parse(self, parser):
        """If any of the :attr:`tags` matched this method is called with the
        parser as first argument. The token the parser stream is pointing at
        is the name token that matched. This method has to return one or a
        list of multiple nodes.

        :param parser: Parser
        """

        # The first token is the token that started the tag. In our case we only listen to "raise" so this will be a
        # name token with "raise" as value. We get the line number so that we can give that line number to
        # the nodes we insert.
        line_no = next(parser.stream).lineno

        # Extract the message from the template
        message_node = parser.parse_expression()

        return nodes.CallBlock(
            self.call_method('_raise', [message_node], lineno=line_no), [], [], [], lineno=line_no
        )

    def _raise(self, msg, caller):
        raise TemplateRuntimeError(msg)


class PrintOnConsole(object):
    """DEBUG utils for printing on screen/console."""

    @staticmethod
    def debug(text):
        """Debug method to print text on screen/console.
        :param text: Text to print
        """
        print(text)
