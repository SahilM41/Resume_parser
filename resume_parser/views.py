from ast import If
from distutils import extension
import imp
from django.shortcuts import redirect, render;
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_protect
from django import forms
from django.core.files.storage import FileSystemStorage
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from pdf2docx import parse ,Converter
import docx2txt
from pdfminer.high_level import extract_text
import nltk
import re
import subprocess
import spacy
from nltk.corpus import stopwords
import pandas as pd
from spacy.matcher import Matcher
import os, subprocess, code, glob, traceback, sys, inspect
from os import link
import logging
from typing import Text
from unicodedata import name
import PyPDF2
from pdfminer.high_level import extract_text
from django.http import HttpResponseRedirect
from django.contrib import messages
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nlp = spacy.load('en_core_web_sm')
matcher = Matcher(nlp.vocab)
data=[]
@csrf_protect
def upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name,myfile)
        uploaded_file_path = fs.path(filename)
        uploaded_file_url = fs.url(filename)
        extension=filename.split(".")[-1]
        urls=extract_urls(uploaded_file_path)
        if extension=='docx':
            text=extract_text_from_docx(uploaded_file_path)
        elif extension == 'pdf':
            text=extract_text_from_pdf(uploaded_file_path)
            convert_pdf_to_docx(uploaded_file_path)
            resume_text=extract_text_from_docx('./demo.docx')    
        else:
            messages.warning(request,'Unsupported File Type')

        """-----------0------------"""
        name=proper_name(resume_text)
        data.append(name)
        """-----------1-------------"""
        phone_number=extract_phone_number(text)
        data.append(phone_number)
        """-----------2-------------"""
        emails=extract_emails(text)
        data.append(emails[0])
        """-----------3-------------"""
        skills_list=list(extract_skills(text))
        data.append(skills_list)
        """-----------4-------------"""
        skills_score=extract_skills_score(text)
        data.append(skills_score)
        """-----------5-------------"""
        linkedin_urls=extract_linkedin(urls)
        data.append(linkedin_urls)
        """-----------6-------------"""
        Github_urls=extract_Github(urls)
        data.append(Github_urls)
        """-----------7-------------"""
        education_score=Validation_education(text)
        data.append(education_score)  
        print(data)      
        if data:
            return redirect('display')
        else:
            messages.warning(request,'Blank Document')
    return render(request, 'upload.html')

def display(request):
    name=data[0]
    phone_number=data[1]
    email=data[2]
    skills_list=data[3]
    skils_score=data[4]
    linkedin_url=data[5]
    Github_url=data[6]
    education_score=data[7]
    data.clear()
    return render(request,'display.html',{ 'name': name,'phone_number':phone_number,
                                            'email':email,
                                            'skills_list':skills_list,
                                            'skills_score':skils_score,
                                            'linkedin_url':linkedin_url,
                                            'Github_url':Github_url,
                                            'education_score':education_score
                                        })

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

"""----------------------------------------------------------------------"""
def extract_text_from_docx(docx_path):
    txt = docx2txt.process(docx_path)
    if txt:
        return txt.replace('\t',' ')
    return None
"""----------------------------------------------------------------------"""
def convert_pdf_to_docx(pdf_path):
        docx_path='./demo.docx'
        cv=Converter(pdf_path)
        cv.convert(docx_path,start=0,end=None)
        cv.close()


"""----------------------------------------------------------------------"""
#Extracting Name Method 1
def extract_name(resume_text):
    nlp_text = nlp(resume_text)
    # First name and Last name are always Proper Nouns
    pattern = [{'POS': 'PROPN'},{'POS': 'PROPN'},{'POS': 'PROPN'}]
    matcher.add('NAME',[pattern])
    matches = matcher(nlp_text)
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text
#Cleaning and Comparing and returning name from Resume      
def proper_name(resume_text):
    name1=extract_name(resume_text)
    if(name1 != None):
        tokenize_name1=name1.split()
        first_name1=tokenize_name1[0]
        last_name1=tokenize_name1[1]
    resume_text=resume_text.split()
    first_name=resume_text[0]
    last_name=resume_text[1]
    full_name=first_name+' '+last_name
    if(name1 == None):
        return full_name
    elif(first_name1==first_name and last_name1==last_name):
        return name1
    else:
        return full_name

"""----------------------------------------------------------------------"""
#Mobile Number Extracting
PHONE_REG = re.compile(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]')
def extract_phone_number(resume_text):
    phone = re.findall(PHONE_REG, resume_text)

    if phone:
        number = ''.join(phone[0])

        if resume_text.find(number) >= 0 and len(number) < 12:
            return number
    return None
