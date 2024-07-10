#IMPORTS
import feedparser
import openai
import csv
import ssl
from email.message import EmailMessage
import smtplib
import time
import os
import re
from flask import Flask, request
#SETUP
key,emaildict,dev,products,analyse = "openai_api_key",{},False,["Celeste. This is one of, if not the absolute best 2d platformers ever. It has beautiful pixelart, an amazing story and a dash mechanic that acts as an aim for any aspiring game developer working on their games' main mechanic","Google Arts & Culture","'A Promised Land' by Barack Obama","The BBC History Magazine","Focusrite Scarlett 2i2 3rd Gen USB Audio Interface","'My System' by Aron Nimzowitsch","Github Copilot"],False
#FUNCTIONS
def add_row_to_csv(email_address,subjects,email_length,time_period,time_since_last_email,file_path="emails.csv"):
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            email_address, subjects, email_length, time_period,
            time_since_last_email
        ])
      
def extract(s):
    pattern = r'%(.*?)%'
    matches = re.findall(pattern, s)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        return matches
    else:
        return None

def replacev2(string, char, first_replace, next_replace):
    first_index = string.find(char)
    if first_index == -1:
        return string
    new_string = string[:first_index] + first_replace
    next_index = string[first_index + 1:].find(char)
    if next_index == -1:
        return new_string + string[first_index + 1:]
    new_string += string[first_index + 1:first_index + 1 +
                         next_index] + next_replace
    new_string += string[first_index + 1 + next_index + 1:]
    return new_string

def byte(subjects, howoften, length):
    openai.api_key = key
    entries = []
    for subject in subjects:
        feed = feedparser.parse(
            f"https://news.google.com/rss/search?q={subject}+when:{howoften}d&hl=en-US&gl=US&ceid=US:en"
        )
        entries += feed.entries
    entries = entries[:100]
    news_items = [entry.title for entry in entries]
    news_items = "/n".join(news_items)
    messages = [{
        "role":
        "system",
        "content":
        f"\nYou are the writer of an email newsletter. You have to summorise the most important news items you are given into {length} bullet points that go into depth on the items but are not too long. Include the country the bullet point is talking about if it specified, but do not include the exact source or news company/paper; these are not supposed to be headlines, merely bullet points summerizing the news items. Be specific and do not repeat points.\n"
    }, {
        "role": "user",
        "content": f"List of news items:\n{news_items[:16000]}"
    }]
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=250,
        n=1,
        stop=None,
        timeout=20,
    )
    for i in summary['choices']:
        output = i['message']['content']
    time.sleep(5)
    return output

def kilobyte(subjects, previous, length):
    subjectstr = "\n".join(subjects)
    previousstr = "\n".join(previous)
    messages = [{
        "role":
        "system",
        "content":
        f"\nYou are the writer of an email newsletter. You will be given some subjects and some previous guides. Your job is to generate 1 short guide (about {length} paragraph(s)) for how to do something to do with 1 of the subjects you are given and that is not in the list of previous guides. Use sarcasm and wit, but make sure you actually teach something and that you discuss a useful topic; the subject of the guide should not be humourus, but the actual guide can include some humor. Include examples for any tools you need. Begin with a heading about the guide, which should be written in title case (the first letter of each word should be capitalised). Surround the heading with '%' on either side (e.g %<heading>%<guide>):"
    }, {
        "role": "user",
        "content": f"Subjects:\n{subjectstr}\nPrevious Guides:\n{previousstr}"
    }]
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        n=1,
        stop=None,
        timeout=20,
    )
    for i in result['choices']:
        output = i['message']['content']
    extraction = extract(output)
    if type(extraction) == list:
        for item in extraction:
            add_to_previous(item)
    else:
        add_to_previous(extraction)
    for i in range(3):
        output = replacev2(output, "%", "<h3>", "</h3>")
    time.sleep(5)
    return output

