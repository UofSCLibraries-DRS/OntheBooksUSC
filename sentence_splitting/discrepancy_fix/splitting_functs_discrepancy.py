from os import listdir
import pandas as pd
from string import punctuation
import nltk
from nltk.metrics import edit_distance
import re

# Functions for word corrections...
def correct_chunk(chunk, target_words, threshold, colName):
    """
    Search and correct words in `chunk` DataFrame's `colName` column
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
    colName: str
        The column name that will searched in.

    Returns
    -------
    Pandas DataFrame
        A modified version of `chunk` which includes a corrected sentence, flag,
        and an original words column.
    """
    
    corrected_sentences_batch, flags_batch, org_words_batch = correct_words_batch(chunk[colName], target_words, threshold)
    corrected_df = pd.DataFrame({'corrected_column': corrected_sentences_batch, 'flag': flags_batch, 'org_words': org_words_batch})

    return pd.concat([chunk.reset_index(drop=True), corrected_df], axis=1)


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


# Functions for adding Section and Act labels...
def process_row(row, pattern, cols, colName):
    """
    Find matches in the 'colName' column of the given row.
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
    colName: str
        Name of the column which will be searched.

    Returns
    -------
    list
        A list of either the original row or 
        two rows split on the 2nd match of `pattern`.
    """

    # Find all matches in the text
    matches = re.finditer(pattern, row[colName], re.IGNORECASE)

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
        split_result = [row[colName][:start_idx], row[colName][end_idx:]]
    else:
        split_result = [row[colName]]

    # Create new rows dynamically with all columns
    new_rows = []
    for i in range(len(split_result)):
        new_row = {}
        for col in cols:
            new_row[col] = row[col]
        new_row[colName] = split_result[i]
        new_rows.append(new_row)

    return new_rows
