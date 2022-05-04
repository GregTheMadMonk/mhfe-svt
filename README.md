## This is a tool for another project
This is a tool to simplify the process of viewing VTK files obtained in computations in an in-developement [NOA](https://github.com/grinisrit/noa) CFD application ([link one](https://github.com/grinisrit/noa/tree/master/docs/cfd), [link two](https://github.com/grinisrit/noa/tree/dev/test/cfd)).

## Known issues
* GIF export camera position could not be set
* FPS couldn't actually be set higher than some value
* `sorted(os.listdir())` gives wrong file order for files starting with the same number (e.g. in a directory containing **1.vtk**, **2.vtk** and **10.vtk** the latter will be placed before **2.vtk** in a sorted list, which is an issue!

## Wishlist
* Open mulitpile directories at once
