import sys
import pandas as pd
from sqlalchemy import create_engine
import nltk
nltk.download(['punkt','wordnet','stopwords'])

import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import classification_report
import joblib

def load_data(database_filepath):
    engine = create_engine('sqlite:///'+database_filepath)
    df= pd.read_sql_table("disaster", engine)
    df.loc[df['related'] == 2, 'related'] = 1
    X = df['message']
    Y = df.iloc[:, 4:]
    return X,Y, Y.columns

def tokenize(text):
    tokens = word_tokenize(text)
    stop_words = stopwords.words("english")
    lemmatizer = WordNetLemmatizer()
    # lemmatize, lowercase and remove stop words
    cleaned_tokens = [lemmatizer.lemmatize(word).lower().strip() for word in tokens if word not in stop_words]
    return cleaned_tokens


def build_model():
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(RandomForestClassifier()))
    ])
    parameters = {
        'vect__ngram_range': ((1, 1), (1, 2)),
        'vect__max_df': (0.5, 0.75, 1.0),
        'vect__max_features': (None, 5000, 10000),
        'tfidf__use_idf': (True, False),
        'clf__estimator__n_estimators': [10, 20, 30],
        'clf__estimator__min_samples_split': [5, 10, 15],
       }
    cv = GridSearchCV(pipeline, param_grid=parameters)
    return cv


def evaluate_model(model, X_test, Y_test, category_names):
    y_pred = model.predict(X_test)
    for i in range(len(Y_test.columns)):
        col = Y_test.columns[i]
        print("category:",col)
        accuracy = (y_pred[:, i] == np.array(Y_test[col])).mean()
        print("accuracy:", accuracy)
        print(classification_report(np.array(Y_test[col]), y_pred[:, i]))
        print("--------------------------------------------------------")

def save_model(model, model_filepath):
    joblib.dump(model, model_filepath)


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()