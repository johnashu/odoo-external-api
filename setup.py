from setuptools import setup, find_packages

setup(
    name="Odoo Base API",
    author='John Ashurst',
    version="2019.1.3",
    description="Odoo XML RPC API Base Class",
    packages=find_packages(),
)

# Project uses reStructuredText, so ensure that the docutils get
# installed or upgraded on the target machine
install_requires = (["docutils>=0.3"],)

package_data = (
    {
        # If any package contains *.txt or *.rst files, include them:
        "": ["*.txt", "*.rst"],
        # And include any *.msg files found in the 'hello' package, too:
        "hello": ["*.msg"],
    },
)
