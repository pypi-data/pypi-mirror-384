import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_discription = f.read()

__version__ = "1.2.8"

REPO_NAME = "observe_traces"
AUTHOR_USER_NAME = "TapanKheni10"
PKG_NAME = "observeLLM"
AUTHOR_EMAIL = "tapankheni10304@gmail.com"

setuptools.setup(
    name=PKG_NAME,
    version=__version__,
    author=AUTHOR_USER_NAME,
    author_email=AUTHOR_EMAIL,
    description="A python package for observing traces of your LLM application.",
    long_description=long_discription,
    long_description_content_type="text/markdown",
    url=f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}",
    project_urls={
        "Bug Tracker": f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}/issues"
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
)