def megabyte(product, length, subjects=None):
    if subjects != None:
        productstr = "\n".join(product)
        subjectstr = "\n".join(subjects)
        messages = [{
            "role":
            "system",
            "content":
            f"\nYou are the writer of an email newsletter. You will be given a range of products and a list of subjects, and your job is to write a {length} paragraph long review of one of the products, the one that is the best fit subjects (e.g given the subjects art and technology and the products a back massager and a site for making online art, you should make the guide on the online art site as this is more to do with art and tech), discussing why it is good and, at the end, giving it a score out of 10. If you do not recognize the product, go off of any information you have been given in the prompt. Tie in the subjects in your review so that it is more tailored to the reader. Be positive about the product, and include sarcasm and wit in your review, but make sure it sounds like a review of the product; do not make it seem like an advert. Begin with a heading about the review, which should just be the type of product and its name (e.g <type>: <name>), should be written in title case (the first letter of each word should be capitalised) and should be surrounded with '%' on either side (e.g %<heading>%\n<guide>). Make sure you ONLY do 1 review, on the product that best fits the subjects:"
        }, {
            "role":
            "user",
            "content":
            f"Products:\n{productstr}\nSubjects:\n{subjectstr}"
        }]
    else:
        messages = [{
            "role":
            "system",
            "content":
            f"\nYou are the writer of an email newsletter. You will be given a product, and your job is to write a {length} paragraph long review of the product, discussing why it is good and, at the end, giving it a score out of 10. If you do not recognize the product, go off of any information you have been given in the prompt. Be positive about the product, and include sarcasm and wit in your review, but make sure it sounds like a review of the product; do not make it seem like an advert. Begin with a heading about the review, which should just be the type of product and its name (e.g <type>: <name>), should be written in title case (the first letter of each word should be capitalised) and should be surrounded with '%' on either side (e.g %<heading>%<guide>):"
        }, {
            "role": "user",
            "content": f"Product:\n{product}"
        }]
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        n=1,
        stop=None,
        timeout=20,
    )
    for i in result['choices']:
        output = i['message']['content']
    output = replacev2(output, "%", "<h3 style='color:white'>", "</h3>")
    time.sleep(30)
    return output.replace('"', '')

def read_csv_file(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    return data
  
def write_csv_file(filename, data):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def getemail(subjects, email_length, time_period, product, previous):
    subjectstr = ",".join(subjects)
    try:
        email = emaildict[f"{subjectstr}-{email_length}"]
    except:
        email = f"""
<div style="border: 1px solid black; padding: 10px; background-color: #222222; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h1>3Bytes</h1>
</div><div style="border: 1px solid black; padding: 10px; background-color: #333333; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h2>Byte:</h2>
{byte(subjects,time_period,int(email_length)+5)}

</div><div style="border: 1px solid black; padding: 10px; background-color: #333333; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h2>Kilobyte:</h2>{kilobyte(subjects,previous,int(email_length)+3)}

</div><div style="border: 1px solid black; padding: 10px; background-color: #333333; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h2 style='color:white'>Megabyte:</h2>{megabyte(product,int(email_length)+3, subjects)}
"""
        emaildict.update({f"{subjectstr}-{email_length}": email})
    return email

def sendemail(email_length, email_address, subjects, time_period, product,
              previous):
    email = getemail(subjects, email_length, time_period, product, previous)
    email = email.replace("\n", "<br>")
    sender = 'isaaclindenbarrierichardson@gmail.com'
    password = 'dpwgtzerczexbkbz'
    if len(subjects) == 1:
        subjectstr = subjects[0]
    elif len(subjects) == 2:
        subjectstr = " & ".join(subjects)
    else:
        subjectstr = ", ".join(subjects[:(
            len(subjects) - 2)]) + " & " + subjects[len(subjects) - 1]
    em = EmailMessage()
    em['From'] = sender
    em['To'] = email_address
    em['Subject'] = f"3bytes: {subjectstr}"
    em.set_content(
        "This is an HTML email. Please enable HTML to view this email.")
    em.add_alternative(email, subtype='html')
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, email_address, em.as_string())
    print(f"3bytes sent to {email_address}")

def get_previous():
    previous = []
    with open("previous.txt", "r") as f:
        for line in f:
            previous.append(line.replace("\n", ""))
    return previous

def add_to_previous(previous):
    with open("previous.txt", "a") as f:
        f.write(f"{previous}\n")

def run(filename, product, previous):
    data = read_csv_file(filename)
    for i in range(1, len(data)):
        time_since_last_email = int(data[i][4])
        time_period = int(data[i][3])
        if time_since_last_email == time_period:
            email_length = data[i][2]
            email_address = data[i][0]
            subjects = data[i][1].split(',')
            sendemail(email_length, email_address, subjects, time_period,
                      product, previous)
            data[i][4] = '1'
        else:
            data[i][4] = str(time_since_last_email + 1)
    write_csv_file(filename, data)

