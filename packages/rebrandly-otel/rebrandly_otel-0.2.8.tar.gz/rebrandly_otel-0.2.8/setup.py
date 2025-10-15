import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rebrandly_otel",
    version="0.2.8",
    author="Antonio Romano",
    author_email="antonio@rebrandly.com",
    description="Python OTEL wrapper by Rebrandly",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rebrandly/rebrandly-otel-python",
    packages=["rebrandly_otel"],
    package_dir={"rebrandly_otel": "src"},
    install_requires=[
        "opentelemetry-api>=1.34.0",
        "opentelemetry-sdk>=1.34.0",
        "opentelemetry-exporter-otlp>=1.34.0",
        "psutil>=5.0.0",
        "fastapi>=0.118.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
