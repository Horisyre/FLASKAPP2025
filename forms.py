from flask_wtf import FlaskForm
from wtforms import HiddenField,Form,SubmitField, StringField, PasswordField, validators, EmailField, IntegerField, DateField,SelectField
from wtforms.validators import DataRequired,Email,Optional

class loginForm(FlaskForm):
    usernumber = StringField("usernumber",validators=[DataRequired()])
    userpassword =StringField("userpassword",validators=[DataRequired()])
    submit= SubmitField("Login")

class Customerform(FlaskForm):
    CustPhoneNo = StringField("CustPhoneNo",validators=[DataRequired()])
    CustomerName =StringField("CustomerName",validators=[DataRequired()])
    TechNo= IntegerField("TechNo", validators=[DataRequired()])
    date =  DateField("date", format='%Y-%m-%d', validators=[DataRequired()])
    CustomerEmail = StringField("CustomerEmail",validators=[Optional(),Email()])
    CustomerDevice = StringField("CustomerDevice",validators=[Optional()])
    CustAddress =StringField("CustAddress",validators=[Optional()])
    fault= StringField("fault",validators=[Optional()])
    submit= SubmitField("submit")

class CroSubmitForm(FlaskForm):
    CroNo= StringField("CroNo",validators=[DataRequired()])
    Fetch= SubmitField("Fetch")

class CroAlterForm(FlaskForm):
    CRO_number= StringField("CRO_number",validators=[DataRequired()])
    CustPhoneNo = StringField("CustPhoneNo",validators=[DataRequired()])
    CustomerName =StringField("CustomerName",validators=[DataRequired()])
    CustomerEmail = StringField("CustomerEmail",validators=[Optional(),Email()])
    CustAddress =StringField("CustAddress",validators=[Optional()])
    Purchased_Items=StringField("Purchased_Items",validators=[Optional()])
    Purchased_Items_Cost=StringField("Purchased_Items_Cost",validators=[Optional()])
    submit= SubmitField("Alter")


class completionForm(FlaskForm):
    #create a custom validator for CRO hidden field
    diagnostics=StringField("diagnostics",validators= [DataRequired()])
    Purchased_Items=StringField("Purchased_Items", validators=[Optional()])
    Purchased_Items_Cost=StringField("Purchased_Items_Cost", validators=[Optional()])
    #add validator for dropdownlist
    RepairType=SelectField("RepairType",choices=[
            ('01', 'Base Troubleshooting'),
            ('02', 'Hardware Installation'),
            ('03', 'Data Recovery'),
            ('04', 'Operating System Repair'),
            ('05', 'Printer Setup'),
            ('06', 'Virus Removal'),
            ('07', 'Software Installation')],
     validators=[DataRequired()]
    )
    submit=SubmitField("submit")

class completeform(FlaskForm):
    CRO_number=StringField("CRO_number",validators=[DataRequired()])
    submit=SubmitField("submit")

class CroAlertForm(FlaskForm):
    Tech_number=StringField("Tech_number",[DataRequired()])
    Fetch=SubmitField("Fetch")
