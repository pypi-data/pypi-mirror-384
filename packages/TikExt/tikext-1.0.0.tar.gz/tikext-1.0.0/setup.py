from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="TikExt",
    version="1.0.0",
    author="Mustafa",
    author_email="tofey.amrie@gmail.com",
    description="مكتبة شاملة للتفاعل مع TikTok API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "faker",
        "requests",
        "user_agent",
        "SignerPy"
        
    ],
    keywords="tiktok api social media automation",
    project_urls={
        "Source": "https://github.com/yourusername/TikExt",
        "Bug Reports": "https://github.com/yourusername/TikExt/issues",
    },
)