def run_program(x_hours):
    last_run_file = "last_run.txt"
    now = time.time()
    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as f:
            last_run_time = float(f.read().strip())
            if now - last_run_time < x_hours * 60 * 60:
                return False
    with open(last_run_file, 'w') as f:
        f.write(str(now))
    return True

def welcomeemail(email_address):
    email = """
<div style="border: 1px solid black; padding: 10px; background-color: #222222; color: white; border-radius:25px">
<h1>3Bytes</h1>
</div><div style="border: 1px solid black; padding: 10px; background-color: #333333; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h2>Byte:</h2>- This will be
- A few bullet points
- On what has been happening
- In the subjects you chose

</div><div style="border: 1px solid black; padding: 10px; background-color: #333333; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h2>Kilobyte:</h2>This will be a guide on how to do something in one or more of the subjects you chose

</div><div style="border: 1px solid black; padding: 10px; background-color: #333333; color: white; border-radius:25px; font-family: 'Comfortaa', monospace;">
<h2>Megabyte:</h2>This will be a review of a product, chosen out of a list to most align with your subjects of choice

</div>
    """
    email = email.replace("\n", "<br>")
    sender = 'isaaclindenbarrierichardson@gmail.com'
    password = 'dpwgtzerczexbkbz'
    em = EmailMessage()
    em['From'] = sender
    em['To'] = email_address
    em['Subject'] = f"3bytes: A Warm Welcome!"
    em.set_content(
        "This is an HTML email. Please enable HTML to view this email.")
    em.add_alternative(email, subtype='html')
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, email_address, em.as_string())

def execute(x_hours):
    if run_program(x_hours):
        run("emails.csv", products, get_previous())
    else:
        print("It has not get been 24 hours since last run")

#RUN
execute(20)
#SITE SETUP
app = Flask(__name__)
site = ""
#HTML
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>3bytes</title>
    <style>
        /* Add your CSS styles here */
        body {
            background-color: #333333;
            color: white;
            font-family: Arial, monospace;
            margin: 0;
            padding: 0;
        }
        /* Add more styles for the sidebar */
        .sidebar {
            background-color: #222222;
            width: 200px;
            height: 100%;
            position: fixed;
            left: 0;
            top: 0;
            overflow-x: hidden;
            padding-top: 20px;
        }
        .sidebar a {
            display: block;
            color: white;
            text-decoration: none;
            padding: 10px;
        }
        .sidebar a:hover {
            background-color: #555555;
        }
        /* Add more styles for the content */
        .content {
            margin-left: 200px;
            padding: 20px;
        }
        /* Add more styles for the forms */
        form {
            margin-bottom: 20px;
        }
        input[type=email], input[type=text], select {
            padding: 10px;
            border: none;
            border-radius: 3px;
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
            font-size: 16px;
        }
        input[type=submit] {
            background-color: #008CBA;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 10px;
            cursor: pointer;
            font-size: 16px;
        }
        input[type=submit]:hover {
            background-color: #005266;
        }
        input[type=range] {
            width: 100%;
            height: 20px;
            -webkit-appearance: none;
            margin-bottom: 10px;
        }
        input[type=range]:focus {
            outline: none;
        }
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: #555555;
            border-radius: 3px;
        }
        input[type=range]::-webkit-slider-thumb {
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #008CBA;
            cursor: pointer;
            -webkit-appearance: none;
            margin-top: -8px;
        }
        input[type=range]:focus::-webkit-slider-runnable-track {
            background: #666666;
        }
    </style>
</head>
<body style="font-family: 'Comfortaa', monospace">
    <div class="sidebar">
        <a href="/">Home</a>
        <a href="/signup">Sign Up</a>
        <a href="/what_is_3bytes">What is 3bytes</a>
    </div>
    <div class="content">
        <h1>Welcome to 3bytes!</h1>
        <p>Sign up with the "Sign Up" page or feel free to look around</p>
    </div>
