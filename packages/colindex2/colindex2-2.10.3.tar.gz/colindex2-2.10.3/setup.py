import setuptools
from pathlib import Path

#this_directory = Path(__file__).parent
#long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setuptools.setup(
    name="colindex2",
    version="v2.10.3",
    author="Satoru Kasuga",
    author_email="kasugab3621@outlook.com",
    description="depression detection/tracking schemes",
    long_description="For full descripiton and usage, please visit: [https://gitlab.com/kasugab3621/colindex2.git](https://gitlab.com/kasugab3621/colindex2.git)",
    long_description_content_type="text/markdown",
    url="https://gitlab.com/kasugab3621/colindex2.git",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'pandas', 'xarray', 'scipy', 'torch', 'netCDF4', 'h5netcdf', 'matplotlib', 'cartopy'],
    license_files=["LICENSE"],
    entry_points={
        'console_scripts': [
            'gen_data_settings=colindex2.commands:gen_data_settings',
            'detect=colindex2.commands:detect',
            'track=colindex2.commands:track',
            'find_track=colindex2.commands:find_track',
            'draw_map=colindex2.draw_map:draw_map',
            ]}
)
