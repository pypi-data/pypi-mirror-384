# butext
Text Mining Library Developed @ Binghamton University

```python
def tokenize(df, col):
  '''Tokenizes the text in a specified column of a DataFrame.

  Parameters
  ----------
  df : pandas.DataFrame
      The input DataFrame containing the text data.
  col : str
       The name of the column in `df` that contains text to tokenize.

  Returns
  -------
  pandas.DataFrame
  A new DataFrame with an additional column called 'word',
  where each row corresponds to a single token.
  '''
  tokens= df.assign(word= df[col].str.lower().str.findall(r"\w+(?:\S?\w+)*")).explode("word")
  return tokens

def rel_freq(df, col):
  '''Calculates the realtive frequency of a word between two documents

  Parameters
  ----------
  df : pandas.DataFrame
      The input DataFrame containing text data
  col : str
       The name of the column containg the two docuemnts you want to find relative frequency of

  Retruns
  ----------
  pandas.DataFrame
  A new DataFrame with the column word, a column of the text frequencies of the word in each document,
  relative frequency column, and logratio column'''
  df = df.pivot(index='word', columns= col, values='proportion')
  df = df.reset_index()
  df.loc[df[df.columns[1]].isna(), df.columns[1]] = 0.0005/2
  df.loc[df[df.columns[2]].isna(), df.columns[2]]  = 0.0005/2
  df['rel_freq'] = df[df.columns[1]]/df[df.columns[2]]
  df["logratio"] = np.log10(df["rel_freq"])
  return df

def tf_idf(df, col):
  '''Calculates the Text Frequency-Inverse Document Frequency(TF-IDF) of each word per document

  Parameters
  ----------
  df: pandas.DataFrame
     The input DataFrame containing text data
  col : str
       The name of the column containing the documents you want to find TF-IDF of

  Returns
  ----------
  A new DataFrame with a column of the document, a column of the word,
  a column of the words text frequency corresponding to document, a column for idf,
  and a column for tf_idf'''
  doc = df.groupby('word')[col].count().reset_index(name='df')
  N = df[col].nunique()
  doc['idf'] = np.log(N / doc['df'])
  result = df.merge(doc[['word', 'idf']], on='word')
  result['tf_idf'] = result['text_freq'] * result['idf']
  return result

spam = pd.read_csv("https://raw.githubusercontent.com/Greg-Hallenbeck/HARP-210-NLP/main/datasets/SMSSpamCollection.tsv", sep="\t")
spam.head()

spam = (
    spam
    .pipe(tokenize, 'text')
)
spam #returns DataFrame with an extra 'word' column that is each token

df = spam[['class', 'word']]
df = df.loc[ ~df["word"].isin(STOPWORDS) ] #remvoes stop words for more meaningful results

spam_freq = (
    df
    .groupby('class')['word']
    .value_counts(normalize= True)
    .reset_index()
    .query('proportion > 0.0005') # gets rid of meaningless words, helps clean the result
    .pipe(rel_freq, 'class')
)
spam_freq = spam_freq.sort_values(by = 'logratio', ascending= True)
spam_freq

df = spam[['class', 'word']]
df = df.loc[ ~df["word"].isin(STOPWORDS) ] #remvoes stop words for more meaningful results

spam_tfidf = (
    df
    .groupby('class')['word']
    .value_counts(normalize=True)
    .reset_index(name='text_freq')
    .pipe(tf_idf, col='class')
)
x = spam_tfidf.sort_values(by = 'tf_idf', ascending= False)
x = x.loc[x.tf_idf != 0] # many words will have tf_idf = 0 but those words usually aren't important, so we can filter them out for cleaner results
x
