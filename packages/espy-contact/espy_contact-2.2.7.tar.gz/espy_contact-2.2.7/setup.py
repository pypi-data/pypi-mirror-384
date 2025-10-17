"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from setuptools import setup, find_packages

VERSION = "0.0.4"
DESCRIPTION = "ESSL users management"
LONG_DESCRIPTION = "Internal helper package for ESSL users management"
setup(
    name="espy_contact",
    version="2.2.7",
    packages=find_packages(),
    install_requires=[
        "bcrypt>=4.2.1",
        "pytest>=8.1.1",
        "pydantic>=2.10.6",
        "sqlalchemy>=2.0.37",
        "PyYAML>=6.0.1",
    ],
    author="Femi Adigun",
    author_email="femi.adigun@myeverlasting.net",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    keywords=["fastapi", "ESSL", "ReachAI", "Horace"],
    license="MIT",
    homepage="https://github.com/babaphemy/py-escontact",
)
