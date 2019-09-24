"""trade.Context

https://github.com/rochars/trade

Copyright (c) 2015-2018 Rafael da Silva Rocha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from __future__ import absolute_import
from __future__ import division

import copy


class Context(object):
    """A class to group occurrences and contextualize them.

    To contextualize a group of occurrences could mean:
    - To identify daytrades and separate them into different occurrences
    - Group occurrences with the same subject into one occurrence
    - Apply costs and other deductions to the value to the occurrences
    - Calculate taxes based on the occurrences in the context

    Objects from this class are created with both a list of occurrences and a
    list of functions (called "context tasks").

    The context tasks are run by calling Context.apply(). Context tasks
    run in the order they are listed.

    Every context task function receives one argument: the context itself. It
    is then free to manipulate the raw occurrence data stored in the
    Context.occurrences list.

    The contextualized occurrence data is then stored in the
    Context.contextualized list.

    The occurrences in Context.contextualized should be informed to a Holder
    as regular occurrences.

    The original Occurrence list is not modified.

    Attributes:
        occurrences: A list of Occurrence objects.
        tasks: A list of functions.
        contextualized: A list of Occurrence objects.
    """

    def __init__(self, occurrences, tasks):
        self.occurrences = occurrences
        self.tasks = tasks
        self.contextualized = []

    def apply(self):
        """Apply the rules of the context to its occurrences.

        This method executes all the functions defined in
        self.tasks in the order they are listed.

        Every function that acts as a context task receives the
        Context object itself as its only argument.

        The contextualized occurrences are then stored in
        Context.contextualized.

        The original Occurrence instances are not modified.
        """
        raw_operations = copy.deepcopy(self.occurrences)
        for task in self.tasks:
            task(self)
        self.occurrences = raw_operations
