from os import listdir
import pandas as pd
from string import punctuation
import nltk
from nltk.metrics import edit_distance
import re

nltk.download('words', quiet=True)

# Functions for data acquisition...
def getActsPaths(dir_OCR):
    """
    This function searches the given OCR directory path to find a path to a 
    text file containing the OCRed output for that year's Acts.
    The function accounts for the fact that there might be many variations in 
    the filename since the Acts and Joints could be seperate or mixed.
    
    Note:
        If the Acts and Joints are seperate for the give year, 
        the acts path will likely contain a filename in the format: 
        `{year}_Acts.txt`.
    
        However, if the Acts and Joints are mixed for the give year, 
        the acts path will might contain a filename as followes: 
        `{year}_both.txt` or `{year}_Acts_Joints.txt`.

    Parameters
    ----------
    dir_OCR : str
        The path for a year's OCR folder.

    Returns
    -------
    tuple of (str, bool)
        The path to the acts text file which is appended to `dir_OCR`.
        A flag identifying whether the Acts and Joints are seperate 
        for this year's volume. See note above.
    """

    # If the Acts and Joints were seperate for the year
    try:
        # Lists of strings that should and should not be in the file name
        mustContain = ['txt']
        eitherContain = ['act', 'acts']
        notContain = ['joint', 'joints', 'concurrent', 'concurrents', 
                      'bill', 'bills']

        for file in listdir(dir_OCR):
            file_lowered = file.lower()

            # Check if each of the mustContain strings are in the name
            # and any of the eitherContain strings are in the name
            # and each of the notContain strings are not in the name
            if all([x in file_lowered for x in mustContain]) and \
               any([x in file_lowered for x in eitherContain]) and \
               all([x not in file_lowered for x in notContain]):
                acts_path = dir_OCR + "/" + file
                break

        # If a path was found
        if 'acts_path' in locals():
            # The flag being True means that the Acts and Joints are seperate
            return (acts_path, True)
        else:
            raise Exception

    # However, if the Acts and Joints were not seperate for this year, 
    # then a FileNotFoundError will be returned for the above code.
    # So, catch that error and read in the combined file
    except:
        # Some years might contain 'both' as a keyword in the filename,
        # but some might contain 'acts_joints' insteads. 
        # So try both possibilities.

        # Try for 'both'
        try:
            # Lists of strings that should and should not be in the file name
            doContain = ['txt', 'both']
            notContain = ['joint', 'joints', 'concurrent', 
                          'concurrents', 'bill', 'bills']

            for file in listdir(dir_OCR):
                file_lowered = file.lower()

                # Check if each of the doContain strings are in the name and 
                # each of the notContain strings are not in the name
                if all([x in file_lowered for x in doContain]) and \
                   all([x not in file_lowered for x in notContain]):
                    acts_path = dir_OCR + "/" + file
                    break
            
            # If a path was found
            if 'acts_path' in locals():
                # True means that the Acts and Joints are seperate
                return (acts_path, True)
            else:
                raise Exception
                    
        # Try 'acts_joints'
        except:
        
            # Lists of strings that should and should not be in the file name
            mustContain = ['txt']
            eitherContain1 = ['act', 'acts']
            eitherContain2 = ['joints', 'joint']
            notContain = ['concurrent', 'concurrents', 'bill', 'bills']

            for file in listdir(dir_OCR):
                file_lowered = file.lower()

                # Check if each of the mustContain strings are in the name
                # and any of the eitherContain strings are in the name
                # and each of the notContain strings are not in the name
                if all([x in file_lowered for x in mustContain]) and \
                   any([x in file_lowered for x in eitherContain1]) and \
                   any([x in file_lowered for x in eitherContain2]) and \
                   all([x not in file_lowered for x in notContain]):
                    acts_path = dir_OCR + "/" + file
                    break

                    
        # After either of the above (nested) try-except statements, 
        # execute the following...
        if 'acts_path' in locals():
            # False means that the Acts and Joints are not seperate
            return (acts_path, False)
        else:
            return (None, False)

        
