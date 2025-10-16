from setuptools import setup, find_packages

setup(
    name="agentbill-langchain",
    version="1.0.0",
    description="LangChain integration for AgentBill",
    author="AgentBill",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
)