</body>
</html>
"""
signup_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Signup</title>
    <style>
        /* Add your CSS styles here */
        body {
            background-color: #333333;
            color: white;
            font-family: Arial, monospace;
            margin: 0;
            padding: 0;
        }
        /* Add more styles for the sidebar */
        .sidebar {
            background-color: #222222;
            width: 200px;
            height: 100%;
            position: fixed;
            left: 0;
            top: 0;
            overflow-x: hidden;
            padding-top: 20px;
        }
        .sidebar a {
            display: block;
            color: white;
            text-decoration: none;
            padding: 10px;
        }
        .sidebar a:hover {
            background-color: #555555;
        }
        /* Add more styles for the content */
        .content {
            margin-left: 200px;
            padding: 20px;
        }
        /* Add more styles for the forms */
        form {
            margin-bottom: 20px;
        }
        input[type=email], input[type=text],input[type=number], select {
            padding: 10px;
            border: none;
            border-radius: 3px;
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
            font-size: 16px;
        }
        input[type=submit] {
            background-color: #008CBA;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 10px;
            cursor: pointer;
            font-size: 16px;
        }
        input[type=submit]:hover {
            background-color: #005266;
        }
        input[type=range] {
            width: 100%;
            height: 20px;
            -webkit-appearance: none;
            margin-bottom: 10px;
            padding: 10px;
        }
        input[type=range]:focus {
            outline: none;
        }
        input[type=range]::-webkit-slider-runnable-track {
            width: 95%;
            height: 4px;
            cursor: pointer;
            background: #555555;
            border-radius: 3px;
            padding: 10px;
        }
        input[type=range]::-webkit-slider-thumb {
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #008CBA;
            cursor: pointer;
            -webkit-appearance: none;
            margin-top: -8px;
            padding: 10px;
        }
        input[type=range]:focus::-webkit-slider-runnable-track {
            background: #666666;
        }
        .advice {
                display: none;
                position: absolute;
                background-color: black;
                border: 1px solid #ccc;
                padding: 10px;
                z-index: 1;
            }
            
            .label:hover .advice {
                display: block;
            }
    </style>
</head>
<body style="font-family: 'Comfortaa', monospace">
    <div class="sidebar">
        <a href="/">Home</a>
        <a href="/signup">Sign Up</a>
        <a href="/what_is_3bytes">What is 3bytes</a>
    </div>
    <div class="content">
    <form method="post">
            <div class="label">
                <label for="email">Email:</label>
                <span class="icon" style='color:lightblue'>?</span>
                <div class="advice">
                    <p>Your email address; this is where the newsletter will be sent</p>
                </div>
            </div>
            <input type="text" id="email" name="email" style='background-color:grey'><br><br>

            <div class="label">
                <label for="subjects">Subjects:</label>
                <span class="icon" style='color:lightblue'>?</span>
                <div class="advice">
                    <p>What your newsletter will be about. These should be separated by commas, e.g chess,politics</p>
                </div>
            </div>
            <input type="text" id="subjects" name="subjects" style='background-color:grey'><br><br>

            <div class="label">
                <label for="email_length">Email Length:</label>
                <span class="icon" style='color:lightblue'>?</span>
                <div class="advice">
                    <p>This should be a number from 1 to 5. It will determine how long your newsletter will be</p>
                </div>
            </div>
            <input type="number" id="email_length" name="email_length" style='background-color:grey'><br><br>

            <div class="label">
                <label for="days_till_next_email">Interval:</label>
                <span class="icon" style='color:lightblue'>?</span>
                <div class="advice">
                    <p>This is how many days each newsletter takes to arrive in days; '7' will mean it is delivered once a week</p>
                </div>
            </div>
            <input type="number" id="days_till_next_email" name="days_till_next_email" style='background-color:grey'><br><br>

        <input type="submit" value="Submit">
    </form>
    </div>
</body>
</html>
"""
what_is_3bytes_html = """
<!DOCTYPE html>
<html>
<head>
    <title>What is 3bytes?</title>
    <style>
        /* Add your CSS styles here */
        body {
            background-color: #333333;
            color: white;
            font-family: Arial, monospace;
            margin: 0;
            padding: 0;
        }
        /* Add more styles for the sidebar */
        .sidebar {
            background-color: #222222;
            width: 200px;
            height: 100%;
            position: fixed;
            left: 0;
            top: 0;
            overflow-x: hidden;
            padding-top: 20px;
        }
        .sidebar a {
            display: block;
            color: white;
            text-decoration: none;
            padding: 10px;
        }
        .sidebar a:hover {
            background-color: #555555;
        }
        /* Add more styles for the content */
        .content {
            margin-left: 200px;
            padding: 20px;
        }
        /* Add more styles for the forms */
        form {
            margin-bottom: 20px;
        }
        input[type=email], input[type=text], select {
            padding: 10px;
            border: none;
            border-radius: 3px;
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
            font-size: 16px;
        }
        input[type=submit] {
            background-color: #008CBA;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 10px;
            cursor: pointer;
            font-size: 16px;
        }
        input[type=submit]:hover {
            background-color: #005266;
        }
        input[type=range] {
            width: 100%;
            height: 20px;
            -webkit-appearance: none;
            margin-bottom: 10px;
        }
        input[type=range]:focus {
            outline: none;
        }
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: #555555;
            border-radius: 3px;
        }
        input[type=range]::-webkit-slider-thumb {
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #008CBA;
            cursor: pointer;
            -webkit-appearance: none;
            margin-top: -8px;
        }
        input[type=range]:focus::-webkit-slider-runnable-track {
            background: #666666;
        }
    </style>
</head>
<body style="font-family: 'Comfortaa', monospace">
    <div class="sidebar">
        <a href="/">Home</a>
        <a href="/signup">Sign Up</a>
        <a href="/what_is_3bytes">What is 3bytes</a>
    </div>
    <div class="content">
        <h1>So, what is 3bytes?</h1>
        <p>3bytes is an AI generated Email Newsletter. It can be on any subject or subjects, sent at any interval and can be any length. Sign up to 3bytes today and get a quality newsletter whenever you want it, tailored just for you! To signup, visit the 'Sign Up' page and enter your email and the details of your personalised newsletter.</p>
    </div>
</body>
</html>
"""
added_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Signup Complete!</title>
    <style>
        /* Add your CSS styles here */
        body {{
            background-color: #333333;
            color: white;
            font-family: Arial, monospace;
            margin: 0;
            padding: 0;
        }}
        /* Add more styles for the sidebar */
        .sidebar {{
            background-color: #222222;
            width: 200px;
            height: 100%;
            position: fixed;
            left: 0;
            top: 0;
            overflow-x: hidden;
            padding-top: 20px;
        }}
        .sidebar a {{
            display: block;
            color: white;
            text-decoration: none;
            padding: 10px;
        }}
        .sidebar a:hover {{
            background-color: #555555;
        }}
        /* Add more styles for the content */
        .content {{
            margin-left: 200px;
            padding: 20px;
        }}
        /* Add more styles for the forms */
        form {{
            margin-bottom: 20px;
        }}
        input[type=email], input[type=text], select {{
            padding: 10px;
            border: none;
            border-radius: 3px;
            margin-bottom: 10px;
            width: 100%;
            box-sizing: border-box;
            font-size: 16px;
        }}
        input[type=submit] {{
            background-color: #008CBA;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 10px;
            cursor: pointer;
            font-size: 16px;
        }}
        input[type=submit]:hover {{
            background-color: #005266;
        }}
        input[type=range] {{
            width: 100%;
            height: 20px;
            -webkit-appearance: none;
            margin-bottom: 10px;
        }}
        input[type=range]:focus {{
            outline: none;
        }}
        input[type=range]::-webkit-slider-runnable-track {{
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: #555555;
            border-radius: 3px;
        }}
        input[type=range]::-webkit-slider-thumb {{
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #008CBA;
            cursor: pointer;
            -webkit-appearance: none;
            margin-top: -8px;
        }}
        input[type=range]:focus::-webkit-slider-runnable-track {{
            background: #666666;
        }}
    </style>
