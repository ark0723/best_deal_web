import os
import pytest
from pathlib import Path


class TestProjectStructure:
    """프로젝트 폴더 구조가 올바르게 생성되었는지 테스트"""
    
    def test_backend_directory_exists(self):
        """backend 디렉토리가 존재하는지 확인"""
        assert os.path.exists("backend"), "backend 디렉토리가 존재해야 합니다"
    
    def test_frontend_directory_exists(self):
        """frontend 디렉토리가 존재하는지 확인"""
        assert os.path.exists("frontend"), "frontend 디렉토리가 존재해야 합니다"
    
    def test_agent_directory_exists(self):
        """agent 디렉토리가 존재하는지 확인"""
        assert os.path.exists("agent"), "agent 디렉토리가 존재해야 합니다"
    
    def test_tests_directory_exists(self):
        """tests 디렉토리가 존재하는지 확인"""
        assert os.path.exists("tests"), "tests 디렉토리가 존재해야 합니다"
    
    def test_requirements_file_exists(self):
        """requirements.txt 파일이 존재하는지 확인"""
        assert os.path.exists("requirements.txt"), "requirements.txt 파일이 존재해야 합니다"
    
    def test_env_example_exists(self):
        """.env.example 파일이 존재하는지 확인"""
        assert os.path.exists(".env.example"), ".env.example 파일이 존재해야 합니다"
    
    def test_config_file_exists(self):
        """config.py 파일이 존재하는지 확인"""
        assert os.path.exists("config.py"), "config.py 파일이 존재해야 합니다"
    
    def test_backend_init_files(self):
        """backend 디렉토리의 __init__.py 파일들이 존재하는지 확인"""
        backend_files = [
            "backend/__init__.py",
            "backend/main.py",
            "backend/models.py",
            "backend/routes.py"
        ]
        for file_path in backend_files:
            assert os.path.exists(file_path), f"{file_path} 파일이 존재해야 합니다"
    
    def test_agent_init_files(self):
        """agent 디렉토리의 필수 파일들이 존재하는지 확인"""
        agent_files = [
            "agent/__init__.py",
            "agent/agent.py",
            "agent/tools.py",
            "agent/memory.py"
        ]
        for file_path in agent_files:
            assert os.path.exists(file_path), f"{file_path} 파일이 존재해야 합니다"
    
    def test_frontend_files(self):
        """frontend 디렉토리의 필수 파일들이 존재하는지 확인"""
        frontend_files = [
            "frontend/app.py",
            "frontend/components.py"
        ]
        for file_path in frontend_files:
            assert os.path.exists(file_path), f"{file_path} 파일이 존재해야 합니다" 