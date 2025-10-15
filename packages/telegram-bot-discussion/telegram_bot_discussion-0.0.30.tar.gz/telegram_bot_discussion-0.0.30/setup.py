from os import path
from setuptools import setup, find_packages, find_namespace_packages

# ln -s ../open_source/telegram_bot_discussion source


def readme():
    with open("README.md", "r") as f:
        return f.read()


if __name__ == "__main__":
    setup(
        name="telegram-bot-discussion",
        version="0.0.30",
        author="ILYA",
        description="Telegram-bot framework `telegram-bot-discussion` based on native Telegram Bot API Python-library `python-telegram-bot`.",
        long_description=readme(),
        long_description_content_type="text/markdown",
        # package_dir={"": "sources"},
        # packages=find_packages(where="sources"),
        packages=find_packages(),
        install_requires=["python-telegram-bot>=22.0"],
        classifiers=[
            "Programming Language :: Python :: 3.9",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Build Tools",
            "Operating System :: OS Independent",
        ],
        keywords="Python Telegram-bot Framework",
        # project_urls={"Documentation": "link"},
        python_requires=">=3.9",
    )