def removeSessionHeaders(df):
    """
    This function removes session headers (containing information about the
    session held) which appear at the start of each volume.
    To remove them, the code removes all sentences until the first valid 
    sentence appears, which usually starts with "An Acts ...".
    
    Parameters
    ----------
    df : pandas.Dataframe
        The dataframe to remove session headers from.

    Returns
    -------
    pandas.Dataframe
        The modified dataframe which session headers removed.
    """
    
    for i, sent in enumerate(df['sentence']):

        # If the sentence with "an" is found, exit the loop
        if 'an act' in sent.lower().strip():
               break

        # Else, disregard the sentence since it does not start with "an"
        df.drop(index=i, inplace=True)
    
    # Reset the index
    df.reset_index(drop=True, inplace=True)
    
    return df


def getImgs(dir_OCR, year):
    """
    This function searches the gives OCR directory path for the images 
    sub-folder. It then returns the path this sub-folder and the list of all 
    images contained in it.

    Parameters
    ----------
    dir_OCR : str
        The path for a year's OCR folder.

    Returns
    -------
    tuple of (list, str)
        The list of all images contained in the images sub-folder.
        Str path (an extension of `dir_OCR`) to the images sub-folder.
    """
    
    # Since many variation might exists, nested try-excepts are needed.
    try:
        dir_imgs = dir_OCR + "/images"
        imgs = listdir(dir_imgs)

    except FileNotFoundError:
        try:
            dir_imgs = dir_OCR + "/Images"
            imgs = listdir(dir_imgs)

        except FileNotFoundError:
            try:
                dir_imgs = dir_OCR + "/images.zip"
                imgs = listdir(dir_imgs)

            except FileNotFoundError:
                try:
                    dir_imgs = dir_OCR + "/Images.zip"
                    imgs = listdir(dir_imgs)

                except FileNotFoundError:
                    dir_imgs = dir_OCR + "/" + year
                    imgs = listdir(dir_imgs)
    
    # Only keep images which have a valid extensions
    imgs = [img for img in imgs if "jpg" in img or "tiff" in img or "JPG" in img or "TIFF" in img]
    imgs.sort()
    return imgs, dir_imgs


def getWordsFrame(acts_path, actsSep):
    """
    This function reads in the path to the acts file and returns a Pandas 
    Dataframe containing the each word in the corpus and its filename.
    
    Parameters
    ----------
    acts_path : str
        The path to the acts text file.
    actsSep : bool
        Flag for whether the the Acts and Joints are seperate for this volume.

    Returns
    -------
    pandas.Dataframe
        A dataframe containing words and their page numbers (filenames).
    """

    # Most likely, the tsv file with be similar to the 'acts_path'
    # but will have '_data' added before the file extension
    # Ex. if 'acts_path' = '1928_Acts.txt', 
    # then 'word_path' = '1928_Acts_data.tsv'
    try:
        words_path = acts_path.split('.')[0] + '_data.tsv'
        # print(words_path)
        df_words = pd.read_table(words_path)

    # If that file does not exist, then search
    except:

        if actsSep:
            # Lists of strings that should and should not be in the file name
            mustContain = ['tsv', 'data']
            eitherContain = ['act', 'acts']
            notContain = ['joint', 'joints', 'concurrent', 'concurrents', 
                          'bill', 'bills']
            
            for file in listdir(dir_OCR):
                file_lowered = file.lower()

                # Check if each of the mustContain strings are in the name
                # and any of the eitherContain strings are in the name
                # and each of the notContain strings are not in the name
                if all([x in file_lowered for x in mustContain]) and \
                   any([x in file_lowered for x in eitherContain]) and \
                   all([x not in file_lowered for x in notContain]):
                    words_path = dir_OCR + '/' + file                
            
        else:
            # Lists of strings that should and should not be in the file name
            mustContain = ['tsv', 'data', 'both']
            eitherContain = ['joint', 'joints']
            notContain = ['concurrent', 'concurrents', 'bill', 'bills']

            for file in listdir(dir_OCR):
                file_lowered = file.lower()

                # Check if each of the mustContain strings are in the name
                # and any of the eitherContain strings are in the name
                # and each of the notContain strings are not in the name
                if all([x in file_lowered for x in mustContain]) and \
                   any([x in file_lowered for x in eitherContain]) and \
                   all([x not in file_lowered for x in notContain]):
                    words_path = dir_OCR + '/' + file               

        df_words = pd.read_table(words_path)

        
    # Drop the columns which are unessecary for our analysis
    df_words.drop(columns=["left", "top", "width", "height", "conf"], inplace=True)

    # Drop the rows which don't contain a word in the "text" column
    df_words.dropna(inplace=True)
    # Reset index
    df_words.reset_index(drop=True)

    # Relabel the "name" column to "page" column
    df_words.rename(columns={"name": "page"}, inplace=True)

    return df_words


