#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.csv_save_format import *

def test():
    app = QApplication([])
    from sffairmaker import model
    sff = model._Model().sff()
    
    sff.create()
    for group, index in product(xrange(5), xrange(5)):
        sff.newSpr(group=group, index=index)
    
    d = CsvSaveFormatDialog()
    d.setSprs(sff.sprs())
    
    d.setCsvPath("spam.csv")
    d.setName("{name}_{group}_{index}")
    d.setExt("png")
    
    assert d._preview.isValid()
    assert d._buttons.okButton().isEnabled()
    
    d.setName("{name}_{group}")
    assert not d._preview.isValid()
    assert not d._buttons.okButton().isEnabled()
    
    d.setName("{name}_{group}-{index}")
    assert d._preview.isValid()
    assert d._buttons.okButton().isEnabled()
    
    d.setName("{name}_{some-invalid-kw}")
    assert not d._preview.isValid()
    assert not d._buttons.okButton().isEnabled()
    
    d.setName("{: broken-format")
    assert not d._preview.isValid()
    assert not d._buttons.okButton().isEnabled()

    
def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
