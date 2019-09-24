"""trade.Occurrence

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


class Occurrence(object):
    """A class to represent occurrences with subjects.

    Attributes:
        subject: A Subject instance.
        date: A string to represent the moment of the occurrence.
        details: A dict with the occurrence details.
    """

    def __init__(self, subject, date, details):
        self.subject = subject
        self.date = date
        self.details = details

    def update_holder(self, holder):
        """Udpate the Holder state according to the occurrence.

        This implementation is a example of how a Occurrence object
        can update the Holder state; this method should be overriden
        by classes that inherit from the Occurrence class.

        This sample implementation simply update the quantity and the average
        price of the Subject in the Holder's possession every time objects
        from this class are passed to Holder.trade().

        This sample implementation considers the following signature for
        the Holder.state dict:
        
        .. code:: python

            {
                "SUBJECT SYMBOL": {
                    "quantity": 0,
                    "value": 0
                }
            }

        And the following signature for the Occurrance.details dict:
        
        .. code:: python

            {
                "quantity": 0,
                "value": 0
            }
        """

        subject_symbol = self.subject.symbol

        # If the Holder already have a state regarding this Subject,
        # update that state
        if subject_symbol in holder.state:

            # If the Holder have zero units of this subject, the average
            # value paid/received for the subject is the value of the trade itself
            if not holder.state[subject_symbol]['quantity']:
                holder.state[subject_symbol]['value'] = self.details['value']

            # If the Holder owns units of this subject then the average value
            # paid/received for the subject may need to be updated with
            # this occurrence details

            # If the occurrence have the same sign as the quantity in the Holder
            # state, a new average value needs to be calculated for the subject
            elif same_sign(
                    holder.state[subject_symbol]['quantity'],
                    self.details['quantity']):
                holder.state[subject_symbol]['value'] = average_price(
                    holder.state[subject_symbol]['quantity'],
                    holder.state[subject_symbol]['value'],
                    self.details['quantity'],
                    self.details['value']
                )

            # If the occurrence does not have the same sign of the quantity in the
            # Holder state, then do other stuff.
            # A trade app would normally implement some sort of profit/loss logic
            # here.
            # This sample implementation only checks if the average value
            # of the subject needs to be updated and then update it as needed.
            else:
                if same_sign(
                        self.details['quantity'],
                        holder.state[subject_symbol]['quantity'] + self.details['quantity']):
                    holder.state[subject_symbol]['value'] = self.details['value']

            # Update the quantity of the subject in the Holder's posession
            holder.state[subject_symbol]['quantity'] += self.details['quantity']

        # If the Holder don't have a state with this occurrence's Subject,
        # then register this occurrence as the first state of the Subject
        # in the Holder's possession
        else:
            holder.state[subject_symbol] = {
                'quantity': self.details['quantity'],
                'value': self.details['value']
            }

        # If the Holder knows about this Subject but don't have any unit
        # of it, the paid value of the subject in the Holder state should
        # be zero.
        if not holder.state[subject_symbol]['quantity']:
            holder.state[subject_symbol]['value'] = 0

def average_price(quantity_1, price_1, quantity_2, price_2):
    """Calculates the average price between two asset states."""
    return (quantity_1 * price_1 + quantity_2 * price_2) / \
            (quantity_1 + quantity_2)

def same_sign(number_1, number_2):
    """Checks if two numbers have the same sign."""
    return (number_1 >= 0) ^ (number_2 < 0)