def getStartEndPages(df, df_words):
    """
    This function reads in given dataframes and fills in the start and end 
    pages for each sentence.
    The data in the two dataframes must match.
    
    Parameters
    ----------
    df : pandas.Dataframe
        The original dataframe which will have start and end pages assigned for 
        each row.
    df_words : pandas.Dataframe
        A dataframe containing words and their page numbers (filenames).

    Returns
    -------
    pandas.Dataframe
        A dataframe with labelled start and end pages.
    """

    # Tracker for df_words:
    words_trkr = 0

    # Loop over the original dataframe
    for i in range(0, df.shape[0]):

        # For each sentence, extract the first and last word
        tmp_sentence = df.iloc[i]['sentence'].split(" ")
        start, last = tmp_sentence[0], tmp_sentence[-1]

        # Get the page number for the start and end word
        try:
            start_page = df_words.iloc[words_trkr]['page']
        except IndexError:
            try:
                words_trkr -= len(tmp_sentence)
                start_page = df_words.iloc[words_trkr]['page']
            except:
                start_page = df_words['page'].iloc[-1]

        try:
            end_page = df_words.iloc[words_trkr + len(tmp_sentence)]['page']
        except IndexError:
            try:
                end_page = df_words.iloc[words_trkr]['page']
            except:
                end_page = df_words['page'].iloc[-1]


        # Remove the filename from the pages:
        start_page = start_page.split(".")[0]
        end_page = end_page.split(".")[0]


        # Assign the page number to their respective columns in the dataframe
        df.at[i, 'start_page'] = start_page
        df.at[i, 'end_page'] = end_page

        # Update tracker
        words_trkr += len(tmp_sentence)
    
    return df


def getImgsPath(df, fileType, dir_imgs):
    """
    This function adds an online image path to each sentence based on its 
    start page.
    
    Parameters
    ----------
    df : pandas.Dataframe
        The dataframe containing start pages for which links will be assigned.
    fileType: str
        The file extension type of the sentences in `df`.
    dir_imgs: str
        Path to the images sub-folder.

    Returns
    -------
    pandas.Dataframe
        A dataframe with online links for each sentence.
    """
    
    pre_path = 'https://emailsc.sharepoint.com/:i:/r/sites/' + \
        'COTEAM-ULIB-OntheBooks/Shared%20Documents/General/' + \
        "/".join(dir_imgs.split("/")[-3:]) + '/'
    
    df['path'] = pre_path + df['start_page'].astype(str) + '.' + fileType
    return df


# Functions for word corrections...
def correct_words_batch(sentences, target_words, threshold):
    """
    Correct some incorrect words in `sentences`. 
    Words which are in `target_words` are checked in `sentences`
    and corrected.
    The correction is based on a Levenshtein distance. A lower limit 
    of 0 and an upper limit of `threshold` is used.

    Parameters
    ----------
    sentences : Pandas.Series
        A series that will be checked and corrected.
    target_words: list
        List of Str words to correct.
    threshold: float
        An upper threshold to check and compare the word 
        in `target_words` with the words in `chunk`.

    Returns
    -------
    tuple of (list, list, list)
        Lists of corrected sentences, 
        flags for each sentence indicating whether a correction was made, 
        and lists of original (incorrect) words for those corrected sentences.
    """

    punct = set(punctuation)
    
    corrected_sentences = []
    flags = []
    org_words = []

    for text in sentences:
        words = text.split()
        # words = word_tokenize(text)
        
        corrected_words = []
        flag = False
        org_word = ''

        for word in words:
            if any(p in word for p in punct):
                corrected_words.append(word)
                continue
            
            corrected_word = word

            for target_word in target_words:
                
                # Calculate Levenshtein distance and correct if close to 'section'
                if 0 <  edit_distance(word.lower(), target_word.lower()) <= threshold:
                    corrected_word = target_word
                    flag = True
                    org_word = word.lower()
                    break

            corrected_words.append(corrected_word)

        corrected_sentences.append(' '.join(corrected_words))
        flags.append(flag)
        org_words.append(org_word)

    return corrected_sentences, flags, org_words


