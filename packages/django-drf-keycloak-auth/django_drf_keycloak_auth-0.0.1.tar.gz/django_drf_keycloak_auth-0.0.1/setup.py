from setuptools import find_packages, setup


def read_files(files):
    data = []
    for file in files:
        with open(file, encoding="utf-8") as f:
            data.append(f.read())
    return "\n".join(data)


long_description = read_files(["README.md", "CHANGELOG.md"])

meta = {}
with open("./django_drf_keycloak_auth/version.py", encoding="utf-8") as f:
    exec(f.read(), meta)

setup(
    name="django-drf-keycloak-auth",
    description="Django app for Keycloak OAuth2 authentication with DRF.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=meta["__version__"],
    author="xiaobitipao",
    author_email="xiaobitipao@gmail.com",
    url="https://github.com/xiaobitipao/django-drf-keycloak-auth",
    keywords=["keycloak", "django", "djangorestframework", "oauth2"],
    packages=find_packages(),
    package_dir={},
    install_requires=[
        "python-dotenv>=1.1.1",
        "Django>=5.2.7",
        "djangorestframework>=3.16.1",
        "python-keycloak>=5.8.1",
        "pydantic>=2.12.1",
        "pydantic-settings>=2.11.0",
    ],
    python_requires=">=3.11",
    license="MIT",
    classifiers=[
        # https://pypi.org/classifiers/
        "Framework :: Django",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
