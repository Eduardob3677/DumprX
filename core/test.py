from pathlib import Path


class TestRunner:
    def run_all(self) -> dict:
        results = {
            'success': True,
            'failures': []
        }
        
        tests = [
            self._test_config,
            self._test_extractors,
            self._test_downloaders
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                results['success'] = False
                results['failures'].append(str(e))
        
        return results
    
    def _test_config(self):
        from core.config import Config
        config = Config()
        assert config is not None
    
    def _test_extractors(self):
        from extractors.manager import ExtractorManager
        manager = ExtractorManager(Path("out"), Path("utils"))
        assert manager is not None
    
    def _test_downloaders(self):
        from downloaders.manager import DownloadManager
        manager = DownloadManager("input")
        assert manager is not None