</head>
<body style="font-family: 'Comfortaa', monospace">
    <div class="sidebar">
        <a href="/">Home</a>
        <a href="/signup">Sign Up</a>
        <a href="/what_is_3bytes">What is 3bytes</a>
    </div>
    <div class="content">
        <h1>Signup Complete!</h1>
        <p>You are now signed up for 3bytes! Your first newsletter will arrive in {days} days! In the meantime, a welcome email should arrive in your inbox soon. Make sure to check that it didn't go into your spam folder; if it did, all 3bytes newsletters may also appear in your spam unless you mark it as not spam!</p>
    </div>
</body>
</html>
"""

#FLASK
@app.route("/")
def index():
    return index_html

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        subjects = request.form['subjects']
        email_length = request.form['email_length']
        days_till_next_email = request.form['days_till_next_email']
        email_length = int(email_length)
        if email_length < -2:
            email_length = -2
        elif email_length > 2:
            email_length = 2
        email_length = email_length - 3
        with open('emails.csv', mode='a') as file:
            writer = csv.writer(file)
            writer.writerow([
                email,
                subjects.replace(" ", "+"), email_length, days_till_next_email,
                1
            ])
        welcomeemail(email)
        return added_html.format(days=days_till_next_email)
    return signup_html

@app.route("/what_is_3bytes")
def what_is_3bytes():
    return what_is_3bytes_html
  
#MAINLOOP
app.run("0.0.0.0")
