# Phase 2: Marginalia Removal and OCR
*Marginalia* is the text that was written in the borders of the pages to highlight or summarize the paragraph content. It was printed in the corpus volumes prior to 1951. The marginalia are not part of the *Acts* and not needed for the OCR process, as did paratextual information from page headers and footers. So, the marginalia had to be removed before OCRing the corpus. The marginalia removal process involved two steps:
- Determine the coordinates of the main text body (bounding box)
- Identify the median page color to allow for the creation of a blank, color-neutral border around the main body text on each page

The volumes from 1934 to 1968 did not have any marginalia. So, we used the [test_functs_SimpleWay_NoMarginalia.ipynb](test_functs_SimpleWay_NoMarginalia.ipynb)to find the bounding box coordinates. 
The [crop_functions_updated_.ipynb](crop_functions_updated_.py) and [test_functs.ipynb](test_functs.ipynb) files were originally from UNC, however they were limited in that it didn’t crop the entire volume. So, they were modified to read all files, either .tiff or .jpg, from the given directory for one volume. All the files in that volume are read in one go. 

Furthermore, the original versions stopped whenever they encountered a file which threw any kind of error that might have stopped the code from running, such as a failure to crop the file. So, the code was also modified to ignore those errors and keep running. The files which throw errors are stored in a separate csv file, called `errors_year.csv` where year is the year from the volume, in the same directory.

The crop coordinates for other files, which are cropped by the code, are stored in another csv file, `year.csv`, in the same directory.
We used "Tesseract 
One important reminder is that some pages are not cropped properly but also don't throw errors. Those pages are not stored in the `errors_year.csv` file, but in the `year.csv` file. The only way to detect them was to manually go through the cell output, which contains a side-by-side view of the original images and their cropped versions, produced by running `test_functs.ipynb` and keeping track of which files are incorrectly cropped.

Lastly, the user should run `test_functs.ipynb` because that notebook calls and utilizes `crop_functions_updated_.py`. However, if the majority of images are not being cropped properly, then it is advised to play with the values of dil_iter, x_buffer, and y_buffer in `crop_functions_updated_.py`.
