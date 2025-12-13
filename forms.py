


#importing libraries
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField, BooleanField, SubmitField, FloatField
from wtforms.validators import InputRequired, Length, EqualTo, NumberRange


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=6, max=24)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=32)])
    confirm_password = PasswordField('confirm password', validators=[InputRequired(), EqualTo('password')])
    is_admin = BooleanField('admin') #optional creation of admin
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=6, max=24)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=32)])
    submit = SubmitField('Register')

class PatientForm(FlaskForm):
    gender = SelectField('gender', choices=[('Male', 'male'), ('Female', 'female'), ('Other', 'other')])
    age = IntegerField('age', validators=[InputRequired(), NumberRange(min=13, max=130)])
    hypertension = IntegerField('hypertension', validators=[InputRequired(), NumberRange(min=0, max=1)])
    ever_married = SelectField('ever_married', choices=[('Yes', 'yes'), ('No', 'no')])
    work_type = SelectField('work_type', choices=[('Private', 'private'), ('Self-employed', 'self-employed'), ('Govt_job', 'govt_job')])
    heart_disease = IntegerField('heart_disease', validators=[InputRequired(), NumberRange(min=0, max=1)])  
    avg_glucose_level = FloatField('avg_glucose_level', validators=[InputRequired(), NumberRange(min=50, max=400)])
    Residence_type = SelectField('Residence_type', choices=[('Urban', 'urban'), ('Rural', 'rural')])
    bmi = FloatField('bmi', validators=[InputRequired(), NumberRange(min=10, max=200)])
    smoking_status = SelectField('smoking_status', choices=[('formerly smoked', 'formerly smoked'), ('never smoked', 'never smoked'), ('smokes', 'smokes')])
    stroke = IntegerField('stroke', validators=[InputRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('Submit Patient')

    