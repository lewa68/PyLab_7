import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, BooleanField, FileField, RadioField
from wtforms.validators import DataRequired, Email
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mars-mission-secret-key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'galery')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def load_crew():
    with open('members/crew.json', 'r', encoding='utf-8') as f:
        return json.load(f)

class AstronautForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    education = StringField('Образование', validators=[DataRequired()])
    main_profession = SelectField('Основная профессия', choices=[
        'инженер-исследователь', 'пилот', 'строитель', 'экзобиолог', 'врач',
        'инженер по терраформированию', 'климатолог', 'специалист по радиационной защите',
        'астрогеолог', 'гляциолог', 'инженер жизнеобеспечения', 'метеоролог',
        'оператор марсохода', 'киберинженер', 'штурман', 'пилот дронов'
    ], validators=[DataRequired()])
    sex = RadioField('Пол', choices=[('male', 'Мужской'), ('female', 'Женский')], validators=[DataRequired()])
    motivation = TextAreaField('Мотивация', validators=[DataRequired()])
    stay_on_mars = BooleanField('Готовы ли остаться на Марсе?')
    photo = FileField('Фото', validators=[DataRequired()])
    submit = BooleanField('Отправить', default=True)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/list_prof/<list_type>')
def list_prof(list_type):
    professions = [
        "Пилот", "Инженер-исследователь", "Строитель", "Экзобиолог", "Врач",
        "Инженер по терраформированию", "Климатолог", "Специалист по радиационной защите",
        "Астрогеолог", "Гляциолог"
    ]
    return render_template('list_prof.html', list_type=list_type, professions=professions)

@app.route('/distribution')
def distribution():
    crew = load_crew()
    return render_template('distribution.html', crew=crew)

@app.route('/member/<int:number>')
@app.route('/member/random')
def member(number=None):
    crew = load_crew()
    if request.url_rule.rule.endswith('random'):
        return render_template('member.html', number='random', crew=crew)
    else:
        return render_template('member.html', number=number, crew=crew)

@app.route('/room/<sex>/<int:age>')
def room(sex, age):
    return render_template('room.html', sex=sex, age=age)

@app.route('/astronaut_selection', methods=['GET', 'POST'])
def astronaut_selection():
    form = AstronautForm()
    if form.validate_on_submit():
        surname = form.surname.data
        name = form.name.data
        email = form.email.data
        education = form.education.data
        main_profession = form.main_profession.data
        sex = form.sex.data
        motivation = form.motivation.data
        stay = form.stay_on_mars.data
        photo = form.photo.data
        filename = secure_filename(photo.filename)
        temp_path = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        photo.save(temp_path)

        msg = MIMEMultipart()
        msg['From'] = 'your_email@gmail.com'
        msg['To'] = email
        msg['Subject'] = 'Заявка на миссию на Марс'
        body = f"Фамилия: {surname}\nИмя: {name}\nEmail: {email}\nОбразование: {education}\nПрофессия: {main_profession}\nПол: {sex}\nМотивация: {motivation}\nОстаться на Марсе: {'Да' if stay else 'Нет'}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with open(temp_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(part)

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('your_email@gmail.com', 'your_app_password')
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
            flash('Заявка отправлена!', 'success')
        except Exception:
            flash('Ошибка отправки', 'danger')
        finally:
            os.remove(temp_path)

        return redirect(url_for('astronaut_selection'))

    return render_template('astronaut_selection.html', form=form)

@app.route('/galery', methods=['GET', 'POST'])
def galery():
    if request.method == 'POST':
        file = request.files['photo']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('galery'))
    images = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return render_template('galery.html', images=images)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)