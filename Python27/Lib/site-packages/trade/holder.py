"""trade.Holder

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


class Holder(object):
    """A class to represent a owner of subjects.

    A Holder object is created with a initial state. The state of Holder
    is then updated by Occurrence objects by calling Holder.trade(occurrence).

    trade apps should define the Holder.state signature according to
    their needs.

    Classes that inherit from Occurrence may add and manipulate new
    items on the Holder.state dictionary.

    Attributes:
        state: A dict representing the state of the Holder.
    """

    def __init__(self, state=None):
        self.state = {}
        if state:
            self.state = state

    def trade(self, occurrence):
        """Update the state of the Holder with an occurrence."""
        occurrence.update_holder(self)
