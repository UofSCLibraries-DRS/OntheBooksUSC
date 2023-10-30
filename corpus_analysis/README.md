# Corpus Analysis

The corpus analysis phase explores the underlying characteristics behind laws from South Carolina.

- Most frequent and TF-IDF

    `corpus_analysis.ipynb` find the most frequent words (along with their scores) for each year. It also finds the top bi-gram and tri-gram TF-IDF words and scores for those years.

- LDA

    `LDA.ipynb` uses an unsupervised method, Latent Dirichlet Allocation (LDA), to build a topic model for the laws.
    <br><br>A visualization of an early LDA model is show below,
    <br><img src="../images/LDAvis.gif" width="50%" height="50%">
    - In the visualization, the topics are represented by the bubbles and sorted by their size.
    - The blue bars on the right side are the total frequency of the word in the corpus. The red bars give the number of times the term was present in the selected topic.
    - If no topic is chosen, then the blue bars show the most frequent words.
    - In the graph on the left, the distance between the bubbles indicates the uniqueness. For example, the closer the bubbles are to each other, the more similar they are.