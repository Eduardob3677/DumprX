"""
Testing module for DumprX integrations and functionality.
"""

from pathlib import Path
from typing import Dict, Any

from dumprxconfig import Config
from dumprxutils.console import print_info, print_error, print_success, print_step, print_substep
from dumprxmodules.validator import validate_url, validate_token, validate_chat_id


class TestRunner:
    """Test runner for DumprX functionality."""
    
    def __init__(self, config: Config):
        self.config = config
        self.test_results: Dict[str, bool] = {}
    
    def test_all(self):
        """Run all tests."""
        print_step("Running DumprX Tests")
        
        self.test_configuration()
        self.test_downloads()
        self.test_extraction()
        self.test_git_integration()
        self.test_telegram()
        
        self._print_test_summary()
    
    def test_configuration(self):
        """Test configuration loading and validation."""
        print_substep("Testing Configuration")
        
        try:
            # Test config loading
            config = Config.load()
            self.test_results['config_loading'] = True
            print_success("Configuration loading: OK")
            
            # Test directory creation
            config.ensure_directories()
            self.test_results['directory_creation'] = True
            print_success("Directory creation: OK")
            
        except Exception as e:
            self.test_results['config_loading'] = False
            print_error(f"Configuration test failed: {e}")
    
    def test_downloads(self):
        """Test download functionality."""
        print_substep("Testing Download Services")
        
        # Test URL validation
        test_urls = [
            "https://mega.nz/file/test#key",
            "https://www.mediafire.com/file/test",
            "https://drive.google.com/file/d/test/view",
            "https://www.androidfilehost.com/?fid=test"
        ]
        
        all_passed = True
        for url in test_urls:
            try:
                if validate_url(url):
                    print_info(f"URL validation OK: {url}")
                else:
                    print_error(f"URL validation failed: {url}")
                    all_passed = False
            except Exception as e:
                print_error(f"URL test error: {e}")
                all_passed = False
        
        self.test_results['download_validation'] = all_passed
        
        if all_passed:
            print_success("Download validation: OK")
        else:
            print_error("Download validation: FAILED")
    
    def test_extraction(self):
        """Test extraction functionality."""
        print_substep("Testing Extraction")
        
        # Test file format validation
        test_files = [
            "firmware.zip",
            "system.new.dat",
            "payload.bin",
            "UPDATE.APP",
            "firmware.kdz"
        ]
        
        all_passed = True
        for filename in test_files:
            try:
                from dumprxmodules.validator import validate_file_format
                if validate_file_format(filename):
                    print_info(f"Format validation OK: {filename}")
                else:
                    print_error(f"Format validation failed: {filename}")
                    all_passed = False
            except Exception as e:
                print_error(f"Format test error: {e}")
                all_passed = False
        
        self.test_results['extraction_validation'] = all_passed
        
        if all_passed:
            print_success("Extraction validation: OK")
        else:
            print_error("Extraction validation: FAILED")
    
    def test_git_integration(self):
        """Test git integration."""
        print_substep("Testing Git Integration")
        
        try:
            from dumprxutils.git import GitManager
            
            git_manager = GitManager(self.config)
            
            # Test git availability
            import shutil
            if shutil.which('git'):
                print_info("Git command available: OK")
                self.test_results['git_available'] = True
            else:
                print_error("Git command not available")
                self.test_results['git_available'] = False
                return
            
            # Test token validation
            github_token_valid = False
            if self.config.git.github_token:
                github_token_valid = validate_token(self.config.git.github_token, 'github')
                if github_token_valid:
                    print_info("GitHub token format: OK")
                else:
                    print_error("GitHub token format: INVALID")
            else:
                print_info("GitHub token: NOT CONFIGURED")
            
            gitlab_token_valid = False
            if self.config.git.gitlab_token:
                gitlab_token_valid = validate_token(self.config.git.gitlab_token, 'gitlab')
                if gitlab_token_valid:
                    print_info("GitLab token format: OK")
                else:
                    print_error("GitLab token format: INVALID")
            else:
                print_info("GitLab token: NOT CONFIGURED")
            
            self.test_results['git_tokens'] = github_token_valid or gitlab_token_valid
            
            if github_token_valid or gitlab_token_valid:
                print_success("Git integration: OK")
            else:
                print_error("Git integration: NO VALID TOKENS")
                
        except Exception as e:
            self.test_results['git_integration'] = False
            print_error(f"Git integration test failed: {e}")
    
    def test_telegram(self):
        """Test Telegram integration."""
        print_substep("Testing Telegram Integration")
        
        try:
            if not self.config.telegram.enabled:
                print_info("Telegram: NOT ENABLED")
                self.test_results['telegram'] = True
                return
            
            # Test token validation
            token_valid = False
            if self.config.telegram.token:
                token_valid = validate_token(self.config.telegram.token, 'telegram')
                if token_valid:
                    print_info("Telegram token format: OK")
                else:
                    print_error("Telegram token format: INVALID")
            else:
                print_error("Telegram token: NOT CONFIGURED")
            
            # Test chat ID validation
            chat_id_valid = False
            if self.config.telegram.chat_id:
                chat_id_valid = validate_chat_id(self.config.telegram.chat_id)
                if chat_id_valid:
                    print_info("Telegram chat ID format: OK")
                else:
                    print_error("Telegram chat ID format: INVALID")
            else:
                print_error("Telegram chat ID: NOT CONFIGURED")
            
            self.test_results['telegram'] = token_valid and chat_id_valid
            
            if token_valid and chat_id_valid:
                print_success("Telegram integration: OK")
            else:
                print_error("Telegram integration: CONFIGURATION INVALID")
                
        except Exception as e:
            self.test_results['telegram'] = False
            print_error(f"Telegram test failed: {e}")
    
    def _print_test_summary(self):
        """Print test results summary."""
        print_step("Test Results Summary")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "PASS" if result else "FAIL"
            status_color = "green" if result else "red"
            print_info(f"{test_name}: {status}")
        
        print_info(f"Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print_success("All tests passed!")
        else:
            print_error(f"{total_tests - passed_tests} tests failed")