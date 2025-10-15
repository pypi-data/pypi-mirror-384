from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-cosmos-toolkit",  
    version="0.1.1",
    author="Vamsi Gudapati",
    author_email="vamsi7673916775@gmail.com",
    description="Reusable toolkit integrating Azure OpenAI and Cosmos DB for semantic search",
    long_description=long_description,             
    long_description_content_type="text/markdown", 
    url="https://github.com/vamsichowdaryg/AI_Cosmos_Toolkit",
    packages=find_packages(),
    install_requires=[
        "openai>=1.3.0",
        "azure-cosmos>=4.5.0"
    ],
    python_requires=">=3.8",
    classifiers=[                                   
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers"
    ],
    license="MIT",                                  
    include_package_data=True,                      
)
