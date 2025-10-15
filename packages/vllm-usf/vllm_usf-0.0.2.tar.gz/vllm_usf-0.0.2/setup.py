from setuptools import setup, find_packages

setup(
    name="vllm-usf",
    packages=find_packages(include=["vllm", "vllm.*"]),
)
