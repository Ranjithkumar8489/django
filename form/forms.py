from django import forms
from .models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(required=False,widget=forms.TextInput(attrs={'class':'form-control my-2','placeholder':'Enter Username','autocomplete':'off'}))
    email = forms.EmailField(required=False,widget=forms.EmailInput(attrs={'class':'form-control my-2','placeholder':'Enter Email Address','autocomplete':'off'}))
    password = forms.CharField(required=False,widget=forms.PasswordInput(attrs={'class':'form-control my-2','placeholder':'Enter Password','autocomplete':'off'}))
    confirm_password = forms.CharField(required=False,widget=forms.PasswordInput(attrs={'class':'form-control my-2','placeholder':'Enter confirm Password','autocomplete':'off'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('Username field is empty. Please enter a username.')
        if not username.isalpha():
            raise ValidationError('Username should contain only letters.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Email field is empty. Please enter an email address.')
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError('Enter a valid email address.')
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already in use.')
        
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError("Enter the password")
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        return password
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if not confirm_password:
            raise ValidationError("Enter the confirm password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match.')
        
        return confirm_password


class LoginForm(forms.Form):
    email = forms.EmailField(required=False,widget=forms.EmailInput(attrs={'class': 'form-control my-2', 'placeholder': 'Enter your email', 'autocomplete': 'off'}))
    password = forms.CharField(required=False,widget=forms.PasswordInput(attrs={'class': 'form-control my-2', 'placeholder': 'Enter your password', 'autocomplete': 'off'}))
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Email field is empty. Please enter your email.')
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError('Enter a valid email address.')
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('Password field is empty. Please enter your password.')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        return password
