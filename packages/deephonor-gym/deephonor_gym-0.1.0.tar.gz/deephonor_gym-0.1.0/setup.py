import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="deephonor_gym",
    version="0.1.0",
    author="DingGuohua",
    author_email="m17797618108@163.com",
    description="deephonor-gym physics simulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    package_data={"deephonor_gym":["dist/*","dist/**/*","core/*","example/*","example/**/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
)