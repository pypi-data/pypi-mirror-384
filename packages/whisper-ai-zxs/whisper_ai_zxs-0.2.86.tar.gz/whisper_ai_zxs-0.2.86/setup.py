from setuptools import setup, find_packages

setup(
    name="whisper_ai_zxs",  # 你的包名
    version="0.2.86",  # 版本号
    author="植想说",
    author_email="lizhenhua@zxslife.com",
    description="植想说的AI客服工具",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/my_package",  # 你的 GitHub 地址
    packages=find_packages(),  # 自动发现包
    install_requires=[
        "openai",
        "pymysql",
        "requests",
        "typing_extensions",
        "openpyxl",
        "cryptography",
        #"pandas>=2.0.0",  # 明确指定版本范围
        #"numpy>=1.23.0,<2.0.0",  # 取消注释并指定兼容版本
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]#,
    #python_requires=">=3.8",  # 提高到 3.8+ 以支持新版 pandas
)
