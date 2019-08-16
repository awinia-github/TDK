from SpyderMU.core.ABC.plugin import SpyderPluginABC

class qdark(SpyderPluginABC):
    service = 'STYLE'
    service_type = 'qdark'

    def __init__(self, spyder=None):
        super().__init__(spyder)
        
    def enable_action(self):
        self.savedStyleSheet = self.spyder.setStyleSheet()
        import qdarkstyle
        dark_qss = qdarkstyle.load_stylesheet_from_environment()
        self.spyder.setStyleSheet(dark_qss)

    def disable_action(self):
        self.spyder.setStyleSheet(self.savedStyleSheet)

if __name__ == '__main__':
    pass