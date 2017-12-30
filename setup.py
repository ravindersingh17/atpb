from setuptools import setup

setup(
        name="tpb",
        version="1.1",
        description="Pirate bay search",
        author="ne0n",
        author_email="",
        install_requires=["requests", "bs4", "aiohttp"],
        packages=["modtpb"],
        scripts=["bin/tpb", "bin/atpbd"],
        python_requires=">=3",
        )

