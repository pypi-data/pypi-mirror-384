import os
from pathlib import Path
import pytest

# Define the root directory of your project here
PROJECT_ROOT = Path(__file__).parent.parent

# Define the copyright text
COPYRIGHT_TEXT = """Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
EXCLUDED_DIRS = {'venv','build','dist'} 

def test_copyright_in_all_files():
    # List of file extensions to check (e.g., Python, HTML, JS, CSS files)
    extensions = ('.py', '.html', '.js', '.css')
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if filename.endswith(extensions) and filename != '__init__.py':
                file_path = Path(dirpath) / filename
                with open(file_path, 'r', encoding='utf-8') as file:
                    contents = file.read()
                    assert COPYRIGHT_TEXT in contents, f"Copyright not found in {file_path}"
