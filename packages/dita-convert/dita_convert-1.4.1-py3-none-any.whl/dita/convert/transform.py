# Copyright (C) 2024, 2025 Jaromir Hradilek

# MIT License
#
# Permission  is hereby granted,  free of charge,  to any person  obtaining
# a copy of  this software  and associated documentation files  (the "Soft-
# ware"),  to deal in the Software  without restriction,  including without
# limitation the rights to use,  copy, modify, merge,  publish, distribute,
# sublicense, and/or sell copies of the Software,  and to permit persons to
# whom the Software is furnished to do so,  subject to the following condi-
# tions:
#
# The above copyright notice  and this permission notice  shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS",  WITHOUT WARRANTY OF ANY KIND,  EXPRESS
# OR IMPLIED,  INCLUDING BUT NOT LIMITED TO  THE WARRANTIES OF MERCHANTABI-
# LITY,  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT
# SHALL THE AUTHORS OR COPYRIGHT HOLDERS  BE LIABLE FOR ANY CLAIM,  DAMAGES
# OR OTHER LIABILITY,  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM,  OUT OF OR IN CONNECTION WITH  THE SOFTWARE  OR  THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from lxml import etree
from .xslt import *

# Define which symbols are to be exported:
__all__ = [
    'to_concept', 'to_reference', 'to_task',
    'to_concept_generated', 'to_reference_generated', 'to_task_generated',
    'to_single_topic', 'to_single_map'
]

# Expose the XSLT transformers:
to_concept             = etree.XSLT(etree.parse(concept))
to_reference           = etree.XSLT(etree.parse(reference))
to_task                = etree.XSLT(etree.parse(task))
to_concept_generated   = etree.XSLT(etree.parse(concept_generated))
to_reference_generated = etree.XSLT(etree.parse(reference_generated))
to_task_generated      = etree.XSLT(etree.parse(task_generated))
to_single_topic        = etree.XSLT(etree.parse(single_topic))
to_single_map          = etree.XSLT(etree.parse(single_map))
