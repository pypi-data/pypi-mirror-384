from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="FuClientForExam",
    version="0.1.2",
    author="VoNiRoNi",
    author_email="alesha.vorobev2017@yandex.ru",
    description="Python client for exam",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aiclient",
    packages=find_packages(),
    install_requires=["requests>=2.25.1"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)