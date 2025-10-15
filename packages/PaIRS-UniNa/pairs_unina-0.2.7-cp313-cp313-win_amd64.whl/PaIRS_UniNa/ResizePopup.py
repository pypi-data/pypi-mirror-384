from .addwidgets_ps import*
from .ui_ResizePopup import*
from .TabTools import*

class ResizePopup(QWidget): 
    FlagTransparentBack=0  #tra 0 e 1

    def __init__(self,callbacks=[]):
        super().__init__()
        ui=Ui_ResizePopup()
        ui.setupUi(self)
        self.ui=ui
        setupWid(self)

        self.setFixedSize(self.width(),self.height())
        self.setWindowFlags(Qt.Window|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint| Qt.Popup)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)

        def createCallb(k,flag):
            if flag:
                def Callb():
                    callbacks[k]()
                    self.hide()
            else:
                def Callb():
                    self.hide()
            return Callb
        for k in range(6):
            b:QToolButton=getattr(self.ui,f'b{k}')
            flag=k<=len(callbacks)-1
            b.clicked.connect(createCallb(k,flag))
            
        self.ui.button_close_tab.clicked.connect(self.hide)
        self.setWidgetColor()
        
    def setWidgetColor(self):
        widget=self.ui.w_b_size
        color = widget.palette().color(QtGui.QPalette.Window)
        alpha=255-self.FlagTransparentBack*255
        col=f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"
        backc="background:"+col
        ss=f"QWidget#{widget.objectName()}"+"{border: 1px solid gray;border-radius: 15px;"+backc+"}"
        widget.setStyleSheet(ss)

if __name__ == "__main__":
    import sys
    app=QApplication.instance()
    if not app: app = QApplication(sys.argv)
    app.setStyle('Fusion')
    object = ResizePopup()
    object.exec()
    #app.exec()
    app.quit()
    app=None
