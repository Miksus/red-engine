from setuptools import setup, find_packages
import versioneer

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="redengine",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Mikael Koli",
    author_email="koli.mikael@gmail.com",
    url="https://github.com/Miksus/red-engine.git",
    packages=find_packages(),
    description="Advanced scheduling framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",

        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Office/Business :: Scheduling",

        "Topic :: System",

        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
    ],
     include_package_data=True, # for MANIFEST.in
     python_requires='>=3.7.0',

    install_requires = [
        'pandas', 'redbird>=0.5.0', 'pydantic'
    ],
)
