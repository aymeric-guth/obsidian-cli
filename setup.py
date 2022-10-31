from setuptools import setup, find_packages


setup(
    name="obsidian_cli",
    version="0.0.1",
    license="GPLv2+",
    url="https://git.ars-virtualis.org/yul/obsidian-cli",
    description="cli util for interracting with obdsidian runtime, and vault",
    author_email="aymeric.guth@protonmail.com",
    author="Aymeric Guth",
    packages=find_packages(),
    package_data={"obsidian_cli": ["py.typed"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v2 or later(GPLv2+)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={"console_scripts": ["obs=obsidian_cli.obsidian_cli:main"]},
)
