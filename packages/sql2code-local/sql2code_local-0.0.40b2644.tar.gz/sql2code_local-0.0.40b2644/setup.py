import setuptools  
PACKAGE_NAME = "sql2code-local"  # TODO sql2code-local?
package_dir = PACKAGE_NAME.replace("-", "_")

setuptools.setup(
    name=PACKAGE_NAME,  # https://pypi.org/project/sql-to-code-local
    version='0.0.40b2644',  # update each time
    author="Circles",
    author_email="info@circlez.ai",
    description="PyPI Package for Circles sql-to-code-local Local Python",
    long_description="PyPI Package for Circles sql-to-code-local Local Python",
    long_description_content_type='text/markdown',
    url="https://github.com/circles-zone/sql2code-local-python-package",

    # old
    # packages=[package_dir],
    # package_dir={package_dir: f'{package_dir}/src'},
    # package_data={package_dir: ['*.py']},

    # new
    packages=setuptools.find_packages(),

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "logger-local>=0.0.71",  # https://pypi.org/project/logger-local/
        # TODO >= 0.1.1
        "database-mysql-local>=0.1.50",  # https://pypi.org/project/database-infrastructure-local/
        "python-sdk-local>=0.0.147",  # https://pypi.org/project/python-sdk-local/
        "python-sdk-remote==0.0.145",  # https://pypi.org/project/python-sdk-remote/ TODO Should change it to >=0.0.148
    ]
)
