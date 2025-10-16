import os
import platform
from pathlib import Path

__all__ = ['clear_screen', 'get_project_root']


def clear_screen():
    """운영체제에 맞춰 화면을 지우는 함수"""
    # Windows 운영체제인 경우
    if platform.system() == 'Windows':
        os.system('cls')
    # Windows가 아닌 경우 (macOS, Linux 등)
    else:
        os.system('clear')


def get_project_root(root: str = '.idea'):
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / root).exists():
            return parent
    return None
