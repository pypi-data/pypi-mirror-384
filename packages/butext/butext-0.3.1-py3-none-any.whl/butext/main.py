import re
import pandas as pd
import numpy as np
from wordcloud import STOPWORDS

def tokenize(df, col):
  #assign method adds new column; .findall creates list of words using regex, .explode creates individual rows for each word in the list
  tokens= df.assign(word= df[col].str.lower().str.findall(r"\w+(?:\S?\w+)*")).explode("word")
  return tokens   #remove ["word"] to get entire dataframe

def rel_freq(df, col):
  df = df.pivot(index='word', columns= col, values='text_freq')
  df = df.reset_index()
  df.loc[df[df.columns[1]].isna(), df.columns[1]] = 0.0005/2
  df.loc[df[df.columns[2]].isna(), df.columns[2]]  = 0.0005/2
  df['rel_freq'] = df[df.columns[1]]/df[df.columns[2]]
  df["logratio"] = np.log10(df["rel_freq"])
  return df
# Let col be the column you want to tokenize and col2 be the categories you want to find rel freq between

def tfidf(df1 , df2, col):
  df1['text_freq'] = df2[df2.columns[2]].values
  doc = df1.groupby('word')[col].count()
  doc.name = 'df'
  doc = doc.reset_index()
  N = df1[col].nunique()
  doc['idf'] = np.log(N / doc["df"])
  result = counts.merge(doc[["word", "idf"]], on="word")
  result["tf_idf"] = result['text_freq'] * result['idf']
  return result