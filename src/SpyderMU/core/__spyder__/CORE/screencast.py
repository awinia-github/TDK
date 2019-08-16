from SpyderMU.core.ABC.plugin import SpyderPluginABC

class screencast(SpyderPluginABC):
    service = 'CORE'
    service_type = 'ScreenCast'

    def __init__(self, spyder=None):
        super().__init__(spyder)
        
    def enable_action(self):
        pass

    def disable_action(self):
        pass

if __name__ == '__main__':
    pass