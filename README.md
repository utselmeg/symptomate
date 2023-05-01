## SymptoMate
Project description: A search engine that leverages rule based expert systems and natural language processing technologies in order to:
Suggest possible wording for ailments and pain that users find hard to put into words
Suggest possible diagnoses for the users’ given symptoms - through asking a series of prompt questions
Direct them to appropriate websites and helplines
Support related search recommendation, search history, and user personalization

## Dependencies

```bash
conda env create -f symptomate.yml
```

## Usage

### Environment setup
Activate the environment by running
```bash
conda activate symptomate
```
Start the app:
```
flask run
```
Open in your browser:

[http://127.0.0.1:5000](http://127.0.0.1:5000)


## Test cases:
* **Test case 1**: 
    * **User input**: I've been having some joint pain lately, particularly in my knees and hips. It's been bothering me for a while now and I'm finding it difficult to move around. The pain is sometimes sharp and intense, and it's been affecting my daily activities.
    * **Additional input**: painful walking
    * **Diagnosis**: Osteoarthristis
* **Test case 2**: 
    * **User input**: I've been feeling really tired lately and don't seem to have much energy. I've also been having cramps in my muscles, particularly in my legs. I've noticed that I'm bruising more easily than usual, and my legs have become swollen.
    * **Additional input**: swollen blood vessels
    * **Diagnosis**: Varicose veins
* **Test case 3**: 
    * **User input**: I've been having an itchy skin rash that's red and bumpy. I also noticed some raised and painful bumps in certain areas, and some parts of my skin are becoming darker or lighter than usual. I'm worried about what might be causing these symptoms.
    * **Additional input**: 
    * **Diagnosis**: Fungal infection
* **Test case 4**: 
    * **User input**: I've been having headaches for a while now, and they're getting worse. Additionally, I've been experiencing chest pain and feeling dizzy. Sometimes I even lose my balance and have trouble walking straight. I'm also having trouble concentrating and my mind feels foggy.
    * **Additional input**: lack of concentration
    * **Diagnosis**: Hypertension


