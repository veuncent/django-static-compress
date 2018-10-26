from setuptools import find_packages, setup

setup(
    name="django-static-compress",
    version="1.2.1",
    url="https://github.com/veuncent/django-static-compress",
    author="Manatsawin Hanmongkolchai + Vincent Meijer",
    author_email="meijer.vincent@gmail.com",
    description="Precompress Django static files with Brotli and Zopfli. Python 2.7 port based on https://github.com/whs/django-static-compress",
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=["Django", "Brotli~=1.0.4", "zopfli~=0.1.4"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Pre-processors",
    ],
)
