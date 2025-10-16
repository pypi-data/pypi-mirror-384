import setuptools
import subprocess
import os

package_version = (
    subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
    .stdout.decode("utf-8")
    .strip()
)
# print(package_version)

if "-" in package_version:
    # when not on tag, git describe outputs: "1.3.3-22-gdf81228"
    # pip has gotten strict with version numbers
    # so change it to: "1.3.3+22.git.gdf81228"
    # See: https://peps.python.org/pep-0440/#local-version-segments
    v,i,s = package_version.split("-")
    # package_version = v + "+" + i + ".git." + s
    package_version = v 

# v_strs = package_version.split(".")
# print(v_strs)
# package_version = ".".join(v_strs[:-1]) + '.' + str(int(v_strs[-1])+1)
assert "-" not in package_version
assert "." in package_version

assert os.path.isfile("quantum_simulation_recipe/version.py")
with open("quantum_simulation_recipe/VERSION", "w", encoding="utf-8") as fh:
    fh.write("%s\n" % package_version)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="quantum_simulation_recipe",
    # name="quantum-simulation-recipe",
    # version='0.1.6',
    version=package_version,
    # setuptools_git_versioning={
    #     "enabled": True,
    # },
    # setup_requires=["setuptools-git-versioning>=2.0,<3"],
    # author="Jue XU",
    author_email="xujue@connect.hku.hk",
    description="Recipe for quantum simulation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jue-Xu/quantum-simulation-recipe",
    packages=setuptools.find_packages(),
    # packages=setuptools.find_packages(include=["quantum_simulation_recipe"]),
    # package_data={"quantum_simulation_recipe": ["VERSION"]},
    # include_package_data=True,
    license="Apache-2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        # "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        # "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={"console_scripts": ["quantum-simulation-recipe = quantum_simulation_recipe.main:main"]},
    install_requires=[
        "qiskit >= 1.0.2",
        "openfermion >= 1.5.1",
        "openfermionpyscf >= 0.5",
        "matplotlib >= 3.8.2",
        "numpy >= 1.23.5",
        "pandas >= 2.2.2",
        "scipy == 1.12.0",
        "jax == 0.4.12",
        "jaxlib == 0.4.12",
        "colorspace==0.4.4",
        "multiprocess==0.70.16",
    ],
)