from pyresparser import ResumeParser
from docx import Document
from flask import Flask,render_template,redirect,request
import numpy as np
import pandas as pd
import re
from ftfy import fix_text
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

stopw  = set(stopwords.words('english'))

df =pd.read_csv('jobs.csv') 
df['test']=df['Job_Description'].apply(lambda x: ' '.join([word for word in str(x).split() if len(word)>2 and word not in (stopw)]))

app=Flask(__name__)



@app.route('/')
def hello():
    return render_template("index.html")



@app.route("/home")
def home():
    return redirect('/')

@app.route('/submit',methods=['POST'])
def submit_data():
    if request.method == 'POST':
        
        f=request.files['userfile']
        f.save(f.filename)
        try:
            doc = Document()
            with open(f.filename, 'r') as file:
                doc.add_paragraph(file.read())
                doc.save("text.docx")
                data = ResumeParser('text.docx').get_extracted_data()
                
        except:
            data = ResumeParser(f.filename).get_extracted_data()
        resume=data['skills']
        print(type(resume))
    
        skills=[]
        skills.append(' '.join(word for word in resume))
        org_name_clean = skills
        
        def ngrams(string, n=3):
            string = fix_text(string) # fix text
            string = string.encode("ascii", errors="ignore").decode() #remove non ascii chars
            string = string.lower()
            chars_to_remove = [")","(",".","|","[","]","{","}","'"]
            rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
            string = re.sub(rx, '', string)
            string = string.replace('&', 'and')
            string = string.replace(',', ' ')
            string = string.replace('-', ' ')
            string = string.title() # normalise case - capital at start of each word
            string = re.sub(' +',' ',string).strip() # get rid of multiple spaces and replace with a single
            string = ' '+ string +' ' # pad names for ngrams...
            string = re.sub(r'[,-./]|\sBD',r'', string)
            ngrams = zip(*[string[i:] for i in range(n)])
            return [''.join(ngram) for ngram in ngrams]
        vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams, lowercase=False)
        tfidf = vectorizer.fit_transform(org_name_clean)
        print('Vecorizing completed...')
        
        
        def getNearestN(query):
          # Transform the query text into a TF-IDF vector using the same vectorizer used for the skills
          queryTFIDF_ = vectorizer.transform(query)
          # Compute cosine similarity between the query TF-IDF vector and all other TF-IDF vectors
          query_cosine_similarities = cosine_similarity(queryTFIDF_, tfidf)
          #Use the fitted nearest neighbors model to find the nearest neighbor(s) of the query
          distances, indices = nbrs.kneighbors(query_cosine_similarities)
          # Return the distances and indices of the nearest neighbor(s)
          return distances, indices
        
        # Compute cosine similarity matrix for the tfidf matrix
        cosine_similarities = cosine_similarity(tfidf, tfidf)

        # Define the nearest neighbors object with k=1 (i.e., find the nearest neighbor)
        nbrs = NearestNeighbors(n_neighbors=1, metric='precomputed')
        # Fit the nearest neighbors model to the cosine similarity matrix
        nbrs.fit(cosine_similarities)
        unique_org = (df['test'].values)
        distances, indices = getNearestN(unique_org)
        unique_org = list(unique_org)
        matches = []
        for i,j in enumerate(indices):
            dist=round(distances[i][0],2)
  
            temp = [dist]
            matches.append(temp)
        matches = pd.DataFrame(matches, columns=['Match confidence'])
        df['match']=matches['Match confidence']
        df1=df.sort_values('match')
        df2=df1[['Position', 'Company','Location']].head(10).reset_index()
        
        
        
        
        
    #return  'nothing' 
    return render_template('index.html',tables=[df2.to_html(classes='job')],titles=['na','Job'])
        
        
        
        
        
if __name__ =="__main__":
    
    
    app.run()