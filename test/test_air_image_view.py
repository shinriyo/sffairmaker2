#encoding:shift-jis
from __future__ import division, print_function
__metaclass__ = type
import nose, nose.tools
from sffairmaker.air_image_view import *

def testAppendingClsn():
    import sffairmaker.model
    import sffairmaker.view
    from sffairmaker.clsn import Clsn
    from pprint import pprint
    
    app = QApplication([])
    
    xview  = sffairmaker.view._View()
    xview._xmodel = xmodel = sffairmaker.model._Model(xview=xview)
    
    class TestAirImageViewCore(AirImageViewCore2):
        _xview = xview
        _xmodel= xmodel
        
    AirImageView = createImageViewClass(TestAirImageViewCore)
    
    v = AirImageView()
    anim, = xmodel.air().anims()
    elm, = anim.elms()
    
    v.setElm(elm)
    
    clsn = Clsn([QRect(i*7, i*7, 7, 7) for i in range(10)])
    elm.change(clsn1=clsn)
    
    v.resize(300, 300)
    
    #appendingClsn
    log1 = []
    log2 = []
    v.appendingClsnChanged.connect(log1.append)
    v.drawingClsnChanged.connect(log2.append)
    for k, name in [(const.ClsnKeys._1, "clsn1"),
                    (const.ClsnKeys._2, "clsn2"),
                    (const.ClsnKeys._1d, "clsn1Default"),
                    (const.ClsnKeys._2d, "clsn2Default")]:
        v.setDrawingClsn(frozenset())
        v.setAppendingClsn(k)
        assert log1[-1] == k
        # assert log2[-1] == frozenset(const.ClsnKeys._values)
        # assert v.drawingClsn() == frozenset(const.ClsnKeys._values)
        assert log2[-1] == frozenset(const.ClsnKeys.get_all_values())
        assert v.drawingClsn() == frozenset(const.ClsnKeys.get_all_values())
        
        for scale in [1, 3, 9]:
            v._core.setScale(scale)
            center = v._core.axis()
            for delta in [QPoint(0, 0), QPoint(20, 10)]:
                v._core.mousePressEvent(QMouseEvent(
                    QEvent.MouseButtonPress,
                    center,
                    Qt.LeftButton,
                    Qt.LeftButton,
                    Qt.KeyboardModifiers(0),
                ))
                v._core.mouseReleaseEvent(QMouseEvent(
                    QEvent.MouseButtonRelease,
                    center + delta,
                    Qt.LeftButton,
                    Qt.NoButton,
                    Qt.KeyboardModifiers(0),
                ))
                v._core.repaint()
                
                rc = QRect(QPoint(0, 0), QPoint(delta.x()//scale, delta.y()//scale))
                
                c = v._core._clsns()[k]
                assert c.clsn[-1] == rc
                assert getattr(elm, name)() == c.clsn
                

def main():
    nose.runmodule()
if __name__ == '__main__':
    main()
