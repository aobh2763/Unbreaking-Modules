This part contains the four modules that will perform the necessary analysis to determine the accuracy of the input (whether its forged or not and whether its content is correct).

## metadata.py
Performs analysis on the given file's metadata after extracting it using `exiftool`.

### Settings
ignoreFields : The user can select which fields will be ignored during the analysis.
dateRange : The user can select the range of dates where both the creation and modification dates should be included.

## visualforensics.py
Performs analysis on the given file using various visual foresics techniques offered by `OpenCV` and computes the accuracy score based on those results.

### Settings
detectionThreshold (default 0.8) : The user can select the threshold under which impurities will be detected.
colorChannels (grayscale or RBG) : The user can select which color channels will be processed.
noiseFilter : The user can select whether or not noise gets filtered out of the image before processing.

## textextractor.py
Performs analysis on the content of the given file by extracting the text from it and fact-checking against other realiable sources to determine its accuracy.

### Settings
plagiarismCheck : The user can select if the analysis takes plagiarism into account.
regexChecks : The user can input regex expressions that will be used to check the content.
fontTolerance : The user can decide if the computer vision model will check the image's font for consistency.

## consistency.py
Performs analysis on the content of the given file by extracting the text from it as well as the metadata and making sure that they align.

### Settings
checkDates : The user can choose whether or not the model compares the dates of the metadata and the content for validity.
consistencyRules : The user can input axioms that the model will use when analysing the content and the metadata.