def correct_chunk(chunk, target_words, threshold):
    """
    Search and correct words in `chunk` DataFrame's 'sentence' column
    using Levenshtein distance.

    Parameters
    ----------
    chunk : Pandas.DataFrame
        DataFrame that needs to be processed. Must have a 'sentence' column.
    target_words: list
        List of Str words to correct.
    threshold: float
        An upper threshold to check and compare the word 
        in `target_words` with the words in `chunk`.

    Returns
    -------
    Pandas DataFrame
        A modified version of `chunk` which includes a corrected sentence, flag,
        and an original words column.
    """
    
    corrected_sentences_batch, flags_batch, org_words_batch = correct_words_batch(chunk['sentence'], target_words, threshold)
    corrected_df = pd.DataFrame({'corrected_sentence': corrected_sentences_batch, 'flag': flags_batch, 'org_words': org_words_batch})

    return pd.concat([chunk.reset_index(drop=True), corrected_df], axis=1)


# Functions for adding Section and Act labels...
def fixCol(colValue, map_dict):
    """
    Fix the given value, if required, by replacing each letter with the
    given replacements from the map_dict.

    Parameters
    ----------
    colValue : str
        The value to check and replace.
    map_dict : dict
        The dictionary containing mappings for incorrect letters.

    Returns
    -------
    str
        The fixed value.
    """

    if pd.isnull(colValue):
        return colValue
    
    ret = ''
    
    # Since a number might be more than one character, such as '15',
    # iterate over each character
    for char in str(colValue):
        if char in map_dict:
            ret += str(map_dict[char])
        else:
            ret += char
        
    return ret


# Functions for adding features...
def addPrefix(fileName: str, nameLen: int) -> str:
    """
    Since the fileNames from the excel parsing could be any of any length
    (ranging from 1-3), this function appends a string of 0's to the 
    start of the input so that it is the specified nameLen lengths long.
    
    Parameters
    ----------
    fileName : str
        The file name that needs to be prefixed
        The fileName shouldn't have a prefix, such as '.tiff'
    nameLen : int
        The length of the expected name of the file
        Ex. '00034.jpg' would have length of 5
        so nameLen should be 5

    Returns
    -------
    str
        A length nameLen file name (prefixed with 0's)
    """
    
    # prefix_length = nameLen - len(fileName)
    prefix = "0" * (nameLen - len(fileName))
    
    return prefix + fileName


def addJoints(sentence):
    """
    Change `law_type` column to accomodate Joint Resolutions.
    
    Parameters
    ----------
    sentence : str
        The sentence that should be checked to determine if the 
        sentence is initializing a Joint Resolution.

    Returns
    -------
    str
        Either "Joint Resolution" or "Act" based on `sentence`.
    """
    return 'Joint Resolution' if 'joint' in sentence.lower().split()[:3] and 'resolution' in sentence.lower().split()[:4] else 'Act'


def process_row(row, pattern, cols):
    """
    Find matches in the 'sentence' column of the given row.
    If 2 or more matches found, then a list of 2 rows 
    split on the 2nd match are returned. Otherwise, the 
    original row is returned in a list.
    
    Parameters
    ----------
    row : Pandas DataFrame row
        The row of a the Pandas dataframe which should atleast 
        contain the 'sentence' column.
    pattern: re.compile
        A Regex pattern.
    cols: list
        A list of the DataFrame's columns.

    Returns
    -------
    list
        A list of either the original row or 
        two rows split on the 2nd match of `pattern`.
    """

    # Find all matches in the text
    matches = re.finditer(pattern, row['sentence'], re.IGNORECASE)

    # Initialize variables to keep track of the start and end indices of the 2nd match
    start_idx = None
    end_idx = None
    
    # Iterate through the matches and store the start and end indices of the second match
    for i, match in enumerate(matches):
        if i == 1:
            start_idx, end_idx = match.span()
        elif i > 1:
            # If there's a third match, break to stop further processing
            break

    if start_idx is not None and end_idx is not None:
        split_result = [row['sentence'][:start_idx], row['sentence'][end_idx:]]
    else:
        split_result = [row['sentence']]

    # Create new rows dynamically with all columns
    new_rows = []
    for i in range(len(split_result)):
        new_row = {}
        for col in cols:
            new_row[col] = row[col]
        new_row['sentence'] = split_result[i]
        new_rows.append(new_row)

    return new_rows
