from setuptools import setup, find_packages

setup(
    name="mlog_util",
    version="0.1.4",
    packages=find_packages(),
    install_requires=["rich", "portalocker"],  # 依赖库
    # author="may",
    # author_email="no",
    description="自用日志库",
    # long_description=open("README.md", encoding="utf-8").read(),
    # long_description_content_type="text/markdown",

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
