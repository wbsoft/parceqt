# livelex-qt
Small Python library to use livelex with Qt's QTextDocument

This module depends on livelex.

Homepage: https://github.com/wbsoft/livelex-qt


Example:

.. code:: python

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QTextDocument

    app = QApplication([])

    import livelexqt
    import livelex.lang.xml

    lexicon = livelex.lang.xml.Xml.root
    doc = QTextDocument()
    livelexqt.SyntaxHighlighter.instance(doc, lexicon)

    # Now the text in the document is automatically highlighted using the
    # specified root lexicon.

