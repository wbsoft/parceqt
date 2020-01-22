parceqt
=======

Small Python library to use parce with Qt's QTextDocument

This module depends on parce.

Homepage: https://github.com/wbsoft/parce-qt
Download: https://pypi.org/project/parce-qt

Example:

.. code:: python

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QTextDocument

    app = QApplication([])

    import parceqt
    import parce.lang.xml

    lexicon = parce.lang.xml.Xml.root
    doc = QTextDocument()
    parceqt.SyntaxHighlighter.instance(doc, lexicon)

    # Now the text in the document is automatically highlighted using the
    # specified root lexicon.

