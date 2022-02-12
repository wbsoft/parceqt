parceqt
=======

Small Python library to use parce with Qt's QTextDocument.

This module depends on parce (https://parce.info/) and PyQt(https://riverbankcomputing.com/software/pyqt)

| Homepage: https://github.com/wbsoft/parceqt
| Download: https://pypi.org/project/parceqt
| Documentation: https://parce.info/parceqt

Example:

.. code:: python

    from PyQt5.QtWidgets import QApplication, QTextEdit
    from PyQt5.QtGui import QTextDocument

    app = QApplication([])
    doc = QTextDocument()
    e = QTextEdit()
    e.setDocument(doc)
    e.resize(600, 400)
    e.show()

    import parceqt
    from parce.lang.xml import Xml

    parceqt.set_root_lexicon(doc, Xml.root)
    parceqt.highlight(doc)
    parceqt.adjust_widget(e)    # adjust widgets font and base colors

Now the text in the document is automatically highlighted using the specified
root lexicon; the highlighting is updated as the user modifies the text.

