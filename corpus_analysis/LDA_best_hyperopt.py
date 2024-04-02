import re
import os
import pandas as pd
import pickle

from gensim import corpora, models
from gensim.models import CoherenceModel
from gensim.models.phrases import Phrases, Phraser
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from pprint import pprint
from typing import List, Set, Dict
from functools import partial

# Since importing hyperopt might generate deprecation warnings
# Filter those warnings here.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from hyperopt import fmin, tpe, hp


## Data Acquisition and Pre-Processing
# Get the data file and read all the sentences.
# To avoid pre-processing the sentences repeatedly when rerunning the notebook, save them on disk.
def load_sentences() -> pd.Series:
    """
    Load the split sentences and return a Pandas Series for those sentences.

    @return: A Pandas Series object that contains the just the sentences 
        (along with a default index).
    """
    
    # Path to the final split csv
    f_path: str = "/work/otb-lab/Split_Cleanup_Updated/updated_results/final_splits_Nov3.csv"

    # Use only the id (containing the years) and the sentences column
    df: pd.DataFrame = pd.read_csv(f_path, index_col = 0, usecols=['id', 'sentence'])
    
    # Get the years
    df['year']: pd.Series = df.index.str.split("_").str[0]
    df.set_index('year', inplace=True)
    df.reset_index(inplace=True)
    
    # Convert to Series to get the 'sentence' column as a string type
    sentences: pd.Series = pd.Series(df['sentence'], dtype="string")

    return sentences


def clean(sentence : str, stop_words: Set[str], lemmatizer: WordNetLemmatizer) -> List[str]:
    """
    Perform a basic cleaning on the given sentences.
    Cleaning includes:
        - Hyphen removals from words that appeared at the end of a sentence and were split to the next line.
        - Lowercasing
        - Tokenization
        - Removal of words that do not exclusively contain letters
        - Removing stopwords
        - Lemmatization

    @param sentence: A string of sentence
    @param stop_words: A set of string stop words
    @param lemmatizer: A WordNetLemmatizer
    @return: A List of strings contained the cleaned words for the sentence
    """

    # Hyphen removal
    sentence = re.sub(r'(—|_|-)( )*', '', str(sentence))
    
    # Lowercase and tokenize
    tokens = word_tokenize(sentence.lower())
    
    # Keep only letters
    words_alpha = [word for word in tokens if word.isalpha()]
    
    # Stopword Removal
    filtered_tokens = [word for word in words_alpha if word not in stop_words]
    
    # Lemmatization
    lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_tokens]
    
    return lemmatized_words


def pre_processing(sentences: pd.Series) -> List[List[str]]:
    """
    Perform pre-processing on the given `sentences`.
    Utilize the `clean` function defined above.
    Also, convert potential words to bigrams.
    Return a List of List of Strings.

    @param sentences: A Pandas Series representing the sentences need for pre processing.
    @return: A List of List of strings that contains the processed sentence tokens.
    """

    # Load in the stopwords from the NLTK library
    stop_words: List[str] = stopwords.words('english')
    
    # Add custom stop words fromt the `custom_stopwords.txt` file
    # This is done to remove corpus sepcific words.
    # Most of these custom words were brought from Dalwadi's paper (see sources).
    with open('stopwords/custom_stopwords.txt', 'r') as f:
        stop_words += f.read().splitlines()
    
    # Convert to a set for faster computations
    stop_words: Set[str] = set(stop_words)
    
    print(f"Number of stop words: {len(stop_words)}")

    # Initialize the WordNetLemmatizer
    lemmatizer = WordNetLemmatizer()

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        # Apply the "clean" function to each sentence
        cleaned_sents: pd.Series = sentences.apply(lambda x: clean(x, stop_words, lemmatizer))

    # Convert potential words to bigrams.
    bigram = Phrases(cleaned_sents, min_count=5, threshold=100)
    bigram_mod = Phraser(bigram)

    cleaned_sents: List[List[str]] = [bigram_mod[text] for text in cleaned_sents.tolist()]

    return cleaned_sents


def objective(params, data):
    num = int(params['num_topics'])
    a = params['alpha']
    b = params['eta']

    lda_model = models.ldamulticore.LdaMulticore(corpus=data['corpus'],
                                                 id2word=data['dictionary'],
                                                 num_topics=num,
                                                 alpha=a,
                                                 eta=b,
                                                 per_word_topics=data['per_word_topics'])

    # Compute coherence
    coherence_model_lda = CoherenceModel(model=lda_model,
                                         texts=data['cleaned_sents'],
                                         dictionary=data['dictionary'],
                                         coherence='c_v')
    coherence_score = coherence_model_lda.get_coherence()

    # Compute perplexity
    perplexity_score = lda_model.log_perplexity(data['corpus'])

    # Combine coherence and perplexity into a single objective
    weight_coherence = 1.0  # adjust according to importance
    weight_perplexity = 1.0  # adjust according to importance
    combined_objective = (weight_coherence * coherence_score) - (weight_perplexity * perplexity_score)

    # We use negative because HyperOpt minimizes the objective function
    return -combined_objective


