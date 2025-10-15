from setuptools import setup, find_packages

setup(
    name="token_service_toolkit",
    version="0.1.5",
    author="Vamsi Gudapati",
    author_email="vamsi7673916775@gmail.com",
    description="A lightweight Azure AD Token Service with no .env or logger dependencies",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vamsichowdaryg/token-service.git",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    python_requires=">=3.8",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
)
