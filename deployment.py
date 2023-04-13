# Importing necessary packages
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st  # for  deployment
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
nltk.download('stopwords')
nltk.download("punkt")
ps = PorterStemmer()
sw = stopwords.words('english')


def text_preprocessing(doc):
    """Cleaning the query"""
    tokens = word_tokenize(doc)
    tmp = ""
    for w in tokens:
        if w.isalpha():
            w = w.lower()
            if w not in sw:
                tmp += ps.stem(w)+" "
    return tmp


# with open('publications.json', 'r') as f:
#     pub = json.load(f)
# with open('corpus.json', 'r') as c:
#     corpus = json.load(c)
def main():

    with open('publications.json', 'r') as f:
        pub = json.load(f)
    with open('corpus.json', 'r') as c:
        corpus = json.load(c)

    st.title('Coventry Research Search')

    query = st.text_input('Query:')
    query_lower = query.lower().split()
    incl_abs = False
    if st.checkbox("Display Abstract"):
        incl_abs = True

    toggle_state = st.radio("Search Method", options=["TfIdf Score Method", "Vector Space Model"])

    if toggle_state == "TfIdf Score Method":
        method= "tfidf"
    else:
        method = "vsm"

    if st.button("Search"):
        filtered_query = text_preprocessing(query)
        query_docs = {}
        q_df = {}
        all_docs = set()
        query_tf = {}
        keep_going = False
        for q in filtered_query.split():
            if q in corpus:
                query_docs[q] = corpus[q]
                q_df[q] = len(corpus[q])
                all_docs = all_docs.union(set(query_docs[q].keys()))
                keep_going = True
                if q in query_tf:
                    query_tf[q] += 1  # term frequency of a word in the query
                else:
                    query_tf[q] = 1
        all_docs=list(all_docs)
        n = len(all_docs)
        if keep_going:
            if method =="tfidf": # For tfidf Score method
                tf_idf = {}
                for q, docs in query_docs.items():
                    df = len(query_docs[q])
                    for d, tf in docs.items():
                        if d in tf_idf:
                            tf_idf[d] += tf * n / df
                        else:
                            tf_idf[d] = tf * n / df
                sorted_docs = sorted(tf_idf, key=lambda x: tf_idf[x]*-1)

            elif method =="vsm": # For Vector Space model
                tfidf_vectors = {}
                vector_dimension = len(query_docs)
                for idx in all_docs:
                    tfidf_vectors[idx] = np.zeros(vector_dimension)
                w_idx = 0
                for qw, docs in query_docs.items():
                    for idx, tf in docs.items():
                        tfidf_vectors[idx][w_idx] = tf * n / q_df[qw]
                    w_idx += 1
                query_vector = np.zeros(vector_dimension)
                w_idx = 0
                for qw, tf in query_tf.items():
                    query_vector[w_idx] = tf * n / q_df[qw]
                    w_idx += 1
                cos_similarity = {}
                for d, v in tfidf_vectors.items():
                    cos_similarity[d] = cosine_similarity(query_vector.reshape(1, -1), v.reshape(1, -1))
                print(cos_similarity)
                sorted_docs = sorted(cos_similarity, key=lambda x: cos_similarity[x] * -1)

            if len(sorted_docs) > 10:
                sorted_docs = sorted_docs[:10]
            print(sorted_docs)
            with st.container():
                for j in sorted_docs:
                    i = int(j)
                    title = pub[i]["Title"]
                    st.subheader(title)
                    pub_year = "Published Year: " + str(pub[i]["Year"]) +\
                           "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Journal: " +\
                           (str(pub[i]['Journal']) if 'Journal' in pub[i] else "")
                    st.write(pub_year)
                    link = pub[i]["Link"]
                    st.markdown(link)
                    if incl_abs:
                        string = str(pub[i]['Abstract']) if 'Abstract' in pub[i] else ""
                        if string != "":
                            string_wp = string.replace("(", "").replace(")", "").replace(",","")
                            string_lower = string_wp.lower().split()
                            string_list = string_wp.split()
                            for qry in query_lower:
                                for in_w in range(len(string_lower)):
                                    if qry == string_lower[in_w]:
                                        replace_word = string_list[in_w]
                                        if replace_word != "" and replace_word not in sw:
                                        # To bold the query words  in  the abstract
                                            string = string.replace(replace_word, "**" + replace_word + "**")

                            st.markdown(string)

                    st.text("Authors:")
                    at = ''
                    for a in pub[i]["Author"]:
                        if "Alink" in a:
                            atl = a["Name"]+" "+a["Alink"]
                            st.markdown(atl)
                        else:
                            at += a["Name"]+" ; "
                    if at != '':
                        st.markdown(at)
        else:
            st.text("Sorry no results!!  Try a different query ")

if __name__ == '__main__':
    main()