def main():
    import sys
    import gensim
    import hyperopt
    import multiprocessing
    print(f"Python version   : {sys.version}")
    print(f"Version info     : {sys.version_info}")
    print(f"gensim version   : {gensim.__version__}")
    print(f"pandas version   : {pd.__version__}")
    print(f"hyperopt version : {hyperopt.__version__}")
    print(f"Total cores      : {multiprocessing.cpu_count()}")
    
    # directory for storing all data, such lda models and cleaned sentences
    model_dir = 'checkpoint'
    if not os.path.isdir(model_dir):
        print(f"\nMaking directory for storing data: {model_dir}")
        os.mkdir(model_dir)

    # Create the path to store the cleaned sentences
    cleaned_sents_path = os.path.join(model_dir, 'cleaned_sentences.pkl')

    if os.path.exists(cleaned_sents_path):
        print(f"\nFile at {cleaned_sents_path}\" exists! Reading from file.")
        
        with open(cleaned_sents_path, 'rb') as f:
            cleaned_sents: List[List[str]] = pickle.load(f)

    else:
        print(f"\nFile at \"{cleaned_sents_path}\" does not exists! Performing calculations.")

        cleaned_sents: List[List[str]] = pre_processing(load_sentences())
        print(f"\nSaving cleaned senteces at \"{cleaned_sents_path}\"")
        
        # Save
        with open(cleaned_sents_path, 'wb') as f:
            pickle.dump(cleaned_sents, f)    

    print(f"\nThe number of cleaned sentences: {len(cleaned_sents):,}")
    print(f"Sample output: {cleaned_sents[:1]}")

    ## LDA & Hyperparameter Tuning
    # There are 3 main types of parameters that effect the LDA model:
    # 1. `num_topics`: Number of Topics
    # 2. `alpha`: Document-Topic Density
    # 3. `beta`: Word-Topic Density
    
    # Create a dictionary: a mapping between words and their integer ids
    dictionary = corpora.Dictionary(cleaned_sents)
    print(f"\nLength of the dictionary before filtering: {len(dictionary):,}")

    # Filter out extreme words that won't be helpful in the topic modeling.
    # Eliminate words below a frequency threshold, meaning that words that occur below the value will be removed
    dictionary.filter_extremes(no_below=10, no_above=1, keep_n=None)
    print(f"\nLength of the dictionary after filtering: {len(dictionary):,}")

    # Convert document into the bag-of-words format
    corpus = [dictionary.doc2bow(text) for text in cleaned_sents]
    
    # Since LDA uses randomness within its algorithms, it yields 
    # slighty different output for different runs on the same data. 
    # To make sure that the output are consistent and to save some time, 
    # the model will be saved without having to rebuild it every single time.

    # Define the hyperparameter values for tuning
    num_topics_vals: List[int] = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
    alpha_vals: List[float | str] = [0.001, 0.01, 0.1, 1.0, 'symmetric', 'asymmetric']
    eta_vals: List[float | str] = [0.001, 0.01, 0.1, 1.0, 'symmetric']

    # Define the search space
    space = {
        'num_topics': hp.choice('num_topics', num_topics_vals),
        'alpha': hp.choice('alpha', alpha_vals),
        'eta': hp.choice('eta', eta_vals)
    }

    # Define the data that will be passed to the objective function
    data = {
        'corpus': corpus,
        'dictionary': dictionary,
        'per_word_topics': True,
        'cleaned_sents': cleaned_sents
    }

    # Make a partial function that accepts the data
    fmin_objective = partial(objective, data=data)

    # Find the best hyperparameters
    best = fmin(fn=fmin_objective, space=space, algo=tpe.suggest, max_evals=1000)

    best_params = {
        'num_topics': num_topics_vals[best['num_topics']],
        'alpha': alpha_vals[best['alpha']],
        'eta': eta_vals[best['eta']]
    }

    # Best hyperparameters (as selected by HyperOpt):
    pprint(best_params)

    # Serialize parameters and write to file using Pickle
    best_params_path = os.path.join(model_dir, 'best_params_comb.pkl')
    with open(best_params_path, "wb") as pickle_file:
        pickle.dump(best_params, pickle_file)

    # Build the final model using the best parameters.
    # Use parallelized Latent Dirichlet Allocation to parallelize and speed up model training
    lda_model = models.ldamulticore.LdaMulticore(corpus=corpus,
                                                 id2word=dictionary,
                                                 num_topics=best_params['num_topics'],
                                                 alpha=best_params['alpha'],
                                                 eta=best_params['eta'],
                                                 per_word_topics=True)
    
    model_path = os.path.join(model_dir, 'topic_model_comb.lda')

    # Save the model
    lda_model.save(model_path)


if __name__ == "__main__":
    main()