"""----------------------------------------------------------------------"""
#Email Extracting
EMAIL_REG = re.compile(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+')
def extract_emails(resume_text):
    return re.findall(EMAIL_REG, resume_text)
"""----------------------------------------------------------------------"""
#Linked Extracting
def extract_linkedin(urls):
    for element in urls:
        if((re.search('linkedin.com/in/', element)!= None) or (re.search('https://linkedin.com/in/', element)!= None)):
            return element
"""----------------------------------------------------------------------"""
#Github Extracting
def extract_Github(urls):
    for el in urls:
        if((re.search('github.com/', el)!= None) or (re.search('https://github.com/', el)!= None)):
            return el
"""----------------------------------------------------------------------"""
#Education Extraction
STOPWORDS = set(stopwords.words('english'))
EDUCATION =["BACHELOR","MASTERS","DIPLOMA","HIGHER","SECONDARY","BCA","MCA","BSC","BE","B.E",'B.COM','M.COM'
            "ME","M.E", "MS", "M.S", "BCS","B.C.S" ,"B.E.","M.E.","M.S.","B.C.S.","C.A","CA",'C.A.', 'MBA','PHD'
            "B.TECH", "M.TECH", "BA","B.A","BS","B.S"
            "SSC", "HSC", "CBSE", "ICSE", "X", "XII"]
def extract_education(resume_text):
    nlp_text = nlp(resume_text)
    # Sentence Tokenizer
    nlp_text = [sent.text.strip() for sent in nlp_text.sents]
    edu = {}
    # Extract education degree
    for index, text in enumerate(nlp_text):
        #print(index, text), print('-'*50)
        for tex in text.split():
            # Replace all special symbols
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in EDUCATION and tex not in STOPWORDS:
                edu[tex] = text + nlp_text[index + 1]
                print(edu.keys())
"""----------------------------------------------------------------------"""
#Valdating That Education Section is Present OR NOT
newData =[]
def Validation_education(resume_text):
    resume_text = resume_text.strip()
    resume_text = resume_text.split()
    for i in range(len(resume_text)):
        resume_text[i]=resume_text[i].upper()
    score = 0
    for i in EDUCATION:
        for j in resume_text:
            if(i==j):
                score += 1
    return score
"""----------------------------------------------------------------------"""
def extract_institute(input_text):
    data=pd.read_csv("./data/schools.csv")
    school_DB=list(data.columns.values)



"""----------------------------------------------------------------------"""

#Extracting Skills and Skills Count From skills and experience Section
def extract_skills(input_text):
    length_of_list=0
    data = pd.read_csv("./data/skills.csv") 
    SKILLS_DB = list(data.columns.values)
    stop_words = set(nltk.corpus.stopwords.words('english'))
    word_tokens = nltk.tokenize.word_tokenize(input_text)
 
    # remove the stop words
    filtered_tokens = [w for w in word_tokens if w not in stop_words]
 
    # remove the punctuation
    filtered_tokens = [w for w in word_tokens if w.isalpha()]
 
    # generate bigrams and trigrams (such as artificial intelligence)
    bigrams_trigrams = list(map(' '.join, nltk.everygrams(filtered_tokens, 2, 3)))
 
    # we create a set to keep the results in.
    found_skills = set()
 
    # we search for each token in our skills database
    for token in filtered_tokens:
        if token.lower() in SKILLS_DB:
            found_skills.add(token)
 
    # we search for each bigram and trigram in our skills database
    for ngram in bigrams_trigrams:
        if ngram.lower() in SKILLS_DB:
            found_skills.add(ngram)
    return found_skills
"""----------------------------------------------------------------------"""
#Skills Score 
def extract_skills_score(resume_text):
    skills_list=extract_skills(resume_text)
    length_of_list=len(skills_list)
    return length_of_list

"""----------------------------------------------------------------------"""
def extract_urls(pdf_path):
    PDFFile = open(pdf_path,'rb')
    PDF = PyPDF2.PdfFileReader(PDFFile)
    pages = PDF.getNumPages()
    key = '/Annots'
    uri = '/URI'
    ank = '/A'
    urls=[]
    for page in range(pages):
        print("Current Page: {}".format(page))
        pageSliced = PDF.getPage(page)
        pageObject = pageSliced.getObject()
        if key in pageObject.keys():
            ann = pageObject[key]
            for a in ann:
                u = a.getObject()
                if uri in u[ank].keys():
                    urls.append(u[ank][uri])
    return urls

