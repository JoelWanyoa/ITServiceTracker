from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import ServiceRequest

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    department = forms.CharField(max_length=100, required=True, help_text="Department the user belongs to")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'department', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create or update UserProfile
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.department = self.cleaned_data['department']
            profile.save()
        return user

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['department', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows':4})
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Make department optional, but pre-populate if user has a profile
        self.fields['department'].required = False
        if user and hasattr(user, 'profile') and user.profile.department:
            self.fields['department'].initial = user.profile.department
