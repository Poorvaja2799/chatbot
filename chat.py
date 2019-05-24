from flask import Flask, render_template, request, jsonify
import nltk
import random
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import dbclass
from dbclass import DbClass
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
app = Flask(__name__)


DbClass = DbClass()
GREETING_INPUTS = ["hello", "hi", "greetings", "sup", "hey", "hey", "hai"]
GREETING_RESPONSES = ["hi", "hey", "hi there", "hello", "I am glad! You are talking to me"]
APPROVAL = ['yes', 'yeah', 'ok', 'okay']
PHYSICIANS = ['Paediatrician', 'Gynaecologist', 'Surgeon', 'Psychiatrist', 'Cardiologist', 'Dermatologist',
              'Endocrinologist', 'Gastroenterologist', 'Nephrologist', 'Ophthalmologist', 'Otolaryngologist', 'ENT',
              'Pulmonologist', 'Neurologist', 'Radiologist', 'Anaesthesiologist', 'Oncologist']
flag = False
p = False
cur_physician = ""
name = ""
f = open('physicians.txt', 'r', errors='ignore')
raw = f.read()
raw = raw.lower()
sent_tokens = nltk.sent_tokenize(raw)
word_tokens = nltk.word_tokenize(raw)
lemmer = nltk.stem.WordNetLemmatizer()
remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)


def send_mail(to, time, name):
    msg = MIMEMultipart()
    msg['From'] = 'from@gmail.com'
    msg['To'] = 'to@gmail.com'
    msg['Subject'] = 'apoointment'
    message = 'Hey '+ to + "\nAppointment fixed at " + time + " for " + name
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP('smtp.gmail.com', 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login('from@gmail.com', "password")
    mailserver.sendmail('from@gmail.com', 'from@gmail.com', msg.as_string())
    mailserver.quit()


def LemNormalize(text):
    tokens = nltk.word_tokenize(text.lower().translate(remove_punct_dict))
    lemmatized_tokens = [lemmer.lemmatize(token) for token in tokens]
    return lemmatized_tokens


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    msg = request.form['message']
    print(msg)
    user_response = msg.lower()
    res = ""
    global flag
    global p
    global name
    global cur_physician
    if flag:
        for word in APPROVAL:
            if word in user_response:
                appointment_no = DbClass.read(dbclass.query1, cur_physician)[0]['appointment_no']
                if appointment_no <= 4:
                    time = str(appointment_no + 8) + ' am'
                    res = "Appointment fixed at " + time + " tomorrow, thankyou!"
                    send_mail(cur_physician, time, name)
                else:
                    if appointment_no <= 8:
                        time = str(appointment_no - 3) + ' pm'
                        res = "Appointment fixed at " + time + ", tomorrow, thankyou!"
                        send_mail(cur_physician, time, name)
                    else:
                        res = "Sorry! No appointments tomorrow"
                appointment_no += 1
                DbClass.simple_update(dbclass.query3)
                DbClass.update(dbclass.query2, (appointment_no, cur_physician))
                cur_physician = ""
                flag = False
                p = False
                name = ""
    else:
        if 'appointment' in user_response.split() or 'meet' in user_response.split():
            if p:
                for word in user_response.split():
                    for physician in PHYSICIANS:
                        if physician.lower() == word:
                            appointment_no = DbClass.read(dbclass.query1, physician)[0]['appointment_no']
                            if appointment_no <= 4:
                                time = str(appointment_no + 8) + ' am'
                                res = "Appointment fixed at " + time + " tomorrow, thankyou!"
                                send_mail(cur_physician, time, name)
                            else:
                                if appointment_no < 8:
                                    time = str(appointment_no - 3) + ' pm'
                                    res = "Appointment fixed at " + time + ", tomorrow, thankyou!"
                                    send_mail(cur_physician, time, name)
                                else:
                                    res = "Sorry! No appointments tomorrow"
                            appointment_no += 1
                            DbClass.update(dbclass.query2, (appointment_no, physician))
                            p = False
                            name = ""
            else:
                res = "May I know your name?"
                p = True
        else:
            if user_response == 'thanks' or user_response == 'thank you':
                res = "You are welcome.."
            else:
                if 'bye' in user_response:
                    res = "Bye! take care.."
                else:
                    for word in user_response.split():
                        robo_res = None
                        if word in GREETING_INPUTS:
                            robo_res = random.choice(GREETING_RESPONSES) + "!, May I know your name?"
                            p = True
                        if robo_res:
                            res = robo_res
                    else:
                        if res is "" and p:
                            if name:
                                sent_tokens.append(user_response)
                                TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
                                tfidf = TfidfVec.fit_transform(sent_tokens)
                                vals = cosine_similarity(tfidf[-1], tfidf)
                                idx = vals.argsort()[0][-2]
                                flat = vals.flatten()
                                flat.sort()
                                req_tfidf = flat[-2]
                                if req_tfidf == 0:
                                    res = "I am sorry! I can't understand you"
                                else:
                                    robo_response = sent_tokens[idx]
                                    for resp in robo_response.split():
                                        for physician in PHYSICIANS:
                                            if physician.lower() == resp:
                                                res = "Do you want me to fix an appointment with the %s?" % physician
                                                cur_physician = physician
                                                flag = True
                                sent_tokens.remove(user_response)
                            else:
                                name = user_response
                                res = "How can I help you?"
    print(res)
    return jsonify({'message': res})


if __name__ == '__main__':
    app.run(debug=True)
