# TexTOM

Welcome to TexTOM, a package for analyzing data from texture tomography, a synchrotron radiation technique currently developed at Institut Fresnel in cooperation with the ESRF.

For information about the technique as well as the mathematical model and for citing, please refer to:
Frewein, M. P. K., Mason, J., Maier, B., Colfen, H., Medjahed, A., Burghammer, M., Allain, M. & Grunewald, T. A. (2024). IUCrJ, 11, 809-820. https://doi.org/10.1107/S2052252524006547

Upon installing, the following commands will be available in your environment:

textom - full program in ipython mode

textom_documentation - open documentation in pdf reader

textom_config - open config file in text editor

Version history:

0.6.0 - Modular arrangement of the model, diffractlet computation new and noiseless, grid based function in test phase. Limited compatibility with 0.5! 

0.5.x - improved optimizer, some fixes and new functions

0.4.11 - flip_fov moved to geometry.py - update your files before running data-import or alignment!

0.4.10 - Important fixes: 
    1) use export_paraview() to create a file for paraview, as the geometry import labels the axis differently (so, axes are switched in the old versions).
    2) the optimization of ghost HSHs was disabled. To import old optimization files, use load_opt(...,exclude_ghosts=False)

0.3.0 - version used at the TexTOM workshop 2025

0.2.x - versions tested on Ubuntu and OpenSUSE with data from ID13 (ESRF), some functions unstable

0.1.x - unstable versions